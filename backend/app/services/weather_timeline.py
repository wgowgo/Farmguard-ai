"""팜맵 관측 + KMA 예보 → 72시간 기상 타임라인"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


def _parse_fcst_dt(fcst_date: str, fcst_time: str) -> datetime | None:
    t = (fcst_time or "").zfill(4)
    if len(fcst_date) != 8 or len(t) < 4:
        return None
    try:
        return datetime.strptime(f"{fcst_date}{t[:4]}", "%Y%m%d%H%M")
    except ValueError:
        return None


def _dew_risk(humidity: float, temp: float) -> str:
    if humidity >= 85 and 5 <= temp <= 25:
        return "high"
    if humidity >= 75:
        return "medium"
    return "low"


def _parse_ultra_hourly(items: list[dict]) -> dict[datetime, dict[str, float]]:
    by_dt: dict[datetime, dict[str, float]] = {}
    for item in items:
        t = item.get("fcstTime", "")
        if len(t) < 12:
            continue
        try:
            dt = datetime.strptime(t[:12], "%Y%m%d%H%M")
        except ValueError:
            continue
        cat = item.get("category")
        try:
            val = float(item.get("fcstValue", 0))
        except (TypeError, ValueError):
            continue
        if dt not in by_dt:
            by_dt[dt] = {}
        by_dt[dt][cat] = val
    return by_dt


def _parse_vilage_hourly(items: list[dict]) -> dict[datetime, dict[str, float]]:
    by_dt: dict[datetime, dict[str, float]] = {}
    for item in items:
        dt = _parse_fcst_dt(str(item.get("fcstDate", "")), str(item.get("fcstTime", "")))
        if not dt:
            continue
        cat = item.get("category")
        val = item.get("fcstValue", "")
        if dt not in by_dt:
            by_dt[dt] = {}
        if cat in ("POP", "REH", "WSD", "TMP"):
            try:
                by_dt[dt][cat] = float(val)
            except (TypeError, ValueError):
                pass
        elif cat == "PCP":
            from app.services.forecast import _parse_pcp_mm
            by_dt[dt]["RN1"] = _parse_pcp_mm(str(val))
    return by_dt


def build_weather_timeline(
    observed: list[dict] | None = None,
    ultra_fcst: list[dict] | None = None,
    vilage_fcst: list[dict] | None = None,
    *,
    now: datetime | None = None,
    hours: int = 72,
) -> dict[str, Any]:
    now = now or datetime.now()
    end = now + timedelta(hours=hours)
    points: list[dict[str, Any]] = []

    for obs in observed or []:
        t = obs.get("time")
        if not t:
            continue
        try:
            dt = datetime.fromisoformat(str(t).replace("Z", "+00:00").split("+")[0])
        except ValueError:
            continue
        if dt < now - timedelta(hours=24) or dt > end:
            continue
        temp = float(obs.get("temp") or 20)
        humidity = float(obs.get("humidity") or 60)
        rain = float(obs.get("rain") or 0)
        dew = float(obs.get("dew_time") or 0)
        points.append({
            "time": dt.isoformat(),
            "label": dt.strftime("%m/%d %H:%M"),
            "temp": round(temp, 1),
            "humidity": round(humidity, 1),
            "rain_mm": round(rain, 1),
            "rain_prob": 100 if rain > 0 else 0,
            "wind_speed": None,
            "dew_time": round(dew, 1),
            "dew_risk": _dew_risk(humidity, temp),
            "period": "observed",
            "source": "farmmap",
        })

    ultra_by = _parse_ultra_hourly(ultra_fcst or [])
    vilage_by = _parse_vilage_hourly(vilage_fcst or [])

    forecast_slots: dict[datetime, dict] = {}
    for dt, vals in {**vilage_by, **ultra_by}.items():
        if dt < now or dt > end:
            continue
        forecast_slots[dt] = vals

    for dt in sorted(forecast_slots.keys()):
        vals = forecast_slots[dt]
        temp = vals.get("T1H", vals.get("TMP", 20))
        humidity = vals.get("REH", 60)
        pop = vals.get("POP", 0)
        rain = vals.get("RN1", 0)
        wind = vals.get("WSD", None)
        points.append({
            "time": dt.isoformat(),
            "label": dt.strftime("%m/%d %H:%M"),
            "temp": round(temp, 1),
            "humidity": round(humidity, 1),
            "rain_mm": round(rain, 1),
            "rain_prob": round(pop, 0),
            "wind_speed": round(wind, 1) if wind is not None else None,
            "dew_time": None,
            "dew_risk": _dew_risk(humidity, temp),
            "period": "forecast",
            "source": "kma",
        })

    points.sort(key=lambda p: p["time"])
    seen = set()
    unique = []
    for p in points:
        key = p["time"][:13]
        if key in seen:
            continue
        seen.add(key)
        unique.append(p)

    high_dew = [p for p in unique if p["dew_risk"] == "high"]
    rain_hours = [p for p in unique if p["rain_prob"] >= 60 or (p["rain_mm"] or 0) >= 1]

    return {
        "hours": hours,
        "points": unique[:48],
        "summary": {
            "high_dew_hours": len(high_dew),
            "rain_risk_hours": len(rain_hours),
            "next_rain": rain_hours[0] if rain_hours else None,
            "peak_humidity": max((p["humidity"] for p in unique), default=0),
        },
        "highlights": [h for h in [
            f"결로, 고습 위험 시간대 {len(high_dew)}건" if high_dew else None,
            f"강수 예상 {rain_hours[0]['label']}" if rain_hours else "72시간 내 강수 예보 낮음",
        ] if h],
    }
