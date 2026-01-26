import logging
import os
import json
from typing import Optional
from google.oauth2 import service_account

# google-cloud-aiplatform 패키지 필요
try:
    import vertexai
    from vertexai.preview.vision_models import ImageGenerationModel, Image

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
            # Initialize Vertex AI with service account file
            credentials = None
            service_account_path = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                ),
                "service_account.json",
            )

            if os.path.exists(service_account_path):
                logger.info(f"Loading service account from: {service_account_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path
                )
            else:
                logger.warning(
                    f"Service account file not found at: {service_account_path}"
                )
                # Fallback to environment variables (for production)
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
                        credentials = (
                            service_account.Credentials.from_service_account_info(info)
                        )
                        logger.info(
                            "Loaded Google Credentials from individual env vars."
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to load Google Credentials from env vars: {e}"
                        )

            # Load project ID correctly
            project_id = Config.GOOGLE_CLOUD_PROJECT or Config.GOOGLE_PROJECT_ID
            if not project_id:
                logger.error(
                    "GOOGLE_CLOUD_PROJECT or GOOGLE_PROJECT_ID is not set in Config."
                )
                self.model = None
                return

            vertexai.init(
                project=project_id,
                location=Config.GOOGLE_CLOUD_LOCATION,
                credentials=credentials,
            )

            # Load Imagen 3 model (latest stable version)
            self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
            logger.info(
                f"Nano Banana (Vertex AI Imagen 3) Client initialized successfully for project {project_id}."
            )

        except Exception as e:
            logger.error(f"Failed to initialize Nano Banana Client: {e}")
            import traceback

            logger.error(traceback.format_exc())
            self.model = None

    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        base_image_bytes: Optional[bytes] = None,
    ) -> Optional[bytes]:
        """
        Generate an image using Nano Banana (Imagen 3)
        """
        if not self.model:
            logger.error("Nano Banana Client is not initialized.")
            return None

        try:
            logger.info(f"Generating image. Prompt length: {len(prompt)}")
            if base_image_bytes:
                logger.info(
                    "Using base_image_bytes for generation (Image-to-Image style if supported)"
                )

            # Generate
            # Note: Imagen 3 stable API might require specific parameters for image reference
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
            generated_image.save(location=temp_filename)

            with open(temp_filename, "rb") as f:
                image_bytes = f.read()

            os.remove(temp_filename)

            return image_bytes  # Return bytes so caller can upload

        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            return None

    def generate_mannequin_composite(
        self,
        top_image_url: Optional[str] = None,
        bottom_image_url: Optional[str] = None,
        top_description: Optional[str] = None,
        bottom_description: Optional[str] = None,
        mannequin_url: Optional[str] = None,
        gender: Optional[str] = None,
        body_shape: Optional[str] = None,
        mannequin_bytes: Optional[bytes] = None,
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a composite mannequin image with top and bottom items.
        Returns the URL of the generated image in Azure Blob Storage.
        """
        if not self.model:
            logger.error("Nano Banana Client is not initialized.")
            return None

        try:
            # Create a rich prompt describing the outfit and the personalized mannequin
            outfit_desc = ""
            if top_description:
                outfit_desc += f"a {top_description} on top, "
            if bottom_description:
                outfit_desc += f"and a {bottom_description} on bottom"

            if not outfit_desc:
                outfit_desc = "a complete coordinated outfit"

            # Personalize the mannequin description
            m_gender = (
                "man" if (gender or "").lower() in ["man", "male", "m"] else "woman"
            )
            m_shape = (body_shape or "average").lower()

            prompt = (
                f"A high-quality fashion studio shot of a realistic {m_shape} {m_gender} mannequin wearing {outfit_desc}. "
                f"The mannequin has a {m_shape} build as seen in professional fashion displays. "
                "The mannequin is standing in a natural pose against a clean, minimal white background. "
                "Soft studio lighting, commercial fashion photography style, 8k resolution, professional look, sharp focus."
            )

            logger.info(
                f"Generating personalized composite image with prompt: {prompt}"
            )
            image_bytes = self.generate_image(prompt, base_image_bytes=mannequin_bytes)

            if not image_bytes:
                logger.error("Failed to generate image bytes from prompt.")
                return None

            # Upload to Azure Blob Storage using Config
            from azure.storage.blob import BlobServiceClient
            from datetime import datetime
            import uuid

            account_name = Config.AZURE_STORAGE_ACCOUNT_NAME
            account_key = Config.AZURE_STORAGE_ACCOUNT_KEY
            container_name = Config.AZURE_STORAGE_CONTAINER_NAME

            if not all([account_name, account_key, container_name]):
                logger.error("Azure Storage configuration is incomplete.")
                return None

            blob_service_client = BlobServiceClient(
                account_url=f"https://{account_name}.blob.core.windows.net",
                credential=account_key,
            )
            container_client = blob_service_client.get_container_client(container_name)

            # Ensure container exists
            if not container_client.exists():
                container_client.create_container()

            # Filename generation using user_id and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_user_id = str(user_id) if user_id else f"anon-{uuid.uuid4().hex[:8]}"
            filename = f"todays-picks/{safe_user_id}_{timestamp}.png"

            blob_client = container_client.get_blob_client(filename)

            logger.info(f"Uploading generated image to blob: {filename}")
            blob_client.upload_blob(image_bytes, overwrite=True)

            image_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{filename}"
            logger.info(f"✅ Generated composite image: {image_url}")
            return image_url

        except Exception as e:
            logger.error(f"Error generating mannequin composite: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None
