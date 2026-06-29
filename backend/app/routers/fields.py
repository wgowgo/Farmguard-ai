from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    FieldMaster, User, RiskScoreDaily, RecommendationCard,
    AlertEvent, WeatherHourly, SoilSnapshot, PestOccurrence,
    SourceMaster, AlertSettings,
)
from app.schemas import FieldCreate, FieldResponse, DashboardResponse, RiskSummary
from app.services.knowledge_service import KnowledgeService
from app.services.api_clients import FarmmapClient
from app.services.collector import DataCollector
from app.services.forecast import (
    build_forecast_7d, build_spray_timing, build_spray_timing_from_kma,
    build_map_layers, build_weekly_report, parse_vilage_daily,
)
from app.services.api_clients import KmaClient
from app.services.risk_engine import calc_crop_stage_risk
from app.services.crop_registry import get_crop_or_default, get_target_pests
from app.services.fertilizer_service import build_fertilizer_calendar
from app.services.soil_api_client import SoilApiClient
from app.services.weather_timeline import build_weather_timeline
from app.utils.coords import latlng_to_farmmap, latlng_to_kma_grid, farmmap_to_latlng

router = APIRouter(prefix="/api/fields", tags=["fields"])


def _field_coords(f: FieldMaster) -> tuple[float | None, float | None]:
    if f.lat is not None and f.lng is not None:
        return f.lat, f.lng
    if f.position_x and f.position_y:
        lng, lat = farmmap_to_latlng(f.position_x, f.position_y)
        return lat, lng
    return None, None


async def _build_field_weather_timeline(db: AsyncSession, field_id: int, f: FieldMaster) -> dict:
    weather_r = await db.execute(
        select(WeatherHourly).where(WeatherHourly.field_id == field_id)
        .order_by(WeatherHourly.obs_time.desc()).limit(48)
    )
    observed = [
        {
            "time": w.obs_time.isoformat(), "temp": w.temperature,
            "humidity": w.humidity, "rain": w.rainfall,
            "dew_time": w.dew_time,
        }
        for w in reversed(weather_r.scalars().all())
    ]
    ultra, vilage = [], []
    if f.kma_nx and f.kma_ny:
        kma = KmaClient()
        ultra = await kma.fetch_ultra_forecast(f.kma_nx, f.kma_ny)
        vilage = await kma.fetch_vilage_forecast(f.kma_nx, f.kma_ny)
    return build_weather_timeline(observed, ultra, vilage)


@router.post("", response_model=FieldResponse)
async def register_field(body: FieldCreate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, body.user_id)
    if not user:
        raise HTTPException(404, "사용자를 찾을 수 없습니다")

    px, py = latlng_to_farmmap(body.lng, body.lat)
    client = FarmmapClient()
    parcel = await client.fetch_parcel(px, py)
    if not parcel:
        raise HTTPException(404, "해당 좌표에 필지를 찾을 수 없습니다")

    nx, ny = latlng_to_kma_grid(body.lat, body.lng)
    address = f"{parcel.get('lglEmdNm', '')} {parcel.get('lnm', '')}".strip()

    crop_profile = get_crop_or_default(body.crop_name)
    field = FieldMaster(
        user_id=body.user_id,
        fmap_innb=str(parcel.get("fmapInnb", "")),
        pnu_code=parcel.get("pnuLnmCd"),
        crop_name=crop_profile["name_ko"],
        crop_code=crop_profile["id"],
        land_type=parcel.get("intprNm"),
        lat=body.lat,
        lng=body.lng,
        position_x=px, position_y=py,
        kma_nx=nx, kma_ny=ny,
        address=address or f"위도 {body.lat:.4f}, 경도 {body.lng:.4f}",
        planting_date=body.planting_date,
    )
    db.add(field)
    await db.flush()

    collector = DataCollector()
    await collector.collect_all(db, field.field_id)

    return FieldResponse(
        field_id=field.field_id,
        fmap_innb=field.fmap_innb,
        pnu_code=field.pnu_code,
        crop_name=field.crop_name,
        land_type=field.land_type,
        address=field.address,
        lat=body.lat, lng=body.lng,
        planting_date=field.planting_date,
    )


