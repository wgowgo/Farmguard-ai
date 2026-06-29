from fastapi import APIRouter

from app.services.crop_registry import get_crop, list_crops

router = APIRouter(prefix="/api/crops", tags=["crops"])


@router.get("")
async def get_crops():
    return {"crops": list_crops(), "count": len(list_crops())}


@router.get("/{crop_id_or_name}")
async def get_crop_detail(crop_id_or_name: str):
    crop = get_crop(crop_id_or_name)
    if not crop:
        return {"error": "not_found", "message": f"작물을 찾을 수 없습니다: {crop_id_or_name}"}
    return crop
