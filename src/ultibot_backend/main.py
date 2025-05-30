from fastapi import FastAPI
from uuid import UUID
import logging
from typing import Optional # Importar Optional

from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.services.market_data_service import MarketDataService # Importar MarketDataService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Importar SupabasePersistenceService
from src.ultibot_backend.services.config_service import ConfigService # Importar ConfigService
from src.shared.data_types import ServiceName, UserConfiguration # Importar UserConfiguration

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="UltiBot Backend")

# Instancias de servicios (se inicializarán al inicio de la aplicación)
credential_service: Optional[CredentialService] = None
notification_service: Optional[NotificationService] = None
binance_adapter: Optional[BinanceAdapter] = None
market_data_service: Optional[MarketDataService] = None
persistence_service: Optional[SupabasePersistenceService] = None # Añadir PersistenceService
config_service: Optional[ConfigService] = None # Añadir ConfigService
user_configuration: Optional[UserConfiguration] = None # Para almacenar la configuración cargada

# Asumimos un user_id fijo para la v1.0 de una aplicación local
# En una aplicación real, esto vendría de la autenticación del usuario.
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001") 

@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación FastAPI.
    Inicializa servicios y realiza verificaciones iniciales.
    """
    global credential_service, notification_service, binance_adapter, market_data_service, persistence_service, config_service, user_configuration
    logger.info("Iniciando UltiBot Backend...")
    
    from src.ultibot_backend.app_config import settings # Importar settings aquí para asegurar que esté disponible
    
    # Leer manualmente CREDENTIAL_ENCRYPTION_KEY desde .env para evitar problemas de carga
    raw_env_key = None
    try:
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("CREDENTIAL_ENCRYPTION_KEY="):
                    raw_env_key = line.strip().split("=", 1)[1].strip('"')
                    break
    except Exception as e:
        logger.error(f"No se pudo leer manualmente CREDENTIAL_ENCRYPTION_KEY desde .env: {e}")

    logger.info(f"CREDENTIAL_ENCRYPTION_KEY desde settings: {settings.CREDENTIAL_ENCRYPTION_KEY}")
    logger.info(f"CREDENTIAL_ENCRYPTION_KEY leída manualmente desde .env: {raw_env_key}")

    # Usar la clave leída manualmente si está disponible, de lo contrario, la de settings
    effective_encryption_key = raw_env_key if raw_env_key else settings.CREDENTIAL_ENCRYPTION_KEY

    # Inicializar PersistenceService primero
    persistence_service = SupabasePersistenceService()
    await persistence_service.connect() # Conectar a la base de datos al inicio

    credential_service = CredentialService(encryption_key=effective_encryption_key)
    notification_service = NotificationService(credential_service=credential_service)
    binance_adapter = BinanceAdapter() # Inicializar BinanceAdapter
    market_data_service = MarketDataService(credential_service=credential_service, binance_adapter=binance_adapter) # Inicializar MarketDataService
    config_service = ConfigService(persistence_service=persistence_service) # Inicializar ConfigService

    logger.info("Servicios CredentialService, NotificationService, PersistenceService y ConfigService inicializados.")

    # Cargar la configuración del usuario al inicio
    try:
        user_configuration = await config_service.load_user_configuration(FIXED_USER_ID)
        logger.info(f"Configuración de usuario cargada exitosamente para {FIXED_USER_ID}.")
    except Exception as e:
        logger.error(f"Error al cargar la configuración de usuario al inicio: {e}", exc_info=True)
        user_configuration = config_service.get_default_configuration() # Asegurar que siempre haya una configuración
        logger.warning("Se utilizará la configuración por defecto debido a un error de carga.")


    # Verificar si la URL de la base de datos está configurada antes de intentar la verificación de credenciales
    if settings.DATABASE_URL:
        # Intentar verificar las credenciales de Telegram al inicio
        try:
            telegram_credential = await credential_service.get_credential(
                user_id=FIXED_USER_ID,
                service_name=ServiceName.TELEGRAM_BOT,
                credential_label="default_telegram_bot"
            )
            if telegram_credential:
                logger.info(f"Credenciales de Telegram encontradas para el usuario {FIXED_USER_ID}. Iniciando verificación...")
                # Usar el método verify_credential del CredentialService, pasándole el notification_service
                is_telegram_verified = await credential_service.verify_credential(
                    credential=telegram_credential,
                    notification_service=notification_service
                )
                if is_telegram_verified:
                    logger.info("Verificación inicial de Telegram completada con éxito.")
                else:
                    logger.warning("La verificación inicial de Telegram falló. Revise las credenciales.")
            else:
                logger.info(f"No se encontraron credenciales de Telegram para el usuario {FIXED_USER_ID}. Omite la verificación inicial.")
        except Exception as e:
            logger.error(f"Error durante la verificación inicial de Telegram: {e}", exc_info=True)
    else:
        logger.warning("DATABASE_URL no está configurada. Se omitirá la verificación inicial de credenciales de Telegram.")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento que se ejecuta al apagar la aplicación FastAPI.
    Cierra recursos.
    """
    logger.info("Apagando UltiBot Backend...")
    if notification_service:
        await notification_service.close()
    if binance_adapter: # Cerrar BinanceAdapter
        await binance_adapter.close()
    if persistence_service: # Cerrar PersistenceService
        await persistence_service.disconnect()
    logger.info("UltiBot Backend apagado.")


@app.get("/")
async def read_root():
    return {"message": "Welcome to UltiBot Backend"}

# Aquí se incluirán los routers de api/v1/endpoints
from src.ultibot_backend.api.v1.endpoints import telegram_status, binance_status, config # Importar config
app.include_router(telegram_status.router, prefix="/api/v1", tags=["telegram"]) # Añadir tags
app.include_router(binance_status.router, prefix="/api/v1", tags=["binance"]) # Incluir el router de Binance
app.include_router(config.router, prefix="/api/v1", tags=["config"]) # Incluir el router de configuración
