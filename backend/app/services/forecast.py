"""7일 예보, 방제 타이밍, 지도 레이어"""
import math
import random
from datetime import date, datetime, timedelta
from typing import Optional

from app.services.risk_engine import (
    calc_weather_risk, calc_final_risk, calc_surveillance_risk,
    calc_soil_vulnerability, calc_crop_stage_risk, risk_level,
)


def _parse_pcp_mm(value: str) -> float:
    if not value or value in ("강수없음", "-"):
        return 0.0
    s = str(value).replace("mm", "").strip()
    if "미만" in s:
        return 0.5
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_vilage_daily(items: list[dict]) -> dict[str, dict]:
    """기상청 단기예보(getVilageFcst) → 일별 기상 dict (ISO date 키)"""
    by_date: dict[str, dict] = {}
    for item in items:
        d = item.get("fcstDate", "")
        if len(d) != 8:
            continue
        if d not in by_date:
            by_date[d] = {
                "pop_max": 0.0, "reh_sum": 0.0, "reh_n": 0,
                "wsd_max": 0.0, "pcp_sum": 0.0, "tmx": None, "tmn": None,
            }
        cat = item.get("category")
        val = item.get("fcstValue", "")
        bucket = by_date[d]
        try:
            if cat == "POP":
                bucket["pop_max"] = max(bucket["pop_max"], float(val))
            elif cat == "REH":
                bucket["reh_sum"] += float(val)
                bucket["reh_n"] += 1
            elif cat == "WSD":
                bucket["wsd_max"] = max(bucket["wsd_max"], float(val))
            elif cat == "PCP":
                bucket["pcp_sum"] += _parse_pcp_mm(str(val))
            elif cat == "TMX":
                bucket["tmx"] = float(val)
            elif cat == "TMN":
                bucket["tmn"] = float(val)
            elif cat == "TMP":
                v = float(val)
                bucket["tmx"] = v if bucket["tmx"] is None else max(bucket["tmx"], v)
                bucket["tmn"] = v if bucket["tmn"] is None else min(bucket["tmn"], v)
        except (TypeError, ValueError):
            continue

    out: dict[str, dict] = {}
    for d, b in sorted(by_date.items()):
        iso = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        reh = b["reh_sum"] / b["reh_n"] if b["reh_n"] else 60.0
        pcp = b["pcp_sum"]
        out[iso] = {
            "rain_6h": min(pcp, 15),
            "humidity_24h": reh,
            "dew_time_24h": 5.0 if reh > 80 else (2.0 if reh > 70 else 0.5),
            "temp_min": b["tmn"] if b["tmn"] is not None else 14.0,
            "temp_max": b["tmx"] if b["tmx"] is not None else 24.0,
            "soil_moisture": 20 + min(pcp, 10),
            "wind_speed": b["wsd_max"] or 2.0,
            "rain_forecast": pcp,
            "pop_max": b["pop_max"],
            "source": "kma",
        }
    return out


def _demo_weather_for_day(base_date: date, offset: int) -> dict:
    """날짜별 데모 기상 (결정적 시드)"""
    rng = random.Random(base_date.toordinal() + offset * 17)
    rain_cycle = (offset % 5)
    rain_forecast = rng.uniform(8, 25) if rain_cycle in (2, 3) else rng.uniform(0, 3)
    humidity = 55 + rng.uniform(0, 35) + (10 if rain_cycle in (2, 3) else 0)
    return {
        "rain_6h": rng.uniform(0, 15) if rain_cycle == 2 else rng.uniform(0, 2),
        "humidity_24h": min(humidity, 95),
        "dew_time_24h": rng.uniform(2, 8) if humidity > 75 else rng.uniform(0, 2),
        "temp_min": 14 + rng.uniform(-2, 4),
        "temp_max": 22 + rng.uniform(0, 10),
        "soil_moisture": 18 + rng.uniform(0, 15),
        "wind_speed": rng.uniform(1, 6),
        "rain_forecast": rain_forecast,
    }


