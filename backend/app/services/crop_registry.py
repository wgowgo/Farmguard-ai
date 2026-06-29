"""작물 마스터 레지스트리 (crops.json)"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "crops.json"
_DEFAULT_CROP = "고추"


@lru_cache(maxsize=1)
def _load_raw() -> list[dict[str, Any]]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def list_crops() -> list[dict[str, Any]]:
    return [
        {
            "id": c["id"],
            "name_ko": c["name_ko"],
            "soil_code": c["soil_code"],
            "category": c["category"],
            "season": c["season"],
            "target_pests": c["target_pests"],
        }
        for c in _load_raw()
    ]


def get_crop(name_or_id: str | None) -> dict[str, Any] | None:
    if not name_or_id:
        return None
    key = name_or_id.strip()
    for c in _load_raw():
        if c["name_ko"] == key or c["id"] == key:
            return c
    return None


def get_crop_or_default(name_or_id: str | None) -> dict[str, Any]:
    return get_crop(name_or_id) or get_crop(_DEFAULT_CROP) or _load_raw()[0]


def get_target_pests(crop_name: str) -> list[str]:
    crop = get_crop_or_default(crop_name)
    return list(crop.get("target_pests") or [])


def get_soil_code(crop_name: str) -> str:
    crop = get_crop_or_default(crop_name)
    return crop.get("soil_code", "00013")


def crop_stage_risk_for(crop_name: str, days_since_planting: int | None) -> float:
    """작물별 생육 민감 구간 기반 위험도"""
    if days_since_planting is None:
        return 20.0
    crop = get_crop_or_default(crop_name)
    start, end = crop.get("growth_sensitive_days") or [30, 120]
    d = days_since_planting
    if d < start:
        return 15.0
    if start <= d <= end:
        return 70.0
    if d <= end + 30:
        return 45.0
    return 25.0
