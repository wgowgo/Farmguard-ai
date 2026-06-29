"""농사로 Open API 클라이언트"""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.runtime_config import is_demo_mode
from app.services.xml_utils import extract_items, xml_to_dict

NONGSARO_BASE = "http://api.nongsaro.go.kr/service"

# 농사로 공공데이터 API 서비스, 오퍼레이션 (공식 샘플/매뉴얼 기준)
NONGSARO_SERVICES: dict[str, dict[str, Any]] = {
    "dbyhsCccrrncInfo": {
        "name": "병해충발생정보",
        "category": "occurrence",
        "operations": {
            "dbyhsCccrrncInfoYear": "연도 목록",
            "dbyhsCccrrncInfoList": "발생정보 목록",
        },
        "default_operation": "dbyhsCccrrncInfoList",
    },
    "healthEduGymMovInfo": {
        "name": "건강안전정보",
        "category": "safety",
        "operations": {
            "healthEduGymMovInfoSafetyEdu": "건강, 안전 교육 목록",
        },
        "default_operation": "healthEduGymMovInfoSafetyEdu",
    },
    "openApiData": {
        "name": "공공데이터",
        "category": "meta",
        "operations": {"openApiDataList": "공공데이터 목록"},
        "default_operation": "openApiDataList",
    },
    "relatedSite": {
        "name": "관련 사이트 정보",
        "category": "meta",
        "operations": {"relatedSiteList": "관련 사이트 목록"},
        "default_operation": "relatedSiteList",
    },
    "agchmQltinsp": {
        "name": "농약 품질검사",
        "category": "pesticide",
        "operations": {"agchmQltinspLst": "품질검사 목록"},
        "default_operation": "agchmQltinspLst",
    },
    "pesticideRegStatus": {
        "name": "농약등록현황",
        "category": "pesticide",
        "operations": {
            "useGubunList": "용도 분류",
            "pesticideRegStatusList": "등록현황 목록",
        },
        "default_operation": "pesticideRegStatusList",
    },
    "agchmSafeManual": {
        "name": "농약안전사용지침",
        "category": "pesticide",
        "operations": {
            "nationList": "국가 목록",
            "agchmSafeManualList": "안전사용지침 목록",
        },
        "default_operation": "agchmSafeManualList",
    },
    "frcDsstrPrevnt": {
        "name": "농작물재해예방정보",
        "category": "disaster",
        "operations": {"frcDsstrPrevntYear": "재해예방 정보 목록"},
        "default_operation": "frcDsstrPrevntYear",
    },
}


class NongsaroClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.nongsaro_api_key
        self.demo = is_demo_mode() or not self.api_key

    async def _get(self, service_name: str, operation_name: str, **params) -> dict[str, Any]:
        if self.demo:
            return self._demo(service_name, operation_name, params)

        url = f"{NONGSARO_BASE}/{service_name}/{operation_name}"
        params = {"apiKey": self.api_key, **params}
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, params=params)
            text = r.text.strip()
            if text.startswith("<"):
                data = xml_to_dict(text)
                header = (data.get("response") or {}).get("header") or {}
                code = str(header.get("resultCode", ""))
                if code not in ("", "0", "00"):
                    return {
                        "error": code,
                        "message": header.get("resultMsg", "농사로 API 오류"),
                        "service": service_name,
                        "operation": operation_name,
                        "items": self._demo(service_name, operation_name, params).get("items", []),
                        "demo_fallback": True,
                    }
                return {
                    "service": service_name,
                    "operation": operation_name,
                    "service_name": NONGSARO_SERVICES.get(service_name, {}).get("name", service_name),
                    "items": extract_items(data),
                    "raw": data,
                }
            return r.json()

    def _demo(self, service_name: str, operation_name: str, params: dict) -> dict:
        meta = NONGSARO_SERVICES.get(service_name, {})
        if service_name == "dbyhsCccrrncInfo":
            if operation_name == "dbyhsCccrrncInfoYear":
                return {"items": [{"yearCode": "2025", "yearCnt": "128"}], "demo": True}
            return {
                "items": [
                    {"cntntsSj": "[고추] 탄저병 발생 주의보", "registDt": "2025-06-15"},
                    {"cntntsSj": "[고추] 담배나방 유충 발생 증가", "registDt": "2025-06-20"},
                ],
                "demo": True,
            }
        if service_name == "pesticideRegStatus":
            return {
                "items": [
                    {
                        "cropName": params.get("cropName", "고추"),
                        "diseaseWeedName": params.get("diseaseWeedName", "탄저병"),
                        "pestiBrandName": "가가방",
                        "prdlstNm": "가가방 수화제",
                        "useName": "살균",
                        "actnNm": "친화보호",
                        "cmpnyNm": "농약사",
                        "dcsnAt": "확인",
                    },
                    {
                        "cropName": params.get("cropName", "고추"),
                        "diseaseWeedName": params.get("diseaseWeedName", "탄저병"),
                        "pestiBrandName": "보르도액",
                        "prdlstNm": "보르도액",
                        "useName": "살균",
                        "actnNm": "예방",
                        "cmpnyNm": "농약사",
                        "dcsnAt": "확인",
                    },
                ],
                "demo": True,
            }
        if service_name == "agchmSafeManual":
            crop = params.get("sCropNm", "고추")
            return {
                "items": [
                    {
                        "cntntsSj": f"[{crop}] 가가방 수화제 안전사용지침",
                        "prdlstCodeNm": "가가방 수화제",
                        "dilutUnit": "1,000배",
                        "prcusePrd": "1회",
                        "harvAfMth": "7",
                        "fileUrl": "https://www.nongsaro.go.kr",
                        "reformYm": "2024-06",
                    },
                ],
                "demo": True,
            }
        return {"items": [{"info": meta.get("name", service_name)}], "demo": True}

    async def call(self, service_name: str, operation_name: str = "", **params) -> dict[str, Any]:
        if service_name not in NONGSARO_SERVICES:
            return {"error": "unknown_service", "service": service_name, "items": []}
        op = operation_name or NONGSARO_SERVICES[service_name]["default_operation"]
        if op not in NONGSARO_SERVICES[service_name]["operations"]:
            return {"error": "unknown_operation", "service": service_name, "operation": op, "items": []}
        return await self._get(service_name, op, **params)

    async def dbyhs_years(self) -> list[dict]:
        data = await self.call("dbyhsCccrrncInfo", "dbyhsCccrrncInfoYear")
        return data.get("items") or []

    async def dbyhs_list(
        self, year: str = "", search_type: str = "sCntntsSj",
        search_text: str = "", page_no: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"pageNo": page_no}
        if year:
            params["sYear"] = year
        if search_type:
            params["sType"] = search_type
        if search_text:
            params["sText"] = search_text
        return await self.call("dbyhsCccrrncInfo", "dbyhsCccrrncInfoList", **params)

    async def pesticide_reg_list(
        self, crop_name: str = "", pest_name: str = "", page_no: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"pageNo": page_no}
        if crop_name:
            params["cropName"] = crop_name
        if pest_name:
            params["diseaseWeedName"] = pest_name
        return await self.call("pesticideRegStatus", "pesticideRegStatusList", **params)

    async def pesticide_safe_manual(self, crop_name: str = "", page_no: int = 1) -> dict[str, Any]:
        params: dict[str, Any] = {"pageNo": page_no}
        if crop_name:
            params["sCropNm"] = crop_name
        return await self.call("agchmSafeManual", "agchmSafeManualList", **params)

    async def disaster_prevention(self, year: str = "", page_no: int = 1) -> dict[str, Any]:
        params: dict[str, Any] = {"pageNo": page_no}
        if year:
            params["sYear"] = year
        return await self.call("frcDsstrPrevnt", "frcDsstrPrevntYear", **params)

    @staticmethod
    def list_services() -> list[dict[str, Any]]:
        return [
            {
                "code": code,
                "name": meta["name"],
                "category": meta["category"],
                "operations": [
                    {"code": op, "name": label}
                    for op, label in meta["operations"].items()
                ],
            }
            for code, meta in NONGSARO_SERVICES.items()
        ]
