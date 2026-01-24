import azure.functions as func
from app.main import app as fastapi_app

app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)

# --------------------------------------------------------------------------------
# [Batch Job Guide] Daily Weather Update (02:00 AM)
# --------------------------------------------------------------------------------
# 팀원 가이드:
# 매일 새벽 2시(KST)에 전국의 모든 사용자 또는 주요 지역의 날씨 예보를
# 미리 가져와 DB에 캐싱하는 배치 작업을 아래와 같이 구현할 수 있습니다.
#
# Azure Functions의 Timer Trigger를 사용합니다.
# schedule="0 0 17 * * *" -> 17:00 UTC = 02:00 KST
#
# @app.schedule(schedule="0 0 17 * * *", arg_name="myTimer", run_on_startup=False,
#               use_monitor=False)
# def daily_weather_update(myTimer: func.TimerRequest) -> None:
#     logging.info('Daily weather update batch started.')
#
#     # 1. DB 세션 생성
#     # db = SessionLocal()
#
#     # 2. 업데이트할 타겟 지역/사용자 목록 조회
#     # users = db.query(User).all()
#
#     # 3. 각 지역에 대해 KMA API 호출 및 캐싱
#     # for user in users:
#     #     weather_service.get_daily_weather_summary(db, user.nx, user.ny)
#
#     # db.close()
#     logging.info('Daily weather update batch finished.')
# --------------------------------------------------------------------------------
