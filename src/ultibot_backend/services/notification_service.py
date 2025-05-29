import logging
import json
from uuid import UUID
from typing import Optional, Dict, Any

from src.shared.data_types import ServiceName, APICredential
from src.ultibot_backend.adapters.telegram_adapter import TelegramAdapter
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import CredentialError, NotificationError, TelegramNotificationError, ExternalAPIError # Importar excepciones

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, credential_service: CredentialService):
        self.credential_service = credential_service
        self._telegram_adapter: Optional[TelegramAdapter] = None

    async def _get_telegram_adapter(self, user_id: UUID) -> Optional[TelegramAdapter]:
        """
        Obtiene y configura el TelegramAdapter usando las credenciales del usuario.
        Crea una instancia si no existe o si el token ha cambiado.
        """
        telegram_credential = await self.credential_service.get_credential(
            user_id=user_id,
            service_name=ServiceName.TELEGRAM_BOT,
            credential_label="default_telegram_bot" # Asumimos una etiqueta por defecto
        )

        if not telegram_credential:
            logger.warning(f"No se encontraron credenciales de Telegram para el usuario {user_id}.")
            raise CredentialError(f"No se encontraron credenciales de Telegram para el usuario {user_id}.", code="TELEGRAM_CREDENTIAL_NOT_FOUND")

        bot_token = telegram_credential.encrypted_api_key # El token del bot se almacena aquí
        
        if not bot_token:
            logger.error(f"Token de bot de Telegram no encontrado en las credenciales para el usuario {user_id}.")
            return None

        # Reutilizar adaptador si el token es el mismo
        if self._telegram_adapter and self._telegram_adapter.bot_token == bot_token:
            return self._telegram_adapter
        
        # Cerrar adaptador existente si el token ha cambiado
        if self._telegram_adapter:
            await self._telegram_adapter.close()

        self._telegram_adapter = TelegramAdapter(bot_token=bot_token)
        return self._telegram_adapter

    async def send_test_telegram_notification(self, user_id: UUID) -> bool:
        """
        Envía un mensaje de prueba a Telegram para verificar la conexión.

        Args:
            user_id: El ID del usuario para el cual enviar la notificación.

        Returns:
            True si el mensaje de prueba se envió con éxito, False en caso contrario.
        """
        logger.info(f"Intentando enviar mensaje de prueba de Telegram para el usuario {user_id}...")
        telegram_credential = await self.credential_service.get_credential(
            user_id=user_id,
            service_name=ServiceName.TELEGRAM_BOT,
            credential_label="default_telegram_bot"
        )

        if not telegram_credential:
            logger.warning(f"No se encontraron credenciales de Telegram para el usuario {user_id}. No se puede enviar mensaje de prueba.")
            raise CredentialError(f"No se encontraron credenciales de Telegram para el usuario {user_id}.", code="TELEGRAM_CREDENTIAL_NOT_FOUND")

        # El chat_id está en encrypted_other_details como un JSON blob
        chat_id = None
        if telegram_credential.encrypted_other_details:
            try:
                other_details = json.loads(telegram_credential.encrypted_other_details)
                chat_id = other_details.get("chat_id")
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar encrypted_other_details para el usuario {user_id}. No se pudo obtener el chat_id.", exc_info=True)
                raise CredentialError(f"Error al decodificar chat_id de Telegram para el usuario {user_id}.", code="TELEGRAM_CHAT_ID_DECODE_ERROR")
        
        if not chat_id:
            logger.error(f"Chat ID de Telegram no encontrado en las credenciales para el usuario {user_id}. No se puede enviar mensaje de prueba.")
            raise CredentialError(f"Chat ID de Telegram no encontrado para el usuario {user_id}.", code="TELEGRAM_CHAT_ID_MISSING")

        telegram_adapter = await self._get_telegram_adapter(user_id)
        if not telegram_adapter:
            logger.error(f"No se pudo inicializar TelegramAdapter para el usuario {user_id}.")
            raise TelegramNotificationError(f"No se pudo inicializar TelegramAdapter para el usuario {user_id}.", code="TELEGRAM_ADAPTER_INIT_FAILED")

        message = "¡Hola! UltiBotInversiones se ha conectado correctamente a este chat y está listo para enviar notificaciones."
        
        try:
            await telegram_adapter.send_message(chat_id, message)
            # Actualizar el estado de la credencial a 'active' si la verificación es exitosa
            await self.credential_service.update_credential(
                credential_id=telegram_credential.id,
                status="active"
            )
            logger.info(f"Mensaje de prueba de Telegram enviado con éxito para el usuario {user_id}.")
            # El estado de la credencial ya se actualiza en CredentialService.verify_credential
            return True
        except ExternalAPIError as e:
            logger.error(f"Fallo de API externa al enviar mensaje de prueba de Telegram para el usuario {user_id}: {str(e)}", exc_info=True)
            # El estado de la credencial ya se actualiza en CredentialService.verify_credential
            raise TelegramNotificationError(
                message=f"Fallo al enviar mensaje de prueba de Telegram: {str(e)}",
                code="TELEGRAM_SEND_FAILED",
                original_exception=e,
                telegram_response=e.response_data # Pasar la respuesta de Telegram si está disponible
            )
        except Exception as e:
            logger.error(f"Fallo inesperado al enviar mensaje de prueba de Telegram para el usuario {user_id}: {e}", exc_info=True)
            # El estado de la credencial ya se actualiza en CredentialService.verify_credential
            raise TelegramNotificationError(
                message=f"Fallo inesperado al enviar mensaje de prueba de Telegram: {e}",
                code="UNEXPECTED_TELEGRAM_ERROR",
                original_exception=e
            )

    async def send_notification(self, user_id: UUID, title: str, message: str, channel: str = "telegram", event_type: str = "SYSTEM_MESSAGE") -> bool:
        """
        Envía una notificación general al usuario a través del canal especificado.
        Por ahora, solo soporta Telegram.

        Args:
            user_id: El ID del usuario.
            title: Título de la notificación.
            message: Contenido del mensaje.
            channel: Canal de notificación (ej. "telegram", "ui").
            event_type: Tipo de evento de la notificación.

        Returns:
            True si la notificación se envió con éxito, False en caso contrario.
        """
        if channel == "telegram":
            telegram_credential = await self.credential_service.get_credential(
                user_id=user_id,
                service_name=ServiceName.TELEGRAM_BOT,
                credential_label="default_telegram_bot"
            )
            if not telegram_credential:
                logger.warning(f"No se encontraron credenciales de Telegram para el usuario {user_id}. No se puede enviar notificación.")
                raise CredentialError(f"No se encontraron credenciales de Telegram para el usuario {user_id}.", code="TELEGRAM_CREDENTIAL_NOT_FOUND")

            chat_id = None
            if telegram_credential.encrypted_other_details:
                try:
                    other_details = json.loads(telegram_credential.encrypted_other_details)
                    chat_id = other_details.get("chat_id")
                except json.JSONDecodeError:
                    logger.error(f"Error al decodificar encrypted_other_details para el usuario {user_id}. No se pudo obtener el chat_id.", exc_info=True)
                    raise CredentialError(f"Error al decodificar chat_id de Telegram para el usuario {user_id}.", code="TELEGRAM_CHAT_ID_DECODE_ERROR")
            
            if not chat_id:
                logger.error(f"Chat ID de Telegram no encontrado en las credenciales para el usuario {user_id}. No se puede enviar notificación.")
                raise CredentialError(f"Chat ID de Telegram no encontrado para el usuario {user_id}.", code="TELEGRAM_CHAT_ID_MISSING")

            telegram_adapter = await self._get_telegram_adapter(user_id)
            if not telegram_adapter:
                logger.error(f"No se pudo inicializar TelegramAdapter para el usuario {user_id}.")
                raise TelegramNotificationError(f"No se pudo inicializar TelegramAdapter para el usuario {user_id}.", code="TELEGRAM_ADAPTER_INIT_FAILED")

            full_message = f"<b>{title}</b>\n\n{message}"
            try:
                await telegram_adapter.send_message(chat_id, full_message)
                logger.info(f"Notificación de Telegram enviada con éxito para el usuario {user_id}.")
                return True
            except ExternalAPIError as e:
                logger.error(f"Fallo de API externa al enviar notificación de Telegram para el usuario {user_id}: {str(e)}", exc_info=True)
                raise TelegramNotificationError(
                    message=f"Fallo al enviar notificación de Telegram: {str(e)}",
                    code="TELEGRAM_SEND_FAILED",
                    original_exception=e,
                    telegram_response=e.response_data
                )
            except Exception as e:
                logger.error(f"Fallo inesperado al enviar notificación de Telegram para el usuario {user_id}: {e}", exc_info=True)
                raise TelegramNotificationError(
                    message=f"Fallo inesperado al enviar notificación de Telegram: {e}",
                    code="UNEXPECTED_TELEGRAM_ERROR",
                    original_exception=e
                )
        elif channel == "ui":
            logger.info(f"Notificación para UI para el usuario {user_id}: {title} - {message}. (Implementación pendiente)")
            # Lógica para enviar a la UI (ej. a través de un WebSocket o un sistema de eventos interno)
            return True
        else:
            logger.warning(f"Canal de notificación '{channel}' no soportado.")
            raise NotificationError(f"Canal de notificación '{channel}' no soportado.", code="UNSUPPORTED_NOTIFICATION_CHANNEL")

    async def close(self):
        """Cierra cualquier adaptador de Telegram activo."""
        if self._telegram_adapter:
            await self._telegram_adapter.close()
