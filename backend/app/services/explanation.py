"""행동 권고 및 AI 설명 생성"""
from typing import Any, Optional

PEST_KNOWLEDGE = {
    "탄저병": {
        "symptoms": "잎, 줄기, 열매에 둥근 갈색 병반",
        "environment": "고온다습, 결로 발생 시 확산",
        "actions": [
            "잎과 열매 표면의 병반을 확인하세요.",
            "비 오기 전 방제 가능 여부를 확인하세요.",
            "감염된 잎, 열매는 즉시 제거하세요.",
        ],
    },
    "역병": {
        "symptoms": "잎 끝부터 갈변, 시들음, 흰 곰팡이 발생",
        "environment": "저온다습, 통풍 불량 시 발생",
        "actions": [
            "배수 상태와 통풍을 점검하세요.",
            "습도가 높은 시간대 방제를 피하세요.",
            "예방 위주의 약제 살포 일정을 검토하세요.",
        ],
    },
    "담배나방": {
        "symptoms": "잎 구멍, 줄기 굴파, 열매 피해",
        "environment": "온난, 건조 시 발생 증가",
        "actions": [
            "성충 유인트랩을 점검하세요.",
            "유충 피해 잎을 수거하세요.",
            "발생 밀도에 따라 방제 시기를 결정하세요.",
        ],
    },
    "잿빛곰팡이병": {
        "symptoms": "잎 뒷면 회색 곰팡이, 황화",
        "environment": "시설 내 고습, 저온야간",
        "actions": ["환기, 제습을 강화하세요.", "감염 잎을 제거하세요.", "예방 위주 살균제를 검토하세요."],
    },
    "담배가루이": {
        "symptoms": "잎 황화, 말림, 끈끈이 분비물",
        "environment": "건조, 고온 시 발생 증가",
        "actions": ["초기 발생 잎을 확인하세요.", "천적, 약제 방제 시기를 검토하세요."],
    },
    "흰가루병": {
        "symptoms": "잎, 과실에 백색 가루상 곰팡이",
        "environment": "건조한 낮, 습한 밤 반복",
        "actions": ["통풍을 개선하세요.", "감염 부위를 제거하세요."],
    },
    "응애": {
        "symptoms": "잎 뒷면 점박이, 거미줄, 황화",
        "environment": "고온건조 시 폭발적 증가",
        "actions": ["잎 뒷면을 관찰하세요.", "천적, 살충제 방제를 검토하세요."],
    },
    "도열병": {
        "symptoms": "잎 끝부터 갈변, 조직 괴사",
        "environment": "장마, 고습, 질소 과다",
        "actions": ["배수, 통풍을 점검하세요.", "도열병 예보, 방제지침을 확인하세요."],
    },
    "잎마름병": {
        "symptoms": "잎 가장자리부터 마름, 갈변",
        "environment": "고온다습, 질소 결핍 시 약해짐",
        "actions": ["시비 균형을 점검하세요.", "예방 살균 일정을 검토하세요."],
    },
    "벼멸구": {
        "symptoms": "벼 잎 황화, 고사, 군집 발생",
        "environment": "이앙 후 건조, 고온 시 증가",
        "actions": ["유충 밀도를 조사하세요.", "등록 살충제 방제 시기를 확인하세요."],
    },
    "노균병": {
        "symptoms": "잎, 과실 황화, 뒷면 회색 곰팡이",
        "environment": "저온다습, 결로",
        "actions": ["환기, 배수를 강화하세요.", "감염 잎, 과실을 제거하세요."],
    },
    "검은점병": {
        "symptoms": "잎, 과실 검은 점상 병반",
        "environment": "봄비, 고습 시 확산",
        "actions": ["낙엽, 병과를 제거하세요.", "예방 살균 시기를 검토하세요."],
    },
    "자주무늬병": {
        "symptoms": "잎에 자주색 무늬, 황화",
        "environment": "저온다습, 밀식",
        "actions": ["통풍을 개선하세요.", "감염 잎을 제거하세요."],
    },
    "총채벌레": {
        "symptoms": "잎, 뿌리 흡즙, 성장 저해",
        "environment": "건조, 고온 시 증가",
        "actions": ["청색 점착트랩을 점검하세요.", "발생 초기 방제가 중요합니다."],
    },
    "파총채벌레": {
        "symptoms": "잎 흡즙, 변형, 황화",
        "environment": "건조한 봄철",
        "actions": ["밀도 조사 후 방제 시기를 결정하세요."],
    },
    "진딧물": {
        "symptoms": "잎, 순 흡즙, 끈끈이, 황화",
        "environment": "봄, 가을 건조 시",
        "actions": ["천적을 활용하세요.", "초기 발생 시 방제하세요."],
    },
    "세균성줄무늬병": {
        "symptoms": "잎에 세로 줄무늬, 위조",
        "environment": "고온다습, 바람",
        "actions": ["병든 잎을 제거하세요.", "종자, 잔재 관리를 점검하세요."],
    },
    "옥수수나방": {
        "symptoms": "심축, 이삭 피해, 구멍",
        "environment": "개화, 비대기 고온",
        "actions": ["유인트랩을 점검하세요.", "심축 피해를 조사하세요."],
    },
}


