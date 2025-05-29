from fastapi import FastAPI
from uuid import UUID
import logging
from typing import Optional # Importar Optional

from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.notification_service import NotificationService
from src.shared.data_types import ServiceName

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="UltiBot Backend")

# Instancias de servicios (se inicializarán al inicio de la aplicación)
credential_service: Optional[CredentialService] = None
notification_service: Optional[NotificationService] = None

# Asumimos un user_id fijo para la v1.0 de una aplicación local
# En una aplicación real, esto vendría de la autenticación del usuario.
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001") 

@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación FastAPI.
    Inicializa servicios y realiza verificaciones iniciales.
    """
    global credential_service, notification_service
    logger.info("Iniciando UltiBot Backend...")
    
    credential_service = CredentialService()
    notification_service = NotificationService(credential_service=credential_service)

    logger.info("Servicios CredentialService y NotificationService inicializados.")

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

@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento que se ejecuta al apagar la aplicación FastAPI.
    Cierra recursos.
    """
    logger.info("Apagando UltiBot Backend...")
    if notification_service:
        await notification_service.close()
    logger.info("UltiBot Backend apagado.")


@app.get("/")
async def read_root():
    return {"message": "Welcome to UltiBot Backend"}

# Aquí se incluirán los routers de api/v1/endpoints
from src.ultibot_backend.api.v1.endpoints import telegram_status
app.include_router(telegram_status.router, prefix="/api/v1")
