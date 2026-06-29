"""재해 예방 센터 — 농사로 + KMA 단기예보 합성"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.services.crop_registry import get_crop_or_default
from app.services.forecast import parse_vilage_daily

_DISASTER_KEYWORDS = ("태풍", "장마", "폭염", "한파", "가뭄", "우박", "강풍", "집중호우", "결빙", "냉해", "dry", "heat")

_CROP_CHECKLISTS: dict[str, list[dict[str, str]]] = {
    "summer": [
        {"id": "rainy", "title": "장마, 집중호우", "actions": "배수로 정비, 예방 살균제 준비, 비료 유실 점검"},
        {"id": "heat", "title": "폭염", "actions": "차광, 관수 강화, 오후 방제 피하기, 열피해 관찰"},
        {"id": "typhoon", "title": "태풍", "actions": "지주대 점검, 막음막, 비닐 고정, 배수 확인"},
    ],
    "winter": [
        {"id": "cold", "title": "한파, 냉해", "actions": "방풍, 보온, 관수 시간 조절, 시설 난방 점검"},
        {"id": "drought", "title": "가뭄, 건조", "actions": "관수 계획 수립, 멀칭 유지, 토양 수분 모니터링"},
    ],
    "year_round": [
        {"id": "wind", "title": "강풍", "actions": "방제 일정 조정, 시설물 고정 상태 확인"},
    ],
}


def _normalize_nongsaro_item(item: dict) -> dict[str, str] | None:
    title = str(
        item.get("cntntsSj") or item.get("title") or item.get("sTitle")
        or item.get("cropNm") or item.get("yearCode") or ""
    ).strip()
    if not title or title.isdigit():
        return None
    body = str(item.get("cntntsCn") or item.get("content") or item.get("preventCn") or "").strip()
    return {
        "title": title,
        "body": body[:300] if body else "농사로 재해예방 자료를 확인하세요.",
        "source": "nongsaro",
        "category": _categorize(title),
    }


def _categorize(text: str) -> str:
    t = text.lower()
    for kw in _DISASTER_KEYWORDS:
        if kw in text or kw in t:
            if "폭염" in text or "heat" in t:
                return "heat"
            if "한파" in text or "냉해" in text or "결빙" in text:
                return "cold"
            if "장마" in text or "호우" in text or "rain" in t:
                return "rain"
            if "태풍" in text:
                return "typhoon"
            if "가뭄" in text:
                return "drought"
    return "general"


def _demo_articles(crop_name: str) -> list[dict[str, str]]:
    return [
        {
            "title": f"[{crop_name}] 장마철 병해충 예방",
            "body": "배수와 통풍을 강화하고, 강수 전후 예방 위주 살균, 살충 일정을 조정하세요.",
            "source": "farmguard",
            "category": "rain",
        },
        {
            "title": f"[{crop_name}] 폭염기 열피해, 결로 관리",
            "body": "오전, 저녁 관수, 차광막 활용, 고온다습 시간대 방제를 피하세요.",
            "source": "farmguard",
            "category": "heat",
        },
        {
            "title": f"[{crop_name}] 태풍, 강풍 대비",
            "body": "지주, 막음막 점검, 낙과, 도복 후 병해 발생 여부를 확인하세요.",
            "source": "farmguard",
            "category": "typhoon",
        },
    ]


def _weather_hazards(kma_daily: dict[str, dict], today: date | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    hazards = []
    for i in range(1, 6):
        dt = today + timedelta(days=i)
        key = dt.isoformat()
        w = kma_daily.get(key)
        if not w:
            continue
        pop = w.get("pop_max", 0)
        tmax = w.get("temp_max", 20)
        tmin = w.get("temp_min", 10)
        pcp = w.get("rain_forecast", 0)
        label = f"{dt.month}/{dt.day}"

        if pop >= 60 or pcp >= 10:
            hazards.append({
                "date": key, "label": label, "type": "heavy_rain",
                "title": "강수, 장마 주의", "level": "주의" if pop < 80 else "경보",
                "message": f"강수확률 {pop:.0f}%, 예상 강수 {pcp:.1f}mm",
                "source": "kma",
            })
        if tmax >= 33:
            hazards.append({
                "date": key, "label": label, "type": "heat_wave",
                "title": "폭염 주의", "level": "주의" if tmax < 35 else "경보",
                "message": f"최고기온 {tmax:.0f}°C 예상",
                "source": "kma",
            })
        if tmin <= 0:
            hazards.append({
                "date": key, "label": label, "type": "cold_snap",
                "title": "한파, 결빙 주의", "level": "경보",
                "message": f"최저기온 {tmin:.0f}°C 예상",
                "source": "kma",
            })
        if w.get("wind_speed", 0) >= 8:
            hazards.append({
                "date": key, "label": label, "type": "strong_wind",
                "title": "강풍 주의", "level": "주의",
                "message": f"풍속 {w['wind_speed']:.1f}m/s 예상",
                "source": "kma",
            })
    return hazards


def build_disaster_center(
    crop_name: str,
    nongsaro_items: list[dict] | None = None,
    vilage_fcst: list[dict] | None = None,
) -> dict[str, Any]:
    crop = get_crop_or_default(crop_name)
    season = crop.get("season", "summer")

    articles: list[dict[str, str]] = []
    for item in nongsaro_items or []:
        norm = _normalize_nongsaro_item(item)
        if norm:
            articles.append(norm)
    if not articles:
        articles = _demo_articles(crop["name_ko"])

    checklists = list(_CROP_CHECKLISTS.get("year_round", []))
    if season in ("summer", "year_round"):
        checklists = _CROP_CHECKLISTS.get("summer", []) + checklists
    if season in ("winter", "year_round"):
        checklists = _CROP_CHECKLISTS.get("winter", []) + checklists

    kma_daily = parse_vilage_daily(vilage_fcst or [])
    hazards = _weather_hazards(kma_daily)

    priority = hazards[0] if hazards else None
    return {
        "crop_name": crop["name_ko"],
        "season": season,
        "priority_alert": priority,
        "weather_hazards": hazards,
        "checklists": checklists,
        "articles": articles[:12],
        "summary": (
            f"{priority['title']}: {priority['message']}"
            if priority
            else f"{crop['name_ko']} 재해예방 체크리스트 {len(checklists)}종을 확인하세요."
        ),
    }
