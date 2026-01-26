"""
Azure DALL-E Client
"""

import logging
import json
from typing import Optional
from openai import AzureOpenAI
from app.core.config import Config

logger = logging.getLogger(__name__)


class AzureDalleClient:
    """Azure DALL-E API Client (Singleton Pattern)"""

    def __init__(self):
        self.api_key = Config.AZURE_DALLE_API_KEY
        self.endpoint = Config.AZURE_DALLE_ENDPOINT
        self.deployment_name = Config.AZURE_DALLE_DEPLOYMENT_NAME
        self.api_version = Config.AZURE_DALLE_MODEL_VERSION

        if not self.api_key or not self.endpoint:
            logger.warning("Azure DALL-E credentials not set.")
            return

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
        )

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1,
    ) -> str:
        """
        Generate image using DALL-E 3

        Args:
            prompt: Image description
            size: Image size (1024x1024, etc)
            quality: 'standard' or 'hd'
            style: 'vivid' or 'natural'
            n: Number of images

        Returns:
            URL of the generated image (temporary URL)
        """
        try:
            logger.info(f"Generating image with DALL-E 3. Prompt: {prompt[:50]}...")

            result = self.client.images.generate(
                model=self.deployment_name,
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=n,
            )

            if not result.data:
                raise Exception("No image data returned from DALL-E")

            # DALL-E 3 returns a URL by default
            image_url = result.data[0].url
            logger.info("Image generated successfully.")
            return image_url

        except Exception as e:
            logger.error(f"DALL-E Generation Error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate image: {str(e)}")


# Singleton instance
azure_dalle_client = AzureDalleClient()
