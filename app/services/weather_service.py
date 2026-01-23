import requests
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.weather import DailyWeather
from app.core.config import Config


def get_daily_weather_summary(db: Session, nx: int, ny: int):
    """
    오늘 날짜의 기상 정보를 조회합니다.
    DB에 없으면 API(02:00 기준)를 호출하여 저장합니다.
    """
    today_str = datetime.now().strftime("%Y%m%d")

    # 1. DB 조회 (오늘 날짜 + 해당 지역)
    cached_data = (
        db.query(DailyWeather).filter_by(date_id=today_str, nx=nx, ny=ny).first()
    )

    if cached_data:
        return cached_data, "DB Cached"

    # 2. DB에 없다면? -> API 호출
    # 무조건 오늘 새벽 2시(0200) 데이터를 요청합니다.
    # 주의: 만약 새벽 2시 15분 전(데이터 생성 전)에 접속했다면,
    # 전날 23시 데이터를 써야 하지만, 편의상 '데이터 준비중' 처리를 하거나 대기해야 합니다.

    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        "serviceKey": Config.KMA_API_KEY,
        "pageNo": "1",
        "numOfRows": "300",  # 하루치(02시~23시) 다 커버됨
        "dataType": "JSON",
        "base_date": today_str,
        "base_time": "0200",  # 핵심: 새벽 2시 고정
        "nx": nx,
        "ny": ny,
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        # 기상청 응답 코드가 정상이 아닐 경우 (예: 아직 02시 데이터 생성 안됨)
        if data["response"]["header"]["resultCode"] != "00":
            return (
                None,
                f"API Error or Not Ready: {data['response']['header']['resultMsg']}",
            )

        items = data["response"]["body"]["items"]["item"]

    except Exception as e:
        print(f"Connection Failed: {e}")
        return None, "Connection Error"

    # 3. 데이터 요약 (Parsing)
    # 0200 데이터에는 TMN(최저), TMX(최고)가 포함되어 있습니다.
    min_val = None
    max_val = None
    max_rain_type = 0  # 0이면 맑음. 숫자가 클수록 궂은 날씨 (비, 눈 등)

    for item in items:
        cat = item["category"]
        val = item["fcstValue"]

        # 최저기온 (TMN)
        if cat == "TMN":
            min_val = float(val)
        # 최고기온 (TMX)
        elif cat == "TMX":
            max_val = float(val)
        # 강수형태 (PTY) - 하루 중 한 번이라도 비가 오면 '비 오는 날'로 간주하기 위함
        # 활동 시간(09시 ~ 21시)만 체크하고 싶다면 item['fcstTime'] 조건 추가 가능
        elif cat == "PTY":
            rain_val = int(val)
            if rain_val > max_rain_type:
                max_rain_type = rain_val

    # 만약 API에서 TMN/TMX가 누락된 경우(드문 경우) TMP(시간별 기온)에서 추출하는 로직 추가 가능

    # 4. DB 저장
    new_weather = DailyWeather(
        date_id=today_str,
        nx=nx,
        ny=ny,
        min_temp=min_val,
        max_temp=max_val,
        rain_type=max_rain_type,
    )

    db.add(new_weather)
    db.commit()
    db.refresh(new_weather)

    return new_weather, "API Fetched & Saved"
