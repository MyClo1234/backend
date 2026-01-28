import logging
from app.database import Base, engine

# Import all models here to ensure they are registered with Base.metadata
from app.domains.user.model import User
from app.domains.wardrobe.model import ClosetItem
from app.domains.outfit.model import OutfitLog, OutfitItem
from app.domains.chat.models import ChatSession, ChatMessage
from app.domains.weather.model import DailyWeather
from app.domains.recommendation.model import TodaysPick

logger = logging.getLogger(__name__)


def init_all_models():
    """
    모든 모델을 임포트하여 SQLAlchemy Base.metadata에 등록합니다.
    Azure Functions 등의 환경에서 모델이 로드되지 않아 관계 설정 오류가 발생하는 것을 방지합니다.
    """
    # 이미 임포트 문에서 로드되었으므로 명시적인 로직은 필요 없음
    # 필요한 경우 여기에 추가 초기화 로직 작성
    logger.info("All models initialized and registered.")
