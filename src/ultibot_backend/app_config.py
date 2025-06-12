import os
import logging
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class UvicornConfig(BaseSettings):
    host: str = Field("127.0.0.1", env="UVICORN_HOST")
    port: int = Field(8000, env="UVICORN_PORT")
    reload: bool = Field(False, env="UVICORN_RELOAD")
    log_level: str = Field("info", env="UVICORN_LOG_LEVEL")

class AppSettings(BaseSettings):
    """
    Main application configuration class.
    Loads settings from environment variables.
    """
    # Project metadata
    PROJECT_NAME: str = "UltiBot Inversiones"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend for UltiBot Inversiones"
    API_V1_STR: str = "/api/v1"

    # Database configuration
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(..., env="DB_PORT")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    db_name: str = Field(..., env="DB_NAME")

    # Binance API configuration
    binance_api_key: str = Field(..., env="BINANCE_API_KEY")
    binance_api_secret: str = Field(..., env="BINANCE_API_SECRET")

    # Mobula API configuration
    mobula_api_key: str = Field(..., env="MOBULA_API_KEY")

    # Telegram Bot configuration
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(..., env="TELEGRAM_CHAT_ID")

    # Gemini AI configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")

    # Application settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    test_mode: bool = Field(False, env="TEST_MODE")
    
    # Fixed user ID for single-user deployment
    FIXED_USER_ID: str = Field("00000000-0000-0000-0000-000000000001", env="FIXED_USER_ID")
    
    # Supabase configuration (optional, for reference)
    supabase_url: Optional[str] = Field(None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(None, env="SUPABASE_KEY")

    @property
    def database_url(self) -> str:
        """Constructs the asynchronous database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

@lru_cache
def get_app_settings() -> AppSettings:
    """
    Returns a cached instance of the AppSettings.
    The configuration is loaded only once.
    """
    return AppSettings()

@lru_cache
def get_uvicorn_config() -> UvicornConfig:
    """
    Returns a cached instance of the UvicornConfig.
    """
    return UvicornConfig()

def setup_logging(config: AppSettings):
    """
    Set up logging for the application.
    """
    log_level = config.log_level.upper()
    # Using force=True to reconfigure logging if it's already been configured
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )
    # Quieten down some chatty libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at level: {log_level}")

settings = get_app_settings()
