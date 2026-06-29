"""런타임 데모 모드 토글 (관리 대시보드)"""
from app.config import settings

_runtime_demo: bool | None = None


def is_demo_mode() -> bool:
    if _runtime_demo is not None:
        return _runtime_demo
    return settings.demo_mode


def set_demo_mode(enabled: bool) -> bool:
    global _runtime_demo
    _runtime_demo = enabled
    return _runtime_demo
