from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.crop_registry import list_crops
from app.runtime_config import is_demo_mode, set_demo_mode
from app.database import get_db
from app.models import (
    SourceMaster, FieldMaster, RawApiLog, AlertSettings, AlertEvent,
    WeatherHourly, SoilSnapshot, PestOccurrence, RiskScoreDaily,
    RecommendationCard,
)
from app.schemas import AlertSettingsUpdate, ApiStatusItem
from app.services.collector import DataCollector

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
async def admin_dashboard(db: AsyncSession = Depends(get_db)):
    today = date.today()

    field_count = (await db.execute(select(func.count(FieldMaster.field_id)))).scalar() or 0
    log_count = (await db.execute(select(func.count(RawApiLog.id)))).scalar() or 0
    alert_count = (await db.execute(select(func.count(AlertEvent.id)))).scalar() or 0
    weather_count = (await db.execute(select(func.count(WeatherHourly.id)))).scalar() or 0
    soil_count = (await db.execute(select(func.count(SoilSnapshot.id)))).scalar() or 0
    pest_count = (await db.execute(select(func.count(PestOccurrence.id)))).scalar() or 0
    risk_count = (await db.execute(select(func.count(RiskScoreDaily.id)))).scalar() or 0
    rec_count = (await db.execute(select(func.count(RecommendationCard.id)))).scalar() or 0

    high_risk = (await db.execute(
        select(func.count(RiskScoreDaily.id)).where(
            RiskScoreDaily.date == today,
            RiskScoreDaily.final_risk >= 70,
        )
    )).scalar() or 0

    sources = (await db.execute(select(SourceMaster))).scalars().all()
    api_ok = sum(1 for s in sources if s.last_status == "success")
    api_total = len(sources)

    return {
        "system": {
            "demo_mode": is_demo_mode(),
            "model_version": settings.model_version,
            "supported_crops": len(list_crops()),
            "crop_names": [c["name_ko"] for c in list_crops()],
            "database": "SQLite" if settings.is_sqlite else "PostgreSQL",
        },
        "stats": {
            "field_count": field_count,
            "api_log_count": log_count,
            "alert_count": alert_count,
            "weather_records": weather_count,
            "soil_records": soil_count,
            "pest_records": pest_count,
            "risk_scores": risk_count,
            "recommendations": rec_count,
            "high_risk_today": high_risk,
        },
        "pipeline": {
            "api_connected": f"{api_ok}/{api_total}",
            "last_collection": _latest_time(sources, "last_called_at"),
            "data_layers": [
                {"name": "팜맵 조회", "status": _source_status(sources, "팜맵 조회")},
                {"name": "팜맵 농업기상", "status": _source_status(sources, "팜맵 농업기상")},
                {"name": "팜맵 토양검정", "status": _source_status(sources, "팜맵 토양검정")},
                {"name": "팜맵 병해충발생", "status": _source_status(sources, "팜맵 병해충발생")},
                {"name": "기상청 단기예보", "status": _source_status(sources, "기상청 단기예보")},
                {"name": "농사로", "status": _source_status(sources, "농사로 병해충발생")},
                {"name": "농약등록", "status": _source_status(sources, "농사로 농약등록")},
                {"name": "토양/비료", "status": _source_status(sources, "토양검정 V2")},
            ],
        },
        "sources": [
            {
                "source_name": s.source_name,
                "license_type": s.license_type,
                "last_called_at": s.last_called_at.isoformat() if s.last_called_at else None,
                "last_status": s.last_status or "unknown",
                "commercial_allowed": s.commercial_allowed,
            }
            for s in sources
        ],
    }


def _source_status(sources, name: str) -> str:
    for s in sources:
        if s.source_name == name:
            return s.last_status or "unknown"
    return "unknown"


def _latest_time(sources, attr: str) -> str | None:
    times = [getattr(s, attr) for s in sources if getattr(s, attr, None)]
    if not times:
        return None
    return max(times).isoformat()


@router.get("/api-status", response_model=list[ApiStatusItem])
async def api_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SourceMaster))
    sources = result.scalars().all()
    return [
        ApiStatusItem(
            source_name=s.source_name,
            last_called_at=s.last_called_at.isoformat() if s.last_called_at else None,
            last_status=s.last_status or "unknown",
            license_type=s.license_type,
        )
        for s in sources
    ]


@router.get("/stats")
async def admin_stats(db: AsyncSession = Depends(get_db)):
    today = date.today()
    field_count = (await db.execute(select(func.count(FieldMaster.field_id)))).scalar() or 0
    log_count = (await db.execute(select(func.count(RawApiLog.id)))).scalar() or 0
    alert_count = (await db.execute(select(func.count(AlertEvent.id)))).scalar() or 0
    high_risk = (await db.execute(
        select(func.count(RiskScoreDaily.id)).where(
            RiskScoreDaily.date == today, RiskScoreDaily.final_risk >= 70,
        )
    )).scalar() or 0
    return {
        "field_count": field_count,
        "api_log_count": log_count,
        "alert_count": alert_count,
        "high_risk_today": high_risk,
        "demo_mode": is_demo_mode(),
    }


