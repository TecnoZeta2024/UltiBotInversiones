from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from uuid import UUID

from app_config import get_app_settings
from dependencies import get_notification_service
from app_config import get_app_settings
from app_config import get_app_settings
from app_config import get_app_settings
from shared.data_types import Notification
from services.notification_service import NotificationService
from core.exceptions import NotificationError

router = APIRouter()

@router.get("/history", response_model=List[Notification])
async def get_notification_history(
    request: Request,
    limit: int = 50,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Recupera el historial de notificaciones para el usuario.
    """
    try:
        app_settings = get_app_settings()
        user_id = app_settings.FIXED_USER_ID # Se mantiene para consistencia si se necesita en el futuro
        notifications = await notification_service.get_notification_history(limit)
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
    request: Request,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Marca una notificación específica como leída para el usuario.
    """
    try:
        app_settings = get_app_settings()
        user_id = app_settings.FIXED_USER_ID # Se mantiene para consistencia si se necesita en el futuro
        updated_notification = await notification_service.mark_notification_as_read(notification_id)
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
