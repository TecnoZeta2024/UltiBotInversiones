import logging
import json
from uuid import UUID
from typing import Optional, Dict, Any, List
from uuid import UUID

from src.shared.data_types import ServiceName, APICredential, Notification, Trade, Opportunity
from src.ultibot_backend.adapters.telegram_adapter import TelegramAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import CredentialError, NotificationError, TelegramNotificationError, ExternalAPIError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, credential_service: CredentialService, persistence_service: SupabasePersistenceService):
        self.credential_service = credential_service
        self.persistence_service = persistence_service
        self._telegram_adapter: Optional[TelegramAdapter] = None

    async def _get_telegram_adapter(self, user_id: UUID) -> Optional[TelegramAdapter]:
        """
        Obtiene y configura el TelegramAdapter usando las credenciales del usuario.
        Crea una instancia si no existe o si el token ha cambiado.
        """
        telegram_credential = await self.credential_service.get_credential(
            user_id=user_id,
            service_name=ServiceName.TELEGRAM_BOT,
            credential_label="default_telegram_bot"
        )

        if not telegram_credential:
            logger.warning(f"No se encontraron credenciales de Telegram para el usuario {user_id}.")
            raise CredentialError(f"No se encontraron credenciales de Telegram para el usuario {user_id}.", code="TELEGRAM_CREDENTIAL_NOT_FOUND")

        bot_token = telegram_credential.encrypted_api_key
        
        if not bot_token:
            logger.error(f"Token de bot de Telegram no encontrado en las credenciales para el usuario {user_id}.")
            return None

        if self._telegram_adapter and self._telegram_adapter.bot_token == bot_token:
            return self._telegram_adapter
        
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
            await self.credential_service.update_credential(
                credential_id=telegram_credential.id,
                status="active"
            )
            logger.info(f"Mensaje de prueba de Telegram enviado con éxito para el usuario {user_id}.")
            return True
        except ExternalAPIError as e:
            logger.error(f"Fallo de API externa al enviar mensaje de prueba de Telegram para el usuario {user_id}: {str(e)}", exc_info=True)
            raise TelegramNotificationError(
                message=f"Fallo al enviar mensaje de prueba de Telegram: {str(e)}",
                code="TELEGRAM_SEND_FAILED",
                original_exception=e,
                telegram_response=e.response_data
            )
        except Exception as e:
            logger.error(f"Fallo inesperado al enviar mensaje de prueba de Telegram para el usuario {user_id}: {e}", exc_info=True)
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
        notification_to_save = Notification(
            userId=user_id,
            eventType=event_type,
            channel=channel,
            title=title,
            message=message,
            dataPayload=dataPayload
        )
        
        try:
            await self.save_notification(notification_to_save)
        except NotificationError as e:
            logger.error(f"No se pudo guardar la notificación en la base de datos: {e}")
            pass

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

    async def send_paper_trade_exit_notification(self, trade: Trade):
        """
        Envía una notificación al usuario confirmando el cierre de una operación simulada en paper trading.
        """
        user_id = trade.user_id
        symbol = trade.symbol
        side = trade.side
        executed_price = trade.exitOrders[-1].executedPrice if trade.exitOrders else None
        pnl_usd = trade.pnl_usd
        pnl_percentage = trade.pnl_percentage
        closing_reason = trade.closingReason
        trade_id = trade.id

        title = f"📉 Operación Simulada Cerrada: {symbol}"
        message = (
            f"Se ha simulado el cierre de una operación en Paper Trading:\n"
            f"Símbolo: {symbol}\n"
            f"Acción: {side}\n"
            f"Razón de Cierre: {closing_reason}\n"
            f"Precio de Salida: {executed_price:.4f} USDT\n"
            f"P&L: {pnl_usd:.2f} USD ({pnl_percentage:.2f}%)\n"
            f"ID de Trade: {trade_id}"
        )
        
        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="ui",
                event_type="PAPER_TRADE_EXIT_SIMULATED",
                dataPayload={"tradeId": str(trade_id), "symbol": symbol, "side": side, "executedPrice": executed_price, "pnl_usd": pnl_usd, "pnl_percentage": pnl_percentage, "closingReason": closing_reason, "mode": "paper"}
            )
            logger.info(f"Notificación UI de cierre de trade simulado {trade_id} enviada.")
        except Exception as e:
            logger.error(f"Error al enviar notificación UI para cierre de trade simulado {trade_id}: {e}", exc_info=True)

        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="telegram",
                event_type="PAPER_TRADE_EXIT_SIMULATED",
                dataPayload={"tradeId": str(trade_id), "symbol": symbol, "side": side, "executedPrice": executed_price, "pnl_usd": pnl_usd, "pnl_percentage": pnl_percentage, "closingReason": closing_reason, "mode": "paper"}
            )
            logger.info(f"Notificación Telegram de cierre de trade simulado {trade_id} enviada.")
        except Exception as e:
            logger.error(f"Error al enviar notificación Telegram para cierre de trade simulado {trade_id}: {e}", exc_info=True)

    async def send_high_confidence_opportunity_notification(self, opportunity: Opportunity):
        """
        Envía una notificación prioritaria cuando se identifica una oportunidad de muy alta confianza para operativa real.
        """
        user_id = opportunity.user_id
        symbol = opportunity.symbol
        suggested_action = opportunity.ai_analysis.suggestedAction if opportunity.ai_analysis else "N/A"
        confidence = opportunity.ai_analysis.calculatedConfidence if opportunity.ai_analysis else 0.0
        reasoning = opportunity.ai_analysis.reasoning_ai if opportunity.ai_analysis else "Sin resumen."
        opportunity_id = opportunity.id

        title = f"🚨 Oportunidad Real de Alta Confianza: {symbol} ({suggested_action})"
        message = (
            f"¡Se ha detectado una oportunidad de trading de muy alta confianza para operativa real!\n"
            f"Símbolo: {symbol}\n"
            f"Acción Sugerida: {suggested_action}\n"
            f"Confianza de IA: {confidence:.2%}\n"
            f"Resumen del Análisis: {reasoning}\n"
            f"ID de Oportunidad: {opportunity_id}\n\n"
            f"Por favor, revisa la sección 'Oportunidades' en la UI para confirmar la operación."
        )
        data_payload = {
            "opportunityId": str(opportunity_id),
            "symbol": symbol,
            "suggestedAction": suggested_action,
            "confidence": confidence,
            "reasoning": reasoning,
            "status": "pending_user_confirmation_real"
        }

        # Notificación UI (prioridad alta)
        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="ui",
                event_type="OPPORTUNITY_HIGH_CONFIDENCE_REAL_TRADING",
                dataPayload=data_payload
            )
            logger.info(f"Notificación UI de oportunidad de alta confianza {opportunity_id} enviada.")
        except Exception as e:
            logger.error(f"Error al enviar notificación UI para oportunidad de alta confianza {opportunity_id}: {e}", exc_info=True)

        # Notificación Telegram (prioridad alta)
        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="telegram",
                event_type="OPPORTUNITY_HIGH_CONFIDENCE_REAL_TRADING",
                dataPayload=data_payload
            )
            logger.info(f"Notificación Telegram de oportunidad de alta confianza {opportunity_id} enviada.")
        except Exception as e:
            logger.error(f"Error al enviar notificación Telegram para oportunidad de alta confianza {opportunity_id}: {e}", exc_info=True)

    async def send_real_trading_mode_activated_notification(self, user_id: UUID):
        """
        Envía una notificación cuando el modo de operativa real limitada se activa exitosamente.
        """
        title = "✅ Modo Real Limitado Activado"
        message = (
            "¡Felicidades! El modo de Operativa Real Limitada ha sido activado exitosamente.\n"
            "Las próximas operaciones de alta confianza utilizarán dinero real de tu cuenta de Binance."
        )
        data_payload = {"mode": "real", "status": "activated"}

        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="ui",
                event_type="REAL_TRADING_MODE_ACTIVATED",
                dataPayload=data_payload
            )
        except Exception as e:
            logger.error(f"Error al enviar notificación UI de activación de modo real para {user_id}: {e}", exc_info=True)

        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="telegram",
                event_type="REAL_TRADING_MODE_ACTIVATED",
                dataPayload=data_payload
            )
        except Exception as e:
            logger.error(f"Error al enviar notificación Telegram de activación de modo real para {user_id}: {e}", exc_info=True)

    async def send_real_trading_mode_activation_failed_notification(self, user_id: UUID, error_message: str):
        """
        Envía una notificación cuando falla la activación del modo de operativa real limitada.
        """
        title = "❌ Fallo al Activar Modo Real Limitado"
        message = (
            "No se pudo activar el modo de Operativa Real Limitada.\n"
            f"Razón: {error_message}\n\n"
            "Por favor, revisa tus credenciales de Binance, el saldo de USDT o el límite de operaciones."
        )
        data_payload = {"mode": "real", "status": "activation_failed", "error": error_message}

        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="ui",
                event_type="REAL_TRADING_MODE_ACTIVATION_FAILED",
                dataPayload=data_payload
            )
        except Exception as e:
            logger.error(f"Error al enviar notificación UI de fallo de activación de modo real para {user_id}: {e}", exc_info=True)

        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="telegram",
                event_type="REAL_TRADING_MODE_ACTIVATION_FAILED",
                dataPayload=data_payload
            )
        except Exception as e:
            logger.error(f"Error al enviar notificación Telegram de fallo de activación de modo real para {user_id}: {e}", exc_info=True)

    async def send_real_trade_status_notification(self, user_id: UUID, message: str, status_level: str = "INFO", symbol: Optional[str] = None, trade_id: Optional[UUID] = None):
        """
        Envía una notificación sobre el estado de una operación real.
        Args:
            user_id: El ID del usuario.
            message: El mensaje de la notificación.
            status_level: Nivel de estado (ej. "INFO", "WARNING", "ERROR", "CRITICAL").
            symbol: Símbolo del par de trading (opcional).
            trade_id: ID del trade (opcional).
        """
        title_prefix = ""
        if status_level == "INFO":
            title_prefix = "ℹ️ Estado de Orden Real"
        elif status_level == "WARNING":
            title_prefix = "⚠️ Advertencia de Orden Real"
        elif status_level == "ERROR":
            title_prefix = "❌ Error de Orden Real"
        elif status_level == "CRITICAL":
            title_prefix = "🚨 Error CRÍTICO de Orden Real"
        
        title = f"{title_prefix}: {symbol}" if symbol else title_prefix
        
        data_payload = {
            "mode": "real",
            "status_level": status_level,
            "symbol": symbol,
            "tradeId": str(trade_id) if trade_id else None,
            "message": message
        }

        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="ui",
                event_type=f"REAL_TRADE_STATUS_{status_level.upper()}",
                dataPayload=data_payload
            )
            logger.info(f"Notificación UI de estado de orden real enviada para {user_id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificación UI de estado de orden real para {user_id}: {e}", exc_info=True)

        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                channel="telegram",
                event_type=f"REAL_TRADE_STATUS_{status_level.upper()}",
                dataPayload=data_payload
            )
            logger.info(f"Notificación Telegram de estado de orden real enviada para {user_id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificación Telegram de estado de orden real para {user_id}: {e}", exc_info=True)

    async def close(self):
        """Cierra cualquier adaptador de Telegram activo."""
        if self._telegram_adapter:
            await self._telegram_adapter.close()