@router.post("/demo-mode")
async def toggle_demo_mode(enabled: bool):
    """데모 / 실 API 모드 전환 (런타임)"""
    set_demo_mode(enabled)
    return {
        "demo_mode": is_demo_mode(),
        "message": "데모 모드" if is_demo_mode() else "실 API 모드",
    }


@router.get("/fields")
async def admin_fields(db: AsyncSession = Depends(get_db)):
    today = date.today()
    fields = (await db.execute(
        select(FieldMaster).order_by(FieldMaster.created_at.desc())
    )).scalars().all()

    result = []
    for f in fields:
        risk_r = await db.execute(
            select(RiskScoreDaily).where(
                RiskScoreDaily.field_id == f.field_id,
                RiskScoreDaily.date == today,
            ).order_by(RiskScoreDaily.final_risk.desc()).limit(1)
        )
        top_risk = risk_r.scalar_one_or_none()

        w_count = (await db.execute(
            select(func.count(WeatherHourly.id)).where(WeatherHourly.field_id == f.field_id)
        )).scalar() or 0

        result.append({
            "field_id": f.field_id,
            "fmap_innb": f.fmap_innb,
            "crop_name": f.crop_name,
            "land_type": f.land_type,
            "address": f.address,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "weather_records": w_count,
            "top_risk": {
                "pest_name": top_risk.pest_name,
                "final_risk": top_risk.final_risk,
                "risk_level": top_risk.risk_level,
            } if top_risk else None,
        })
    return result


@router.get("/risk-logs")
async def risk_logs(limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RiskScoreDaily, FieldMaster.address)
        .join(FieldMaster, RiskScoreDaily.field_id == FieldMaster.field_id)
        .order_by(RiskScoreDaily.date.desc(), RiskScoreDaily.final_risk.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": risk.id,
            "field_id": risk.field_id,
            "address": address,
            "date": risk.date.isoformat(),
            "pest_name": risk.pest_name,
            "weather_risk": risk.weather_risk,
            "pest_risk": risk.pest_risk,
            "soil_risk": risk.soil_risk,
            "final_risk": risk.final_risk,
            "risk_level": risk.risk_level,
            "model_version": risk.model_version,
        }
        for risk, address in rows
    ]


@router.get("/logs")
async def api_logs(limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RawApiLog, SourceMaster.source_name)
        .outerjoin(SourceMaster, RawApiLog.source_id == SourceMaster.source_id)
        .order_by(RawApiLog.created_at.desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": log.id,
            "source_name": source_name or "-",
            "endpoint": log.endpoint,
            "status_code": log.status_code,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "field_id": log.field_id,
        }
        for log, source_name in rows
    ]


@router.post("/collect-all")
async def collect_all(db: AsyncSession = Depends(get_db)):
    fields = (await db.execute(select(FieldMaster))).scalars().all()
    collector = DataCollector()
    results = []
    for f in fields:
        try:
            r = await collector.collect_all(db, f.field_id)
            results.append({"field_id": f.field_id, "status": "ok", **r})
        except Exception as e:
            results.append({"field_id": f.field_id, "status": "error", "message": str(e)})
    return {"collected": len(results), "results": results}


router_alerts = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router_alerts.get("")
async def list_alerts(field_id: int | None = None, db: AsyncSession = Depends(get_db)):
    q = select(AlertEvent).order_by(AlertEvent.created_at.desc())
    if field_id:
        q = q.where(AlertEvent.field_id == field_id)
    result = await db.execute(q.limit(50))
    return [
        {
            "id": a.id, "field_id": a.field_id, "type": a.alert_type,
            "title": a.title, "message": a.message, "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in result.scalars().all()
    ]


@router_alerts.get("/settings")
async def get_alert_settings(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertSettings).where(AlertSettings.user_id == user_id))
    s = result.scalar_one_or_none()
    if not s:
        return AlertSettingsUpdate().model_dump()
    return {
        "risk_rise": s.risk_rise, "rain_before_spray": s.rain_before_spray,
        "high_humidity": s.high_humidity, "nearby_pest": s.nearby_pest,
        "weekly_report": s.weekly_report,
    }


@router_alerts.put("/settings")
async def update_alert_settings(body: AlertSettingsUpdate, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertSettings).where(AlertSettings.user_id == user_id))
    s = result.scalar_one_or_none()
    if not s:
        s = AlertSettings(user_id=user_id)
        db.add(s)
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    return {"status": "ok"}
