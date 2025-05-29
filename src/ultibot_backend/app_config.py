from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ejemplo de variable de configuración
    # APP_NAME: str = "UltiBotInversiones"

settings = AppSettings()