def generate_explanation(
    crop_name: str,
    pest_name: str,
    final_risk: float,
    risk_level: str,
    weather_factors: dict,
    pest_details: list,
    soil_factors: dict,
    nongsaro_news: Optional[list[dict]] = None,
    pesticide_items: Optional[list[dict]] = None,
) -> dict:
    pest_info = PEST_KNOWLEDGE.get(pest_name, {
        "symptoms": "병해충 증상 관찰 필요",
        "environment": "기상 조건에 따라 발생",
        "actions": ["필지를 직접 관찰하세요.", "전문가 상담을 권장합니다."],
    })

    reasons = []
    if weather_factors.get("humidity_score", 0) > 30:
        reasons.append("최근 24시간 평균습도가 높아 병 발생 조건에 가깝습니다.")
    if weather_factors.get("dew_score", 0) > 20:
        reasons.append("결로시간이 길어 병원균 번식 환경이 형성되었습니다.")
    if weather_factors.get("rain_score", 0) > 15:
        reasons.append("강수가 있어 병해 확산 가능성이 있습니다.")

    nearby = [p for p in pest_details if p.get("pest_name") == pest_name]
    if nearby:
        d = nearby[0].get("distance_km", 3)
        reasons.append(f"주변 {d}km 이내에서 {pest_name} 발생 기록이 확인되었습니다.")

    news = nongsaro_news or []
    if news:
        title = news[0].get("cntntsSj") or news[0].get("title") or ""
        if title:
            reasons.append(f"농사로 발생정보: {title[:60]}")

    if soil_factors.get("organic_matter_deficit", 0) > 10:
        reasons.append("토양 유기물이 부족해 작물 저항성이 낮을 수 있습니다.")

    if not reasons:
        reasons.append("현재 기상, 토양, 예찰 데이터를 종합한 결과입니다.")

    title = f"오늘 {crop_name} {pest_name} 위험도가 {risk_level}입니다."
    reason_text = "\n".join(f"• {r}" for r in reasons)

    action_list = list(pest_info["actions"])
    if pesticide_items:
        p = pesticide_items[0]
        brand = p.get("pestiBrandName") or p.get("pestiBrandNm") or ""
        if brand:
            action_list = action_list[:2] + [f"등록 농약 참고: {brand} (농사로 등록현황)"]

    source_refs = [
        {"source": "팜맵 농업기상", "type": "weather"},
        {"source": "팜맵 병해충발생", "type": "surveillance"},
        {"source": "팜맵 토양검정", "type": "soil"},
        {"source": "농사로 발생정보", "type": "nongsaro"},
        {"source": "농사로 농약등록", "type": "pesticide"},
    ]

    return {
        "title": title,
        "reason": reason_text,
        "action_list": action_list,
        "symptoms": pest_info.get("symptoms"),
        "environment": pest_info.get("environment"),
        "source_refs": source_refs,
        "risk_score": final_risk,
        "pest_name": pest_name,
    }
