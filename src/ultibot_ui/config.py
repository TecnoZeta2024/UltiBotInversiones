import os

class AppConfig:
    """
    Configuración centralizada para la aplicación de UI.
    """
    # La URL base para la API del backend.
    # Se puede sobrescribir con la variable de entorno BACKEND_API_URL.
    BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")

# Instancia única de la configuración para ser importada en otros módulos.
app_config = AppConfig()
