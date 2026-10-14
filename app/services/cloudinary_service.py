import io
import os
import uuid
from pathlib import Path
from typing import Dict, Optional
import cloudinary
import cloudinary.uploader

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class CloudinaryService:
    def get_credentials(self) -> Dict[str, str]:
        """Dynamically resolves Cloudinary credentials from environment, live .env file, or settings."""
        creds = {
            "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME", ""),
            "api_key": os.getenv("CLOUDINARY_API_KEY", ""),
            "api_secret": os.getenv("CLOUDINARY_API_SECRET", ""),
            "cloudinary_url": os.getenv("CLOUDINARY_URL", ""),
        }

        # Check live .env file on demand
        if not (creds["cloudinary_url"] or (creds["cloud_name"] and creds["api_key"] and creds["api_secret"])):
            try:
                env_path = os.path.join(os.getcwd(), ".env")
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if "=" in line:
                                key, _, val = line.partition("=")
                                key = key.strip().upper()
                                val = val.strip().strip("'\"")
                                if key == "CLOUDINARY_CLOUD_NAME" and val:
                                    creds["cloud_name"] = val
                                elif key == "CLOUDINARY_API_KEY" and val:
                                    creds["api_key"] = val
                                elif key == "CLOUDINARY_API_SECRET" and val:
                                    creds["api_secret"] = val
                                elif key == "CLOUDINARY_URL" and val:
                                    creds["cloudinary_url"] = val
            except Exception as e:
                logger.debug(f"Could not read .env for Cloudinary credentials: {e}")

        # Check settings
        if not creds["cloud_name"]:
            creds["cloud_name"] = getattr(settings, "CLOUDINARY_CLOUD_NAME", "")
        if not creds["api_key"]:
            creds["api_key"] = getattr(settings, "CLOUDINARY_API_KEY", "")
        if not creds["api_secret"]:
            creds["api_secret"] = getattr(settings, "CLOUDINARY_API_SECRET", "")
        if not creds["cloudinary_url"]:
            creds["cloudinary_url"] = getattr(settings, "CLOUDINARY_URL", "")

        # Clean invalid CLOUDINARY_URL format (must start with cloudinary://)
        if creds["cloudinary_url"] and not creds["cloudinary_url"].startswith("cloudinary://"):
            creds["cloudinary_url"] = ""

        # Strip whitespace
        for k in creds:
            creds[k] = creds[k].strip() if creds[k] else ""

        return creds

    def is_configured(self) -> bool:
        creds = self.get_credentials()
        return bool(
            creds.get("cloudinary_url")
            or (creds.get("cloud_name") and creds.get("api_key") and creds.get("api_secret"))
        )

    def upload_resume(self, content: bytes, filename: str, user_id: str) -> str:
        """Uploads the resume PDF to Cloudinary and returns the secure URL.
        Falls back to local file storage if Cloudinary credentials are not configured or fail.
        """
        creds = self.get_credentials()

        if self.is_configured():
            try:
                if creds.get("cloudinary_url"):
                    cloudinary.config(cloudinary_url=creds["cloudinary_url"], secure=True)
                else:
                    cloudinary.config(
                        cloud_name=creds["cloud_name"],
                        api_key=creds["api_key"],
                        api_secret=creds["api_secret"],
                        secure=True,
                    )

                unique_public_id = f"resumes/{user_id}_{uuid.uuid4().hex[:8]}"
                logger.info(f"Uploading resume for user {user_id} to Cloudinary...")

                upload_result = cloudinary.uploader.upload(
                    io.BytesIO(content),
                    resource_type="auto",
                    public_id=unique_public_id,
                    use_filename=True,
                    unique_filename=True,
                    overwrite=False,
                )

                secure_url = upload_result.get("secure_url") or upload_result.get("url")
                if secure_url:
                    logger.info(f"Resume uploaded successfully to Cloudinary: {secure_url}")
                    return secure_url
            except Exception as e:
                logger.error(
                    f"Cloudinary upload failed ({type(e).__name__}: {e}). "
                    "Please verify your CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in .env. "
                    "Falling back to local storage in uploads/resumes."
                )

        # Fallback to local storage
        logger.warning("Saving resume to local storage in uploads/resumes.")
        upload_dir = Path("uploads/resumes")
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{user_id}_{uuid.uuid4().hex[:8]}_{filename}"
        local_path = upload_dir / unique_name
        local_path.write_bytes(content)
        return str(local_path).replace("\\", "/")


cloudinary_service = CloudinaryService()
