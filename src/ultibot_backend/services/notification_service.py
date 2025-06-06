import logging
import json
from uuid import UUID
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from src.shared.data_types import ServiceName, APICredential, Notification, Trade, Opportunity
from src.ultibot_backend.adapters.telegram_adapter import TelegramAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import CredentialError, NotificationError, TelegramNotificationError, ExternalAPIError

if TYPE_CHECKING:
    from src.ultibot_backend.services.configuration_service import ConfigurationService
    from src.ultibot_backend.core.domain_models.user_configuration_models import UserConfiguration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, credential_service: CredentialService, persistence_service: SupabasePersistenceService, config_service: "ConfigurationService"):
        self.credential_service = credential_service
        self.persistence_service = persistence_service
        self.config_service = config_service
        self._telegram_adapter: Optional[TelegramAdapter] = None

    async def _get_telegram_adapter(self, user_id: UUID) -> Optional[TelegramAdapter]:
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
        try:
            saved_notification = await self.persistence_service.save_notification(notification)
            logger.info(f"Notificación {notification.id} guardada en la base de datos.")
            return saved_notification
        except Exception as e:
            logger.error(f"Error al guardar notificación {notification.id} en la base de datos: {e}", exc_info=True)
            raise NotificationError(f"Error al guardar notificación: {e}", code="NOTIFICATION_SAVE_FAILED")

    async def get_notification_history(self, user_id: UUID, limit: int = 50) -> List[Notification]:
        try:
            history = await self.persistence_service.get_notification_history(user_id, limit)
            logger.info(f"Historial de notificaciones recuperado para el usuario {user_id}.")
            return history
        except Exception as e:
            logger.error(f"Error al obtener historial de notificaciones para el usuario {user_id}: {e}", exc_info=True)
            raise NotificationError(f"Error al obtener historial de notificaciones: {e}", code="NOTIFICATION_HISTORY_FAILED")

    async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
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

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        event_type: str,
        opportunity_id: Optional[UUID] = None,
        dataPayload: Optional[Dict[str, Any]] = None
    ) -> bool:
        user_config: "Optional[UserConfiguration]" = await self.config_service.get_user_configuration(user_id=str(user_id))
        if not user_config:
            logger.error(f"No se pudo obtener la configuración para el usuario {user_id}. No se pueden enviar notificaciones.")
            return False

        sent_to_at_least_one_channel = False
        effective_payload = dataPayload or {}
        if opportunity_id:
            effective_payload['opportunity_id'] = str(opportunity_id)

        # Determinar si se debe enviar a cada canal según las preferencias
        send_ui_notification = False
        send_telegram_notification = False

        if user_config.notification_preferences:
            for pref in user_config.notification_preferences:
                if pref.event_type == event_type and pref.is_enabled:
                    if pref.channel == "ui":
                        send_ui_notification = True
                    elif pref.channel == "telegram":
                        send_telegram_notification = True

        # Procesar notificación UI
        if send_ui_notification:
            ui_notification = Notification(
                userId=user_id, eventType=event_type, channel="ui",
                title=title, message=message, dataPayload=effective_payload
            )
            try:
                await self.save_notification(ui_notification)
                logger.info(f"Notificación UI para evento '{event_type}' (OID: {opportunity_id}) guardada para usuario {user_id}.")
                sent_to_at_least_one_channel = True
            except NotificationError as e:
                logger.error(f"No se pudo guardar la notificación UI en la DB para OID {opportunity_id}, User {user_id}: {e}")

        # Procesar notificación Telegram
        if send_telegram_notification and user_config.enable_telegram_notifications:
            chat_id = None
            try:
                telegram_credential = await self.credential_service.get_credential(
                    user_id=user_id, service_name=ServiceName.TELEGRAM_BOT, credential_label="default_telegram_bot"
                )
                if not telegram_credential or not telegram_credential.encrypted_other_details:
                     raise CredentialError("Credenciales de Telegram o 'other_details' no encontrados.", code="TELEGRAM_CREDENTIAL_INCOMPLETE")
                
                other_details = json.loads(telegram_credential.encrypted_other_details)
                chat_id = other_details.get("chat_id")

                if not chat_id:
                    raise CredentialError("chat_id no encontrado en las credenciales de Telegram.", code="TELEGRAM_CHAT_ID_MISSING")

                telegram_adapter = await self._get_telegram_adapter(user_id)
                if not telegram_adapter:
                    raise TelegramNotificationError("No se pudo inicializar TelegramAdapter.", code="TELEGRAM_ADAPTER_INIT_FAILED")

                telegram_notification = Notification(
                    userId=user_id, eventType=event_type, channel="telegram",
                    title=title, message=message, dataPayload=effective_payload
                )
                await self.save_notification(telegram_notification)

                full_message = f"<b>{title}</b>\n\n{message}"
                if opportunity_id:
                    full_message += f"\n\nOportunidad ID: {opportunity_id}"
                
                await telegram_adapter.send_message(chat_id, full_message)
                logger.info(f"Notificación Telegram para evento '{event_type}' (OID: {opportunity_id}) enviada a usuario {user_id}.")
                sent_to_at_least_one_channel = True

            except (CredentialError, TelegramNotificationError, NotificationError) as e:
                logger.error(f"Error al procesar notificación Telegram para OID {opportunity_id}, User {user_id}: {e}")
            except json.JSONDecodeError:
                logger.error(f"Error al decodificar 'other_details' de credencial Telegram para User {user_id}.")
            except Exception as e:
                logger.error(f"Error inesperado al enviar notificación Telegram para OID {opportunity_id}, User {user_id}: {e}", exc_info=True)

        if not sent_to_at_least_one_channel:
            logger.info(f"No se envió notificación para el evento '{event_type}' (OID: {opportunity_id}) para el usuario {user_id} debido a preferencias o configuración.")
        
        return sent_to_at_least_one_channel

    async def send_paper_trade_entry_notification(self, trade: Trade):
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
                event_type="PAPER_TRADE_ENTRY_SIMULATED",
                dataPayload={"tradeId": str(trade_id), "symbol": symbol, "side": side, "quantity": quantity, "executedPrice": executed_price, "mode": "paper"}
            )
            logger.info(f"Notificación de trade simulado {trade_id} (entrada) procesada para envío.")
        except Exception as e:
            logger.error(f"Error al procesar notificación para trade simulado {trade_id} (entrada): {e}", exc_info=True)

    async def send_paper_trade_exit_notification(self, trade: Trade):
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
                event_type="PAPER_TRADE_EXIT_SIMULATED",
                dataPayload={"tradeId": str(trade_id), "symbol": symbol, "side": side, "executedPrice": executed_price, "pnl_usd": pnl_usd, "pnl_percentage": pnl_percentage, "closingReason": closing_reason, "mode": "paper"}
            )
            logger.info(f"Notificación de cierre de trade simulado {trade_id} procesada para envío.")
        except Exception as e:
            logger.error(f"Error al procesar notificación para cierre de trade simulado {trade_id}: {e}", exc_info=True)

    async def send_real_trade_exit_notification(self, trade: Trade):
        user_id = trade.user_id
        symbol = trade.symbol
        side = trade.side
        executed_price = trade.exitOrders[-1].executedPrice if trade.exitOrders else None
        pnl_usd = trade.pnl_usd
        pnl_percentage = trade.pnl_percentage
        closing_reason = trade.closingReason
        trade_id = trade.id
        title = f"✅ Operación Real Cerrada: {symbol}"
        message = (
            f"Se ha cerrado una operación real en Binance:\n"
            f"Símbolo: {symbol}\n"
            f"Acción: {side}\n"
            f"Razón de Cierre: {closing_reason}\n"
            f"Precio de Salida: {executed_price:.4f} USDT\n"
            f"P&L: {pnl_usd:.2f} USD ({pnl_percentage:.2f}%)\n"
            f"ID de Trade: {trade_id}"
        )
        data_payload = {
            "tradeId": str(trade_id),
            "symbol": symbol,
            "side": side,
            "executedPrice": executed_price,
            "pnl_usd": pnl_usd,
            "pnl_percentage": pnl_percentage,
            "closingReason": closing_reason,
            "mode": "real"
        }
        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                event_type="REAL_TRADE_EXIT",
                dataPayload=data_payload
            )
            logger.info(f"Notificación de cierre de trade real {trade_id} procesada para envío.")
        except Exception as e:
            logger.error(f"Error al procesar notificación para cierre de trade real {trade_id}: {e}", exc_info=True)

    async def send_high_confidence_opportunity_notification(self, opportunity: Opportunity):
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
        try:
            await self.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                event_type="OPPORTUNITY_HIGH_CONFIDENCE_REAL_TRADING",
                dataPayload=data_payload
            )
            logger.info(f"Notificación de oportunidad de alta confianza {opportunity_id} procesada para envío.")
        except Exception as e:
            logger.error(f"Error al procesar notificación para oportunidad de alta confianza {opportunity_id}: {e}", exc_info=True)

    async def send_real_trading_mode_activated_notification(self, user_id: UUID):
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
                event_type="REAL_TRADING_MODE_ACTIVATED",
                dataPayload=data_payload
            )
            logger.info(f"Notificación de activación de modo real para {user_id} procesada para envío.")
        except Exception as e:
            logger.error(f"Error al procesar notificación de activación de modo real para {user_id}: {e}", exc_info=True)

    async def send_real_trading_mode_activation_failed_notification(self, user_id: UUID, error_message: str):
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
                event_type="REAL_TRADING_MODE_ACTIVATION_FAILED",
                dataPayload=data_payload
            )
            logger.info(f"Notificación de fallo de activación de modo real para {user_id} procesada para envío.")
        except Exception as e:
            logger.error(f"Error al procesar notificación de fallo de activación de modo real para {user_id}: {e}", exc_info=True)

    async def send_real_trade_status_notification(self, user_id: UUID, message: str, status_level: str = "INFO", symbol: Optional[str] = None, trade_id: Optional[UUID] = None):
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
                event_type=f"REAL_TRADE_STATUS_{status_level.upper()}",
                dataPayload=data_payload
            )
            logger.info(f"Notificación de estado de orden real ({status_level}) para {user_id} procesada para envío.")
        except Exception as e:
            logger.error(f"Error al procesar notificación de estado de orden real ({status_level}) para {user_id}: {e}", exc_info=True)

    async def close(self):
        if self._telegram_adapter:
            await self._telegram_adapter.close()
