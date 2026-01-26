import logging
import azure.functions as func
from app.main import app as fastapi_app
from app.database import get_db
from app.batch import run_daily_weather_batch

# 1. FastAPI 앱 연결
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)


# --------------------------------------------------------------------------------
# [Batch Job] Daily Weather Update (02:16 AM KST)
# --------------------------------------------------------------------------------
# schedule="0 16 17 * * *" -> 17:16 UTC = 02:16 KST (다음날)
# 기상청 데이터 생성 지연을 고려하여 16분의 안전 마진(Safety Buffer)을 둠
@app.schedule(
    schedule="0 16 17 * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
async def daily_weather_update(myTimer: func.TimerRequest) -> None:
    """매일 02:16 KST에 전국 날씨 데이터 수집"""
    logging.info("☀️ [Batch] Daily weather update started")

    # DB 세션 컨텍스트 매니저로 관리 (자동 close)
    db = next(get_db())
    try:
        result = await run_daily_weather_batch(db)
        logging.info(f"✅ Batch completed: {result}")
    except Exception as e:
        logging.error(f"❌ Batch failed: {str(e)}")
    finally:
        db.close()
