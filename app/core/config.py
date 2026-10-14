from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "01 Project"

    # Database
    DATABASE_URL: str

    @property
    def SYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRY: int
    JWT_REFRESH_TOKEN_EXPIRY: int 

    # Services
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = "noreply@example.com"
    BREVO_SENDER_NAME: str = "01 Project"

    # Cloudinary Storage Configuration
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_URL: str = ""

    # Google Gemini AI Configuration
    GEMINI_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GEMINI_API_KEY"),
    )
    GEMINI_MODEL: str = "gemini-3-flash-preview"

    # Hugging Face Configuration (Optional)
    HUGGINGFACE_API_TOKEN: str = Field(
        default="",
        validation_alias=AliasChoices("HUGGINGFACE_API_TOKEN", "HF_TOKEN", "HUGGINGFACE_HUB_TOKEN"),
    )
    HUGGINGFACE_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
        "case_sensitive": False,
        "enable_decoding": "utf-8",
    }


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
