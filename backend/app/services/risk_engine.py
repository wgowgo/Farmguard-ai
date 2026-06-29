"""위험도 산정 엔진 - 설명 가능한 점수식"""
import math
from datetime import date
from typing import Optional


def clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


def risk_level(score: float) -> str:
    if score < 40:
        return "낮음"
    if score < 70:
        return "주의"
    if score < 85:
        return "위험"
    return "매우 위험"


def calc_weather_risk(
    rain_6h: float = 0,
    humidity_24h: float = 50,
    dew_time_24h: float = 0,
    temp_min: float = 15,
    temp_max: float = 25,
    soil_moisture: float = 20,
    wind_speed: float = 2,
    rain_forecast: float = 0,
) -> tuple[float, dict]:
    """기상 위험도 0~100"""
    humidity_score = clamp((humidity_24h - 60) * 2) if humidity_24h > 60 else humidity_24h * 0.3
    dew_score = clamp(dew_time_24h * 8)
    rain_score = clamp(rain_6h * 6 + rain_forecast * 4)
    temp_score = 0
    if temp_min < 10 or temp_max > 35:
        temp_score = 30
    elif 20 <= temp_max <= 30 and humidity_24h > 70:
        temp_score = 40
    soil_score = clamp((soil_moisture - 25) * 2) if soil_moisture > 25 else 0
    wind_penalty = -5 if wind_speed > 5 else 0

    score = clamp(
        humidity_score * 0.30 + dew_score * 0.25 + rain_score * 0.20
        + temp_score * 0.15 + soil_score * 0.10 + wind_penalty
    )
    factors = {
        "humidity_score": round(humidity_score, 1),
        "dew_score": round(dew_score, 1),
        "rain_score": round(rain_score, 1),
        "temp_score": round(temp_score, 1),
        "soil_moisture_score": round(soil_score, 1),
    }
    return score, factors


def calc_surveillance_risk(pests: list[dict], target_crop: str = "고추") -> tuple[float, list[dict]]:
    """병해충 예찰 위험도"""
    if not pests:
        return 0, []

    details = []
    total = 0.0
    for p in pests:
        iq = float(p.get("occurrence_value") or p.get("iqVl") or 0)
        dist = float(p.get("occurrence_distance") or p.get("ocrdst") or 3)
        crop = p.get("crop_name") or p.get("crpTynm") or ""
        days_old = p.get("days_since_report", 7)

        dist_w = math.exp(-dist / 1.5)
        time_w = math.exp(-days_old / 14)
        crop_w = 1.2 if target_crop in crop else 0.8
        score = iq * dist_w * time_w * crop_w
        total += score
        details.append({
            "pest_name": p.get("pest_name") or p.get("dbyhsNm"),
            "score": round(score, 2),
            "distance_km": dist,
            "occurrence_value": iq,
        })

    normalized = clamp(total / max(len(pests), 1) * 1.2)
    details.sort(key=lambda x: x["score"], reverse=True)
    return normalized, details


def calc_soil_vulnerability(
    acidity: float = 6.5,
    organic_matter: float = 2.5,
    ec: float = 0.5,
    available_phosphate: float = 100,
) -> tuple[float, dict]:
    """토양 취약성 0~100"""
    acid_score = abs(acidity - 6.0) * 15
    om_score = clamp((2.0 - organic_matter) * 20) if organic_matter < 2.0 else 0
    ec_score = clamp((ec - 1.0) * 30) if ec > 1.0 else 0
    p_score = clamp((80 - available_phosphate) * 0.3) if available_phosphate < 80 else 0

    score = clamp(acid_score * 0.25 + om_score * 0.30 + ec_score * 0.25 + p_score * 0.20)
    return score, {
        "acidity_deviation": round(acid_score, 1),
        "organic_matter_deficit": round(om_score, 1),
        "ec_excess": round(ec_score, 1),
        "phosphate_deficit": round(p_score, 1),
    }


def calc_crop_stage_risk(
    planting_date: Optional[date],
    today: Optional[date] = None,
    crop_name: str = "고추",
) -> float:
    """재배 시기 민감도 (작물별)"""
    if not planting_date:
        return 20
    today = today or date.today()
    days = (today - planting_date).days
    from app.services.crop_registry import crop_stage_risk_for
    return crop_stage_risk_for(crop_name, days)


def calc_final_risk(
    weather_risk: float,
    pest_risk: float,
    soil_risk: float,
    crop_stage_risk: float = 0,
    feedback_risk: float = 0,
) -> float:
    return clamp(
        0.40 * weather_risk
        + 0.30 * pest_risk
        + 0.15 * soil_risk
        + 0.10 * crop_stage_risk
        + 0.05 * feedback_risk
    )
