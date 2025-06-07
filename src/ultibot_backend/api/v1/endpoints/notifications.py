from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.ultibot_backend import dependencies as deps
from src.ultibot_backend.app_config import settings
from src.shared.data_types import Notification
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.core.exceptions import NotificationError

router = APIRouter()

@router.get("/history", response_model=List[Notification])
async def get_notification_history(
    limit: int = 50,
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    """
    Recupera el historial de notificaciones para el usuario.
    """
    try:
        user_id = settings.FIXED_USER_ID
        notifications = await notification_service.get_notification_history(user_id, limit)
        return notifications
    except NotificationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial de notificaciones: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al obtener historial de notificaciones: {str(e)}"
        )

@router.post("/{notification_id}/mark-as-read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: UUID,
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    """
    Marca una notificación específica como leída para el usuario.
    """
    try:
        user_id = settings.FIXED_USER_ID
        updated_notification = await notification_service.mark_notification_as_read(notification_id, user_id)
        if not updated_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notificación con ID {notification_id} no encontrada o no pertenece al usuario."
            )
        return updated_notification
    except NotificationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar notificación como leída: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al marcar notificación como leída: {str(e)}"
        )
