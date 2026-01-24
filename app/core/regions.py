import math
from typing import Tuple, Dict

# 대한민국 주요 도시 및 지역의 대표 좌표와 기상청 격자 정보 (NX, NY)
# 출처: 기상청 격자 정보 (일부 대표 예시)
# Format: { "Region Name": { "lat": float, "lon": float, "nx": int, "ny": int } }
KOREA_REGIONS = {
    "Seoul": {"lat": 37.5665, "lon": 126.9780, "nx": 60, "ny": 127},
    "Busan": {"lat": 35.1796, "lon": 129.0756, "nx": 98, "ny": 76},
    "Daegu": {"lat": 35.8714, "lon": 128.6014, "nx": 89, "ny": 90},
    "Incheon": {"lat": 37.4563, "lon": 126.7052, "nx": 55, "ny": 124},
    "Gwangju": {"lat": 35.1595, "lon": 126.8526, "nx": 58, "ny": 74},
    "Daejeon": {"lat": 36.3504, "lon": 127.3845, "nx": 67, "ny": 100},
    "Ulsan": {"lat": 35.5384, "lon": 129.3114, "nx": 102, "ny": 84},
    "Sejong": {"lat": 36.4800, "lon": 127.2890, "nx": 66, "ny": 103},
    "Gyeonggi-do": {
        "lat": 37.4138,
        "lon": 127.5183,
        "nx": 60,
        "ny": 120,
    },  # Representative
    "Gangwon-do": {
        "lat": 37.8228,
        "lon": 128.1555,
        "nx": 73,
        "ny": 134,
    },  # Representative (Chuncheon)
    "Chungcheongbuk-do": {
        "lat": 36.6350,
        "lon": 127.4914,
        "nx": 69,
        "ny": 107,
    },  # Representative (Cheongju)
    "Chungcheongnam-do": {
        "lat": 36.6588,
        "lon": 126.6728,
        "nx": 68,
        "ny": 100,
    },  # Representative
    "Jeollabuk-do": {
        "lat": 35.7175,
        "lon": 127.1530,
        "nx": 63,
        "ny": 89,
    },  # Representative (Jeonju)
    "Jeollanam-do": {
        "lat": 34.8161,
        "lon": 126.4629,
        "nx": 51,
        "ny": 67,
    },  # Representative (Mokpo)
    "Gyeongsangbuk-do": {
        "lat": 36.5760,
        "lon": 128.5056,
        "nx": 87,
        "ny": 106,
    },  # Representative (Andong)
    "Gyeongsangnam-do": {
        "lat": 35.2383,
        "lon": 128.6922,
        "nx": 91,
        "ny": 77,
    },  # Representative (Changwon)
    "Jeju-do": {"lat": 33.4890, "lon": 126.4983, "nx": 52, "ny": 38},
}


def get_nearest_region(lat: float, lon: float) -> Tuple[str, Dict]:
    """
    주어진 위도/경도와 가장 가까운 '대표 지역'을 찾습니다.
    간단한 유클리드 거리를 사용합니다 (대한민국 범위 내에서는 충분히 근사함).
    """
    nearest_region = None
    min_distance = float("inf")

    for name, data in KOREA_REGIONS.items():
        # 유클리드 거리 제곱 (루트 생략 가능)
        # 위도 차이 보정을 위해 lat에 대략적인 상수를 곱할 수도 있지만,
        # 도시 간 간격이 넓으므로 단순 계산으로도 충분히 구분 가능합니다.
        dist = (data["lat"] - lat) ** 2 + (data["lon"] - lon) ** 2

        if dist < min_distance:
            min_distance = dist
            nearest_region = name

    if nearest_region:
        return nearest_region, KOREA_REGIONS[nearest_region]

    # Fallback (Default to Seoul)
    return "Seoul", KOREA_REGIONS["Seoul"]