def build_forecast_7d(
    field_id: int,
    today: date,
    base_pest_risk: float,
    base_soil_risk: float,
    crop_stage_risk: float,
    top_pest_name: str,
    historical: list[dict],
    kma_daily: dict[str, dict] | None = None,
) -> list[dict]:
    """과거 7일 + 향후 7일 위험도 예보 (kma_daily 있으면 단기예보 반영)"""
    result = []

    hist_map = {h["date"]: h["avg_risk"] for h in historical}
    for d in range(6, -1, -1):
        dt = today - timedelta(days=d)
        key = dt.isoformat()
        if key in hist_map and hist_map[key] > 0:
            avg = hist_map[key]
        else:
            w = _demo_weather_for_day(today, -d)
            wr, _ = calc_weather_risk(**w)
            avg = calc_final_risk(wr, base_pest_risk, base_soil_risk, crop_stage_risk)
        result.append({
            "date": key,
            "avg_risk": round(avg, 1),
            "type": "observed",
            "label": _day_label(dt, today),
        })

    kma_daily = kma_daily or {}
    for d in range(1, 8):
        dt = today + timedelta(days=d)
        key = dt.isoformat()
        if key in kma_daily:
            w = kma_daily[key]
            source = "kma"
        else:
            w = _demo_weather_for_day(today, d)
            source = "model"
        wr, _ = calc_weather_risk(
            rain_6h=w.get("rain_6h", 0),
            humidity_24h=w.get("humidity_24h", 60),
            dew_time_24h=w.get("dew_time_24h", 0),
            temp_min=w.get("temp_min", 15),
            temp_max=w.get("temp_max", 25),
            soil_moisture=w.get("soil_moisture", 20),
            wind_speed=w.get("wind_speed", 2),
            rain_forecast=w.get("rain_forecast", 0),
        )
        pest_adj = base_pest_risk * (1 + 0.05 * d)
        final = calc_final_risk(wr, pest_adj, base_soil_risk, crop_stage_risk)
        point: dict = {
            "date": key,
            "avg_risk": round(final, 1),
            "type": "forecast",
            "label": _day_label(dt, today),
            "top_pest": top_pest_name,
            "rain_forecast_mm": round(w.get("rain_forecast", 0), 1),
            "source": source,
        }
        if w.get("pop_max") is not None:
            point["pop_max"] = round(w["pop_max"])
        result.append(point)

    return result


def _day_label(dt: date, today: date) -> str:
    diff = (dt - today).days
    if diff == 0:
        return "오늘"
    if diff == 1:
        return "내일"
    if diff == -1:
        return "어제"
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    return f"{weekdays[dt.weekday()]}({dt.month}/{dt.day})"


def build_spray_timing(today: date | None = None) -> dict:
    """오늘, 내일 방제 가능 시간대"""
    today = today or date.today()
    rng = random.Random(today.toordinal())

    hours = []
    rain_start_hour: Optional[int] = None
    for h in range(6, 22):
        rain_prob = 0
        if h >= 17:
            rain_prob = rng.uniform(40, 90) if rng.random() > 0.3 else rng.uniform(5, 20)
        elif h >= 14:
            rain_prob = rng.uniform(10, 40)
        else:
            rain_prob = rng.uniform(0, 15)

        wind = rng.uniform(0.5, 5.5)
        humidity = rng.uniform(50, 85)
        suitable = rain_prob < 30 and wind < 4.5 and humidity < 85

        if rain_prob >= 60 and rain_start_hour is None:
            rain_start_hour = h

        hours.append({
            "hour": h,
            "label": f"{h:02d}:00",
            "rain_prob": round(rain_prob),
            "wind_speed": round(wind, 1),
            "humidity": round(humidity),
            "suitable": suitable,
        })

    windows = []
    start = None
    for h in hours:
        if h["suitable"] and start is None:
            start = h["hour"]
        elif not h["suitable"] and start is not None:
            windows.append({"from": start, "to": h["hour"], "label": f"{start:02d}:00~{h['hour']:02d}:00"})
            start = None
    if start is not None:
        windows.append({"from": start, "to": 22, "label": f"{start:02d}:00~22:00"})

    best = windows[0] if windows else None
    rain_msg = f"{rain_start_hour:02d}:00부터 강수 예보" if rain_start_hour else "오늘 저녁까지 강수 가능성 낮음"

    return {
        "date": today.isoformat(),
        "best_window": best,
        "all_windows": windows,
        "rain_warning": rain_msg,
        "rain_start_hour": rain_start_hour,
        "hourly": hours,
        "summary": _spray_summary(best, rain_start_hour),
    }


def _spray_summary(best: Optional[dict], rain_hour: Optional[int]) -> str:
    if best and rain_hour:
        return f"오늘 {best['label']} 방제 적기. {rain_hour:02d}:00 이전 마무리 권장."
    if best:
        return f"오늘 {best['label']} 방제에 적합합니다."
    return "오늘은 바람, 강수 예보로 방제를 피하고 내일 오전을 검토하세요."


