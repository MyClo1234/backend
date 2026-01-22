import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4o")
    
    # Validation
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'}
    
    # Paths
    OUTPUT_DIR = "extracted_attributes"
    
    @staticmethod
    def check_api_key():
        if not Config.AZURE_OPENAI_API_KEY:
            print("Warning: AZURE_OPENAI_API_KEY environment variable is not set.")
            print("       Please set AZURE_OPENAI_API_KEY in .env file or environment variables.")
        if not Config.AZURE_OPENAI_ENDPOINT:
            print("Warning: AZURE_OPENAI_ENDPOINT environment variable is not set.")
            print("       Please set AZURE_OPENAI_ENDPOINT in .env file or environment variables.")
