"""흙토람 비료처방 → 시비 캘린더"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.services.crop_registry import get_crop_or_default

_UNIT = "kg/10a"

# 작물별 시비 일정 (정식일 기준 offset 일)
_SCHEDULE_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "벼": [
        {"id": "basal", "label": "이앙 전 기비", "offset_days": -7, "slot": "pre"},
        {"id": "tillering", "label": "분억기 추비", "offset_days": 25, "slot": "post1"},
        {"id": "heading", "label": "출수 전 추비", "offset_days": 55, "slot": "post2"},
    ],
    "default": [
        {"id": "basal", "label": "정식 전 기비", "offset_days": -3, "slot": "pre"},
        {"id": "mid", "label": "생육 중기 추비", "offset_days": 40, "slot": "post1"},
        {"id": "late", "label": "착과, 비대기 추비", "offset_days": 70, "slot": "post2"},
    ],
}

_DEFAULT_NPK: dict[str, dict[str, float]] = {
    "pre": {"n": 4.9, "p": 3.2, "k": 3.0},
    "post1": {"n": 3.5, "p": 0.0, "k": 1.2},
    "post2": {"n": 2.0, "p": 0.0, "k": 0.8},
}


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _pick(raw: dict, *keys: str) -> Any:
    for k in keys:
        if k in raw and raw[k] not in (None, ""):
            return raw[k]
    return None


def extract_fertilizer_amounts(raw: dict | None) -> dict[str, dict[str, float | None]]:
    """API 응답 필드명 변형 대응"""
    raw = raw or {}
    return {
        "pre": {
            "n": _to_float(_pick(raw, "pre_Fert_N", "preFertN", "base_N", "basal_N")),
            "p": _to_float(_pick(raw, "pre_Fert_P", "preFertP", "base_P", "basal_P")),
            "k": _to_float(_pick(raw, "pre_Fert_K", "preFertK", "base_K", "basal_K")),
        },
        "post1": {
            "n": _to_float(_pick(raw, "post_Fert_N", "postFertN", "fst_Sb_N", "top1_N")),
            "p": _to_float(_pick(raw, "post_Fert_P", "postFertP", "fst_Sb_P", "top1_P")),
            "k": _to_float(_pick(raw, "post_Fert_K", "postFertK", "fst_Sb_K", "top1_K")),
        },
        "post2": {
            "n": _to_float(_pick(raw, "snd_Sb_N", "top2_N", "late_N")),
            "p": _to_float(_pick(raw, "snd_Sb_P", "top2_P", "late_P")),
            "k": _to_float(_pick(raw, "snd_Sb_K", "top2_K", "late_K")),
        },
    }


def _fill_defaults(amounts: dict[str, dict[str, float | None]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for slot, defaults in _DEFAULT_NPK.items():
        src = amounts.get(slot, {})
        out[slot] = {
            "n": src.get("n") if src.get("n") is not None else defaults["n"],
            "p": src.get("p") if src.get("p") is not None else defaults["p"],
            "k": src.get("k") if src.get("k") is not None else defaults["k"],
        }
    return out


def _schedule_for_crop(crop_name: str) -> list[dict[str, Any]]:
    if crop_name == "벼":
        return _SCHEDULE_TEMPLATES["벼"]
    return _SCHEDULE_TEMPLATES["default"]


def _timing_label(offset: int) -> str:
    if offset < 0:
        return f"정식 {abs(offset)}일 전"
    if offset == 0:
        return "정식일"
    return f"정식 후 {offset}일"


def build_fertilizer_calendar(
    crop_name: str,
    planting_date: date | None,
    fert_raw: dict | None = None,
    *,
    reference_date: date | None = None,
) -> dict[str, Any]:
    crop = get_crop_or_default(crop_name)
    amounts = _fill_defaults(extract_fertilizer_amounts(fert_raw))
    template = _schedule_for_crop(crop["name_ko"])
    today = reference_date or date.today()
    base = planting_date or today

    events = []
    for step in template:
        slot = step["slot"]
        npk = amounts.get(slot, amounts["pre"])
        event_date = base + timedelta(days=step["offset_days"])
        events.append({
            "id": step["id"],
            "label": step["label"],
            "timing_label": _timing_label(step["offset_days"]),
            "date": event_date.isoformat(),
            "offset_days": step["offset_days"],
            "nitrogen": npk["n"],
            "phosphate": npk["p"],
            "potassium": npk["k"],
            "unit": _UNIT,
            "status": _event_status(event_date, today),
            "notes": f"질소 {npk['n']}, 인산 {npk['p']}, 칼리 {npk['k']} ({_UNIT})",
        })

    upcoming = [e for e in events if e["status"] in ("upcoming", "today")]
    next_event = upcoming[0] if upcoming else None

    total_n = sum(e["nitrogen"] for e in events)
    total_p = sum(e["phosphate"] for e in events)
    total_k = sum(e["potassium"] for e in events)

    has_api = bool(fert_raw and any(
        _to_float(fert_raw.get(k)) is not None
        for k in fert_raw
        if "Fert" in k or "Sb" in k or "fert" in k.lower()
    ))

    return {
        "crop_name": crop["name_ko"],
        "planting_date": planting_date.isoformat() if planting_date else None,
        "source": "soil_api" if has_api else "estimated",
        "unit": _UNIT,
        "total": {"nitrogen": round(total_n, 1), "phosphate": round(total_p, 1), "potassium": round(total_k, 1)},
        "next_event": next_event,
        "events": events,
        "summary": (
            f"다음 시비: {next_event['label']} ({next_event['timing_label']})"
            if next_event
            else "예정된 시비 일정이 없습니다"
        ),
        "raw_prescription": fert_raw or {},
    }


def _event_status(event_date: date, today: date) -> str:
    if event_date < today:
        return "past"
    if event_date == today:
        return "today"
    if (event_date - today).days <= 14:
        return "upcoming"
    return "scheduled"
