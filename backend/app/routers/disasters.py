"""재해 예방 API"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import FieldMaster
from app.services.api_clients import KmaClient
from app.services.disaster_service import build_disaster_center
from app.services.nongsaro_client import NongsaroClient

router = APIRouter(prefix="/api/disasters", tags=["disasters"])


@router.get("")
async def get_disaster_center(
    crop_name: str = Query("고추"),
    field_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    if field_id:
        f = await db.get(FieldMaster, field_id)
        if f:
            crop_name = f.crop_name

    nongsaro = await NongsaroClient().disaster_prevention(year="2026")
    vilage: list = []
    if field_id:
        f = await db.get(FieldMaster, field_id)
        if f and f.kma_nx and f.kma_ny:
            vilage = await KmaClient().fetch_vilage_forecast(f.kma_nx, f.kma_ny)

    return build_disaster_center(
        crop_name,
        nongsaro_items=nongsaro.get("items") or [],
        vilage_fcst=vilage,
    )
