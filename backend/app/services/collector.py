"""데이터 수집, 정규화, 피처 생성 파이프라인"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    FieldMaster, WeatherHourly, SoilSnapshot, PestOccurrence,
    FeatureDaily, RiskScoreDaily, RecommendationCard,
    SourceMaster, RawApiLog,
)
from app.services.api_clients import FarmmapClient, KmaClient
from app.services.nongsaro_client import NongsaroClient
from app.services.soil_api_client import SoilApiClient
from app.services.risk_engine import (
    calc_weather_risk, calc_surveillance_risk, calc_soil_vulnerability,
    calc_crop_stage_risk, calc_final_risk, risk_level,
)
from app.services.explanation import generate_explanation
from app.services.alert_engine import AlertEngine
from app.services.crop_registry import get_target_pests


def parse_obs_time(obsr_tm: str) -> datetime:
    return datetime.strptime(obsr_tm[:12], "%Y%m%d%H%M")


class DataCollector:
    def __init__(self):
        self.farmmap = FarmmapClient()
        self.kma = KmaClient()
        self.nongsaro = NongsaroClient()
        self.soil_api = SoilApiClient()

    async def collect_all(self, session: AsyncSession, field_id: int) -> dict:
        field = await session.get(FieldMaster, field_id)
        if not field:
            raise ValueError(f"field {field_id} not found")

        weather_count = await self._collect_weather(session, field)
        kma_data = await self._collect_kma(session, field)
        soil_ok = await self._collect_soil(session, field)
        soil_v2_ok = await self._collect_soil_v2(session, field)
        pest_count = await self._collect_pests(session, field)
        nongsaro_ok = await self._collect_nongsaro(session, field)
        fert_ok = await self._collect_fertilizer(session, field)
        features = await self._build_features(session, field)
        risks = await self._compute_risks(session, field)
        alerts = await self._evaluate_alerts(session, field, risks, kma_data)

        return {
            "field_id": field_id,
            "weather_records": weather_count,
            "kma_collected": bool(kma_data.get("ncst")),
            "soil_collected": soil_ok,
            "soil_v2_collected": soil_v2_ok,
            "pest_records": pest_count,
            "nongsaro_collected": nongsaro_ok,
            "fertilizer_collected": fert_ok,
            "features": features,
            "risks": risks,
            "alerts_created": len(alerts),
        }

    async def _log_api(self, session, source_name, field_id, endpoint, params, body, status):
        src = await session.execute(
            select(SourceMaster).where(SourceMaster.source_name == source_name)
        )
        source = src.scalar_one_or_none()
        if source:
            source.last_called_at = datetime.utcnow()
            source.last_status = "success" if status == 200 else "error"
        session.add(RawApiLog(
            source_id=source.source_id if source else None,
            field_id=field_id, endpoint=endpoint,
            request_params=params, response_body=body, status_code=status,
        ))

    async def _collect_weather(self, session: AsyncSession, field: FieldMaster) -> int:
        today = date.today()
        items = await self.farmmap.fetch_weather_hourly(field.position_x, field.position_y, today)
        await self._log_api(session, "팜맵 농업기상", field.field_id,
                            "getCoordinateBasedHourFarmimgWeatherInfo",
                            {"x": field.position_x, "y": field.position_y}, {"count": len(items)}, 200)

        count = 0
        for item in items:
            obs = parse_obs_time(item["obsrTm"])
            existing = await session.execute(
                select(WeatherHourly).where(
                    WeatherHourly.field_id == field.field_id,
                    WeatherHourly.obs_time == obs,
                )
            )
            if existing.scalar_one_or_none():
                continue
            session.add(WeatherHourly(
                field_id=field.field_id, obs_time=obs,
                temperature=float(item.get("tp150") or 0),
                humidity=float(item.get("hd150") or 0),
                rainfall=float(item.get("afp") or 0),
                wind_speed=float(item.get("ws150") or 0),
                soil_moisture=float(item.get("sm10") or 0),
                dew_time=float(item.get("dwcnTime") or 0),
            ))
            count += 1
        return count

    async def _collect_kma(self, session: AsyncSession, field: FieldMaster) -> dict:
        if not field.kma_nx or not field.kma_ny:
            return {"ncst": {}, "ultra_fcst": [], "vilage_fcst": []}
        ncst = await self.kma.fetch_ultra_nowcast(field.kma_nx, field.kma_ny)
        fcst = await self.kma.fetch_ultra_forecast(field.kma_nx, field.kma_ny)
        vilage = await self.kma.fetch_vilage_forecast(field.kma_nx, field.kma_ny)
        await self._log_api(session, "기상청 단기예보", field.field_id,
                            "getUltraSrtNcst+getVilageFcst",
                            {"nx": field.kma_nx, "ny": field.kma_ny},
                            {"ncst": ncst, "fcst_count": len(fcst), "vilage_count": len(vilage)}, 200)
        return {"ncst": ncst, "ultra_fcst": fcst, "vilage_fcst": vilage}

    async def _collect_soil_v2(self, session: AsyncSession, field: FieldMaster) -> bool:
        if not field.pnu_code:
            return False
        data = await self.soil_api.soil_chem_v2(field.pnu_code)
        await self._log_api(session, "토양검정 V2", field.field_id,
                            "getSoilExam", {"PNU_CD": field.pnu_code},
                            {"count": len(data.get("items") or []), "code": data.get("result_code")}, 200)
        return bool(data.get("items"))

    async def _collect_nongsaro(self, session: AsyncSession, field: FieldMaster) -> bool:
        data = await self.nongsaro.dbyhs_list(search_text=field.crop_name)
        await self._log_api(session, "농사로 병해충발생", field.field_id,
                            "dbyhsCccrrncInfoList", {"crop": field.crop_name},
                            {"count": len(data.get("items") or [])}, 200)
        pest = await self.nongsaro.pesticide_reg_list(field.crop_name)
        await self._log_api(session, "농사로 농약등록", field.field_id,
                            "pesticideRegStatusList", {"crop": field.crop_name},
                            {"count": len(pest.get("items") or [])}, 200)
        return bool(data.get("items") or pest.get("items"))

    async def _collect_fertilizer(self, session: AsyncSession, field: FieldMaster) -> bool:
        if not field.pnu_code:
            return False
        data = await self.soil_api.fertilizer_prescription(field.pnu_code, field.crop_name)
        endpoint = (
            "getSoilFrtlzrExamRiceInfo" if field.crop_name == "벼"
            else "getSoilFrtlzrExamInfo"
        )
        await self._log_api(session, "비료사용처방", field.field_id,
                            endpoint, {"crop": field.crop_name, "pnu": field.pnu_code},
                            {"items": len(data.get("items") or []), "code": data.get("result_code")}, 200)
        return bool(data.get("items"))

    async def _collect_soil(self, session: AsyncSession, field: FieldMaster) -> bool:
        data = await self.farmmap.fetch_soil(field.position_x, field.position_y)
        await self._log_api(session, "팜맵 토양검정", field.field_id,
                            "getCoordinateBasedSoilAnalsInfo", {}, data, 200)
        if not data:
            return False
        session.add(SoilSnapshot(
            field_id=field.field_id,
            sample_year=int(data.get("pickYr") or date.today().year),
            acidity=float(data.get("acidity") or 6.5),
            organic_matter=float(data.get("ormtCont") or 2.5),
            available_phosphate=float(data.get("vdphdy") or 100),
            ec=float(data.get("ecd") or 0.5),
            potassium=float(data.get("rlfzKlusq") or 0.4),
            magnesium=float(data.get("rlfzMgusq") or 1.0),
            lime_requirement=float(data.get("lreq") or 0),
        ))
        return True

    async def _collect_pests(self, session: AsyncSession, field: FieldMaster) -> int:
        year = date.today().year
        items = await self.farmmap.fetch_pests(field.position_x, field.position_y, year)
        await self._log_api(session, "팜맵 병해충발생", field.field_id,
                            "getCoordinateBasedYearDbyhsInfo", {"year": year},
                            {"count": len(items)}, 200)

        await session.execute(delete(PestOccurrence).where(PestOccurrence.field_id == field.field_id))
        for item in items:
            report = item.get("inptDe", date.today().strftime("%Y%m%d"))
            session.add(PestOccurrence(
                field_id=field.field_id,
                pest_name=item.get("dbyhsNm", ""),
                crop_name=item.get("crpTynm", field.crop_name),
                occurrence_value=float(item.get("iqVl") or 0),
                occurrence_distance=float(item.get("ocrdst") or 3),
                report_date=datetime.strptime(str(report)[:8], "%Y%m%d").date(),
            ))
        return len(items)

    async def _build_features(self, session: AsyncSession, field: FieldMaster) -> dict:
        today = date.today()
        since = datetime.combine(today - timedelta(days=1), datetime.min.time())

        result = await session.execute(
            select(WeatherHourly).where(
                WeatherHourly.field_id == field.field_id,
                WeatherHourly.obs_time >= since,
            ).order_by(WeatherHourly.obs_time)
        )
        rows = result.scalars().all()

        if not rows:
            return {}

        rain_6h = sum(r.rainfall or 0 for r in rows[-6:])
        humidity_24h = sum(r.humidity or 0 for r in rows) / len(rows)
        dew_24h = sum(r.dew_time or 0 for r in rows)
        temps = [r.temperature or 20 for r in rows]
        soil_avg = sum(r.soil_moisture or 0 for r in rows) / len(rows)

        soil_result = await session.execute(
            select(SoilSnapshot).where(SoilSnapshot.field_id == field.field_id)
            .order_by(SoilSnapshot.sample_year.desc()).limit(1)
        )
        soil = soil_result.scalar_one_or_none()
        soil_risk, _ = calc_soil_vulnerability(
            soil.acidity if soil else 6.5,
            soil.organic_matter if soil else 2.5,
            soil.ec if soil else 0.5,
            soil.available_phosphate if soil else 100,
        )

        pest_result = await session.execute(
            select(PestOccurrence).where(PestOccurrence.field_id == field.field_id)
        )
        pests = [
            {
                "pest_name": p.pest_name, "occurrence_value": p.occurrence_value,
                "occurrence_distance": p.occurrence_distance,
                "crop_name": p.crop_name,
                "days_since_report": (today - p.report_date).days if p.report_date else 7,
            }
            for p in pest_result.scalars().all()
        ]
        pest_prior, _ = calc_surveillance_risk(pests, field.crop_name)

        feat = FeatureDaily(
            field_id=field.field_id, date=today,
            rain_6h=rain_6h, humidity_24h=humidity_24h,
            dew_time_24h=dew_24h, temp_min=min(temps), temp_max=max(temps),
            soil_moisture_avg=soil_avg, soil_risk_index=soil_risk,
            pest_prior_score=pest_prior,
        )
        existing = await session.execute(
            select(FeatureDaily).where(FeatureDaily.field_id == field.field_id, FeatureDaily.date == today)
        )
        old = existing.scalar_one_or_none()
        if old:
            for k in ["rain_6h", "humidity_24h", "dew_time_24h", "temp_min", "temp_max",
                      "soil_moisture_avg", "soil_risk_index", "pest_prior_score"]:
                setattr(old, k, getattr(feat, k))
        else:
            session.add(feat)

        return {
            "rain_6h": rain_6h, "humidity_24h": humidity_24h,
            "dew_time_24h": dew_24h, "soil_risk_index": soil_risk,
        }

    async def _compute_risks(self, session: AsyncSession, field: FieldMaster) -> list[dict]:
        today = date.today()
        feat_result = await session.execute(
            select(FeatureDaily).where(FeatureDaily.field_id == field.field_id, FeatureDaily.date == today)
        )
        feat = feat_result.scalar_one_or_none()
        if not feat:
            return []

        weather_risk, weather_factors = calc_weather_risk(
            rain_6h=feat.rain_6h or 0, humidity_24h=feat.humidity_24h or 50,
            dew_time_24h=feat.dew_time_24h or 0, temp_min=feat.temp_min or 15,
            temp_max=feat.temp_max or 25, soil_moisture=feat.soil_moisture_avg or 20,
        )
        soil_risk = feat.soil_risk_index or 0
        crop_risk = calc_crop_stage_risk(field.planting_date, crop_name=field.crop_name)

        pest_result = await session.execute(
            select(PestOccurrence).where(PestOccurrence.field_id == field.field_id)
        )
        all_pests = pest_result.scalars().all()
        soil_result = await session.execute(
            select(SoilSnapshot).where(SoilSnapshot.field_id == field.field_id)
            .order_by(SoilSnapshot.sample_year.desc()).limit(1)
        )
        soil = soil_result.scalar_one_or_none()
        _, soil_factors = calc_soil_vulnerability(
            soil.acidity if soil else 6.5, soil.organic_matter if soil else 2.5,
            soil.ec if soil else 0.5, soil.available_phosphate if soil else 100,
        )

        target_pests = get_target_pests(field.crop_name)
        results = []
        for pest_name in target_pests:
            pest_rows = [p for p in all_pests if p.pest_name == pest_name]
            pest_dicts = [
                {
                    "pest_name": p.pest_name, "occurrence_value": p.occurrence_value,
                    "occurrence_distance": p.occurrence_distance,
                    "crop_name": p.crop_name,
                    "days_since_report": (today - p.report_date).days if p.report_date else 7,
                }
                for p in pest_rows
            ]
            if not pest_dicts:
                pest_risk = feat.pest_prior_score * 0.5
                pest_details = []
            else:
                pest_risk, pest_details = calc_surveillance_risk(pest_dicts, field.crop_name)

            nongsaro_news = (await self.nongsaro.dbyhs_list(search_text=pest_name)).get("items") or []
            pesticide = (await self.nongsaro.pesticide_reg_list(field.crop_name, pest_name)).get("items") or []

            final = calc_final_risk(weather_risk, pest_risk, soil_risk, crop_risk)
            level = risk_level(final)

            existing = await session.execute(
                select(RiskScoreDaily).where(
                    RiskScoreDaily.field_id == field.field_id,
                    RiskScoreDaily.date == today,
                    RiskScoreDaily.pest_name == pest_name,
                )
            )
            row = existing.scalar_one_or_none()
            if row:
                row.weather_risk, row.pest_risk, row.soil_risk = weather_risk, pest_risk, soil_risk
                row.crop_stage_risk, row.final_risk, row.risk_level = crop_risk, final, level
            else:
                session.add(RiskScoreDaily(
                    field_id=field.field_id, date=today, pest_name=pest_name,
                    weather_risk=weather_risk, pest_risk=pest_risk, soil_risk=soil_risk,
                    crop_stage_risk=crop_risk, final_risk=final, risk_level=level,
                ))

            expl = generate_explanation(
                field.crop_name, pest_name, final, level,
                weather_factors, pest_details, soil_factors,
                nongsaro_news=nongsaro_news,
                pesticide_items=pesticide,
            )

            rec_existing = await session.execute(
                select(RecommendationCard).where(
                    RecommendationCard.field_id == field.field_id,
                    RecommendationCard.pest_name == pest_name,
                ).order_by(RecommendationCard.created_at.desc()).limit(1)
            )
            rec_row = rec_existing.scalar_one_or_none()
            if rec_row:
                rec_row.risk_score = final
                rec_row.title = expl["title"]
                rec_row.reason = expl["reason"]
                rec_row.action_list = expl["action_list"]
                rec_row.source_refs = expl["source_refs"]
            else:
                session.add(RecommendationCard(
                    field_id=field.field_id, pest_name=pest_name,
                    risk_score=final, title=expl["title"],
                    reason=expl["reason"], action_list=expl["action_list"],
                    source_refs=expl["source_refs"],
                ))

            results.append({
                "pest_name": pest_name, "final_risk": final,
                "risk_level": level, "weather_risk": weather_risk,
                "pest_risk": pest_risk, "soil_risk": soil_risk,
            })

        return results

    async def _evaluate_alerts(
        self,
        session: AsyncSession,
        field: FieldMaster,
        risks: list[dict],
        kma_data: dict,
    ) -> list[dict]:
        today = date.today()
        feat_result = await session.execute(
            select(FeatureDaily).where(FeatureDaily.field_id == field.field_id, FeatureDaily.date == today)
        )
        feat = feat_result.scalar_one_or_none()
        pest_result = await session.execute(
            select(PestOccurrence).where(PestOccurrence.field_id == field.field_id)
        )
        pests = pest_result.scalars().all()

        trend = []
        for d in range(6, -1, -1):
            dt = today - timedelta(days=d)
            tr = await session.execute(
                select(func.avg(RiskScoreDaily.final_risk)).where(
                    RiskScoreDaily.field_id == field.field_id,
                    RiskScoreDaily.date == dt,
                )
            )
            avg = tr.scalar() or 0
            trend.append({"date": dt.isoformat(), "avg_risk": round(float(avg), 1)})

        return await AlertEngine().evaluate(
            session, field,
            risks=risks,
            feat=feat,
            pests=pests,
            ultra_fcst=kma_data.get("ultra_fcst") or [],
            vilage_fcst=kma_data.get("vilage_fcst") or [],
            trend=trend,
        )
