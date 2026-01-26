import logging
import os
import json
from typing import Optional
from google.oauth2 import service_account

# google-cloud-aiplatform 패키지 필요
try:
    import vertexai
    from vertexai.preview.vision_models import ImageGenerationModel

    HAS_VERTEX_AI = True
except ImportError:
    HAS_VERTEX_AI = False

from app.core.config import Config

logger = logging.getLogger(__name__)


class NanoBananaClient:
    """
    Google Vertex AI (Imagen) Wrapper Client
    'Nano Banana'라는 이름으로 사용됩니다.
    """

    def __init__(self):
        if not HAS_VERTEX_AI:
            logger.warning(
                "google-cloud-aiplatform package is not installed. Nano Banana features will be disabled."
            )
            self.model = None
            return

        try:
            # Initialize Vertex AI
            credentials = None
            if Config.GOOGLE_PRIVATE_KEY and Config.GOOGLE_CLIENT_EMAIL:
                try:
                    info = {
                        "type": Config.GOOGLE_TYPE,
                        "project_id": Config.GOOGLE_PROJECT_ID,
                        "private_key_id": Config.GOOGLE_PRIVATE_KEY_ID,
                        "private_key": (
                            Config.GOOGLE_PRIVATE_KEY.replace("\\n", "\n")
                            if Config.GOOGLE_PRIVATE_KEY
                            else None
                        ),
                        "client_email": Config.GOOGLE_CLIENT_EMAIL,
                        "client_id": Config.GOOGLE_CLIENT_ID,
                        "auth_uri": Config.GOOGLE_AUTH_URI,
                        "token_uri": Config.GOOGLE_TOKEN_URI,
                        "auth_provider_x509_cert_url": Config.GOOGLE_AUTH_PROVIDER_X509_CERT_URL,
                        "client_x509_cert_url": Config.GOOGLE_CLIENT_X509_CERT_URL,
                        "universe_domain": Config.GOOGLE_UNIVERSE_DOMAIN,
                    }
                    credentials = service_account.Credentials.from_service_account_info(
                        info
                    )
                    logger.info("Loaded Google Credentials from individual env vars.")
                except Exception as e:
                    logger.error(
                        f"Failed to load Google Credentials from env vars: {e}"
                    )

            vertexai.init(
                project=Config.GOOGLE_CLOUD_PROJECT,
                location=Config.GOOGLE_CLOUD_LOCATION,
                credentials=credentials,
            )

            # Load the model
            # "imagegeneration@006" is Imagen 3
            self.model = ImageGenerationModel.from_pretrained("imagegeneration@006")
            logger.info("Nano Banana (Vertex AI) Client initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize Nano Banana Client: {e}")
            self.model = None

    def generate_image(
        self, prompt: str, negative_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate an image using Nano Banana (Imagen 3)

        Args:
            prompt: Text prompt for generation
            negative_prompt: Negative prompt

        Returns:
            GCS URI or base64 string or local path (Depending on implementation)
            For this implementation, let's assume we upload to Azure Blob and return the URL,
            but first we need to get the image content.
        """
        if not self.model:
            logger.error("Nano Banana Client is not initialized.")
            return None

        try:
            logger.info(f"Generating image with prompt: {prompt}")

            # Generate
            images = self.model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                # negative_prompt=negative_prompt, # Check SDK version support
                language="ko",  # Support Korean prompts if needed, or translate
                safety_filter_level="block_some",
                person_generation="allow_adult",
            )

            if not images:
                logger.warning("No images generated.")
                return None

            # GeneratedImage object from Vertex AI
            generated_image = images[0]

            # We need to save this image to Azure Blob Storage
            # The GeneratedImage object usually has a method to save or get bytes
            # generated_image.save("temp.png")

            # For now, let's returning the temporary local path or bytes logic needs to be handled
            # But the requirement asks to return a URL.
            # So this client might need to depend on BlobStorage?
            # Or better, return bytes and let the caller handle upload.

            # generated_image._image_bytes (Internal) or save to buffer
            # Vertex AI SDK returns `GeneratedImage` which has `_image_bytes`?
            # Creating a temp file is safer for now.

            temp_filename = f"temp_{os.urandom(4).hex()}.png"
            generated_image.save(filename=temp_filename)

            with open(temp_filename, "rb") as f:
                image_bytes = f.read()

            os.remove(temp_filename)

            return image_bytes  # Return bytes so caller can upload

        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            return None
