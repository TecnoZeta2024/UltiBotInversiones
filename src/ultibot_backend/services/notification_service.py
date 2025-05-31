import logging
import json
from uuid import UUID
from typing import Optional, Dict, Any, List
from uuid import UUID

from src.shared.data_types import ServiceName, APICredential, Notification, Trade # Importar Trade
from src.ultibot_backend.adapters.telegram_adapter import TelegramAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Importar PersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import CredentialError, NotificationError, TelegramNotificationError, ExternalAPIError # Importar excepciones

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, credential_service: CredentialService, persistence_service: SupabasePersistenceService):
        self.credential_service = credential_service
        self.persistence_service = persistence_service # Inyectar el servicio de persistencia
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

    async def save_notification(self, notification: Notification) -> Notification:
        """
        Guarda una notificación en la base de datos.
        """
        try:
            saved_notification = await self.persistence_service.save_notification(notification)
            logger.info(f"Notificación {notification.id} guardada en la base de datos.")
            return saved_notification
        except Exception as e:
            logger.error(f"Error al guardar notificación {notification.id} en la base de datos: {e}", exc_info=True)
            raise NotificationError(f"Error al guardar notificación: {e}", code="NOTIFICATION_SAVE_FAILED")

    async def get_notification_history(self, user_id: UUID, limit: int = 50) -> List[Notification]:
        """
        Recupera el historial de notificaciones para un usuario desde la base de datos.
        """
        try:
            history = await self.persistence_service.get_notification_history(user_id, limit)
            logger.info(f"Historial de notificaciones recuperado para el usuario {user_id}.")
            return history
        except Exception as e:
            logger.error(f"Error al obtener historial de notificaciones para el usuario {user_id}: {e}", exc_info=True)
            raise NotificationError(f"Error al obtener historial de notificaciones: {e}", code="NOTIFICATION_HISTORY_FAILED")

    async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """
        Marca una notificación como leída en la base de datos.
        """
        try:
            updated_notification = await self.persistence_service.mark_notification_as_read(notification_id, user_id)
            if updated_notification:
                logger.info(f"Notificación {notification_id} marcada como leída para el usuario {user_id}.")
            else:
                logger.warning(f"No se encontró la notificación {notification_id} para marcar como leída para el usuario {user_id}.")
            return updated_notification
        except Exception as e:
            logger.error(f"Error al marcar notificación {notification_id} como leída: {e}", exc_info=True)
            raise NotificationError(f"Error al marcar notificación como leída: {e}", code="NOTIFICATION_MARK_READ_FAILED")

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

    async def send_notification(self, user_id: UUID, title: str, message: str, channel: str = "telegram", event_type: str = "SYSTEM_MESSAGE", dataPayload: Optional[Dict[str, Any]] = None) -> bool:
        """
        Envía una notificación general al usuario a través del canal especificado.
        Por ahora, soporta Telegram y UI.

        Args:
            user_id: El ID del usuario.
            title: Título de la notificación.
            message: Contenido del mensaje.
            channel: Canal de notificación (ej. "telegram", "ui").
            event_type: Tipo de evento de la notificación.

        Returns:
            True si la notificación se envió con éxito, False en caso contrario.
        """
        # Crear la notificación para guardar en la base de datos
        notification_to_save = Notification(
            userId=user_id,
            eventType=event_type,
            channel=channel,
            title=title,
            message=message,
            dataPayload=dataPayload
            # Otros campos pueden ser poblados según sea necesario
        )
        
        # Guardar la notificación en la base de datos
        try:
            await self.save_notification(notification_to_save)
        except NotificationError as e:
            logger.error(f"No se pudo guardar la notificación en la base de datos: {e}")
            # Continuar con el envío si el guardado falla, pero registrar el error
            pass # O re-raise si el guardado es crítico para todos los canales

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

    async def send_paper_trade_entry_notification(self, trade: Trade):
        """
        Envía una notificación al usuario confirmando la apertura de una operación simulada en paper trading.
        """
        user_id = trade.user_id
        symbol = trade.symbol
        side = trade.side
        executed_price = trade.entryOrder.executedPrice
        quantity = trade.entryOrder.executedQuantity
        trade_id = trade.id

        title = f"📈 Operación Simulada Abierta: {symbol}"
        message = (
            f"Se ha simulado la apertura de una operación en Paper Trading:\n"
            f"Símbolo: {symbol}\n"
            f"Acción: {side}\n"
            f"Cantidad: {quantity:.4f}\n"
            f"Precio de Entrada: {executed_price:.4f} USDT\n"
            f"ID de Trade: {trade_id}"
        )
        
        # Enviar a la UI
        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="ui",
                event_type="PAPER_TRADE_ENTRY_SIMULATED",
                dataPayload={"tradeId": str(trade_id), "symbol": symbol, "side": side, "quantity": quantity, "executedPrice": executed_price, "mode": "paper"}
            )
            logger.info(f"Notificación UI de trade simulado {trade_id} enviada.")
        except Exception as e:
            logger.error(f"Error al enviar notificación UI para trade simulado {trade_id}: {e}", exc_info=True)

        # Enviar a Telegram si está configurado
        # Aquí asumimos que la configuración del usuario (enableTelegramNotifications)
        # se verifica en un nivel superior o que send_notification ya lo maneja.
        # Por simplicidad, llamamos directamente a send_notification para Telegram.
        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="telegram",
                event_type="PAPER_TRADE_ENTRY_SIMULATED",
                dataPayload={"tradeId": str(trade_id), "symbol": symbol, "side": side, "quantity": quantity, "executedPrice": executed_price, "mode": "paper"}
            )
            logger.info(f"Notificación Telegram de trade simulado {trade_id} enviada.")
        except Exception as e:
            logger.error(f"Error al enviar notificación Telegram para trade simulado {trade_id}: {e}", exc_info=True)

    async def close(self):
        """Cierra cualquier adaptador de Telegram activo."""
        if self._telegram_adapter:
            await self._telegram_adapter.close()
