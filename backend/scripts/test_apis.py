"""전체 API 연동 테스트 스크립트"""
import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from app.services.api_clients import FarmmapClient, KmaClient
from app.services.nongsaro_client import NongsaroClient, NONGSARO_SERVICES
from app.services.soil_api_client import SoilApiClient
from app.utils.coords import latlng_to_farmmap

# 경북 안동 인근 좌표 (고추 재배지) — 팜맵 EPSG:5179
LAT, LNG = 36.567, 128.728
PX, PY = latlng_to_farmmap(LNG, LAT)
PNU = "5271033027106720012"


def status(ok: bool, detail: str = "") -> str:
    return f"{'OK' if ok else 'FAIL'} {detail}".strip()


async def main():
    results: list[tuple[str, str, str]] = []
    today = date.today().strftime("%Y%m%d")

    farmmap = FarmmapClient()
    kma = KmaClient()
    nongsaro = NongsaroClient()
    soil = SoilApiClient()

    # --- 팜맵 ---
    try:
        parcel = await farmmap.fetch_parcel(PX, PY)
        ok = bool(parcel.get("fmapInnb"))
        fb = " (fallback)" if parcel.get("_fallback") else ""
        results.append(("팜맵 조회", status(ok, f"fmapInnb={parcel.get('fmapInnb')}{fb}"), ""))
    except Exception as e:
        results.append(("팜맵 조회", "FAIL", str(e)))

    try:
        weather = await farmmap.fetch_weather_hourly(PX, PY, date.today())
        demo = weather and weather[0].get("obsrTm", "").startswith("20") if weather else False
        results.append(("팜맵 농업기상", status(len(weather) > 0, f"{len(weather)}건"), ""))
    except Exception as e:
        results.append(("팜맵 농업기상", "FAIL", str(e)))

    try:
        s = await farmmap.fetch_soil(PX, PY)
        fb = " fallback" if s.get("_fallback") else ""
        results.append(("팜맵 토양검정", status(bool(s), f"acidity={s.get('acidity')}{fb}"), ""))
    except Exception as e:
        results.append(("팜맵 토양검정", "FAIL", str(e)))

    try:
        pests = await farmmap.fetch_pests(PX, PY, date.today().year)
        results.append(("팜맵 병해충발생", status(len(pests) > 0, f"{len(pests)}건"), ""))
    except Exception as e:
        results.append(("팜맵 병해충발생", "FAIL", str(e)))

    # --- 기상청 ---
    nx, ny = 89, 104  # 안동 근처 격자
    try:
        ncst = await kma.fetch_ultra_nowcast(nx, ny)
        ok = bool(ncst.get("T1H") or ncst.get("RN1"))
        results.append(("기상청 초단기실황", status(ok, str(ncst)[:80]), ""))
    except Exception as e:
        results.append(("기상청 초단기실황", "FAIL", str(e)))

    try:
        fcst = await kma.fetch_ultra_forecast(nx, ny)
        results.append(("기상청 초단기예보", status(len(fcst) > 0, f"{len(fcst)}건"), ""))
    except Exception as e:
        results.append(("기상청 초단기예보", "FAIL", str(e)))

    try:
        vil = await kma.fetch_vilage_forecast(nx, ny)
        results.append(("기상청 단기예보", status(len(vil) > 0, f"{len(vil)}건"), ""))
    except Exception as e:
        results.append(("기상청 단기예보", "FAIL", str(e)))

    # --- 농사로 (8종) ---
    for svc_code, meta in NONGSARO_SERVICES.items():
        op = meta["default_operation"]
        try:
            params: dict = {"pageNo": 1}
            if svc_code == "dbyhsCccrrncInfo":
                params["sText"] = "고추"
            elif svc_code == "pesticideRegStatus":
                params["cropName"] = "고추"
                params["diseaseWeedName"] = "탄저병"
            elif svc_code == "agchmSafeManual":
                params["sCropNm"] = "고추"
            r = await nongsaro.call(svc_code, op, **params)
            items = r.get("items") or []
            demo = r.get("demo") or r.get("demo_fallback")
            tag = " [데모]" if demo else ""
            if r.get("error") and not demo:
                tag += f" err={r.get('error')}"
            results.append((f"농사로 {meta['name']}", status(len(items) > 0, f"{len(items)}건{tag}"), ""))
        except Exception as e:
            results.append((f"농사로 {meta['name']}", "FAIL", str(e)))

    # --- 토양/비료 ---
    try:
        chem = await soil.soil_chem_v2(PNU)
        items = chem.get("items") or []
        tag = f" code={chem.get('result_code')}" if chem.get("result_code") else ""
        if chem.get("demo_fallback") or chem.get("demo"):
            tag += " [데모]"
        results.append(("토양검정 V2 getSoilExam", status(len(items) > 0, f"{len(items)}건{tag}"), ""))
    except Exception as e:
        results.append(("토양검정 V2 getSoilExam", "FAIL", str(e)))

    try:
        lst = await soil.soil_chem_list(pnu_code=PNU)
        items = lst.get("items") or []
        tag = f" code={lst.get('result_code')}" if lst.get("result_code") else ""
        results.append(("토양검정 목록 getSoilExamList", status(len(items) > 0, f"{len(items)}건{tag}"), ""))
    except Exception as e:
        results.append(("토양검정 목록 getSoilExamList", "FAIL", str(e)))

    try:
        rice = await soil.fertilizer_rice(PNU)
        items = rice.get("items") or []
        tag = f" code={rice.get('result_code')}" if rice.get("result_code") else ""
        results.append(("벼 비료처방 getSoilFrtlzrExamRiceInfo", status(len(items) > 0, f"{len(items)}건{tag}"), ""))
    except Exception as e:
        results.append(("벼 비료처방 getSoilFrtlzrExamRiceInfo", "FAIL", str(e)))

    try:
        other = await soil.fertilizer_other(PNU, "고추")
        items = other.get("items") or []
        code = other.get("result_code") or other.get("error") or ""
        tag = f" code={code}" if code else ""
        ok = len(items) > 0 or code == "201"
        results.append(("고추 비료처방 getSoilFrtlzrExamInfo", status(ok, f"{len(items)}건{tag} (201=검정없음)"), ""))
    except Exception as e:
        results.append(("고추 비료처방 getSoilFrtlzrExamInfo", "FAIL", str(e)))

    # 출력
    print("=" * 70)
    print(f"팜가드 AI API 테스트  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"좌표: lat={LAT}, lng={LNG}  farmmap=({int(PX)},{int(PY)})  DEMO_MODE=false")
    print("=" * 70)
    ok_count = sum(1 for _, s, _ in results if s.startswith("OK"))
    for name, st, err in results:
        line = f"  {name:<28} {st}"
        if err:
            line += f"  | {err[:50]}"
        print(line)
    print("-" * 70)
    print(f"  결과: {ok_count}/{len(results)} OK")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