@router.get("", response_model=list[FieldResponse])
async def list_fields(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FieldMaster).where(FieldMaster.user_id == user_id).order_by(FieldMaster.created_at.desc())
    )
    fields = result.scalars().all()
    out = []
    for f in fields:
        lat, lng = _field_coords(f)
        out.append(FieldResponse(
            field_id=f.field_id, fmap_innb=f.fmap_innb, pnu_code=f.pnu_code,
            crop_name=f.crop_name, land_type=f.land_type, address=f.address,
            lat=lat, lng=lng, planting_date=f.planting_date,
        ))
    return out


@router.get("/{field_id}", response_model=FieldResponse)
async def get_field(field_id: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")
    lat, lng = _field_coords(f)
    return FieldResponse(
        field_id=f.field_id, fmap_innb=f.fmap_innb, pnu_code=f.pnu_code,
        crop_name=f.crop_name, land_type=f.land_type, address=f.address,
        lat=lat, lng=lng, planting_date=f.planting_date,
    )


@router.post("/{field_id}/collect")
async def trigger_collect(field_id: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")
    collector = DataCollector()
    result = await collector.collect_all(db, field_id)
    return {"status": "ok", **result}


@router.get("/{field_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(field_id: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")

    today = date.today()
    risks_result = await db.execute(
        select(RiskScoreDaily).where(
            RiskScoreDaily.field_id == field_id,
            RiskScoreDaily.date == today,
        ).order_by(RiskScoreDaily.final_risk.desc())
    )
    risks = risks_result.scalars().all()
    if not risks:
        collector = DataCollector()
        await collector.collect_all(db, field_id)
        risks_result = await db.execute(
            select(RiskScoreDaily).where(
                RiskScoreDaily.field_id == field_id,
                RiskScoreDaily.date == today,
            ).order_by(RiskScoreDaily.final_risk.desc())
        )
        risks = risks_result.scalars().all()

    risk_list = [
        RiskSummary(
            pest_name=r.pest_name, final_risk=r.final_risk or 0,
            risk_level=r.risk_level or "낮음",
            weather_risk=r.weather_risk or 0, pest_risk=r.pest_risk or 0,
            soil_risk=r.soil_risk or 0,
        )
        for r in risks
    ]

    trend = []
    for d in range(6, -1, -1):
        dt = today - timedelta(days=d)
        tr = await db.execute(
            select(func.avg(RiskScoreDaily.final_risk)).where(
                RiskScoreDaily.field_id == field_id, RiskScoreDaily.date == dt,
            )
        )
        avg = tr.scalar() or 0
        trend.append({"date": dt.isoformat(), "avg_risk": round(float(avg), 1)})

    alerts_result = await db.execute(
        select(AlertEvent).where(AlertEvent.field_id == field_id)
        .order_by(AlertEvent.created_at.desc()).limit(5)
    )
    alerts = [
        {
            "id": a.id, "type": a.alert_type, "title": a.title, "message": a.message,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts_result.scalars().all()
    ]

    rec_result = await db.execute(
        select(RecommendationCard).where(RecommendationCard.field_id == field_id)
        .order_by(RecommendationCard.created_at.desc()).limit(1)
    )
    rec = rec_result.scalar_one_or_none()
    recommendation = None
    if rec:
        recommendation = {
            "title": rec.title, "reason": rec.reason,
            "action_list": rec.action_list, "pest_name": rec.pest_name,
            "risk_score": rec.risk_score,
        }

    lat, lng = _field_coords(f)

    return DashboardResponse(
        field=FieldResponse(
            field_id=f.field_id, fmap_innb=f.fmap_innb, pnu_code=f.pnu_code,
            crop_name=f.crop_name, land_type=f.land_type, address=f.address,
            lat=lat, lng=lng, planting_date=f.planting_date,
        ),
        today_risks=risk_list,
        top_pests=risk_list[:3],
        trend_7d=trend,
        alerts=alerts,
        recommendation=recommendation,
    )


@router.get("/{field_id}/detail")
async def get_field_detail(field_id: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")

    soil_r = await db.execute(
        select(SoilSnapshot).where(SoilSnapshot.field_id == field_id)
        .order_by(SoilSnapshot.sample_year.desc()).limit(1)
    )
    soil = soil_r.scalar_one_or_none()

    weather_r = await db.execute(
        select(WeatherHourly).where(WeatherHourly.field_id == field_id)
        .order_by(WeatherHourly.obs_time.desc()).limit(24)
    )
    weather = [
        {
            "time": w.obs_time.isoformat(), "temp": w.temperature,
            "humidity": w.humidity, "rain": w.rainfall,
            "soil_moisture": w.soil_moisture, "dew_time": w.dew_time,
        }
        for w in reversed(weather_r.scalars().all())
    ]

    pest_r = await db.execute(
        select(PestOccurrence).where(PestOccurrence.field_id == field_id)
        .order_by(PestOccurrence.occurrence_value.desc())
    )
    pests = [
        {
            "name": p.pest_name, "crop": p.crop_name,
            "value": p.occurrence_value, "distance_km": p.occurrence_distance,
            "report_date": p.report_date.isoformat() if p.report_date else None,
        }
        for p in pest_r.scalars().all()
    ]

    enrichment = None
    fertilizer_calendar = None
    if f.pnu_code:
        enrichment = await KnowledgeService().enrich_field_soil(
            f.pnu_code, f.crop_name,
            soil.acidity if soil else 6.2,
            soil.organic_matter if soil else 2.8,
            soil.available_phosphate if soil else 100,
            soil.ec if soil else 0.5,
        )
        fert_raw = None
        if enrichment and enrichment.get("fertilizer"):
            fert_raw = enrichment["fertilizer"] if isinstance(enrichment["fertilizer"], dict) else None
        fertilizer_calendar = build_fertilizer_calendar(
            f.crop_name, f.planting_date, fert_raw,
        )

    weather_timeline = await _build_field_weather_timeline(db, field_id, f)

    return {
        "field": {"field_id": f.field_id, "address": f.address, "crop_name": f.crop_name,
                  "land_type": f.land_type, "fmap_innb": f.fmap_innb, "pnu_code": f.pnu_code,
                  "planting_date": f.planting_date.isoformat() if f.planting_date else None},
        "soil": {
            "year": soil.sample_year, "acidity": soil.acidity,
            "organic_matter": soil.organic_matter, "ec": soil.ec,
            "phosphate": soil.available_phosphate,
        } if soil else None,
        "weather_summary": weather[-6:] if weather else [],
        "pests": pests,
        "enrichment": enrichment,
        "fertilizer_calendar": fertilizer_calendar,
        "weather_timeline": weather_timeline,
    }


@router.get("/{field_id}/pest/{pest_name}")
async def get_pest_detail(field_id: int, pest_name: str, db: AsyncSession = Depends(get_db)):
    today = date.today()
    risk_r = await db.execute(
        select(RiskScoreDaily).where(
            RiskScoreDaily.field_id == field_id,
            RiskScoreDaily.pest_name == pest_name,
            RiskScoreDaily.date == today,
        )
    )
    risk = risk_r.scalar_one_or_none()
    if not risk:
        raise HTTPException(404, "해당 병해충 위험 데이터가 없습니다")

    rec_r = await db.execute(
        select(RecommendationCard).where(
            RecommendationCard.field_id == field_id,
            RecommendationCard.pest_name == pest_name,
        ).order_by(RecommendationCard.created_at.desc()).limit(1)
    )
    rec = rec_r.scalar_one_or_none()

    pest_r = await db.execute(
        select(PestOccurrence).where(
            PestOccurrence.field_id == field_id,
            PestOccurrence.pest_name == pest_name,
        )
    )
    occurrences = [
        {"distance_km": p.occurrence_distance, "value": p.occurrence_value,
         "report_date": p.report_date.isoformat() if p.report_date else None}
        for p in pest_r.scalars().all()
    ]

    field = await db.get(FieldMaster, field_id)
    knowledge = await KnowledgeService().enrich_pest(field.crop_name if field else "고추", pest_name)

    return {
        "pest_name": pest_name,
        "final_risk": risk.final_risk,
        "risk_level": risk.risk_level,
        "weather_risk": risk.weather_risk,
        "pest_risk": risk.pest_risk,
        "soil_risk": risk.soil_risk,
        "occurrences": occurrences,
        "knowledge": knowledge,
        "spray_prescriptions": knowledge.get("spray_prescriptions") or [],
        "recommendation": {
            "title": rec.title, "reason": rec.reason,
            "action_list": rec.action_list, "source_refs": rec.source_refs,
        } if rec else None,
    }


@router.get("/{field_id}/weather-timeline")
async def get_weather_timeline(field_id: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")
    return await _build_field_weather_timeline(db, field_id, f)


@router.get("/{field_id}/fertilizer-calendar")
async def get_fertilizer_calendar(field_id: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")

    fert_raw: dict | None = None
    if f.pnu_code:
        fert = await SoilApiClient().fertilizer_prescription(f.pnu_code, f.crop_name)
        items = fert.get("items") or []
        if items:
            fert_raw = items[0]

    return build_fertilizer_calendar(f.crop_name, f.planting_date, fert_raw)


@router.get("/{field_id}/insights")
async def get_field_insights(field_id: int, db: AsyncSession = Depends(get_db)):
    """7일 예보, 방제 타이밍, 지도 레이어, 주간 리포트"""
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")

    today = date.today()
    lat, lng = _field_coords(f)
    if lat is None or lng is None:
        lat, lng = 36.5, 127.8

    risks_result = await db.execute(
        select(RiskScoreDaily).where(
            RiskScoreDaily.field_id == field_id, RiskScoreDaily.date == today,
        ).order_by(RiskScoreDaily.final_risk.desc())
    )
    risks = risks_result.scalars().all()
    top = risks[0] if risks else None
    base_pest = top.pest_risk if top else 40
    base_soil = top.soil_risk if top else 25
    crop_risk = top.crop_stage_risk if top else calc_crop_stage_risk(f.planting_date, crop_name=f.crop_name)
    top_pest_name = top.pest_name if top else (get_target_pests(f.crop_name)[0] if get_target_pests(f.crop_name) else "탄저병")

    trend = []
    for d in range(6, -1, -1):
        dt = today - timedelta(days=d)
        tr = await db.execute(
            select(func.avg(RiskScoreDaily.final_risk)).where(
                RiskScoreDaily.field_id == field_id, RiskScoreDaily.date == dt,
            )
        )
        avg = tr.scalar() or 0
        trend.append({"date": dt.isoformat(), "avg_risk": round(float(avg), 1)})

    spray = build_spray_timing(today)
    kma_daily: dict = {}
    if f.kma_nx and f.kma_ny:
        kma_client = KmaClient()
        kma_fcst = await kma_client.fetch_ultra_forecast(f.kma_nx, f.kma_ny)
        if kma_fcst:
            spray = build_spray_timing_from_kma(kma_fcst, today)
        vilage = await kma_client.fetch_vilage_forecast(f.kma_nx, f.kma_ny)
        if vilage:
            kma_daily = parse_vilage_daily(vilage)

    forecast_14d = build_forecast_7d(
        field_id, today, base_pest, base_soil, crop_risk or 0,
        top_pest_name, trend,
        kma_daily=kma_daily,
    )

    pest_r = await db.execute(
        select(PestOccurrence).where(PestOccurrence.field_id == field_id)
    )
    pests = [
        {"name": p.pest_name, "value": p.occurrence_value, "distance_km": p.occurrence_distance}
        for p in pest_r.scalars().all()
    ]
    map_layers = build_map_layers(lat, lng, pests)

    rec_r = await db.execute(
        select(RecommendationCard).where(RecommendationCard.field_id == field_id)
        .order_by(RecommendationCard.created_at.desc()).limit(1)
    )
    rec = rec_r.scalar_one_or_none()
    recommendation = {
        "title": rec.title, "reason": rec.reason, "action_list": rec.action_list,
    } if rec else None

    top_pests = [
        {"pest_name": r.pest_name, "final_risk": r.final_risk, "risk_level": r.risk_level}
        for r in risks[:3]
    ]

    weekly = build_weekly_report(
        {"address": f.address, "crop_name": f.crop_name},
        forecast_14d, spray, top_pests, recommendation,
    )

    fert_cal = None
    if f.pnu_code:
        fert = await SoilApiClient().fertilizer_prescription(f.pnu_code, f.crop_name)
        items = fert.get("items") or []
        fert_cal = build_fertilizer_calendar(
            f.crop_name, f.planting_date, items[0] if items else None,
        )

    week_plan = {
        "spray_summary": spray.get("summary"),
        "spray_best_window": spray.get("best_window"),
        "fertilizer_summary": fert_cal.get("summary") if fert_cal else None,
        "fertilizer_next": fert_cal.get("next_event") if fert_cal else None,
        "top_pest": top_pest_name,
    }

    weather_timeline = await _build_field_weather_timeline(db, field_id, f)

    return {
        "forecast_14d": forecast_14d,
        "spray_timing": spray,
        "map_layers": map_layers,
        "weekly_report": weekly,
        "top_pests": top_pests,
        "fertilizer_calendar": fert_cal,
        "week_plan": week_plan,
        "weather_timeline": weather_timeline,
    }
