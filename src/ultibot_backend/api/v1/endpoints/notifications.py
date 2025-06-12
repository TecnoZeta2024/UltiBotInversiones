"""
Endpoints de la API para la gestión de notificaciones.
"""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query

from ....shared.data_types import Notification
from ...core.exceptions import NotificationError
from ...dependencies import NotificationServiceDep

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)

@router.get("/history", response_model=List[Notification])
async def get_notification_history(
    limit: int = Query(50, ge=1, le=200, description="Número máximo de notificaciones a devolver."),
    notification_service = NotificationServiceDep,
):
    """
    Recupera el historial de notificaciones para el usuario.
    """
    try:
        logger.info(f"Recuperando las últimas {limit} notificaciones.")
        # Se asume que el servicio de notificación tiene un método para obtener el historial.
        # La implementación real de este método podría estar en el PersistenceAdapter.
        notifications = await notification_service.get_notification_history(limit=limit)
        return notifications
    except NotificationError as e:
        logger.error(f"Error al obtener el historial de notificaciones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial de notificaciones: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error inesperado al obtener el historial de notificaciones: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )

@router.post("/{notification_id}/mark-as-read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: UUID,
    notification_service = NotificationServiceDep,
):
    """
    Marca una notificación específica como leída.
    """
    try:
        logger.info(f"Marcando la notificación {notification_id} como leída.")
        # Se asume que el servicio de notificación tiene un método para esta acción.
        updated_notification = await notification_service.mark_notification_as_read(notification_id=notification_id)
        if not updated_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notificación con ID {notification_id} no encontrada.",
            )
        return updated_notification
    except NotificationError as e:
        logger.error(f"Error al marcar la notificación como leída: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar notificación como leída: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error inesperado al marcar la notificación como leída: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}",
        )
