"""공공 API XML 응답 파싱"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def _strip_tag(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _elem_to_obj(elem: ET.Element) -> Any:
    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        return text
    result: dict[str, Any] = {}
    for child in children:
        val = _elem_to_obj(child)
        key = _strip_tag(child.tag)
        if key in result:
            existing = result[key]
            if isinstance(existing, list):
                existing.append(val)
            else:
                result[key] = [existing, val]
        else:
            result[key] = val
    return result


def xml_to_dict(xml_text: str) -> dict[str, Any]:
    root = ET.fromstring(xml_text.strip())
    return {_strip_tag(root.tag): _elem_to_obj(root)}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if value == "":
        return []
    return [value]


def extract_items(data: dict[str, Any] | list) -> list[dict[str, Any]]:
    """JSON/XML 혼합 응답에서 item 목록 추출"""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if not isinstance(data, dict):
        return []

    # data.go.kr JSON
    resp = data.get("response")
    if isinstance(resp, dict):
        body = resp.get("body") or {}
        items = body.get("items")
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]
        if isinstance(items, dict):
            item = items.get("item")
            return [x for x in _as_list(item) if isinstance(x, dict)]

    # XML root response
    for key in ("response", "Response"):
        if key in data:
            return extract_items(data[key])

    body = data.get("body") or data.get("Body") or data
    if not isinstance(body, dict):
        return []

    items = body.get("items") or body.get("Items")
    if isinstance(items, dict):
        item = items.get("item") or items.get("Item")
        return [x for x in _as_list(item) if isinstance(x, dict)]
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]

    return []


def api_result_code(data: dict[str, Any]) -> tuple[str, str]:
    """resultCode / resultMsg 추출"""
    resp = data.get("response") or data
    if not isinstance(resp, dict):
        return "", ""
    header = resp.get("header") or resp.get("Header") or {}
    if not isinstance(header, dict):
        return "", ""
    code = str(
        header.get("resultCode") or header.get("resultcode")
        or header.get("Result_Code") or header.get("result_Code") or ""
    )
    msg = str(
        header.get("resultMsg") or header.get("resultmsg")
        or header.get("Result_Msg") or header.get("result_Msg") or ""
    )
    return code, msg
