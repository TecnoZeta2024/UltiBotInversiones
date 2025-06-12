"""
Endpoints de la API para verificar el estado y la conectividad con Telegram.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from ....shared.data_types import TelegramConnectionStatus
from ...core.ports import INotificationPort
from ...core.exceptions import TelegramNotificationError
from ...dependencies import NotificationServiceDep

router = APIRouter(prefix="/telegram", tags=["Telegram"])
logger = logging.getLogger(__name__)

@router.get("/status", response_model=TelegramConnectionStatus, summary="Obtener el estado de la conexión de Telegram")
async def get_telegram_connection_status(
    notification_port = NotificationServiceDep,
):
    """
    Obtiene el estado actual de la conexión del bot de Telegram.
    """
    try:
        # Se asume que el puerto de notificación tiene un método para obtener el estado.
        status_result = await notification_port.get_connection_status()
        return status_result
    except Exception as e:
        logger.error(f"Error al obtener el estado de la conexión de Telegram: {e}", exc_info=True)
        return TelegramConnectionStatus(
            is_connected=False,
            status_message=f"Error interno al verificar el estado: {e}",
            status_code="INTERNAL_ERROR"
        )

@router.post("/verify", response_model=TelegramConnectionStatus, summary="Disparar verificación manual de la conexión de Telegram")
async def verify_telegram_connection_manually(
    notification_port = NotificationServiceDep,
):
    """
    Permite al usuario disparar manualmente un reintento de verificación de la conexión de Telegram.
    """
    try:
        # Se asume que el puerto de notificación tiene un método para verificar la conexión.
        status_result = await notification_port.verify_connection()
        return status_result
    except TelegramNotificationError as e:
        logger.error(f"Error al verificar la conexión de Telegram: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar conexión de Telegram: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inesperado durante la verificación de Telegram: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante la verificación de Telegram: {e}"
        )
