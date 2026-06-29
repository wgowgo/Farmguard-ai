"""농사로, 토양/비료, 통합 지식 API"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import FieldMaster, SoilSnapshot
from app.services.knowledge_service import KnowledgeService
from app.services.nongsaro_client import NongsaroClient, NONGSARO_SERVICES
from app.services.soil_api_client import SoilApiClient
from sqlalchemy import select

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
_svc = KnowledgeService()


@router.get("/services")
async def list_services():
    return _svc.list_all_services()


@router.get("/nongsaro/dbyhs")
async def nongsaro_dbyhs(
    year: str = "",
    search_text: str = "",
    page_no: int = 1,
):
    client = NongsaroClient()
    years = await client.dbyhs_years()
    items = await client.dbyhs_list(year=year, search_text=search_text, page_no=page_no)
    return {"years": years, **items}


@router.get("/nongsaro/call")
async def nongsaro_call(
    service: str = Query(..., description="농사로 serviceName"),
    operation: str = Query("", description="operationName (비우면 기본값)"),
    page_no: int = Query(1, alias="pageNo"),
    search_text: str = Query("", alias="sText"),
    crop_name: str = Query("", alias="cropName"),
    pest_name: str = Query("", alias="diseaseWeedName"),
    year: str = Query("", alias="sYear"),
):
    if service not in NONGSARO_SERVICES:
        raise HTTPException(400, f"알 수 없는 service: {service}")
    params: dict[str, Any] = {"pageNo": page_no}
    if search_text:
        params["sText"] = search_text
    if crop_name:
        params["cropName"] = crop_name
        params["sCropNm"] = crop_name
    if pest_name:
        params["diseaseWeedName"] = pest_name
    if year:
        params["sYear"] = year
    client = NongsaroClient()
    return await client.call(service, operation, **params)


@router.get("/nongsaro/pesticide")
async def nongsaro_pesticide(
    crop_name: str = Query("고추"),
    pest_name: str = Query(""),
    page_no: int = 1,
):
    client = NongsaroClient()
    reg = await client.pesticide_reg_list(crop_name, pest_name, page_no)
    manual = await client.pesticide_safe_manual(crop_name, page_no)
    return {"registration": reg, "safe_manual": manual}


@router.get("/soil/chem/{pnu_code}")
async def soil_chem_v2(pnu_code: str):
    client = SoilApiClient()
    return await client.soil_chem_v2(pnu_code)


@router.get("/soil/fertilizer")
async def soil_fertilizer(
    crop_name: str = "고추",
    pnu_code: str = "",
    rice_quality: int = 1,
):
    client = SoilApiClient()
    if not pnu_code:
        raise HTTPException(400, "pnu_code가 필요합니다")
    if crop_name == "벼":
        return await client.fertilizer_rice(pnu_code, rice_quality)
    return await client.fertilizer_other(pnu_code, crop_name)


@router.get("/soil/list/{pnu_code}")
async def soil_chem_list(pnu_code: str, page_no: int = 1, page_size: int = 10):
    client = SoilApiClient()
    return await client.soil_chem_list(pnu_code=pnu_code, page_no=page_no, page_size=page_size)


@router.get("/field/{field_id}/enrichment")
async def field_enrichment(field_id: int, db: AsyncSession = Depends(get_db)):
    f = await db.get(FieldMaster, field_id)
    if not f:
        raise HTTPException(404, "필지를 찾을 수 없습니다")

    soil_r = await db.execute(
        select(SoilSnapshot).where(SoilSnapshot.field_id == field_id)
        .order_by(SoilSnapshot.sample_year.desc()).limit(1)
    )
    soil = soil_r.scalar_one_or_none()

    soil_data = await _svc.enrich_field_soil(
        f.pnu_code or "",
        f.crop_name,
        soil.acidity if soil else 6.2,
        soil.organic_matter if soil else 2.8,
        soil.available_phosphate if soil else 100,
        soil.ec if soil else 0.5,
    )

    pest_knowledge = {}
    from app.services.crop_registry import get_target_pests
    for pest in get_target_pests(f.crop_name):
        pest_knowledge[pest] = await _svc.enrich_pest(f.crop_name, pest)

    nongsaro = await NongsaroClient().dbyhs_list(search_text=f.crop_name)
    disaster = await NongsaroClient().disaster_prevention()

    return {
        "field_id": field_id,
        "crop_name": f.crop_name,
        "pnu_code": f.pnu_code,
        "soil_enrichment": soil_data,
        "pest_knowledge": pest_knowledge,
        "nongsaro_news": nongsaro.get("items") or [],
        "disaster_prevention": disaster.get("items") or [],
    }


@router.get("/search")
async def unified_search(
    q: str = Query(..., min_length=1),
    crop_name: str = Query("고추"),
):
    nongsaro = await NongsaroClient().dbyhs_list(search_text=q)
    pesticide = await NongsaroClient().pesticide_reg_list(crop_name, q)
    return {
        "query": q,
        "nongsaro_occurrence": nongsaro.get("items") or [],
        "pesticide_registration": pesticide.get("items") or [],
    }
