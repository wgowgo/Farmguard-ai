"""알림 생성 엔진 — 설정, 중복 방지, 4종 규칙 + 주간 리포트"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertEvent, AlertSettings, FieldMaster, FeatureDaily, PestOccurrence
from app.services.forecast import build_spray_timing_from_kma, build_weekly_report, build_forecast_7d
from app.services.crop_registry import get_target_pests


class AlertEngine:
    async def evaluate(
        self,
        session: AsyncSession,
        field: FieldMaster,
        *,
        risks: list[dict],
        feat: FeatureDaily | None,
        pests: list[PestOccurrence],
        ultra_fcst: list[dict] | None = None,
        vilage_fcst: list[dict] | None = None,
        trend: list[dict] | None = None,
    ) -> list[dict]:
        settings = await self._get_settings(session, field.user_id)
        created: list[dict] = []

        if settings.risk_rise:
            created.extend(await self._risk_rise(session, field, risks, settings))

        if settings.rain_before_spray and ultra_fcst:
            a = await self._rain_before_spray(session, field, ultra_fcst, settings)
            if a:
                created.append(a)

        if settings.high_humidity:
            a = await self._high_humidity(session, field, feat, ultra_fcst, settings)
            if a:
                created.append(a)

        if settings.nearby_pest:
            created.extend(await self._nearby_pest(session, field, pests, settings))

        if settings.weekly_report:
            a = await self._weekly_report(session, field, risks, trend or [], settings)
            if a:
                created.append(a)

        return created

    async def _get_settings(self, session: AsyncSession, user_id: int) -> AlertSettings:
        result = await session.execute(
            select(AlertSettings).where(AlertSettings.user_id == user_id)
        )
        s = result.scalar_one_or_none()
        if s:
            return s
        return AlertSettings(user_id=user_id)

    async def _already_today(
        self, session: AsyncSession, field_id: int, alert_type: str, keyword: str = "",
    ) -> bool:
        today = date.today()
        q = select(func.count(AlertEvent.id)).where(
            AlertEvent.field_id == field_id,
            AlertEvent.alert_type == alert_type,
            func.date(AlertEvent.created_at) == today,
        )
        if keyword:
            q = q.where(AlertEvent.title.contains(keyword))
        count = (await session.execute(q)).scalar() or 0
        return count > 0

    async def _emit(
        self,
        session: AsyncSession,
        field_id: int,
        alert_type: str,
        title: str,
        message: str,
    ) -> dict:
        event = AlertEvent(
            field_id=field_id,
            alert_type=alert_type,
            title=title,
            message=message,
            status="sent",
            sent_at=datetime.utcnow(),
        )
        session.add(event)
        return {"type": alert_type, "title": title, "message": message}

    async def _risk_rise(
        self, session: AsyncSession, field: FieldMaster, risks: list[dict], _settings: AlertSettings,
    ) -> list[dict]:
        out = []
        for r in risks:
            if (r.get("final_risk") or 0) < 70:
                continue
            pest = r.get("pest_name", "")
            if await self._already_today(session, field.field_id, "risk_rise", pest):
                continue
            level = r.get("risk_level", "위험")
            out.append(await self._emit(
                session, field.field_id, "risk_rise",
                f"{pest} 위험 경보",
                f"{pest} 위험도 {r['final_risk']:.0f}점({level}). 즉시 예찰, 방제 검토가 필요합니다.",
            ))
        return out

    async def _rain_before_spray(
        self, session: AsyncSession, field: FieldMaster, ultra_fcst: list[dict], _settings: AlertSettings,
    ) -> dict | None:
        if await self._already_today(session, field.field_id, "rain_before_spray"):
            return None

        now = datetime.now()
        rain_fcst: datetime | None = None
        rain_pop = 0.0
        for item in ultra_fcst:
            if item.get("category") != "POP":
                continue
            t = item.get("fcstTime", "")
            if len(t) < 12:
                continue
            try:
                fcst_dt = datetime.strptime(t[:12], "%Y%m%d%H%M")
                pop = float(item.get("fcstValue", 0))
            except (TypeError, ValueError):
                continue
            hours_ahead = (fcst_dt - now).total_seconds() / 3600
            if 0 <= hours_ahead <= 6 and pop >= 60:
                if rain_fcst is None or hours_ahead < (rain_fcst - now).total_seconds() / 3600:
                    rain_fcst = fcst_dt
                    rain_pop = pop

        spray = build_spray_timing_from_kma(ultra_fcst)
        rain_hour: int | None = rain_fcst.hour if rain_fcst else None
        if rain_hour is None:
            for h in spray.get("hourly", []):
                if h.get("rain_prob", 0) >= 60 and 0 <= h["hour"] - now.hour <= 6:
                    rain_hour = h["hour"]
                    rain_pop = h["rain_prob"]
                    break

        if rain_hour is None:
            return None

        return await self._emit(
            session, field.field_id, "rain_before_spray",
            "강우 전 방제 알림",
            f"{rain_hour:02d}:00경 강수 가능성 {rain_pop:.0f}%. "
            f"6시간 내 방제 시 {spray.get('summary', '일정 조정을 권장합니다.')}",
        )

    async def _high_humidity(
        self,
        session: AsyncSession,
        field: FieldMaster,
        feat: FeatureDaily | None,
        ultra_fcst: list[dict] | None,
        _settings: AlertSettings,
    ) -> dict | None:
        if await self._already_today(session, field.field_id, "high_humidity"):
            return None

        humidity = feat.humidity_24h if feat else 0
        peak_reh = 0.0
        peak_hour: int | None = None
        if ultra_fcst:
            for item in ultra_fcst:
                if item.get("category") != "REH":
                    continue
                try:
                    reh = float(item.get("fcstValue", 0))
                    hour = int(item.get("fcstTime", "0000000000")[8:10])
                except (TypeError, ValueError):
                    continue
                if reh > peak_reh:
                    peak_reh = reh
                    peak_hour = hour

        trigger = humidity >= 80 or peak_reh >= 85
        if not trigger:
            return None

        if peak_reh >= 85 and peak_hour is not None:
            msg = f"예보 습도 최고 {peak_reh:.0f}%({peak_hour:02d}시). 결로, 병해 발생에 유의하세요."
        else:
            msg = f"24시간 평균 습도 {humidity:.0f}%. 결로, 곰팡이병 위험이 높습니다."

        return await self._emit(
            session, field.field_id, "high_humidity",
            "고습 / 결로 주의",
            msg,
        )

    async def _nearby_pest(
        self, session: AsyncSession, field: FieldMaster, pests: list[PestOccurrence], _settings: AlertSettings,
    ) -> list[dict]:
        out = []
        for p in pests:
            dist = float(p.occurrence_distance or 99)
            val = float(p.occurrence_value or 0)
            if dist > 2 or val < 40:
                continue
            if await self._already_today(session, field.field_id, "nearby_pest", p.pest_name):
                continue
            out.append(await self._emit(
                session, field.field_id, "nearby_pest",
                f"주변 {p.pest_name} 발생",
                f"반경 {dist:.1f}km 내 {p.pest_name} 발생 지수 {val:.0f}. 예찰 강화를 권장합니다.",
            ))
        return out

    async def _weekly_report(
        self,
        session: AsyncSession,
        field: FieldMaster,
        risks: list[dict],
        trend: list[dict],
        _settings: AlertSettings,
    ) -> dict | None:
        if date.today().weekday() != 0:
            return None
        if await self._already_today(session, field.field_id, "weekly_report"):
            return None

        top = risks[0] if risks else {}
        pests = get_target_pests(field.crop_name)
        default_pest = pests[0] if pests else "탄저병"
        forecast = build_forecast_7d(
            field.field_id, date.today(),
            top.get("pest_risk", 40), top.get("soil_risk", 25),
            0, top.get("pest_name", default_pest), trend,
        )
        spray = build_spray_timing_from_kma([])
        top_pests = [
            {"pest_name": r.get("pest_name"), "final_risk": r.get("final_risk"), "risk_level": r.get("risk_level")}
            for r in risks[:3]
        ]
        weekly = build_weekly_report(
            {"address": field.address, "crop_name": field.crop_name},
            forecast, spray, top_pests, None,
        )
        return await self._emit(
            session, field.field_id, "weekly_report",
            weekly["title"],
            weekly["text"][:500],
        )