def build_spray_timing_from_kma(fcst_items: list[dict], today: date | None = None) -> dict:
    """기상청 초단기예보 기반 방제 타이밍 (POP, WSD, REH)"""
    today = today or date.today()
    if not fcst_items:
        return build_spray_timing(today)

    by_hour: dict[int, dict[str, float]] = {}
    for item in fcst_items:
        cat = item.get("category")
        t = item.get("fcstTime", "")
        if len(t) < 10:
            continue
        hour = int(t[8:10])
        if hour not in by_hour:
            by_hour[hour] = {}
        try:
            by_hour[hour][cat] = float(item.get("fcstValue", 0))
        except (TypeError, ValueError):
            pass

    hours = []
    rain_start_hour: int | None = None
    for h in range(6, 22):
        vals = by_hour.get(h, {})
        rain_prob = vals.get("POP", vals.get("RN1", 0))
        wind = vals.get("WSD", 2.0)
        humidity = vals.get("REH", 60)
        suitable = rain_prob < 30 and wind < 4.5 and humidity < 85
        if rain_prob >= 60 and rain_start_hour is None:
            rain_start_hour = h
        hours.append({
            "hour": h,
            "label": f"{h:02d}:00",
            "rain_prob": round(rain_prob),
            "wind_speed": round(wind, 1),
            "humidity": round(humidity),
            "suitable": suitable,
            "source": "kma",
        })

    if not hours:
        return build_spray_timing(today)

    windows = []
    start = None
    for h in hours:
        if h["suitable"] and start is None:
            start = h["hour"]
        elif not h["suitable"] and start is not None:
            windows.append({"from": start, "to": h["hour"], "label": f"{start:02d}:00~{h['hour']:02d}:00"})
            start = None
    if start is not None:
        windows.append({"from": start, "to": 22, "label": f"{start:02d}:00~22:00"})

    best = windows[0] if windows else None
    rain_msg = f"{rain_start_hour:02d}:00부터 강수 예보" if rain_start_hour else "오늘 저녁까지 강수 가능성 낮음"
    return {
        "date": today.isoformat(),
        "best_window": best,
        "all_windows": windows,
        "rain_warning": rain_msg,
        "rain_start_hour": rain_start_hour,
        "hourly": hours,
        "summary": _spray_summary(best, rain_start_hour),
        "source": "kma",
    }


def build_map_layers(
    lat: float, lng: float, pests: list[dict],
) -> dict:
    """필지 + 주변 병해충 거리 원"""
    circles = []
    markers = []

    for i, p in enumerate(pests):
        dist_km = float(p.get("distance_km") or p.get("occurrence_distance") or 2)
        circles.append({
            "center": {"lat": lat, "lng": lng},
            "radius_m": dist_km * 1000,
            "pest_name": p.get("name") or p.get("pest_name"),
            "intensity": p.get("value") or p.get("occurrence_value"),
            "distance_km": dist_km,
        })
        markers.append({
            "lat": lat, "lng": lng,
            "pest_name": p.get("name") or p.get("pest_name"),
            "value": p.get("value") or p.get("occurrence_value"),
            "distance_km": dist_km,
            "note": f"반경 {dist_km}km",
        })

    return {
        "field": {"lat": lat, "lng": lng},
        "circles": circles,
        "pest_markers": markers,
    }


def _offset_latlng(lat: float, lng: float, dist_km: float, bearing_deg: float) -> tuple[float, float]:
    R = 6371.0
    br = math.radians(bearing_deg)
    lat1, lng1 = math.radians(lat), math.radians(lng)
    lat2 = math.asin(
        math.sin(lat1) * math.cos(dist_km / R)
        + math.cos(lat1) * math.sin(dist_km / R) * math.cos(br)
    )
    lng2 = lng1 + math.atan2(
        math.sin(br) * math.sin(dist_km / R) * math.cos(lat1),
        math.cos(dist_km / R) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lng2)


def build_weekly_report(
    field: dict,
    forecast: list[dict],
    spray: dict,
    top_pests: list[dict],
    recommendation: Optional[dict],
) -> dict:
    """주간 리포트 텍스트 (공유용)"""
    future = [f for f in forecast if f.get("type") == "forecast"]
    peak = max(future, key=lambda x: x["avg_risk"]) if future else None
    lines = [
        f"🌾 팜가드 AI 주간 리포트",
        f"📍 {field.get('address', '내 농지')}",
        f"🌱 작물: {field.get('crop_name', '고추')}",
        "",
        "【 이번 주 위험 요약 】",
    ]
    if peak:
        lines.append(f"• 최고 위험 예상: {peak['label']} ({peak['avg_risk']}점)")
    if top_pests:
        lines.append(f"• 주의 병해충: {', '.join(p.get('pest_name', p.get('name', '')) for p in top_pests[:3])}")
    lines.extend(["", "【 방제 타이밍 】", f"• {spray.get('summary', '')}"])
    if recommendation:
        lines.extend(["", "【 권장 행동 】"])
        for i, a in enumerate(recommendation.get("action_list", [])[:3], 1):
            lines.append(f"{i}. {a}")
    lines.extend(["", "— 팜가드 AI | data.go.kr 기반"])
    text = "\n".join(lines)

    return {
        "title": f"팜가드 AI 주간 리포트 - {field.get('crop_name', '고추')}",
        "text": text,
        "generated_at": datetime.now().isoformat(),
        "peak_day": peak,
        "spray_summary": spray.get("summary"),
    }
