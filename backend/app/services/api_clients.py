"""공공 API 클라이언트 + 데모 데이터"""

import math

import random

from datetime import date, datetime, timedelta

from typing import Any, Optional

from urllib.parse import quote



import httpx



from app.config import settings

from app.runtime_config import is_demo_mode

from app.services.xml_utils import extract_items, xml_to_dict, api_result_code



FARMMAP_BASE = "http://apis.data.go.kr/B552895"

KMA_BASE = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"





def _kma_base_time(now: datetime | None = None) -> tuple[str, str]:

    now = now or datetime.now()

    base = now.replace(minute=0, second=0, microsecond=0)

    if now.minute < 40:

        base -= timedelta(hours=1)

    return base.strftime("%Y%m%d"), base.strftime("%H00")





class FarmmapClient:

    def __init__(self, service_key: str = ""):

        self.service_key = service_key or settings.public_data_service_key

        self.demo = is_demo_mode() or not self.service_key



    async def _get(self, url: str, params: dict) -> dict | list:

        params = {**params, "serviceKey": self.service_key, "type": "json"}

        async with httpx.AsyncClient(timeout=25) as client:

            r = await client.get(url, params=params)

            if r.status_code == 403:

                return {"error": "403", "items": []}

            r.raise_for_status()

            text = r.text.strip()

            if text.startswith("<"):

                data = xml_to_dict(text)

                code, msg = api_result_code(data)

                if code and code not in ("00", "0"):

                    return {"error": code, "message": msg, "items": []}

                return {"items": extract_items(data), "raw": data}

            data = r.json()

            if isinstance(data, dict):

                items = extract_items(data)

                if items:

                    return items

                resp = data.get("response", {})

                body_items = resp.get("body", {}).get("items", [])

                if isinstance(body_items, list):

                    return body_items

            return data



    async def fetch_parcel(self, position_x: float, position_y: float, radius: int = 300) -> dict:

        if self.demo:

            return {

                "fmapInnb": f"DEMO{int(position_x) % 100000}",

                "pnuLnmCd": "5271033027106720012",

                "lglEmdNm": "데모리",

                "lnm": "123",

                "intprNm": "밭",

            }

        url = f"{FARMMAP_BASE}/getFarmmapService/getAreaBasedFarmmapInfo"

        data = await self._get(url, {

            "numOfRows": 10, "pageNo": 1,

            "positionX": int(position_x), "positionY": int(position_y), "radius": radius,

        })

        if isinstance(data, dict) and data.get("error") == "403":

            return {

                "fmapInnb": f"TMP{int(position_x) % 100000}",

                "pnuLnmCd": "",

                "lglEmdNm": "미확인",

                "lnm": "",

                "intprNm": "밭",

                "_fallback": True,

            }

        items = data if isinstance(data, list) else data.get("items", [])

        return items[0] if items else {}



    async def fetch_weather_hourly(self, position_x: float, position_y: float, dt: date) -> list[dict]:

        if self.demo:

            return self._demo_weather(dt)

        url = f"{FARMMAP_BASE}/rest/farmmap/getFarmmapAgricultureWeatherService/getCoordinateBasedHourFarmimgWeatherInfo"

        data = await self._get(url, {

            "numOfRows": 100, "pageNo": 1,

            "positionX": int(position_x), "positionY": int(position_y),

            "date": dt.strftime("%Y%m%d"),

        })

        items = data if isinstance(data, list) else data.get("items", [])

        if not items and not self.demo:

            return self._demo_weather(dt)

        return items



    async def fetch_soil(self, position_x: float, position_y: float, year: int = 2023) -> dict:

        if self.demo:

            return {

                "pickYr": year, "acidity": 6.2, "ormtCont": 2.8,

                "vdphdy": 120, "ecd": 0.8, "rlfzKlusq": 0.45,

                "rlfzMgusq": 1.2, "lreq": 0.5,

            }

        url = f"{FARMMAP_BASE}/rest/farmmap/getFarmmapSoilAnalysisService/getCoordinateBasedSoilAnalsInfo"

        data = await self._get(url, {

            "numOfRows": 10, "pageNo": 1,

            "positionX": int(position_x), "positionY": int(position_y), "year": year,

        })

        items = data if isinstance(data, list) else data.get("items", [])

        if items:

            return items[0]

        return {

            "pickYr": year, "acidity": 6.2, "ormtCont": 2.8,

            "vdphdy": 120, "ecd": 0.8, "rlfzKlusq": 0.45,

            "rlfzMgusq": 1.2, "lreq": 0.5,

            "_fallback": True,

        }



    async def fetch_pests(

        self, position_x: float, position_y: float,

        year: int, begin_month: int = 1, end_month: int = 12,

    ) -> list[dict]:

        if self.demo:

            return self._demo_pests()

        url = f"{FARMMAP_BASE}/rest/farmmap/getFarmmapDbyhsService/getCoordinateBasedYearDbyhsInfo"

        data = await self._get(url, {

            "numOfRows": 1000, "pageNo": 1,

            "positionX": int(position_x), "positionY": int(position_y),

            "year": year,

            "beginMonth": f"{begin_month:02d}",

            "endMonth": f"{end_month:02d}",

        })

        items = data if isinstance(data, list) else data.get("items", [])

        return items if items else self._demo_pests()



    def _demo_weather(self, dt: date) -> list[dict]:

        rows = []

        for h in range(24):

            t = datetime.combine(dt, datetime.min.time()) + timedelta(hours=h)

            humidity = 65 + random.uniform(-10, 25)

            rows.append({

                "obsrTm": t.strftime("%Y%m%d%H%M"),

                "tp150": round(18 + random.uniform(-3, 8), 1),

                "hd150": round(humidity, 1),

                "afp": round(random.uniform(0, 5) if humidity > 75 else 0, 1),

                "ws150": round(random.uniform(0.5, 4), 1),

                "sm10": round(random.uniform(15, 35), 1),

                "dwcnTime": round(random.uniform(0, 4) if humidity > 70 else 0, 1),

            })

        return rows



    def _demo_pests(self) -> list[dict]:

        pests = [

            ("탄저병", 72, 1), ("역병", 45, 2), ("담배나방", 58, 1),

            ("흰가루병", 30, 3), ("진딧물", 40, 2),

        ]

        today = date.today()

        return [

            {

                "dbyhsNm": name, "crpTynm": "고추", "iqVl": val,

                "ocrdst": dist, "inptDe": today.strftime("%Y%m%d"),

            }

            for name, val, dist in pests

        ]





