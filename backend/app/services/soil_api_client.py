"""흙토람(토양검정 V2, 비료사용처방) API 클라이언트"""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.runtime_config import is_demo_mode
from app.services.xml_utils import api_result_code, extract_items, xml_to_dict

SOIL_BASE = "https://apis.data.go.kr/1390802/SoilEnviron"

from app.services.crop_registry import get_soil_code

_SOIL_OK_CODES = {"00", "200"}


def pnu_to_stdg(pnu_code: str) -> str:
    """PNU 19자리 → 법정동코드 10자리 (getSoilExamList용)"""
    return pnu_code[:10] if len(pnu_code) >= 10 else pnu_code


class SoilApiClient:
    def __init__(self, service_key: str = ""):
        self.service_key = service_key or settings.public_data_service_key
        self.demo = is_demo_mode() or not self.service_key

    async def _get(self, path: str, params: dict) -> dict[str, Any]:
        if self.demo:
            return {"demo": True, "items": [], "path": path}

        params = {**params, "serviceKey": self.service_key}
        url = f"{SOIL_BASE}/{path}"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, params=params)
            if r.status_code == 403:
                return {"error": "403", "message": "해당 API 활용신청 필요", "items": self._demo(path, params)}
            text = r.text.strip()
            if text.startswith("<"):
                if r.status_code == 404 or "not found" in text.lower()[:200]:
                    return {"error": "404", "items": self._demo(path, params), "demo_fallback": True}
                data = xml_to_dict(text)
                code, msg = api_result_code(data)
                items = extract_items(data)
                result: dict[str, Any] = {"items": items, "raw": data, "result_code": code, "result_msg": msg}
                if code and code not in _SOIL_OK_CODES:
                    result["error"] = code
                    result["message"] = msg
                if not items and code in ("201", "301"):
                    items = self._demo(path, params)
                    result["items"] = items
                    result["estimated"] = True
                return result
            try:
                data = r.json()
                return {"items": extract_items(data), "raw": data}
            except Exception:
                return {"error": "parse", "text": text[:300]}

    def _demo(self, path: str, params: dict) -> list[dict]:
        crop = params.get("crop_name") or params.get("cropName") or "고추"
        if "Frtlzr" in path:
            return [{
                "crop_Nm": crop,
                "pre_Fert_N": 4.9, "pre_Fert_P": 3.2, "pre_Fert_K": 3.0,
                "post_Fert_N": 3.5, "post_Fert_P": 0, "post_Fert_K": 1.2,
                "snd_Sb_N": 2.0, "snd_Sb_P": 0, "snd_Sb_K": 0.8,
            }]
        if "SoilExam" in path:
            return [{
                "PNU_Cd": params.get("PNU_CD", ""),
                "ACID": 6.2, "OM": 28.0, "VLDPHA": 120, "ELCD": 0.8,
                "Any_Year": "2024",
            }]
        return []

    async def soil_chem_v2(self, pnu_code: str) -> dict[str, Any]:
        """토양검정 화학성 상세 V2 — PNU 기반 (getSoilExam)"""
        return await self._get(
            "SoilExam/V2/getSoilExam",
            {"PNU_CD": pnu_code},
        )

    async def soil_chem_list(
        self, stdg_code: str = "", pnu_code: str = "",
        page_no: int = 1, page_size: int = 10,
    ) -> dict[str, Any]:
        """읍면동 단위 토양검정 목록 (getSoilExamList, 최근 3년)"""
        stdg = stdg_code or pnu_to_stdg(pnu_code)
        return await self._get(
            "SoilExam/V2/getSoilExamList",
            {"STDG_CD": stdg, "Page_No": page_no, "Page_Size": page_size},
        )

    async def fertilizer_rice(self, pnu_code: str, rice_quality: int = 1) -> dict[str, Any]:
        """벼 작물 비료사용처방 (getSoilFrtlzrExamRiceInfo)"""
        return await self._get(
            "FrtlzrUse/getSoilFrtlzrExamRiceInfo",
            {"PNU_Code": pnu_code, "crop_Code": "00001", "rice_Qlt_Code": rice_quality},
        )

    async def fertilizer_other(self, pnu_code: str, crop_name: str = "고추") -> dict[str, Any]:
        """벼 이외 작물 비료사용처방 (getSoilFrtlzrExamInfo)"""
        crop_code = get_soil_code(crop_name)
        return await self._get(
            "FrtlzrUse/getSoilFrtlzrExamInfo",
            {"PNU_Code": pnu_code, "crop_Code": crop_code, "crop_name": crop_name},
        )

    async def fertilizer_prescription(
        self, pnu_code: str, crop_name: str, rice_quality: int = 1,
    ) -> dict[str, Any]:
        """작물에 따라 벼/기타 비료처방 API 자동 선택"""
        if not pnu_code:
            return {"error": "missing_pnu", "message": "PNU 코드 필요", "items": []}
        if get_soil_code(crop_name) == "00001" or crop_name == "벼":
            return await self.fertilizer_rice(pnu_code, rice_quality)
        return await self.fertilizer_other(pnu_code, crop_name)

    async def fertilizer_standard(self, crop_code: str = "00013") -> dict[str, Any]:
        return await self._get(
            "FrtlzrStdUse/getSoilFrtlzrQyList",
            {"fstd_Crop_Code": crop_code, "pageNo": 1, "numOfRows": 10},
        )
