"""병해충 지식, 외부 API 통합 서비스"""
from __future__ import annotations

from typing import Any

from app.services.nongsaro_client import NongsaroClient, NONGSARO_SERVICES
from app.services.soil_api_client import SoilApiClient
from app.services.explanation import PEST_KNOWLEDGE
from app.services.spray_prescription import build_spray_prescriptions


class KnowledgeService:
    def __init__(self):
        self.nongsaro = NongsaroClient()
        self.soil = SoilApiClient()

    def list_all_services(self) -> dict[str, Any]:
        return {
            "nongsaro": NongsaroClient.list_services(),
            "soil": [
                {"code": "soil_chem_v2", "name": "토양검정 화학성 V2 (getSoilExam)", "category": "soil"},
                {"code": "soil_chem_list", "name": "토양검정 목록 (getSoilExamList)", "category": "soil"},
                {"code": "fertilizer_rice", "name": "벼 비료사용처방", "category": "fertilizer"},
                {"code": "fertilizer_other", "name": "벼 이외 비료사용처방", "category": "fertilizer"},
            ],
            "farmmap": [
                {"code": "parcel", "name": "팜맵 조회"},
                {"code": "weather", "name": "팜맵 농업기상"},
                {"code": "soil", "name": "팜맵 토양검정"},
                {"code": "pests", "name": "팜맵 병해충발생"},
            ],
            "kma": [
                {"code": "ultra_ncst", "name": "초단기실황"},
                {"code": "ultra_fcst", "name": "초단기예보"},
                {"code": "vilage_fcst", "name": "단기예보"},
            ],
        }

    async def enrich_pest(self, crop_name: str, pest_name: str) -> dict[str, Any]:
        nongsaro = await self.nongsaro.dbyhs_list(search_text=pest_name)
        pesticide = await self.nongsaro.pesticide_reg_list(crop_name, pest_name)
        manual = await self.nongsaro.pesticide_safe_manual(crop_name)
        base = PEST_KNOWLEDGE.get(pest_name, {})
        reg_items = pesticide.get("items") or []
        manual_items = manual.get("items") or []
        return {
            "pest_name": pest_name,
            "crop_name": crop_name,
            "symptoms": base.get("symptoms", ""),
            "environment": base.get("environment", ""),
            "actions": base.get("actions", []),
            "nongsaro_occurrence": nongsaro.get("items") or [],
            "pesticide_registration": reg_items,
            "pesticide_safe_manual": manual_items,
            "spray_prescriptions": build_spray_prescriptions(
                crop_name, pest_name, reg_items, manual_items,
            ),
        }

    async def enrich_field_soil(
        self, pnu_code: str, crop_name: str,
        acidity: float, organic_matter: float, phosphate: float, ec: float,
    ) -> dict[str, Any]:
        chem = await self.soil.soil_chem_v2(pnu_code) if pnu_code else {"items": []}
        fert = await self.soil.fertilizer_prescription(pnu_code, crop_name) if pnu_code else {"items": []}
        return {
            "soil_chem_v2": chem.get("items") or [],
            "fertilizer": (fert.get("items") or [{}])[0] if fert.get("items") else fert,
        }
