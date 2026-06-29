"""NCPMS(국가농작물병해충관리시스템) Open API 클라이언트"""
from __future__ import annotations

from typing import Any, Optional

import httpx

from app.config import settings
from app.runtime_config import is_demo_mode
from app.services.xml_utils import extract_items, xml_to_dict

NCPMS_BASE = "https://ncpms.rda.go.kr/openApi/service.do"

# 공식 매뉴얼 serviceCode 매핑
NCPMS_SERVICES: dict[str, dict[str, str]] = {
    "SVC01": {"name": "병 검색", "category": "search"},
    "SVC02": {"name": "병 상세정보", "category": "search"},
    "SVC03": {"name": "병원체 검색", "category": "search"},
    "SVC04": {"name": "병원체 상세정보", "category": "search"},
    "SVC05": {"name": "해충 검색", "category": "search"},
    "SVC06": {"name": "해충 상세정보", "category": "search"},
    "SVC07": {"name": "곤충 검색", "category": "search"},
    "SVC08": {"name": "곤충 상세정보", "category": "search"},
    "SVC09": {"name": "잡초 검색", "category": "search"},
    "SVC10": {"name": "잡초 상세정보", "category": "search"},
    "SVC11": {"name": "작물 대분류별 이미지 검색", "category": "search"},
    "SVC12": {"name": "작물 중분류별 이미지 검색", "category": "search"},
    "SVC13": {"name": "작물 소분류별 이미지 검색", "category": "search"},
    "SVC14": {"name": "천적곤충 검색", "category": "search"},
    "SVC15": {"name": "천적곤충 상세정보", "category": "search"},
    "SVC16": {"name": "통합검색", "category": "search"},
    "SVC17": {"name": "병해충예측지도", "category": "predict"},
    "SVC18": {"name": "지점자료예측조회", "category": "predict"},
    "SVC19": {"name": "예측조사비교", "category": "predict"},
    "SVC20": {"name": "벼도열병 방제결정지원", "category": "predict"},
    "SVC21": {"name": "병해충예찰검색", "category": "surveillance"},
    "SVC22": {"name": "병해충예찰검색상세(시도별)", "category": "surveillance"},
    "SVC23": {"name": "병해충예찰검색상세(시군구별)", "category": "surveillance"},
    "SVC24": {"name": "병해충상담 검색", "category": "consult"},
    "SVC25": {"name": "병해충상담 상세정보", "category": "consult"},
}

_DEMO_DISEASE = {
    "탄저병": {
        "diseaseName": "탄저병", "cropName": "고추",
        "symptoms": "잎, 줄기, 열매에 둥근 갈색 병반, 중앙이 회색, 검은색",
        "developmentCondition": "25~28°C, 습도 85% 이상, 결로 시 확산",
        "preventionMethod": "발병 전 예방 위주 약제 살포, 병든 잎, 과 일광소독 후 폐기",
        "biologyPrvnbeMthod": "통풍 확보, 과밀 재배 피하기, 저항성 품종 선택",
    },
    "역병": {
        "diseaseName": "역병", "cropName": "고추",
        "symptoms": "잎 끝부터 갈변, 시들음, 습한 환경에서 흰 곰팡이 발생",
        "developmentCondition": "저온다습, 배수 불량, 통풍 불량",
        "preventionMethod": "배수, 통풍 개선, 칼슘 결핍 예방, 예방 약제 살포",
        "biologyPrvnbeMthod": "과습 방지, 토양 pH 6.0~6.5 유지",
    },
}

_DEMO_INSECT = {
    "담배나방": {
        "insectName": "담배나방", "cropName": "고추",
        "symptoms": "잎 구멍, 줄기 굴파, 열매 피해",
        "developmentCondition": "온난, 건조 시 발생 증가, 25°C 전후 성장",
        "preventionMethod": "성충 유인트랩, 살충제 살포, 유충 수동 제거",
        "biologyPrvnbeMthod": "천적곤충 보호, 유인제 활용",
    },
}


class NcpmsClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.ncpms_api_key
        self.demo = is_demo_mode() or not self.api_key

    async def call(self, service_code: str, **params) -> dict[str, Any]:
        meta = NCPMS_SERVICES.get(service_code, {"name": service_code, "category": "unknown"})
        if self.demo:
            return {
                "demo": True,
                "service_code": service_code,
                "service_name": meta["name"],
                "items": self._demo_items(service_code, params),
                "params": params,
            }

        req = {
            "apiKey": self.api_key,
            "serviceCode": service_code,
            "serviceType": params.pop("serviceType", "AA001"),
            "displayCount": params.pop("displayCount", 10),
            "startPoint": params.pop("startPoint", 1),
            **params,
        }
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            r = await client.get(
                NCPMS_BASE, params=req,
                headers={"User-Agent": "FarmGuardAI/1.0", "Referer": "https://ncpms.rda.go.kr/"},
            )
            text = r.text.strip()
            if text.startswith("<!") or "<html" in text[:200].lower():
                return {
                    "error": "invalid_response",
                    "message": "NCPMS API 키 또는 승인 상태를 확인하세요",
                    "service_code": service_code,
                    "items": self._demo_items(service_code, params),
                    "demo_fallback": True,
                }
            data = xml_to_dict(text) if text.startswith("<") else r.json()
            items = extract_items(data)
            return {
                "service_code": service_code,
                "service_name": meta["name"],
                "items": items,
                "raw": data,
                "params": req,
            }

    def _demo_items(self, service_code: str, params: dict) -> list[dict]:
        crop = params.get("cropName", "고추")
        name = params.get("diseaseName") or params.get("insectName") or params.get("searchWord", "")

        if service_code == "SVC01":
            items = [{"diseaseName": k, "cropName": crop, **v} for k, v in _DEMO_DISEASE.items()]
            if name:
                items = [i for i in items if name in i["diseaseName"]]
            return items
        if service_code == "SVC02":
            d = _DEMO_DISEASE.get(name, _DEMO_DISEASE["탄저병"])
            return [d]
        if service_code == "SVC05":
            items = [{"insectName": k, "cropName": crop, **v} for k, v in _DEMO_INSECT.items()]
            if name:
                items = [i for i in items if name in i["insectName"]]
            return items
        if service_code == "SVC06":
            d = _DEMO_INSECT.get(name, _DEMO_INSECT["담배나방"])
            return [d]
        if service_code == "SVC16":
            q = name or "탄저"
            return [
                {"type": "disease", "name": "탄저병", "cropName": crop},
                {"type": "insect", "name": "담배나방", "cropName": crop},
            ] if q else []
        if service_code == "SVC21":
            return [{
                "cropName": crop, "diseaseName": name or "탄저병",
                "surveyYear": "2025", "surveyMonth": "06",
                "occurrenceLevel": "중", "region": "경북",
            }]
        if service_code == "SVC24":
            return [{
                "title": f"{crop} {name or '병해'} 상담",
                "question": "잎에 갈색 반점이 생겼습니다.",
                "answer": "탄저병 가능성이 높습니다. 즉시 현장 확인 후 방제하세요.",
            }]
        if service_code in ("SVC17", "SVC18", "SVC19"):
            return [{"predictDate": "2025-06-29", "riskLevel": "중", "cropName": crop}]
        return [{"info": meta["name"], "cropName": crop} for meta in [NCPMS_SERVICES.get(service_code, {"name": service_code})]]

    async def search_disease(self, crop_name: str, disease_name: str = "", **kw) -> dict:
        return await self.call("SVC01", cropName=crop_name, diseaseName=disease_name, **kw)

    async def disease_detail(self, crop_name: str, disease_name: str, **kw) -> dict:
        return await self.call("SVC02", cropName=crop_name, diseaseName=disease_name, **kw)

    async def search_insect_pest(self, crop_name: str, insect_name: str = "", **kw) -> dict:
        return await self.call("SVC05", cropName=crop_name, insectName=insect_name, **kw)

    async def insect_pest_detail(self, crop_name: str, insect_name: str, **kw) -> dict:
        return await self.call("SVC06", cropName=crop_name, insectName=insect_name, **kw)

    async def total_search(self, search_word: str, **kw) -> dict:
        return await self.call("SVC16", searchWord=search_word, **kw)

    async def surveillance_search(self, crop_name: str, disease_name: str = "", **kw) -> dict:
        return await self.call("SVC21", cropName=crop_name, diseaseName=disease_name, **kw)

    async def consultation_search(self, search_word: str = "", **kw) -> dict:
        return await self.call("SVC24", searchWord=search_word, **kw)

    async def point_predict(self, crop_name: str, disease_name: str = "", **kw) -> dict:
        return await self.call("SVC18", cropName=crop_name, diseaseName=disease_name, **kw)

    async def get_pest_knowledge(self, crop_name: str, pest_name: str) -> dict[str, Any]:
        """병/해충 자동 판별 후 상세정보 조회"""
        is_insect = any(k in pest_name for k in ("나방", "진딧물", "응애", "벌레", "충"))
        if is_insect:
            search = await self.search_insect_pest(crop_name, pest_name)
            detail = await self.insect_pest_detail(crop_name, pest_name)
        else:
            search = await self.search_disease(crop_name, pest_name)
            detail = await self.disease_detail(crop_name, pest_name)

        surveillance = await self.surveillance_search(crop_name, pest_name)
        consultation = await self.consultation_search(pest_name)
        predict = await self.point_predict(crop_name, pest_name)

        detail_item = (detail.get("items") or [{}])[0]
        return {
            "pest_name": pest_name,
            "crop_name": crop_name,
            "type": "insect" if is_insect else "disease",
            "detail": detail_item,
            "search_count": len(search.get("items") or []),
            "surveillance": surveillance.get("items") or [],
            "consultation": consultation.get("items") or [],
            "prediction": predict.get("items") or [],
            "sources": ["NCPMS"],
        }

    @staticmethod
    def list_services() -> list[dict[str, str]]:
        return [
            {"code": code, **meta}
            for code, meta in NCPMS_SERVICES.items()
        ]
