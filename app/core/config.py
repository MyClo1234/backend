import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Config:
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION = os.getenv(
        "AZURE_OPENAI_API_VERSION", "2024-02-15-preview"
    )
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4o")

    # Azure DALL-E Configuration
    AZURE_DALLE_API_KEY = os.getenv("AZURE_DALLE_API_KEY", "")
    AZURE_DALLE_ENDPOINT = os.getenv("AZURE_DALLE_ENDPOINT", "")
    AZURE_DALLE_DEPLOYMENT_NAME = os.getenv(
        "AZURE_DALLE_DEPLOYMENT_NAME", "codify-dall-e-3"
    )
    AZURE_DALLE_MODEL_VERSION = os.getenv(
        "AZURE_DALLE_MODEL_VERSION", "2024-04-01-preview"
    )

    # Google Cloud Configuration
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "google_credentials.json"
    )
    GOOGLE_CLOUD_PROJECT = os.getenv(
        "GOOGLE_CLOUD_PROJECT", "industrial-keep-485507-g3"
    )
    GOOGLE_CLOUD_LOCATION = os.getenv(
        "GOOGLE_CLOUD_LOCATION", "us-central1"
    )  # Vertex AI is regional

    # Google Credentials (Split)
    GOOGLE_TYPE = os.getenv("GOOGLE_TYPE", "service_account")
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", GOOGLE_CLOUD_PROJECT)
    GOOGLE_PRIVATE_KEY_ID = os.getenv("GOOGLE_PRIVATE_KEY_ID")
    GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY")
    GOOGLE_CLIENT_EMAIL = os.getenv("GOOGLE_CLIENT_EMAIL")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_AUTH_URI = os.getenv("GOOGLE_AUTH_URI")
    GOOGLE_TOKEN_URI = os.getenv("GOOGLE_TOKEN_URI")
    GOOGLE_AUTH_PROVIDER_X509_CERT_URL = os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL")
    GOOGLE_CLIENT_X509_CERT_URL = os.getenv("GOOGLE_CLIENT_X509_CERT_URL")
    GOOGLE_UNIVERSE_DOMAIN = os.getenv("GOOGLE_UNIVERSE_DOMAIN", "googleapis.com")

    # Security

    SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key-change-in-prod")

    # Database Configuration
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "app_db")

    # Azure Blob Storage Configuration
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY", "")
    AZURE_STORAGE_CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "images")

    # KMA Weather API Configuration
    # NOTE: 프로젝트 내 설정 파일(.env / local.settings.json)에서 키 이름이
    # `KMA_SERVICE_KEY`로 쓰이는 경우가 있어 하위 호환을 지원합니다.
    KMA_API_KEY = os.getenv("KMA_API_KEY") or os.getenv("KMA_SERVICE_KEY", "")

    @property
    def DATABASE_URL(self):
        url = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        # Azure Postgres requires SSL
        if "azure" in self.POSTGRES_SERVER and "?" not in url:
            url += "?sslmode=require"
        return url

    # Validation
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
    }

    # Paths
    OUTPUT_DIR = "extracted_attributes"

    @staticmethod
    def check_api_key():
        if not Config.AZURE_OPENAI_API_KEY:
            print("Warning: AZURE_OPENAI_API_KEY environment variable is not set.")
            print(
                "       Please set AZURE_OPENAI_API_KEY in .env file or environment variables."
            )
        if not Config.AZURE_OPENAI_ENDPOINT:
            print("Warning: AZURE_OPENAI_ENDPOINT environment variable is not set.")
            print(
                "       Please set AZURE_OPENAI_ENDPOINT in .env file or environment variables."
            )
        if not Config.AZURE_STORAGE_ACCOUNT_NAME:
            print(
                "Warning: AZURE_STORAGE_ACCOUNT_NAME environment variable is not set."
            )
            print(
                "       Please set AZURE_STORAGE_ACCOUNT_NAME in .env file or environment variables."
            )
        if not Config.KMA_API_KEY:
            print("Warning: KMA API key environment variable is not set.")
            print(
                "       Please set KMA_API_KEY (or KMA_SERVICE_KEY) in .env/local.settings.json or environment variables."
            )

        if not Config.AZURE_DALLE_API_KEY:
            print("Warning: AZURE_DALLE_API_KEY environment variable is not set.")
            print(
                "       Please set AZURE_DALLE_API_KEY in .env file or environment variables."
            )
        if not Config.AZURE_DALLE_ENDPOINT:
            print("Warning: AZURE_DALLE_ENDPOINT environment variable is not set.")
            print(
                "       Please set AZURE_DALLE_ENDPOINT in .env file or environment variables."
            )

        if not os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS):
            print(
                f"Warning: Google Credentials file not found at {Config.GOOGLE_APPLICATION_CREDENTIALS}"
            )
