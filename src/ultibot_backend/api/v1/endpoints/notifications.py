from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

# Importar el módulo de dependencias
from src.ultibot_backend import dependencies as deps

from src.shared.data_types import Notification
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.core.exceptions import NotificationError
# SupabasePersistenceService y CredentialService ya no son necesarios aquí directamente
# ya que NotificationService se obtendrá de deps

router = APIRouter()

# Ya no se necesita la función local get_notification_service
# async def get_notification_service(
#     credential_service: CredentialService = Depends(CredentialService),
#     persistence_service: SupabasePersistenceService = Depends(SupabasePersistenceService)
# ) -> NotificationService:
#     # Esta función crearía una instancia de NotificationService que podría no estar
#     # completamente configurada o ser diferente de la instancia global.
#     return NotificationService(credential_service, persistence_service)

@router.get("/history", response_model=List[Notification])
async def get_notification_history(
    user_id: UUID,
    limit: int = 50,
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    """
    Recupera el historial de notificaciones para un usuario.
    """
    try:
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
    user_id: UUID,
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    """
    Marca una notificación específica como leída.
    """
    try:
        updated_notification = await notification_service.mark_notification_as_read(notification_id, user_id)
        if not updated_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notificación con ID {notification_id} no encontrada o no pertenece al usuario {user_id}."
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
