import logging
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class UvicornConfig(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="UVICORN_")

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
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    
    # Test Database configuration
    test_db_name: str = "test_ultibot"

    # Binance API configuration
    binance_api_key: str
    binance_api_secret: str

    # Mobula API configuration
    mobula_api_key: str

    # Telegram Bot configuration
    telegram_bot_token: str
    telegram_chat_id: str

    # Gemini AI configuration
    gemini_api_key: str

    # Credential Encryption Key
    credential_encryption_key: str

    # Application settings
    log_level: str = "INFO"
    test_mode: bool = False
    
    # Fixed user ID for single-user deployment
    fixed_user_id: str = "00000000-0000-0000-0000-000000000001"
    
    # Supabase configuration (optional, for reference)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        """Constructs the asynchronous database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def get_test_database_url(self) -> str:
        """Constructs the asynchronous test database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.test_db_name}"

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
