"""농사로 등록농약 + 안전사용지침 → 방제 처방 카드"""
from __future__ import annotations

from typing import Any


def _s(item: dict, *keys: str) -> str:
    for k in keys:
        v = item.get(k)
        if v not in (None, ""):
            return str(v).strip()
    return ""


def normalize_registration(item: dict) -> dict[str, str]:
    return {
        "brand_name": _s(item, "pestiBrandName", "brandNm", "brandName"),
        "product_name": _s(item, "prdlstNm", "productName", "pestiKorName"),
        "crop_name": _s(item, "cropName", "cropsNm", "cropNm"),
        "pest_name": _s(item, "diseaseWeedName", "applcDbyhs", "pestName"),
        "purpose": _s(item, "useName", "prpos", "purpose"),
        "action_type": _s(item, "actnNm", "actionType"),
        "company": _s(item, "cmpnyNm", "companyName"),
        "confirmed": _s(item, "dcsnAt", "confirmYn"),
    }


def normalize_manual(item: dict) -> dict[str, str]:
    return {
        "title": _s(item, "cntntsSj", "title"),
        "product_name": _s(item, "prdlstCodeNm", "productName", "pestiKorName"),
        "file_url": _s(item, "fileUrl", "url"),
        "file_name": _s(item, "fileNm", "fileName"),
        "reform_date": _s(item, "reformYm", "reformDate"),
        "dilution": _s(item, "dilutUnit", "thiningMul", "dilution"),
        "safe_period": _s(item, "prcusePrd", "safeUsePeriod", "safePeriod"),
        "harvest_before_days": _s(item, "harvAfMth", "harvestBeforeDays", "harvestInterval"),
    }


def _match_score(reg: dict, manual: dict) -> int:
    brand = reg["brand_name"].lower()
    product = reg["product_name"].lower()
    m_product = manual["product_name"].lower()
    m_title = manual["title"].lower()
    score = 0
    if brand and brand in m_product:
        score += 3
    if brand and brand in m_title:
        score += 2
    if product and product in m_product:
        score += 3
    if product and product in m_title:
        score += 2
    return score


def build_spray_prescriptions(
    crop_name: str,
    pest_name: str,
    reg_items: list[dict] | None,
    manual_items: list[dict] | None,
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    registrations = [normalize_registration(i) for i in (reg_items or [])]
    manuals = [normalize_manual(i) for i in (manual_items or [])]

    cards: list[dict[str, Any]] = []
    for reg in registrations[:limit]:
        best_manual = None
        best_score = 0
        for m in manuals:
            sc = _match_score(reg, m)
            if sc > best_score:
                best_score = sc
                best_manual = m

        brand = reg["brand_name"] or reg["product_name"] or "등록 농약"
        card: dict[str, Any] = {
            "brand_name": brand,
            "product_name": reg["product_name"],
            "crop_name": reg["crop_name"] or crop_name,
            "pest_name": reg["pest_name"] or pest_name,
            "purpose": reg["purpose"],
            "action_type": reg["action_type"],
            "company": reg["company"],
            "confirmed": reg["confirmed"],
            "dilution": best_manual["dilution"] if best_manual else "",
            "safe_period": best_manual["safe_period"] if best_manual else "",
            "harvest_before_days": best_manual["harvest_before_days"] if best_manual else "",
            "manual_title": best_manual["title"] if best_manual else "",
            "manual_url": best_manual["file_url"] if best_manual else "",
            "manual_matched": best_score >= 2,
            "usage_note": _usage_note(reg, best_manual),
            "source": "nongsaro",
        }
        cards.append(card)

    if not cards and manuals:
        for m in manuals[:3]:
            cards.append({
                "brand_name": m["product_name"] or m["title"],
                "product_name": m["product_name"],
                "crop_name": crop_name,
                "pest_name": pest_name,
                "purpose": "안전사용지침",
                "action_type": "",
                "company": "",
                "confirmed": "",
                "dilution": m["dilution"],
                "safe_period": m["safe_period"],
                "harvest_before_days": m["harvest_before_days"],
                "manual_title": m["title"],
                "manual_url": m["file_url"],
                "manual_matched": True,
                "usage_note": m["title"] or "안전사용지침 PDF를 확인하세요.",
                "source": "nongsaro_manual",
            })

    return cards


def _usage_note(reg: dict, manual: dict | None) -> str:
    parts = []
    if reg["purpose"]:
        parts.append(reg["purpose"])
    if reg["action_type"]:
        parts.append(reg["action_type"])
    if manual and manual.get("dilution"):
        parts.append(f"희석 {manual['dilution']}")
    if manual and manual.get("safe_period"):
        parts.append(f"안전기간 {manual['safe_period']}")
    if manual and manual.get("harvest_before_days"):
        parts.append(f"수확 전 {manual['harvest_before_days']}일")
    if manual and manual.get("file_url") and not parts:
        parts.append("안전사용지침 PDF 참고")
    return ", ".join(parts) if parts else "등록 현황 확인 후 라벨, 안전지침을 따르세요."
