import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 현재 파일(database.py) 위치에서 상위 폴더(backend)에 있는 .env를 찾습니다.
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

# app/database.py 수정

if not env_path.exists():
    print(f"❌ 에러: .env 파일을 찾을 수 없습니다!")
else:
    # 파일의 생생한 내용을 한 줄 읽어서 출력해봅니다.
    content = env_path.read_text()
    print(f"--- .env 파일 원본 내용 일부 출력 ---")
    print(content[:50])  # 보안을 위 앞부분 50자만 출력
    print(f"------------------------------------")

    load_dotenv(dotenv_path=env_path)

# 환경 변수 로드
AZURE_DATABASE_ID = os.getenv("AZURE_DATABASE_ID")
AZURE_DATABASE_PASSWORD = os.getenv("AZURE_DATABASE_PASSWORD")
AZURE_DATABASE_ENDPOINT = os.getenv("AZURE_DATABASE_ENDPOINT")
DB_NAME = os.getenv("DB_NAME")

# 디버깅용 (로그에 주소가 나오는지 확인)

if AZURE_DATABASE_ENDPOINT is None:
    print(
        "❌ 경고: .env 파일은 있지만 내부에서 AZURE_DATABASE_ENDPOINT 정보를 읽지 못했습니다."
    )
    print("파일 내용이 'AZURE_DATABASE_ENDPOINT=주소' 형식인지 확인하세요.")

SQLALCHEMY_DATABASE_URL = f"postgresql://{AZURE_DATABASE_ID}:{AZURE_DATABASE_PASSWORD}@{AZURE_DATABASE_ENDPOINT}:5432/{DB_NAME}?sslmode=require"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
