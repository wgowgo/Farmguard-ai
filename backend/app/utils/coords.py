"""좌표 변환: WGS84 ↔ EPSG:5179 (팜맵 API 투영좌표)"""
from pyproj import Transformer

_wgs_to_5179 = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)
_5179_to_wgs = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)


def latlng_to_farmmap(lng: float, lat: float) -> tuple[float, float]:
    x, y = _wgs_to_5179.transform(lng, lat)
    return x, y


def farmmap_to_latlng(x: float, y: float) -> tuple[float, float]:
    lng, lat = _5179_to_wgs.transform(x, y)
    return lng, lat


def latlng_to_kma_grid(lat: float, lng: float) -> tuple[int, int]:
    """기상청 격자 좌표 변환 (Lambert conformal conic)"""
    import math

    re = 6371.00877 / 5.0
    grid = 5.0
    slat1 = 30.0
    slat2 = 60.0
    olon = 126.0
    olat = 38.0
    xo = 42.0
    yo = 135.0

    def deg2rad(d):
        return d * math.pi / 180.0

    re = re / grid
    slat1 = deg2rad(slat1)
    slat2 = deg2rad(slat2)
    olon = deg2rad(olon)
    olat = deg2rad(olat)

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = (sf**sn * math.cos(slat1)) / sn
    ro = re * sf / (math.tan(math.pi * 0.25 + olat * 0.5) ** sn)

    ra = re * sf / (math.tan(math.pi * 0.25 + deg2rad(lat) * 0.5) ** sn)
    theta = lng * math.pi / 180.0 - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    x = int(ra * math.sin(theta) + xo + 0.5)
    y = int(ro - ra * math.cos(theta) + yo + 0.5)
    return x, y
