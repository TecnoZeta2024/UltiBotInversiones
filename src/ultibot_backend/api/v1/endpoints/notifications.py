from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.ultibot_backend.security import core as security_core # Importar security_core
from src.ultibot_backend.security import schemas as security_schemas # Importar security_schemas
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
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    limit: int = 50,
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    """
    Recupera el historial de notificaciones para el usuario autenticado.
    """
    try:
        if not isinstance(current_user.id, UUID):
            # Esto no debería ocurrir si la autenticación funciona y User.id se popula correctamente.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")
        notifications = await notification_service.get_notification_history(current_user.id, limit)
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
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    notification_service: NotificationService = Depends(deps.get_notification_service)
):
    """
    Marca una notificación específica como leída para el usuario autenticado.
    """
    try:
        if not isinstance(current_user.id, UUID):
            # Esto no debería ocurrir si la autenticación funciona y User.id se popula correctamente.
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")
        updated_notification = await notification_service.mark_notification_as_read(notification_id, current_user.id)
        if not updated_notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notificación con ID {notification_id} no encontrada o no pertenece al usuario {current_user.id}."
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
