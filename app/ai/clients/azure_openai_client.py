"""
Azure OpenAI API 클라이언트
"""
import base64
import logging
from typing import Optional, List, Dict, Any
from openai import AzureOpenAI
from app.core.config import Config

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Azure OpenAI API 클라이언트 (싱글톤 패턴)"""
    
    def __init__(self):
        Config.check_api_key()
        
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME
        self.model_name = Config.AZURE_OPENAI_MODEL_NAME
    
    def _encode_image(self, image_bytes: bytes) -> str:
        """이미지를 base64로 인코딩"""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def generate_content(
        self, 
        prompt: str, 
        image: Optional[Any] = None, 
        image_bytes: Optional[bytes] = None,
        **kwargs
    ) -> str:
        """
        텍스트 또는 이미지+텍스트를 사용하여 콘텐츠 생성
        
        Args:
            prompt: 텍스트 프롬프트
            image: PIL Image 객체 (선택사항)
            image_bytes: 이미지 바이트 데이터 (선택사항)
            **kwargs: 추가 생성 파라미터 (temperature, max_tokens 등)
        
        Returns:
            생성된 텍스트 응답
        """
        try:
            messages = []
            
            # 이미지가 있는 경우 Vision API 사용
            if image_bytes is not None:
                base64_image = self._encode_image(image_bytes)
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })
            elif image is not None:
                # PIL Image 객체인 경우 바이트로 변환
                import io
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                img_byte_arr = img_byte_arr.getvalue()
                base64_image = self._encode_image(img_byte_arr)
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })
            else:
                # 텍스트만 사용
                messages.append({
                    "role": "user",
                    "content": prompt
                })
            
            # 기본 파라미터 설정 (kwargs에서 가져오거나 기본값 사용)
            api_params = {
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000),
            }
            
            # kwargs에서 다른 파라미터도 추가 (temperature, max_tokens 제외)
            for key, value in kwargs.items():
                if key not in ["temperature", "max_tokens"]:
                    api_params[key] = value
            
            # Azure OpenAI API 호출
            logger.info(f"Calling Azure OpenAI API with model: {self.deployment_name}")
            logger.debug(f"API params: temperature={api_params.get('temperature')}, max_tokens={api_params.get('max_tokens')}")
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                **api_params
            )
            
            # 응답 추출
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.info(f"API response received (length: {len(content)})")
                    logger.debug(f"Response preview: {content[:200]}")
                else:
                    logger.warning("API returned empty content")
                return content or ""
            else:
                logger.error("No choices in API response")
                raise Exception("No response from Azure OpenAI API")
                
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}", exc_info=True)
            raise Exception(f"Azure OpenAI API error: {str(e)}")
    
    def generate_with_vision(
        self,
        prompt: str,
        image_bytes: bytes,
        **kwargs
    ) -> str:
        """
        Vision API를 사용하여 이미지 분석
        
        Args:
            prompt: 이미지 분석 프롬프트
            image_bytes: 이미지 바이트 데이터
            **kwargs: 추가 생성 파라미터
        
        Returns:
            생성된 텍스트 응답
        """
        return self.generate_content(prompt, image_bytes=image_bytes, **kwargs)


# Singleton instance
azure_openai_client = AzureOpenAIClient()
