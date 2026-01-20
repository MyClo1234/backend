import google.generativeai as genai
from typing import List, Optional
from app.core.config import Config

class GeminiClient:
    def __init__(self):
        Config.check_api_key()
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL_NAME)

    def generate_content(self, prompt: str, image: Optional[any] = None, **kwargs) -> str:
        try:
            contents = [prompt]
            if image:
                contents.append(image)
            
            response = self.model.generate_content(contents, **kwargs)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

# Singleton instance
gemini_client = GeminiClient()
