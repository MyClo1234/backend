import httpx
import logging
from uuid import UUID
from app.domains.generation.schema import (
    OutfitGenerationRequest,
    OutfitGenerationResponse,
)
from app.ai.clients.nano_banana_client import NanoBananaClient
from app.utils.blob_storage import get_blob_storage_service
from app.domains.wardrobe.schema import WardrobeItemSchema

logger = logging.getLogger(__name__)


class GenerationService:
    def __init__(self):
        self.nano_banana_client = NanoBananaClient()
        self.blob_service = get_blob_storage_service()

    def _construct_prompt(self, request: OutfitGenerationRequest) -> str:
        """Construct a detailed prompt for DALL-E based on outfit items."""

        def is_valid_value(value: str) -> bool:
            """Check if a value is valid (not a placeholder or empty)."""
            if not value:
                return False
            # Filter out common placeholder values
            invalid_values = {"string", "unknown", "none", "null", "n/a", ""}
            return value.lower().strip() not in invalid_values

        def get_desc(item: WardrobeItemSchema) -> str:
            attrs = item.attributes
            parts = []

            # Extract category (main + sub) - most important
            if attrs.category:
                main = attrs.category.main or ""
                sub = attrs.category.sub or ""
                if is_valid_value(main) and is_valid_value(sub):
                    category = f"{sub} {main}".strip()
                    parts.append(category)
                elif is_valid_value(main):
                    parts.append(main)
                elif is_valid_value(sub):
                    parts.append(sub)

            # If no valid category, use default
            if not parts:
                parts.append("clothing item")

            # Extract color
            if (
                attrs.color
                and attrs.color.primary
                and is_valid_value(attrs.color.primary)
            ):
                parts.insert(0, attrs.color.primary)

            # Extract pattern
            if (
                attrs.pattern
                and attrs.pattern.type
                and is_valid_value(attrs.pattern.type)
            ):
                parts.append(f"with {attrs.pattern.type} pattern")

            # Extract material
            if (
                attrs.material
                and attrs.material.guess
                and is_valid_value(attrs.material.guess)
            ):
                parts.append(f"made of {attrs.material.guess}")

            description = " ".join(parts).strip()
            return description if description else "clothing item"

        top_desc = get_desc(request.top)
        bottom_desc = get_desc(request.bottom)
        style = request.style_description or "casual"
        gender = request.gender or "unisex"

        # Validate style and gender
        if not is_valid_value(style):
            style = "casual"
        if not is_valid_value(gender):
            gender = "unisex"

        prompt = (
            f"A realistic full-body photo of a {gender} model wearing "
            f"a {top_desc} on top and {bottom_desc} on the bottom. "
            f"Style: {style}. "
            f"The image should focus on the outfit coordination. "
            f"High quality, photorealistic, studio lighting."
        )
        return prompt

    async def create_outfit_image(
        self, request: OutfitGenerationRequest, user_id: UUID
    ) -> str:
        """
        Generate an outfit image using Nano Banana and save it to Blob Storage.
        Returns the permanent Blob URL.
        """
        try:
            # 1. Construct Prompt
            prompt = self._construct_prompt(request)
            logger.info(f"Generated prompt: {prompt}")

            # 2. Call Nano Banana (Imagen 3)
            # generate_image returns bytes directly
            image_bytes = self.nano_banana_client.generate_image(prompt=prompt)

            if not image_bytes:
                raise Exception("Failed to generate image bytes from Nano Banana")

            # 3. Upload to Blob Storage
            # We use a distinct filename prefix or rely on the blob service's unique naming
            result = self.blob_service.upload_image(
                image_bytes=image_bytes,
                user_id=str(user_id),
                original_filename="generated_outfit.png",
                content_type="image/png",
            )

            return result["blob_url"]

        except Exception as e:
            logger.error(f"Error in create_outfit_image: {str(e)}")
            raise


# Singleton
generation_service = GenerationService()
