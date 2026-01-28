import logging
import os
import io
from typing import Optional
from google.oauth2 import service_account

# google-genai SDK 사용
from google import genai
from google.genai import types

from app.core.config import Config

logger = logging.getLogger(__name__)


class NanoBananaClient:
    """
    Google Vertex AI (Imagen) Wrapper Client using google-genai SDK
    'Nano Banana'라는 이름으로 사용됩니다.
    
    Supports both generate_images and edit_image with reference images.
    """

    def __init__(self):
        self.client = None

        try:
            credentials = self._get_credentials()
            project_id = Config.GOOGLE_CLOUD_PROJECT or Config.GOOGLE_PROJECT_ID
            location = Config.GOOGLE_CLOUD_LOCATION or "asia-northeast3"

            if not project_id:
                logger.error(
                    "GOOGLE_CLOUD_PROJECT or GOOGLE_PROJECT_ID is not set in Config."
                )
                return

            self.client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location,
                credentials=credentials,
            )
            logger.info(
                f"[SUCCESS] Nano Banana initialized with google-genai SDK (project={project_id}, location={location})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize google-genai SDK: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _get_credentials(self):
        """Get Google Cloud credentials from file or env vars with proper scopes"""
        # Vertex AI requires cloud-platform scope
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        
        service_account_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ),
            "service_account.json",
        )

        if os.path.exists(service_account_path):
            logger.info(f"Loading service account from: {service_account_path}")
            creds = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=scopes
            )
            return creds
        else:
            logger.warning(
                f"Service account file not found at: {service_account_path}"
            )
            # Fallback to environment variables
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
                    creds = service_account.Credentials.from_service_account_info(
                        info, scopes=scopes
                    )
                    logger.info("Loaded Google Credentials from env vars.")
                    return creds
                except Exception as e:
                    logger.error(f"Failed to load credentials from env vars: {e}")
                    raise
            else:
                raise ValueError("No credentials found (file or env vars)")

    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        base_image_bytes: Optional[bytes] = None,
        reference_images: Optional[list[bytes]] = None,
        aspect_ratio: str = "9:16",
    ) -> Optional[bytes]:
        """
        Generate an image using Nano Banana (Imagen 3)
        
        Args:
            prompt: Text prompt
            negative_prompt: Negative prompt (optional)
            base_image_bytes: Base image (currently not used, kept for compatibility)
            reference_images: List of reference image bytes (currently not used)
            aspect_ratio: Image aspect ratio (default: "9:16"). Supported: "1:1", "3:4", "4:3", "9:16", "16:9"
        
        Returns:
            Image bytes (PNG) or None on failure
        """
        if not self.client:
            logger.error("Nano Banana Client is not initialized.")
            return None

        return self._generate_with_genai(
            prompt, negative_prompt, base_image_bytes, reference_images, aspect_ratio
        )

    def _generate_with_genai(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        base_image_bytes: Optional[bytes],
        reference_images: Optional[list[bytes]],
        aspect_ratio: str = "9:16",
    ) -> Optional[bytes]:
        """Generate image using google-genai SDK"""
        try:
            logger.info(f"Generating image with google-genai SDK. Prompt length: {len(prompt)}")

            # Use generate_images API (text-to-image only)
            logger.info("Using generate_images API")
            try:
                # Use GenerateImagesConfig (note: plural "Images")
                config = types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    person_generation="allow_adult",
                )

                # Use standard generate-002 model (for comparison with fast model)
                model_name = "imagen-3.0-generate-002"
                logger.info(f"Using {model_name} for generation")
                response = self.client.models.generate_images(
                    model=model_name,
                    prompt=prompt,
                    config=config,
                )

                if response.generated_images:
                    generated_img = response.generated_images[0]
                    # Access image bytes - may be .image.image_bytes or .image_bytes
                    try:
                        if hasattr(generated_img, 'image') and hasattr(generated_img.image, 'image_bytes'):
                            img_bytes = generated_img.image.image_bytes
                        elif hasattr(generated_img, 'image_bytes'):
                            img_bytes = generated_img.image_bytes
                        elif hasattr(generated_img, 'to_bytes'):
                            img_bytes = generated_img.to_bytes()
                        else:
                            # Fallback: try to get bytes from image object
                            img_bytes = bytes(generated_img.image) if hasattr(generated_img, 'image') else None
                            if not img_bytes:
                                raise AttributeError("Could not extract image bytes")
                        logger.info(f"[SUCCESS] Generated image via generate_images ({len(img_bytes)} bytes)")
                        return img_bytes
                    except Exception as e:
                        logger.error(f"Failed to extract image bytes: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                else:
                    logger.warning("generate_images returned no images")
                    return None
            except Exception as e:
                logger.error(f"generate_images failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return None

        except Exception as e:
            logger.error(f"Error during image generation with google-genai: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
        reference_images: Optional[list[bytes]] = None,
        aspect_ratio: str = "9:16",
    ) -> Optional[str]:
        """
        Generate a composite mannequin image with top and bottom items.
        Returns the URL of the generated image in Azure Blob Storage.
        
        Args:
            aspect_ratio: Image aspect ratio (default: "9:16"). Supported: "1:1", "3:4", "4:3", "9:16", "16:9"
        """
        if not self.client:
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

            # Body profile mapping based on gender and body shape
            body_profiles = {
                "man": {
                    "slim": "narrow shoulders, small chest, narrow waist, narrow hips, low muscle definition, low body fat, slim arms and legs",
                    "average": "average shoulders, average chest, average waist, average hips, medium body fat, low-to-medium muscle definition, average limbs",
                    "athletic": "broad shoulders, medium chest, narrow waist, narrow hips, medium muscle definition, low body fat, athletic limbs (not bulky)",
                    "muscular": "very broad shoulders, large chest, narrow waist, narrow hips, high muscle definition, low body fat, thick arms and thighs",
                    "stocky": "broad shoulders, large waist, wider midsection, average hips, higher body fat, low muscle definition, thick arms and legs",
                },
                "woman": {
                    "slim": "narrow shoulders, small bust, narrow waist, narrow hips, low body fat, low muscle definition, slim arms and legs",
                    "average": "average shoulders, average bust, average waist, average hips, medium body fat, low-to-medium muscle definition, average limbs",
                    "athletic": "slightly broad/average shoulders, small-to-average bust, narrow waist, average hips, medium muscle definition, low body fat, toned limbs",
                    "toned_curvy": "average shoulders, average bust, defined waist, wider hips, medium muscle definition, medium body fat, curvy silhouette with toned legs",
                    "stocky": "average-to-broad shoulders, average bust, wider waist, wider hips, higher body fat, low muscle definition, thick limbs",
                },
            }

            # Get body profile description
            profile_map = body_profiles.get(m_gender, body_profiles["woman"])
            body_profile_desc = profile_map.get(m_shape, profile_map.get("average", "average body proportions"))

            # 1:1 정사각형 비율에 최적화된 프롬프트 (전신 정면)
            prompt = (
                f"Full-body, full shot, head-to-toe, front-facing, straight-on view studio photo of a realistic {m_gender} mannequin with a {m_shape} body type, wearing {outfit_desc}. "
                f"Body profile: {body_profile_desc}. "
                f"The mannequin must be facing directly towards the camera, standing straight, with head, torso, and legs fully visible from top to bottom. "
                f"Use a clean light-gray or white seamless background and professional soft fashion studio lighting.\n\n"
            )

            # CRITICAL 섹션: 체형 보존
            prompt += (
                "CRITICAL:\n"
                "- Preserve the mannequin's body proportions EXACTLY from the base mannequin image (do not change body shape, height, or limb length).\n"
                "- The subject is a mannequin: matte plastic/fiberglass, featureless head, no facial features, no hair, no skin texture.\n\n"
            )

            # GARMENT FIDELITY 섹션: 옷의 정확성
            prompt += (
                "GARMENT FIDELITY:\n"
                "- Preserve the exact garment colors, patterns, logos, and text. Do not alter prints or invent new details.\n"
                "- Natural fit and drape with realistic wrinkles consistent with the fabric.\n\n"
            )

            # COMPOSITION 섹션: 구도
            prompt += (
                "COMPOSITION:\n"
                "- Full shot: head, torso, and legs must be completely visible from top to bottom (head-to-toe).\n"
                "- Front-facing: mannequin must face directly towards the camera, straight-on view, no side angle or profile view.\n"
                "- Centered, relaxed standing pose, sharp focus, commercial fashion catalog quality.\n\n"
            )

            # 금지 문구 (사고 방지)
            prompt += (
                "No human skin, no realistic face, no nipples, no lingerie, no nude appearance.\n"
                "No extra accessories unless specified. No hats, no sunglasses, no jewelry.\n"
                "No background props, no text overlays, no watermarks."
            )

            logger.info(
                f"Generating personalized composite image with prompt (len={len(prompt)})"
            )

            image_bytes = self.generate_image(
                prompt,
                base_image_bytes=mannequin_bytes,
                reference_images=reference_images,
                aspect_ratio=aspect_ratio,
            )

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
            logger.info(f"[SUCCESS] Generated composite image: {image_url}")
            return image_url

        except Exception as e:
            logger.error(f"Error generating mannequin composite: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None
