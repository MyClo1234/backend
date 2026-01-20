import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    
    # Validation
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'}
    
    # Paths
    OUTPUT_DIR = "extracted_attributes"
    
    @staticmethod
    def check_api_key():
        if not Config.GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY environment variable is not set.")
            print("       Please set GEMINI_API_KEY in .env file or environment variables.")