class KmaClient:

    def __init__(self, service_key: str = ""):

        self.service_key = service_key or settings.public_data_service_key

        self.demo = is_demo_mode() or not self.service_key



    async def _kma_get(self, operation: str, params: dict) -> dict:

        if self.demo:

            return {"demo": True, "items": []}

        url = f"{KMA_BASE}/{operation}"

        params = {

            **params,

            "ServiceKey": self.service_key,

            "pageNo": 1,

            "numOfRows": 1000,

            "dataType": "JSON",

        }

        async with httpx.AsyncClient(timeout=20) as client:

            r = await client.get(url, params=params)

            r.raise_for_status()

            data = r.json()

        header = data.get("response", {}).get("header", {})

        if header.get("resultCode") != "00":

            return {"error": header.get("resultCode"), "message": header.get("resultMsg"), "items": []}

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

        if isinstance(items, dict):

            items = [items]

        return {"items": items or [], "raw": data}



    async def fetch_ultra_nowcast(self, nx: int, ny: int, base_date: str = "", base_time: str = "") -> dict:

        if self.demo:

            return {"RN1": "0", "T1H": "22", "WSD": "2.1", "REH": "78", "PTY": "0"}

        if not base_date or not base_time:

            base_date, base_time = _kma_base_time()

        data = await self._kma_get("getUltraSrtNcst", {

            "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny,

        })

        items = data.get("items") or []

        return {item["category"]: item["obsrValue"] for item in items}



    async def fetch_ultra_forecast(self, nx: int, ny: int) -> list[dict]:

        """초단기예보 (6시간)"""

        if self.demo:

            return []

        base_date, base_time = _kma_base_time()

        data = await self._kma_get("getUltraSrtFcst", {

            "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny,

        })

        return data.get("items") or []



    async def fetch_vilage_forecast(self, nx: int, ny: int) -> list[dict]:
        """단기예보 (3일) — base_time 0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300"""
        if self.demo:
            return []
        now = datetime.now()
        slots = [2, 5, 8, 11, 14, 17, 20, 23]
        base_date = now.date()
        base_hour = 23
        for h in reversed(slots):
            if now.hour > h or (now.hour == h and now.minute >= 10):
                base_hour = h
                break
        else:
            base_date = base_date - timedelta(days=1)
            base_hour = 23
        base_time = f"{base_hour:02d}00"
        data = await self._kma_get("getVilageFcst", {
            "base_date": base_date.strftime("%Y%m%d"), "base_time": base_time, "nx": nx, "ny": ny,
        })
        return data.get("items") or []


