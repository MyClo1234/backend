import sys
import os

# Create a fake env if needed, or just run it.
# We need to add current dir to path
sys.path.append(os.getcwd())

print("Attempting imports...")

try:
    from app.database import engine, Base

    print("Base imported")
    from app.domains.user import model as user_model

    print("user_model imported")
    from app.domains.user.model import User

    print("User imported")
    from app.domains.wardrobe.model import ClosetItem

    print("ClosetItem imported")
    from app.domains.outfit.model import OutfitLog, OutfitItem

    print("OutfitLog imported")
    from app.domains.chat.model import ChatSession, ChatMessage

    print("ChatSession imported")
    from app.domains.weather.model import DailyWeather

    print("DailyWeather imported")
    from app.domains.recommendation.model import TodaysPick

    print("TodaysPick imported")
    from app.domains.auth.router import router as auth_router

    print("auth_router imported")

    print("ALL IMPORTS SUCCESSFUL")
except ImportError as e:
    print(f"IMPORT ERROR: {e}")
except Exception as e:
    print(f"OTHER ERROR: {e}")
