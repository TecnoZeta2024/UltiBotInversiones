from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Optional

from src.shared.data_types import TelegramConnectionStatus, ServiceName
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.core.exceptions import CredentialError, TelegramNotificationError, NotificationError

router = APIRouter()

# Dependencias para inyección de servicios
def get_credential_service() -> CredentialService:
    # Esto debería ser manejado por un sistema de inyección de dependencias más robusto en una app real
    # Por ahora, asumimos que la instancia global de main.py está disponible
    from src.ultibot_backend.main import credential_service
    if not credential_service:
        raise HTTPException(status_code=500, detail="CredentialService no inicializado.")
    return credential_service

def get_notification_service(
    credential_service: CredentialService = Depends(get_credential_service)
) -> NotificationService:
    # Similarmente, para NotificationService
    from src.ultibot_backend.main import notification_service
    if not notification_service:
        # Si notification_service no está inicializado, lo inicializamos aquí
        # Esto puede ocurrir si el endpoint se llama antes del evento startup de FastAPI
        # O si se quiere una instancia por solicitud (menos eficiente para este caso)
        # Para simplificar, asumimos que ya está inicializado por el evento startup
        raise HTTPException(status_code=500, detail="NotificationService no inicializado.")
    return notification_service

# Asumimos un user_id fijo para la v1.0 de una aplicación local
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001") 

@router.get("/telegram/status", response_model=TelegramConnectionStatus, summary="Obtener el estado de la conexión de Telegram")
async def get_telegram_connection_status(
    credential_service: CredentialService = Depends(get_credential_service),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Obtiene el estado actual de la conexión del bot de Telegram para el usuario.
    """
    telegram_credential = await credential_service.get_credential(
        user_id=FIXED_USER_ID,
        service_name=ServiceName.TELEGRAM_BOT,
        credential_label="default_telegram_bot"
    )

    if not telegram_credential:
        return TelegramConnectionStatus(
            is_connected=False,
            last_verified_at=None,
            status_message="Credenciales de Telegram no configuradas.",
            status_code="CREDENTIALS_NOT_CONFIGURED"
        )
    
    # El estado de la credencial ya refleja si la última verificación fue exitosa
    is_connected = telegram_credential.status == "active"
    status_message = ""
    status_code = None

    if is_connected:
        status_message = "Conexión con Telegram activa y verificada."
    else:
        status_message = "Conexión con Telegram fallida o pendiente de verificación."
        status_code = telegram_credential.status.upper() # Usar el estado de la credencial como código de error

    return TelegramConnectionStatus(
        is_connected=is_connected,
        last_verified_at=telegram_credential.last_verified_at,
        status_message=status_message,
        status_code=status_code
    )

@router.post("/telegram/verify", response_model=TelegramConnectionStatus, summary="Disparar verificación manual de la conexión de Telegram")
async def verify_telegram_connection_manually(
    credential_service: CredentialService = Depends(get_credential_service),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Permite al usuario disparar manualmente un reintento de verificación de la conexión de Telegram.
    """
    telegram_credential = await credential_service.get_credential(
        user_id=FIXED_USER_ID,
        service_name=ServiceName.TELEGRAM_BOT,
        credential_label="default_telegram_bot"
    )

    if not telegram_credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credenciales de Telegram no encontradas. Por favor, configúrelas primero."
        )
    
    try:
        is_verified = await credential_service.verify_credential(
            credential=telegram_credential,
            notification_service=notification_service
        )
        
        # Recargar la credencial para obtener el estado más reciente después de la verificación
        updated_credential = await credential_service.get_credential(
            user_id=FIXED_USER_ID,
            service_name=ServiceName.TELEGRAM_BOT,
            credential_label="default_telegram_bot"
        )
        
        if updated_credential:
            is_connected = updated_credential.status == "active"
            status_message = "Verificación de Telegram completada con éxito." if is_connected else "Verificación de Telegram fallida. Revise las credenciales."
            status_code = updated_credential.status.upper() if not is_connected else None
            return TelegramConnectionStatus(
                is_connected=is_connected,
                last_verified_at=updated_credential.last_verified_at,
                status_message=status_message,
                status_code=status_code
            )
        else:
            # Esto no debería ocurrir si telegram_credential existía
            raise HTTPException(status_code=500, detail="Error interno al recuperar credenciales después de la verificación.")

    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de credenciales: {str(e)}"
        )
    except TelegramNotificationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar conexión de Telegram: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante la verificación de Telegram: {e}"
        )
