"""Application configuration using environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    # Vobiz.ai Configuration
    VOBIZ_AUTH_ID: str
    VOBIZ_AUTH_TOKEN: str
    VOBIZ_API_URL: str = "https://api.vobiz.ai"

    # Deepgram Configuration
    DEEPGRAM_API_KEY: str

    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"

    # Database/Storage
    DATABASE_URL: str = "sqlite:///./voice_agent.db"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
