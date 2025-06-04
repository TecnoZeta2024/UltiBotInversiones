from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Optional

from src.shared.data_types import TelegramConnectionStatus, ServiceName
from src.ultibot_backend.services.credential_service import CredentialService # Mantener para type hinting
from src.ultibot_backend.services.notification_service import NotificationService # Mantener para type hinting
from src.ultibot_backend.core.exceptions import CredentialError, TelegramNotificationError, NotificationError
from src.ultibot_backend import dependencies as deps # Importar deps
from src.ultibot_backend.app_config import settings # Importar settings

router = APIRouter()

# Las funciones de dependencia locales ya no son necesarias. Se usarán las de deps.

@router.get("/telegram/status", response_model=TelegramConnectionStatus, summary="Obtener el estado de la conexión de Telegram")
async def get_telegram_connection_status(
    credential_service: CredentialService = Depends(deps.get_credential_service),
    notification_service: NotificationService = Depends(deps.get_notification_service) # Aunque no se usa directamente, puede ser parte de la lógica de verificación futura
):
    """
    Obtiene el estado actual de la conexión del bot de Telegram para el usuario.
    """
    telegram_credential = await credential_service.get_credential(
        user_id=settings.FIXED_USER_ID,
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
    credential_service: CredentialService = Depends(deps.get_credential_service),
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    """
    Permite al usuario disparar manualmente un reintento de verificación de la conexión de Telegram.
    """
    telegram_credential = await credential_service.get_credential(
        user_id=settings.FIXED_USER_ID,
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
            user_id=settings.FIXED_USER_ID,
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
