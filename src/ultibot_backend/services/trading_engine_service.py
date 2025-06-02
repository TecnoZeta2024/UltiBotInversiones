import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List
import asyncio

from src.shared.data_types import TradeOrderDetails, ServiceName, Opportunity, Trade, PortfolioSnapshot, OpportunityStatus, OrderCategory
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService, PaperOrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter # Importar BinanceAdapter
from src.ultibot_backend.core.exceptions import OrderExecutionError, ConfigurationError, CredentialError, MarketDataError, PortfolioError

logger = logging.getLogger(__name__)

class TradingEngineService:
    """
    Servicio central del motor de trading que decide si ejecutar 贸rdenes
    en modo real o paper trading, bas谩ndose en la configuraci贸n del usuario.
    """
    def __init__(
        self,
        config_service: ConfigService,
        order_execution_service: OrderExecutionService,
        paper_order_execution_service: PaperOrderExecutionService,
        credential_service: CredentialService,
        market_data_service: MarketDataService,
        portfolio_service: PortfolioService,
        persistence_service: SupabasePersistenceService,
        notification_service: NotificationService,
        binance_adapter: BinanceAdapter # A帽adir BinanceAdapter al constructor
    ):
        self.config_service = config_service
        self.order_execution_service = order_execution_service
        self.paper_order_execution_service = paper_order_execution_service
        self.credential_service = credential_service
        self.market_data_service = market_data_service
        self.portfolio_service = portfolio_service
        self.persistence_service = persistence_service
        self.notification_service = notification_service
        self.binance_adapter = binance_adapter # Asignar BinanceAdapter
        self._monitor_task: Optional[asyncio.Task] = None
        self._real_trade_monitor_task: Optional[asyncio.Task] = None

    # Constantes por defecto para c谩lculo de TSL/TP si no est谩n en la configuraci贸n del usuario
    TP_PERCENTAGE_DEFAULT = 0.02  # 2% de ganancia
    TSL_PERCENTAGE_DEFAULT = 0.01  # 1% de p茅rdida inicial
    TSL_CALLBACK_RATE_DEFAULT = 0.005 # 0.5% de retroceso para TSL

    async def start_paper_trading_monitor(self):
        """
        Inicia el monitoreo continuo de trades abiertos en Paper Trading.
        """
        if self._monitor_task and not self._monitor_task.done():
            logger.info("El monitor de Paper Trading ya est谩 en ejecuci贸n.")
            return

        logger.info("Iniciando el monitor de Paper Trading...")
        self._monitor_task = asyncio.create_task(self._run_paper_trading_monitor_loop())

    async def stop_paper_trading_monitor(self):
        """
        Detiene el monitoreo continuo de trades abiertos en Paper Trading.
        """
        if self._monitor_task:
            logger.info("Deteniendo el monitor de Paper Trading...")
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                logger.info("Monitor de Paper Trading detenido.")
            self._monitor_task = None

    async def _run_paper_trading_monitor_loop(self):
        """
        Bucle principal del monitor de Paper Trading.
        """
        # TODO: Hacer el intervalo de monitoreo configurable
        MONITOR_INTERVAL_SECONDS = 5

        while True:
            try:
                logger.debug("Ejecutando ciclo de monitoreo de Paper Trading...")
                # Subtask 1.4: Obtener trades abiertos en Paper Trading
                open_paper_trades = await self.persistence_service.get_open_paper_trades()
                
                if not open_paper_trades:
                    logger.debug("No hay trades abiertos en Paper Trading para monitorear.")
                
                for trade in open_paper_trades:
                    # Subtask 1.5: Dentro del monitoreo, obtener el precio de mercado actual
                    # Subtask 1.6: Implementar la l贸gica para ajustar el TSL
                    # Subtask 1.7: Implementar la l贸gica para detectar si el precio alcanza el TSL o TP
                    # Subtask 1.8: Si se alcanza TSL/TP, simular el cierre de la posici贸n
                    await self.monitor_and_manage_paper_trade_exit(trade)
                
            except Exception as e:
                logger.error(f"Error en el bucle de monitoreo de Paper Trading: {e}", exc_info=True)
            
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)

    async def start_real_trading_monitor(self):
        """
        Inicia el monitoreo continuo de trades abiertos en Real Trading.
        """
        if self._real_trade_monitor_task and not self._real_trade_monitor_task.done():
            logger.info("El monitor de Real Trading ya est谩 en ejecuci贸n.")
            return

        logger.info("Iniciando el monitor de Real Trading...")
        self._real_trade_monitor_task = asyncio.create_task(self._run_real_trading_monitor_loop())

    async def stop_real_trading_monitor(self):
        """
        Detiene el monitoreo continuo de trades abiertos en Real Trading.
        """
        if self._real_trade_monitor_task:
            logger.info("Deteniendo el monitor de Real Trading...")
            self._real_trade_monitor_task.cancel()
            try:
                await self._real_trade_monitor_task
            except asyncio.CancelledError:
                logger.info("Monitor de Real Trading detenido.")
            self._real_trade_monitor_task = None

    async def _run_real_trading_monitor_loop(self):
        """
        Bucle principal del monitor de Real Trading.
        """
        # TODO: Hacer el intervalo de monitoreo configurable
        MONITOR_INTERVAL_SECONDS = 5

        while True:
            try:
                logger.debug("Ejecutando ciclo de monitoreo de Real Trading...")

                # Obtener credenciales de Binance una vez por ciclo de monitoreo
                # Asumimos que todos los trades reales son del mismo usuario o que las credenciales son globales/por defecto
                # Si se necesita por usuario, esta l贸gica deber铆a estar dentro del bucle 'for trade'.
                # TODO: Adaptar para m煤ltiples usuarios si es necesario.
                binance_credential = await self.credential_service.get_credential(
                    user_id=UUID("00000000-0000-0000-0000-000000000001"), # Usar un ID de usuario por defecto o el del primer trade
                    service_name=ServiceName.BINANCE_SPOT,
                    credential_label="default_binance_spot"
                )
                if not binance_credential:
                    logger.error("No se encontraron credenciales de Binance para el monitoreo de trades reales.")
                    await asyncio.sleep(MONITOR_INTERVAL_SECONDS)
                    continue # Saltar este ciclo y reintentar en el siguiente

                api_key = self.credential_service.decrypt_data(binance_credential.encrypted_api_key)
                api_secret: Optional[str] = None
                if binance_credential.encrypted_api_secret:
                    api_secret = self.credential_service.decrypt_data(binance_credential.encrypted_api_secret)

                if not api_key or api_secret is None:
                    logger.error("API Key o Secret de Binance no pudieron ser desencriptados para el monitoreo de trades reales.")
                    await asyncio.sleep(MONITOR_INTERVAL_SECONDS)
                    continue # Saltar este ciclo y reintentar en el siguiente
                # Subtask 2.3: Obtener trades abiertos en Real Trading
                open_real_trades = await self.persistence_service.get_open_real_trades()
                
                if not open_real_trades:
                    logger.debug("No hay trades abiertos en Real Trading para monitorear.")
                
                for trade in open_real_trades:
                    # Subtask 2.3: Monitorear 贸rdenes OCO en Binance si existen
                    if trade.ocoOrderListId:
                        logger.debug(f"Trade REAL {trade.id} tiene ocoOrderListId: {trade.ocoOrderListId}. Monitoreando orden OCO.")
                        await self._monitor_binance_oco_orders(trade, api_key, api_secret)
                    else:
                        # Si no hay orden OCO, continuar con el monitoreo de TSL/TP basado en precio
                        logger.debug(f"Trade REAL {trade.id} no tiene ocoOrderListId. Monitoreando TSL/TP basado en precio.")
                        await self.monitor_and_manage_real_trade_exit(trade)
                
            except Exception as e:
                logger.error(f"Error en el bucle de monitoreo de Real Trading: {e}", exc_info=True)
            
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)

    async def _monitor_binance_oco_orders(self, trade: Trade, api_key: str, api_secret: str) -> None:
        """
        Monitorea el estado de las 贸rdenes OCO en Binance para un trade real.
        """
        logger.info(f"Monitoreando orden OCO {trade.ocoOrderListId} para trade REAL {trade.id} ({trade.symbol})")

        try:
            # Asegurarse de que ocoOrderListId no sea None antes de pasarlo
            if trade.ocoOrderListId is None:
                logger.error(f"Trade REAL {trade.id} tiene ocoOrderListId como None, pero se esperaba un string. Saltando monitoreo OCO.")
                return
            
            oco_order_status = await self.binance_adapter.get_oco_order_by_list_client_order_id(
                api_key=api_key,
                api_secret=api_secret,
                listClientOrderId=str(trade.ocoOrderListId) # Convertir a str expl韈itamente
            )
            logger.debug(f"Estado de orden OCO {trade.ocoOrderListId}: {oco_order_status}")

            if oco_order_status and oco_order_status.get('listStatusType') == 'ALL_DONE':
                logger.info(f"Orden OCO {trade.ocoOrderListId} para trade {trade.id} ha sido ejecutada (ALL_DONE).")
                
                executed_order_report = None
                closing_reason = None
                executed_price = 0.0
                
                # Identificar cu谩l de las 贸rdenes (TP o SL) se ejecut贸
                for order_report in oco_order_status.get('orderReports', []):
                    if order_report.get('status') == 'FILLED':
                        executed_order_report = order_report
                        executed_price = float(order_report.get('price')) if order_report.get('price') else 0.0
                        if order_report.get('type') == 'TAKE_PROFIT_LIMIT':
                            closing_reason = 'TP_HIT'
                        elif order_report.get('type') == 'STOP_LOSS_LIMIT':
                            closing_reason = 'SL_HIT'
                        break # Encontramos la orden ejecutada

                if executed_order_report and closing_reason:
                    logger.info(f"Orden de salida ejecutada para trade {trade.id}: {closing_reason} a precio {executed_price:.4f}")
                    
                    # Crear TradeOrderDetails para la orden de salida ejecutada
                    exit_order_details = TradeOrderDetails(
                        orderId_internal=uuid4(),
                        orderId_exchange=str(executed_order_report.get('orderId')),
                        clientOrderId_exchange=str(executed_order_report.get('clientOrderId', '')), # A帽adir clientOrderId_exchange
                        orderCategory=OrderCategory.TAKE_PROFIT if closing_reason == 'TP_HIT' else OrderCategory.STOP_LOSS,
                        type=executed_order_report.get('type'),
                        status='filled', # Ya sabemos que est谩 FILLED
                        requestedPrice=float(executed_order_report.get('price', 0.0)), # A帽adir requestedPrice
                        requestedQuantity=float(executed_order_report.get('origQty')),
                        executedQuantity=float(executed_order_report.get('executedQty')),
                        executedPrice=executed_price,
                        cumulativeQuoteQty=float(executed_order_report.get('cummulativeQuoteQty', 0.0)), # A帽adir cumulativeQuoteQty
                        commissions=[{ # A帽adir commissions
                            "amount": float(executed_order_report.get('commission', 0.0)),
                            "asset": executed_order_report.get('commissionAsset', '')
                        }],
                        commission=float(executed_order_report.get('commission')) if executed_order_report.get('commission') else None, # Campo legado
                        commissionAsset=executed_order_report.get('commissionAsset'), # Campo legado
                        timestamp=datetime.fromtimestamp(executed_order_report.get('updateTime') / 1000, tz=timezone.utc),
                        submittedAt=datetime.fromtimestamp(executed_order_report.get('updateTime') / 1000, tz=timezone.utc), # A帽adir submittedAt
                        fillTimestamp=datetime.fromtimestamp(executed_order_report.get('updateTime') / 1000, tz=timezone.utc), # A帽adir fillTimestamp
                        rawResponse=executed_order_report,
                        ocoOrderListId=trade.ocoOrderListId
                    )
                    
                    # Llamar a _close_real_trade para finalizar el trade en la DB y notificar
                    await self._close_real_trade(trade, executed_price, closing_reason, exit_order_details)
                else:
                    logger.warning(f"Orden OCO {trade.ocoOrderListId} ALL_DONE pero no se pudo identificar la orden ejecutada para trade {trade.id}.")
            elif oco_order_status and oco_order_status.get('listStatusType') == 'REJECT':
                logger.error(f"Orden OCO {trade.ocoOrderListId} para trade {trade.id} fue RECHAZADA. Necesita atenci贸n manual.")
                await self.notification_service.send_real_trade_status_notification(
                    trade.user_id, f"CR脥TICO: Orden OCO {trade.ocoOrderListId} para {trade.symbol} fue RECHAZADA. Revise manualmente.", "CRITICAL"
                )
            # Si el estado es 'EXECUTING' o 'REJECT' (pero no ALL_DONE), no hacemos nada, seguimos monitoreando.
            # Si el estado es 'CANCELED', tambi茅n se podr铆a manejar aqu铆 si se cancela manualmente.

        except Exception as e:
            logger.error(f"Error al monitorear orden OCO {trade.ocoOrderListId} para trade REAL {trade.id}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                trade.user_id, f"Error al monitorear orden OCO para {trade.symbol}: {str(e)}", "ERROR"
            )

    async def monitor_and_manage_real_trade_exit(self, trade: Trade) -> None:
        """
        Monitorea y gestiona las 贸rdenes de salida (TSL/TP) para un trade en Real Trading.
        Este m茅todo se enfoca en el ajuste del Trailing Stop Loss basado en el precio.
        La detecci贸n de ejecuci贸n de TP/SL para 贸rdenes OCO se maneja en _monitor_binance_oco_orders.
        """
        # Si el trade ya tiene una orden OCO asociada, su monitoreo de cierre se hace en _monitor_binance_oco_orders
        if trade.ocoOrderListId:
            logger.debug(f"Trade REAL {trade.id} tiene ocoOrderListId. Saltando monitoreo de TSL/TP basado en precio en monitor_and_manage_real_trade_exit.")
            return

        logger.info(f"Monitoreando TSL/TP basado en precio para trade REAL {trade.id} ({trade.symbol})")

        # Subtask 2.3: Obtener el precio de mercado actual
        try:
            current_price = await self.market_data_service.get_latest_price(trade.symbol)
            logger.debug(f"Precio actual de {trade.symbol}: {current_price}")
        except MarketDataError as e:
            logger.error(f"Error al obtener precio de mercado para trade REAL {trade.symbol} en monitoreo: {e}", exc_info=True)
            return

        # Subtask 2.3: Implementar la l贸gica para ajustar el TSL si el precio se mueve favorablemente
        if trade.positionStatus == 'open':
            if trade.trailingStopCallbackRate is None or trade.currentStopPrice_tsl is None:
                logger.warning(f"Trade REAL {trade.id} no tiene TSL configurado correctamente. Saltando ajuste de TSL.")
                return

            if trade.side == 'BUY':
                # Para BUY, TSL sube si el precio sube
                if current_price > trade.entryOrder.executedPrice:
                    new_potential_stop = current_price * (1 - trade.trailingStopCallbackRate)
                    if new_potential_stop > trade.currentStopPrice_tsl:
                        trade.currentStopPrice_tsl = new_potential_stop
                        trade.updated_at = datetime.now(timezone.utc)
                        logger.info(f"TSL para trade REAL {trade.symbol} (BUY) ajustado a {trade.currentStopPrice_tsl:.4f} (precio actual: {current_price:.4f})")
                        trade.riskRewardAdjustments.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "type": "TSL_ADJUSTMENT_REAL",
                            "new_stop_price": new_potential_stop,
                            "current_price": current_price
                        })
                        await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
                        logger.info(f"Trade REAL {trade.id} con TSL actualizado persistido.")
            elif trade.side == 'SELL':
                # Para SELL, TSL baja si el precio baja
                if current_price < trade.entryOrder.executedPrice:
                    new_potential_stop = current_price * (1 + trade.trailingStopCallbackRate)
                    if new_potential_stop < trade.currentStopPrice_tsl:
                        trade.currentStopPrice_tsl = new_potential_stop
                        trade.updated_at = datetime.now(timezone.utc)
                        logger.info(f"TSL para trade REAL {trade.symbol} (SELL) ajustado a {trade.currentStopPrice_tsl:.4f} (precio actual: {current_price:.4f})")
                        trade.riskRewardAdjustments.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "type": "TSL_ADJUSTMENT_REAL",
                            "new_stop_price": new_potential_stop,
                            "current_price": current_price
                        })
                        await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
                        logger.info(f"Trade REAL {trade.id} con TSL actualizado persistido.")


    async def _close_real_trade(self, trade: Trade, executed_price: float, closing_reason: str, exit_order_details: Optional[TradeOrderDetails] = None):
        """
        Cierra una posici贸n real en Binance.
        Puede ser llamado por la ejecuci贸n de una orden OCO o por un cierre manual.
        """
        logger.info(f"Cerrando trade REAL {trade.id} por {closing_reason} a precio {executed_price:.4f}")

        # Verificar si la posici贸n ya est谩 cerrada o si ya tiene una orden de salida ejecutada
        if trade.positionStatus == 'closed':
            logger.info(f"Trade REAL {trade.id} ya est谩 cerrado. Raz贸n: {trade.closingReason}. No se requiere acci贸n adicional.")
            return
        
        # Si la orden de salida ya viene pre-cargada (ej. desde el monitoreo OCO), usarla.
        # De lo contrario, se enviar谩 una nueva orden de mercado.
        if exit_order_details and exit_order_details.status == 'filled':
            logger.info(f"Usando detalles de orden de salida pre-existentes para trade {trade.id}.")
            # Asegurarse de que la orden de salida est茅 en la lista de exitOrders del trade
            if not any(o.orderId_exchange == exit_order_details.orderId_exchange for o in trade.exitOrders):
                trade.exitOrders.append(exit_order_details)
        else:
            logger.info(f"Enviando nueva orden de mercado para cerrar trade {trade.id}.")
            # Obtener credenciales de Binance para cerrar la orden
            binance_credential = await self.credential_service.get_credential(
                user_id=trade.user_id,
                service_name=ServiceName.BINANCE_SPOT,
                credential_label="default_binance_spot"
            )
            if not binance_credential:
                logger.error(f"No se encontraron credenciales de Binance para cerrar trade {trade.id}.")
                raise CredentialError(f"No se encontraron credenciales de Binance para cerrar trade {trade.id}.")
            
            api_key = self.credential_service.decrypt_data(binance_credential.encrypted_api_key)
            api_secret: Optional[str] = None
            if binance_credential.encrypted_api_secret:
                api_secret = self.credential_service.decrypt_data(binance_credential.encrypted_api_secret)

            if not api_key or api_secret is None:
                logger.error(f"API Key o Secret de Binance no pudieron ser desencriptados para cerrar trade {trade.id}.")
                raise CredentialError("API Key o Secret de Binance no v谩lidos para cerrar trade.")

            # Determinar el lado de la orden de cierre
            close_side = 'SELL' if trade.side == 'BUY' else 'BUY'
            
            # Enviar orden de mercado para cerrar la posici贸n
            try:
                # Pasar ocoOrderListId como None ya que es una orden de cierre directa
                exit_order_details = await self.order_execution_service.execute_market_order(
                    user_id=trade.user_id,
                    symbol=trade.symbol,
                    side=close_side,
                    quantity=trade.entryOrder.executedQuantity,
                    api_key=api_key,
                    api_secret=api_secret,
                    ocoOrderListId=None # Asegurar que se pasa None
                )
                # Asegurarse de que la categor铆a de la orden de salida sea correcta
                if closing_reason == 'SL_HIT':
                    exit_order_details.orderCategory = OrderCategory.STOP_LOSS
                elif closing_reason == 'TP_HIT':
                    exit_order_details.orderCategory = OrderCategory.TAKE_PROFIT
                else:
                    exit_order_details.orderCategory = OrderCategory.MANUAL_CLOSE # O cualquier otra raz贸n de cierre
                # ocoOrderListId ya se asigna como None en la llamada a execute_market_order
                
                logger.info(f"Orden de cierre real enviada a Binance para trade {trade.id}: {exit_order_details.orderId_internal}")
            except OrderExecutionError as e:
                logger.error(f"Fallo al enviar orden de cierre real para trade {trade.id}: {e}", exc_info=True)
                await self.notification_service.send_real_trade_status_notification(
                    trade.user_id, f"Error al cerrar trade real {trade.symbol} por {closing_reason}: {str(e)}", "ERROR"
                )
                raise
            
            trade.exitOrders.append(exit_order_details)

        # La l贸gica de obtenci贸n de credenciales y env铆o de orden de mercado ya est谩 dentro del 'else'
        # de la verificaci贸n 'if exit_order_details and exit_order_details.status == 'filled':'
        # No es necesario duplicarla aqu铆.
        # El par谩metro exit_order_details ya est谩 definido en la firma de la funci贸n.

        # Actualizar el Trade con la orden de salida, P&L y estado
        trade.positionStatus = 'closed'
        trade.closingReason = closing_reason
        trade.closed_at = datetime.now(timezone.utc)

        # Calcular P&L (usando el precio de ejecuci贸n de la orden de salida)
        entry_value = trade.entryOrder.executedQuantity * trade.entryOrder.executedPrice
        exit_value = exit_order_details.executedQuantity * exit_order_details.executedPrice

        if trade.side == 'BUY':
            trade.pnl_usd = exit_value - entry_value
        elif trade.side == 'SELL':
            trade.pnl_usd = entry_value - exit_value

        if entry_value > 0 and trade.pnl_usd is not None:
            trade.pnl_percentage = (trade.pnl_usd / entry_value) * 100
        else:
            trade.pnl_percentage = 0.0

        logger.info(f"Trade REAL {trade.id} cerrado. P&L: {trade.pnl_usd:.2f} USD ({trade.pnl_percentage:.2f}%)")

        # Persistir el Trade actualizado
        try:
            await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info(f"Trade REAL {trade.id} cerrado y persistido exitosamente.")
        except Exception as e:
            logger.error(f"Error al persistir el trade REAL cerrado {trade.id}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                trade.user_id, f"Error cr铆tico: Trade real cerrado en Binance pero fallo al persistir {trade.id}: {str(e)}", "CRITICAL"
            )
            raise OrderExecutionError(f"Orden real cerrada pero fallo al persistir el trade: {e}") from e

        # Actualizar el portafolio real tras el cierre de una posici贸n.
        try:
            await self.portfolio_service.update_real_portfolio_after_exit(trade)
            logger.info(f"Portafolio real actualizado para trade {trade.id}.")
        except Exception as e:
            logger.error(f"Error al actualizar el portafolio real tras cierre de trade {trade.id}: {e}", exc_info=True)

        # Subtask 2.5: Enviar notificaciones al usuario sobre la ejecuci贸n de TSL/TP.
        try:
            await self.notification_service.send_real_trade_exit_notification(trade)
            logger.info(f"Notificaci贸n de cierre de trade real enviada para trade {trade.id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificaci贸n de cierre para trade REAL {trade.id}: {e}", exc_info=True)

    async def simulate_paper_entry_order(self, opportunity: Opportunity) -> Trade:
        """
        Simula la ejecuci贸n de una orden de entrada en modo Paper Trading
        para una oportunidad de trading validada por la IA.
        """
        logger.info(f"Simulando orden de entrada para oportunidad {opportunity.id} ({opportunity.symbol})")
        user_id = opportunity.user_id
        symbol = opportunity.symbol
        side = opportunity.ai_analysis.suggestedAction if opportunity.ai_analysis else None

        if not symbol or not side:
            logger.error(f"Oportunidad {opportunity.id} no tiene s铆mbolo o acci贸n sugerida. No se puede simular.")
            raise OrderExecutionError(f"Oportunidad inv谩lida para simulaci贸n: {opportunity.id}")

        # Subtask 1.2: Obtener el precio de mercado actual
        try:
            current_price = await self.market_data_service.get_latest_price(symbol)
            logger.info(f"Precio actual de {symbol}: {current_price}")
        except MarketDataError as e:
            logger.error(f"Error al obtener precio de mercado para {symbol}: {e}", exc_info=True)
            raise OrderExecutionError(f"No se pudo obtener el precio de mercado para {symbol}.") from e

        # Subtask 1.3: Calcular el tama帽o de la posici贸n (quantity)
        user_config = await self.config_service.get_user_configuration(str(user_id))
        
        # Obtener el capital disponible del portafolio de paper trading
        portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(user_id)
        available_capital = portfolio_snapshot.paper_trading.available_balance_usdt

        # Reglas de gesti贸n de capital (FR3.1 - no m谩s del 50% del capital diario, FR3.2 - ajuste din谩mico al 25%)
        # Simplificaci贸n: Usaremos perTradeCapitalRiskPercentage sobre el capital disponible para esta simulaci贸n.
        # La l贸gica de "capital diario" es m谩s compleja y podr铆a requerir un seguimiento de trades diarios.
        per_trade_risk_percentage = user_config.riskProfileSettings.perTradeCapitalRiskPercentage if user_config.riskProfileSettings else None
        
        if not per_trade_risk_percentage:
            logger.warning(f"No se encontr贸 'perTradeCapitalRiskPercentage' para usuario {user_id}. Usando 0.01 (1%).")
            per_trade_risk_percentage = 0.01

        capital_to_invest = available_capital * per_trade_risk_percentage
        
        if capital_to_invest <= 0:
            logger.warning(f"Capital a invertir es cero o negativo para {user_id}. No se puede simular la orden.")
            raise OrderExecutionError("Capital insuficiente para simular la orden.")

        # Calcular la cantidad (quantity)
        # Asumimos que el precio es en USDT y la cantidad es del activo base (ej. BTC en BTCUSDT)
        quantity = capital_to_invest / current_price
        
        # TODO: Considerar la precisi贸n de los s铆mbolos (pasos de cantidad y precio) de Binance para redondear correctamente.
        # Esto requerir铆a obtener informaci贸n de los s铆mbolos de Binance, lo cual puede ser una tarea futura o una mejora.
        # Por ahora, usaremos la cantidad calculada directamente.
        logger.info(f"Calculado: Capital disponible={available_capital}, % riesgo por trade={per_trade_risk_percentage}, Capital a invertir={capital_to_invest}, Cantidad={quantity}")

        # Subtask 1.4: Crear una instancia de TradeOrderDetails
        simulated_order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            orderId_exchange=None, 
            clientOrderId_exchange=None, 
            orderCategory=OrderCategory.ENTRY, 
            type='market',
            status='filled',
            requestedPrice=current_price, 
            requestedQuantity=quantity,
            executedQuantity=quantity,
            executedPrice=current_price,
            cumulativeQuoteQty=quantity * current_price, 
            commissions=[], 
            commission=None, 
            commissionAsset=None, 
            timestamp=datetime.now(timezone.utc),
            submittedAt=datetime.now(timezone.utc), 
            fillTimestamp=datetime.now(timezone.utc), 
            rawResponse=None,
            ocoOrderListId=None 
        )
        logger.info(f"Orden simulada creada: {simulated_order_details.orderId_internal}")

        # Subtask 1.2: Calcular los niveles iniciales de TSL y TP (AC1)
        # Usar la configuraci贸n del usuario para los porcentajes de TSL/TP
        tp_percentage = user_config.riskProfileSettings.takeProfitPercentage if user_config.riskProfileSettings and user_config.riskProfileSettings.takeProfitPercentage is not None else self.TP_PERCENTAGE_DEFAULT
        tsl_percentage = user_config.riskProfileSettings.trailingStopLossPercentage if user_config.riskProfileSettings and user_config.riskProfileSettings.trailingStopLossPercentage is not None else self.TSL_PERCENTAGE_DEFAULT
        tsl_callback_rate = user_config.riskProfileSettings.trailingStopCallbackRate if user_config.riskProfileSettings and user_config.riskProfileSettings.trailingStopCallbackRate is not None else self.TSL_CALLBACK_RATE_DEFAULT

        take_profit_price = current_price * (1 + tp_percentage) if side == 'BUY' else current_price * (1 - tp_percentage)
        trailing_stop_activation_price = current_price * (1 - tsl_percentage) if side == 'BUY' else current_price * (1 + tsl_percentage)
        current_stop_price_tsl = trailing_stop_activation_price

        logger.info(f"Calculado para {symbol} ({side}): TP={take_profit_price:.4f}, TSL Act.={trailing_stop_activation_price:.4f}, TSL Callback={tsl_callback_rate}, Current TSL={current_stop_price_tsl:.4f}")

        # Subtask 1.5: Crear una nueva instancia de Trade
        new_trade = Trade(
            id=uuid4(),
            user_id=user_id,
            mode='paper',
            symbol=symbol,
            side=side,
            entryOrder=simulated_order_details,
            exitOrders=[],
            positionStatus='open',
            opportunityId=opportunity.id,
            aiAnalysisConfidence=opportunity.ai_analysis.calculatedConfidence if opportunity.ai_analysis else None,
            pnl_usd=None,
            pnl_percentage=None,
            closingReason=None,
            ocoOrderListId=None, # Argumento añadido
            takeProfitPrice=take_profit_price,
            trailingStopActivationPrice=trailing_stop_activation_price,
            trailingStopCallbackRate=tsl_callback_rate,
            currentStopPrice_tsl=current_stop_price_tsl,
            riskRewardAdjustments=[],
            created_at=datetime.now(timezone.utc),
            opened_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            closed_at=None
        )
        logger.info(f"Trade simulado creado: {new_trade.id}")

        # Subtask 1.6: Persistir el nuevo Trade
        try:
            await self.persistence_service.upsert_trade(new_trade.user_id, new_trade.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info(f"Trade simulado {new_trade.id} persistido exitosamente.")
        except Exception as e:
            logger.error(f"Error al persistir el trade simulado {new_trade.id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo al persistir el trade simulado: {e}") from e
        
        # Task 2: Actualizar el portafolio de Paper Trading (Subtasks 2.1 - 2.4)
        # Esto se har谩 en PortfolioService, pero lo llamamos desde aqu铆.
        try:
            await self.portfolio_service.update_paper_portfolio_after_entry(new_trade)
            logger.info(f"Portafolio de paper trading actualizado para trade {new_trade.id}.")
        except Exception as e:
            logger.error(f"Error al actualizar el portafolio de paper trading para trade {new_trade.id}: {e}", exc_info=True)

        # Task 3: Enviar notificaciones al usuario (Subtasks 3.1 - 3.2)
        try:
            await self.notification_service.send_paper_trade_entry_notification(new_trade)
            logger.info(f"Notificaci贸n de trade simulado enviada para trade {new_trade.id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificaci贸n para trade {new_trade.id}: {e}", exc_info=True)
        
        return new_trade


    async def process_opportunity_for_real_trading(self, opportunity: Opportunity):
        """
        Procesa una oportunidad de trading analizada por la IA para determinar
        si es una candidata de muy alta confianza para operativa real.
        """
        logger.info(f"Procesando oportunidad {opportunity.id} para posible operativa real.")

        user_id = opportunity.user_id
        user_config = await self.config_service.get_user_configuration(str(user_id))

        # Acceder a realTradingSettings de forma segura
        real_trading_settings = user_config.realTradingSettings
        if not real_trading_settings or not real_trading_settings.real_trading_mode_active:
            logger.info(f"Modo de operativa real no activo para usuario {user_id}. Oportunidad {opportunity.id} no considerada para real trading.")
            return

        if not opportunity.ai_analysis or opportunity.ai_analysis.calculatedConfidence is None:
            logger.warning(f"Oportunidad {opportunity.id} no tiene an谩lisis de IA o confianza calculada. No se puede procesar para real trading.")
            return

        # Subtask 1.1: Filtrar oportunidades bas谩ndose en aiAnalysis.calculatedConfidence > 0.95
        confidence_threshold = 0.95
        if user_config.aiAnalysisConfidenceThresholds and user_config.aiAnalysisConfidenceThresholds.realTrading is not None:
            confidence_threshold = user_config.aiAnalysisConfidenceThresholds.realTrading
        
        if opportunity.ai_analysis.calculatedConfidence <= confidence_threshold:
            logger.info(f"Confianza de IA ({opportunity.ai_analysis.calculatedConfidence:.2f}) para oportunidad {opportunity.id} no supera el umbral de {confidence_threshold:.2f}. No es candidata para operativa real.")
            return

        # Subtask 1.3: Verificar el real_trades_executed_count
        real_trades_executed_count = real_trading_settings.real_trades_executed_count if real_trading_settings.real_trades_executed_count is not None else 0
        max_real_trades = real_trading_settings.max_real_trades if real_trading_settings.max_real_trades is not None else 5

        if real_trades_executed_count >= max_real_trades:
            logger.warning(f"L铆mite de operaciones reales ({max_real_trades}) alcanzado para usuario {user_id}. Oportunidad {opportunity.id} no presentada para operativa real.")
            return

        # Subtask 1.4: Actualizar el status de la Opportunity a PENDING_USER_CONFIRMATION_REAL
        opportunity.status = OpportunityStatus.PENDING_USER_CONFIRMATION_REAL
        opportunity.updated_at = datetime.now(timezone.utc)
        try:
            await self.persistence_service.upsert_opportunity(opportunity.user_id, opportunity.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info(f"Oportunidad {opportunity.id} actualizada a 'pending_user_confirmation_real' y persistida.")
        except Exception as e:
            logger.error(f"Error al persistir la oportunidad {opportunity.id} con estado 'pending_user_confirmation_real': {e}", exc_info=True)
            return

        # Subtask 4.2: Disparar notificaci贸n prioritaria
        try:
            await self.notification_service.send_high_confidence_opportunity_notification(opportunity)
            logger.info(f"Notificaci贸n de oportunidad de alta confianza enviada para {opportunity.id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificaci贸n de alta confianza para oportunidad {opportunity.id}: {e}", exc_info=True)

        logger.info(f"Oportunidad {opportunity.id} es una candidata de muy alta confianza para operativa real y ha sido marcada para confirmaci贸n del usuario.")

    async def execute_real_trade(self, opportunity_id: UUID, user_id: UUID) -> Trade:
        """
        Ejecuta una orden real en Binance basada en una oportunidad confirmada por el usuario.
        """
        logger.info(f"Iniciando ejecuci贸n de orden REAL para oportunidad {opportunity_id} y usuario {user_id}.")

        # 2.2: Recuperar la Opportunity completa de la base de datos
        opportunity = await self.persistence_service.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            logger.error(f"Oportunidad {opportunity_id} no encontrada para ejecuci贸n real.")
            raise OrderExecutionError(f"Oportunidad {opportunity_id} no encontrada.")

        if opportunity.status != OpportunityStatus.PENDING_USER_CONFIRMATION_REAL:
            logger.error(f"Oportunidad {opportunity_id} no est谩 en estado PENDING_USER_CONFIRMATION_REAL. Estado actual: {opportunity.status}")
            await self.notification_service.send_real_trade_status_notification(
                user_id, 
                f"Error al enviar orden real para {opportunity.symbol} ({(opportunity.ai_analysis.suggestedAction if opportunity.ai_analysis else 'N/A')}): Oportunidad no est谩 en estado PENDING_USER_CONFIRMATION_REAL. Estado actual: {opportunity.status.value}", 
                "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, f"Oportunidad {opportunity_id} no est谩 en estado PENDING_USER_CONFIRMATION_REAL. Estado actual: {opportunity.status.value}"
            )
            raise OrderExecutionError(f"Oportunidad {opportunity_id} no est谩 lista para ejecuci贸n real.")

        if not opportunity.symbol or not opportunity.ai_analysis or opportunity.ai_analysis.suggestedAction is None:
            logger.error(f"Oportunidad {opportunity_id} carece de s铆mbolo o acci贸n sugerida por IA.")
            raise OrderExecutionError(f"Oportunidad {opportunity_id} incompleta para ejecuci贸n real.")

        symbol = opportunity.symbol
        side = opportunity.ai_analysis.suggestedAction # Ya se verific贸 que no es None
        
        # 2.3: Calcular la cantidad a operar (requestedQuantity)
        user_config = await self.config_service.get_user_configuration(str(user_id))
        if not user_config or not user_config.realTradingSettings or not user_config.riskProfileSettings:
            logger.error(f"Configuraci贸n de usuario o de trading real/riesgo no encontrada para {user_id}.")
            await self.notification_service.send_real_trade_status_notification(
                user_id, 
                f"Error al enviar orden real para {symbol} ({side}): Configuraci贸n de usuario incompleta para operativa real.", 
                "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Configuraci贸n de usuario incompleta para operativa real."
            )
            raise ConfigurationError("Configuraci贸n de usuario incompleta para operativa real.")

        real_trading_settings = user_config.realTradingSettings
        risk_profile_settings = user_config.riskProfileSettings

        # Obtener el saldo real disponible y el capital total
        try:
            portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(user_id)
            available_capital = portfolio_snapshot.real_trading.available_balance_usdt
            total_real_capital = portfolio_snapshot.real_trading.total_portfolio_value_usd
            logger.info(f"Saldo real disponible para {user_id}: {available_capital} USDT. Capital total real: {total_real_capital} USDT.")
        except PortfolioError as e:
            logger.error(f"Error al obtener el saldo real para {user_id}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): No se pudo obtener el saldo real: {str(e)}", "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, f"No se pudo obtener el saldo real: {e}"
            )
            raise OrderExecutionError(f"No se pudo obtener el saldo real: {e}") from e

        # Subtask 1.3: Implementar mecanismo para monitorear y resetear daily_capital_risked_usd
        today = datetime.now(timezone.utc).date()
        if real_trading_settings.last_daily_reset.date() != today:
            logger.info(f"Reiniciando daily_capital_risked_usd para {user_id}. 脷ltimo reinicio: {real_trading_settings.last_daily_reset.date()}")
            real_trading_settings.daily_capital_risked_usd = 0.0
            real_trading_settings.last_daily_reset = datetime.now(timezone.utc)
            await self.config_service.save_user_configuration(user_config)

        # Subtask 1.2: Asegurar que el c谩lculo respete dailyCapitalRiskPercentage (50% del capital total)
        daily_capital_risk_percentage = risk_profile_settings.dailyCapitalRiskPercentage
        if daily_capital_risk_percentage is None:
            logger.warning(f"dailyCapitalRiskPercentage no configurado para {user_id}. Usando 0.50 (50%) como valor por defecto.")
            daily_capital_risk_percentage = 0.50
        
        max_daily_risk_usd = total_real_capital * daily_capital_risk_percentage
        logger.info(f"M谩ximo capital diario a arriesgar para {user_id}: {max_daily_risk_usd:.2f} USDT (basado en {daily_capital_risk_percentage*100}% de {total_real_capital:.2f}).")
        logger.info(f"Capital ya arriesgado hoy: {real_trading_settings.daily_capital_risked_usd:.2f} USDT.")

        # Subtask 1.1: Calcular el tama帽o de la posici贸n bas谩ndose en perTradeCapitalRiskPercentage
        per_trade_capital_risk_percentage = risk_profile_settings.perTradeCapitalRiskPercentage
        if per_trade_capital_risk_percentage is None:
            logger.warning(f"perTradeCapitalRiskPercentage no configurado para {user_id}. Usando 0.25 (25%) como valor por defecto.")
            per_trade_capital_risk_percentage = 0.25

        capital_to_invest_per_trade = available_capital * per_trade_capital_risk_percentage
        
        # Subtask 1.3: Verificar si la nueva operaci贸n excede el l铆mite diario
        if (real_trading_settings.daily_capital_risked_usd + capital_to_invest_per_trade) > max_daily_risk_usd:
            error_msg = (f"La operaci贸n exceder铆a el l铆mite de riesgo diario para {user_id}. "
                         f"Capital a invertir: {capital_to_invest_per_trade:.2f}, "
                         f"Capital arriesgado hoy: {real_trading_settings.daily_capital_risked_usd:.2f}, "
                         f"L铆mite diario: {max_daily_risk_usd:.2f}.")
            logger.error(error_msg)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): L铆mite de riesgo de capital diario excedido.", "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, "L铆mite de riesgo de capital diario excedido."
            )
            raise OrderExecutionError("L铆mite de riesgo de capital diario excedido.")

        if capital_to_invest_per_trade <= 0:
            logger.error(f"Capital a invertir es cero o negativo para {user_id}. Capital disponible: {available_capital}.")
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): Capital insuficiente para la operaci贸n real.", "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Capital insuficiente para la operaci贸n real."
            )
            raise OrderExecutionError("Capital insuficiente para la operaci贸n real.")

        # Obtener el precio de mercado actual para calcular la cantidad
        try:
            current_price = await self.market_data_service.get_latest_price(symbol)
            logger.info(f"Precio actual de {symbol}: {current_price}")
        except MarketDataError as e:
            logger.error(f"Error al obtener precio de mercado para {symbol}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): No se pudo obtener el precio de mercado para {symbol}.", "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, f"No se pudo obtener el precio de mercado para {symbol}."
            )
            raise OrderExecutionError(f"No se pudo obtener el precio de mercado para {symbol}.") from e

        requested_quantity = capital_to_invest_per_trade / current_price
        logger.info(f"Calculado para orden real: Capital a invertir={capital_to_invest_per_trade:.2f}, Cantidad={requested_quantity:.8f}")

        # Verificar cupos disponibles de nuevo (doble chequeo)
        if real_trading_settings.real_trades_executed_count >= real_trading_settings.max_real_trades:
            logger.error(f"L铆mite de operaciones reales ({real_trading_settings.max_real_trades}) alcanzado para usuario {user_id}.")
            raise OrderExecutionError("L铆mite de operaciones reales alcanzado.")

        # 2.4: Utilizar el BinanceAdapter para enviar la orden real a Binance
        # Obtener credenciales de Binance
        binance_credential = await self.credential_service.get_credential(
            user_id=user_id,
            service_name=ServiceName.BINANCE_SPOT,
            credential_label="default_binance_spot"
        )
        
        if not binance_credential:
            logger.error(f"No se encontraron credenciales de Binance para el usuario {user_id}.")
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): No se encontraron credenciales de Binance para el usuario {user_id}.", "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, f"No se encontraron credenciales de Binance para el usuario {user_id}."
            )
            raise CredentialError(f"No se encontraron credenciales de Binance para el usuario {user_id}.")
        
        api_key = self.credential_service.decrypt_data(binance_credential.encrypted_api_key)
        api_secret: Optional[str] = None
        if binance_credential.encrypted_api_secret:
            api_secret = self.credential_service.decrypt_data(binance_credential.encrypted_api_secret)

        if not api_key or api_secret is None:
            logger.error(f"API Key o Secret de Binance no pudieron ser desencriptados para {user_id}.")
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): API Key o Secret de Binance no v谩lidos.", "ERROR"
            )
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, "API Key o Secret de Binance no v谩lidos."
            )
            raise CredentialError("API Key o Secret de Binance no v谩lidos.")

        trade_order_details: Optional[TradeOrderDetails] = None
        try:
            # La orden de entrada real se ejecuta a trav茅s de OrderExecutionService, que ya deber铆a manejar TradeOrderDetails
            # con los nuevos campos. Sin embargo, para asegurar la consistencia, la instanciaci贸n aqu铆 debe reflejarlo.
            # Asumimos que execute_market_order devuelve un TradeOrderDetails ya completo.
            trade_order_details = await self.order_execution_service.execute_market_order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=requested_quantity,
                api_key=api_key,
                api_secret=api_secret,
                ocoOrderListId=None # Asegurar que se pasa None para la orden de entrada directa
            )
            # Asegurarse de que la categor铆a de la orden de entrada sea correcta
            trade_order_details.orderCategory = OrderCategory.ENTRY
            trade_order_details.ocoOrderListId = None # No aplica para la orden de entrada

            logger.info(f"Orden real enviada a Binance: {trade_order_details.orderId_internal}")
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Orden real enviada para {symbol} ({side}). Estado: {trade_order_details.status}", "INFO"
            )
        except OrderExecutionError as e:
            logger.error(f"Fallo al enviar orden real a Binance para oportunidad {opportunity_id}: {e}", exc_info=True)
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, f"Fallo al enviar orden real: {str(e)}"
            )
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): {str(e)}", "ERROR"
            )
            raise

        # Subtask 2.1: Calcular los niveles iniciales de TSL y TP para trades reales
        # Usar la configuraci贸n del usuario para los porcentajes de TSL/TP
        tp_percentage_real = risk_profile_settings.takeProfitPercentage if risk_profile_settings and risk_profile_settings.takeProfitPercentage is not None else self.TP_PERCENTAGE_DEFAULT
        tsl_percentage_real = risk_profile_settings.trailingStopLossPercentage if risk_profile_settings and risk_profile_settings.trailingStopLossPercentage is not None else self.TSL_PERCENTAGE_DEFAULT
        tsl_callback_rate_real = risk_profile_settings.trailingStopCallbackRate if risk_profile_settings and risk_profile_settings.trailingStopCallbackRate is not None else self.TSL_CALLBACK_RATE_DEFAULT

        take_profit_price = current_price * (1 + tp_percentage_real) if side == 'BUY' else current_price * (1 - tp_percentage_real)
        trailing_stop_activation_price = current_price * (1 - tsl_percentage_real) if side == 'BUY' else current_price * (1 + tsl_percentage_real)
        current_stop_price_tsl = trailing_stop_activation_price

        # Subtask 2.2: Enviar 贸rdenes de TSL y TP a Binance (usando OCO si es posible)
        # Determinar el lado opuesto para las 贸rdenes de salida
        exit_side = 'SELL' if side == 'BUY' else 'BUY'
        
        oco_list_client_order_id = None # Inicializar a None
        oco_exit_orders: List[TradeOrderDetails] = [] # Inicializar a lista vac铆a
        
        try:
            # Binance OCO order: STOP_LOSS_LIMIT and TAKE_PROFIT_LIMIT
            # stopPrice es el precio que activa la orden stop-loss
            # limitPrice es el precio al que se ejecuta la orden stop-loss (puede ser el mismo que stopPrice o ligeramente peor)
            # quantity es la cantidad de la posici贸n abierta
            
            # Para TSL, el stopPrice es currentStopPrice_tsl
            # Para TP, el price es takeProfitPrice
            
            # Necesitamos la cantidad de la orden de entrada para las 贸rdenes de salida
            quantity_to_close = trade_order_details.executedQuantity

            # TODO: Considerar la precisi贸n de los s铆mbolos (pasos de cantidad y precio) de Binance para redondear correctamente.
            # Esto requerir铆a obtener informaci贸n de los s铆mbolos de Binance, lo cual puede ser una tarea futura o una mejora.
            # Por ahora, usaremos la cantidad y precios calculados directamente.

            oco_order_response = await self.binance_adapter.create_oco_order(
                api_key=api_key,
                api_secret=api_secret,
                symbol=symbol,
                side=exit_side,
                quantity=quantity_to_close,
                price=take_profit_price, # Precio para la orden Take Profit Limit
                stopPrice=current_stop_price_tsl, # Precio para la orden Stop Loss Limit
                stopLimitPrice=current_stop_price_tsl * (0.99) if exit_side == 'SELL' else current_stop_price_tsl * (1.01), # Precio l铆mite para la orden Stop Loss (ligeramente peor para asegurar ejecuci贸n)
                stopLimitTimeInForce='GTC' # Good Till Cancelled
            )
            logger.info(f"脫rdenes OCO (TSL/TP) enviadas a Binance para trade {opportunity_id}: {oco_order_response}")
            
            oco_list_client_order_id = oco_order_response.get('listClientOrderId')
            oco_orders_in_response = oco_order_response.get('orderReports', [])
            
            # Crear TradeOrderDetails para cada orden dentro del OCO
            for order_report in oco_orders_in_response:
                order_type = order_report.get('type')
                order_category = None
                if order_type == 'STOP_LOSS_LIMIT':
                    order_category = OrderCategory.STOP_LOSS
                elif order_type == 'TAKE_PROFIT_LIMIT':
                    order_category = OrderCategory.TAKE_PROFIT
                
                if order_category:
                    oco_exit_orders.append(TradeOrderDetails(
                        orderId_internal=uuid4(),
                        orderId_exchange=str(order_report.get('orderId')),
                        orderCategory=order_category,
                        type=order_type,
                        status=order_report.get('status'),
                        requestedQuantity=float(order_report.get('origQty')),
                        executedQuantity=float(order_report.get('executedQty')),
                        executedPrice=float(order_report.get('price')) if order_report.get('price') else 0.0, # Precio de la orden l铆mite
                        commission=float(order_report.get('commission')) if order_report.get('commission') else None,
                        commissionAsset=order_report.get('commissionAsset'), # Campo legado
                        timestamp=datetime.fromtimestamp(order_report.get('updateTime') / 1000, tz=timezone.utc), # Momento de la última actualización del estado de esta orden específica
                        # --- Campos adicionales requeridos ---
                        clientOrderId_exchange=str(order_report.get('clientOrderId', '')),
                        requestedPrice=float(order_report.get('price', 0.0)), # Este es el 'limitPrice' de la orden (TP o SL)
                        cumulativeQuoteQty=float(order_report.get('cummulativeQuoteQty', 0.0)),
                        commissions=[{
                            "amount": float(order_report.get('commission', 0.0)), # Comisión de esta orden específica
                            "asset": str(order_report.get('commissionAsset', '')) # Activo de la comisión
                        }],
                        submittedAt=datetime.fromtimestamp(order_report.get('time') / 1000, tz=timezone.utc) if order_report.get('time') else datetime.fromtimestamp(order_report.get('transactTime') / 1000, tz=timezone.utc) if order_report.get('transactTime') else datetime.fromtimestamp(order_report.get('updateTime') / 1000, tz=timezone.utc), # Preferir 'time' (tiempo de la transacción) o 'transactTime' si existen, sino 'updateTime'
                        fillTimestamp=datetime.fromtimestamp(order_report.get('updateTime') / 1000, tz=timezone.utc) if order_report.get('status') == 'FILLED' else None,
                        # --- Fin de campos adicionales ---
                        rawResponse=order_report,
                        ocoOrderListId=oco_list_client_order_id
                    ))
            
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"脫rdenes OCO (TSL/TP) enviadas para {symbol} ({exit_side}). TP: {take_profit_price:.4f}, TSL: {current_stop_price_tsl:.4f}", "INFO"
            )

        except Exception as e:
            logger.error(f"Fallo al enviar 贸rdenes OCO (TSL/TP) a Binance para oportunidad {opportunity_id}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar 贸rdenes OCO (TSL/TP) para {symbol}: {str(e)}", "ERROR"
            )
            # No se eleva la excepci贸n para no bloquear la ejecuci贸n del trade principal, pero se registra el error.
            oco_exit_orders = [] # Asegurarse de que la lista est茅 vac铆a si falla

        # 2.5: Registrar la orden enviada y su estado inicial en la base de datos (creando una nueva entidad Trade)
        new_trade = Trade(
            id=uuid4(),
            user_id=user_id,
            mode='real',
            symbol=symbol,
            side=side,
            entryOrder=trade_order_details,
            exitOrders=oco_exit_orders, # Las 贸rdenes OCO se a帽adir谩n al monitorear su estado
            positionStatus='open',
            opportunityId=opportunity_id,
            aiAnalysisConfidence=opportunity.ai_analysis.calculatedConfidence if opportunity.ai_analysis else None,
            pnl_usd=None,
            pnl_percentage=None,
            closingReason=None,
            ocoOrderListId=oco_list_client_order_id, # A帽adir el ID de la lista OCO al trade
            takeProfitPrice=take_profit_price, # Usar el precio calculado
            trailingStopActivationPrice=trailing_stop_activation_price, # Usar el precio calculado
            trailingStopCallbackRate=tsl_callback_rate_real,
            currentStopPrice_tsl=current_stop_price_tsl, # Usar el precio calculado
            riskRewardAdjustments=[], # A帽adir expl铆citamente la lista vac铆a
            created_at=datetime.now(timezone.utc),
            opened_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            closed_at=None
        )
        try:
            await self.persistence_service.upsert_trade(new_trade.user_id, new_trade.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info(f"Trade real {new_trade.id} persistido exitosamente.")
        except Exception as e:
            logger.error(f"Error al persistir el trade real {new_trade.id}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error cr铆tico: Orden real enviada pero fallo al registrar el trade {new_trade.id}: {str(e)}", "CRITICAL"
            )
            raise OrderExecutionError(f"Orden real enviada pero fallo al registrar el trade: {e}") from e

        # 2.6: Actualizar el status de la Opportunity a converted_to_trade_real y vincular el trade_id
        try:
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.CONVERTED_TO_TRADE_REAL, f"Convertida a trade real: {new_trade.id}"
            )
            logger.info(f"Oportunidad {opportunity_id} actualizada a 'converted_to_trade_real'.")
        except Exception as e:
            logger.error(f"Error al actualizar estado de oportunidad {opportunity_id} a 'converted_to_trade_real': {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Advertencia: Orden real enviada, pero fallo al actualizar estado de oportunidad {opportunity_id}: {str(e)}", "WARNING"
            )

        # Subtask 1.4: Integrar con ConfigService para obtener y actualizar la configuraci贸n del usuario relacionada con la gesti贸n de capital.
        # Subtask 1.3: Incrementar daily_capital_risked_usd
        try:
            real_trading_settings.real_trades_executed_count += 1
            real_trading_settings.daily_capital_risked_usd += capital_to_invest_per_trade
            await self.config_service.save_user_configuration(user_config)
            logger.info(f"Contador de trades reales incrementado y capital diario arriesgado actualizado para usuario {user_id}.")
            logger.info(f"Nuevo conteo: {real_trading_settings.real_trades_executed_count}, Capital arriesgado hoy: {real_trading_settings.daily_capital_risked_usd:.2f}")
        except Exception as e:
            logger.error(f"Error al actualizar contador de trades reales o capital diario arriesgado para usuario {user_id}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Advertencia: Orden real enviada, pero fallo al actualizar contador/capital arriesgado para {user_id}: {str(e)}", "WARNING"
            )
        
        return new_trade

    async def monitor_and_manage_paper_trade_exit(self, trade: Trade) -> None:
        """
        Monitorea y gestiona las 贸rdenes de salida (TSL/TP) para un trade en Paper Trading.
        Este m茅todo ser谩 llamado despu茅s de que un trade de paper trading se abra.
        """
        logger.info(f"Monitoreando TSL/TP para trade {trade.id} ({trade.symbol})")

        # Subtask 1.5: Obtener el precio de mercado actual
        try:
            current_price = await self.market_data_service.get_latest_price(trade.symbol)
            logger.debug(f"Precio actual de {trade.symbol}: {current_price}")
        except MarketDataError as e:
            logger.error(f"Error al obtener precio de mercado para {trade.symbol} en monitoreo: {e}", exc_info=True)
            return

        # Subtask 1.6: Implementar la l贸gica para ajustar el TSL si el precio se mueve favorablemente (AC3)
        if trade.positionStatus == 'open':
            if trade.trailingStopCallbackRate is None or trade.currentStopPrice_tsl is None:
                logger.warning(f"Trade {trade.id} no tiene TSL configurado correctamente. Saltando ajuste de TSL.")
                return

            if trade.side == 'BUY':
                if current_price > trade.entryOrder.executedPrice:
                    new_potential_stop = current_price * (1 - trade.trailingStopCallbackRate)
                    if new_potential_stop > trade.currentStopPrice_tsl:
                        trade.currentStopPrice_tsl = new_potential_stop
                        trade.updated_at = datetime.now(timezone.utc)
                        logger.info(f"TSL para {trade.symbol} (BUY) ajustado a {trade.currentStopPrice_tsl:.4f} (precio actual: {current_price:.4f})")
                        trade.riskRewardAdjustments.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "type": "TSL_ADJUSTMENT",
                            "new_stop_price": new_potential_stop,
                            "current_price": current_price
                        })
                        await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
                        logger.info(f"Trade {trade.id} con TSL actualizado persistido.")
            elif trade.side == 'SELL':
                if current_price < trade.entryOrder.executedPrice:
                    new_potential_stop = current_price * (1 + trade.trailingStopCallbackRate)
                    if new_potential_stop < trade.currentStopPrice_tsl:
                        trade.currentStopPrice_tsl = new_potential_stop
                        trade.updated_at = datetime.now(timezone.utc)
                        logger.info(f"TSL para {trade.symbol} (SELL) ajustado a {trade.currentStopPrice_tsl:.4f} (precio actual: {current_price:.4f})")
                        trade.riskRewardAdjustments.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "type": "TSL_ADJUSTMENT",
                            "new_stop_price": new_potential_stop,
                            "current_price": current_price
                        })
                        await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
                        logger.info(f"Trade {trade.id} con TSL actualizado persistido.")

            # Subtask 1.7: Implementar la l贸gica para detectar si el precio alcanza el TSL o TP (AC4)
            closing_reason = None
            if trade.side == 'BUY':
                if trade.takeProfitPrice is not None and current_price >= trade.takeProfitPrice:
                    closing_reason = 'TP_HIT'
                    logger.info(f"TP alcanzado para {trade.symbol} (BUY). Precio: {current_price:.4f}, TP: {trade.takeProfitPrice:.4f}")
                elif trade.currentStopPrice_tsl is not None and current_price <= trade.currentStopPrice_tsl:
                    closing_reason = 'SL_HIT'
                    logger.info(f"TSL alcanzado para {trade.symbol} (BUY). Precio: {current_price:.4f}, TSL: {trade.currentStopPrice_tsl:.4f}")
            elif trade.side == 'SELL':
                if trade.takeProfitPrice is not None and current_price <= trade.takeProfitPrice:
                    closing_reason = 'TP_HIT'
                    logger.info(f"TP alcanzado para {trade.symbol} (SELL). Precio: {current_price:.4f}, TP: {trade.takeProfitPrice:.4f}")
                elif trade.currentStopPrice_tsl is not None and current_price >= trade.currentStopPrice_tsl:
                    closing_reason = 'SL_HIT'
                    logger.info(f"TSL alcanzado para {trade.symbol} (SELL). Precio: {current_price:.4f}, TSL: {trade.currentStopPrice_tsl:.4f}")

            if closing_reason:
                # Subtask 1.8: Si se alcanza TSL/TP, simular el cierre de la posici贸n
                await self._close_paper_trade(trade, current_price, closing_reason)

    async def _close_paper_trade(self, trade: Trade, executed_price: float, closing_reason: str):
        """
        Simula el cierre de una posici贸n en Paper Trading.
        """
        logger.info(f"Cerrando trade {trade.id} por {closing_reason} a precio {executed_price:.4f}")

        # Subtask 1.8.1: Crear una instancia de TradeOrderDetails para la orden de salida simulada
        exit_order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            orderId_exchange=None, 
            clientOrderId_exchange=None, 
            orderCategory=OrderCategory.TRAILING_STOP_LOSS if closing_reason == 'SL_HIT' else OrderCategory.TAKE_PROFIT,
            type='trailing_stop_loss' if closing_reason == 'SL_HIT' else 'take_profit',
            status='filled',
            requestedPrice=executed_price, 
            requestedQuantity=trade.entryOrder.executedQuantity,
            executedQuantity=trade.entryOrder.executedQuantity,
            executedPrice=executed_price,
            cumulativeQuoteQty=trade.entryOrder.executedQuantity * executed_price, 
            commissions=[], 
            commission=None, 
            commissionAsset=None, 
            timestamp=datetime.now(timezone.utc),
            submittedAt=datetime.now(timezone.utc), 
            fillTimestamp=datetime.now(timezone.utc), 
            rawResponse=None,
            ocoOrderListId=None 
        )
        trade.exitOrders.append(exit_order_details)

        # Subtask 1.8.2: Actualizar el Trade con la orden de salida, P&L y estado
        trade.positionStatus = 'closed'
        trade.closingReason = closing_reason
        trade.closed_at = datetime.now(timezone.utc)

        # Calcular P&L
        entry_value = trade.entryOrder.executedQuantity * trade.entryOrder.executedPrice
        exit_value = exit_order_details.executedQuantity * exit_order_details.executedPrice

        if trade.side == 'BUY':
            trade.pnl_usd = exit_value - entry_value
        elif trade.side == 'SELL':
            trade.pnl_usd = entry_value - exit_value

        if entry_value > 0 and trade.pnl_usd is not None:
            trade.pnl_percentage = (trade.pnl_usd / entry_value) * 100
        else:
            trade.pnl_percentage = 0.0

        logger.info(f"Trade {trade.id} cerrado. P&L: {trade.pnl_usd:.2f} USD ({trade.pnl_percentage:.2f}%)")

        # Subtask 1.8.3: Persistir el Trade actualizado
        try:
            await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info(f"Trade {trade.id} cerrado y persistido exitosamente.")
        except Exception as e:
            logger.error(f"Error al persistir el trade cerrado {trade.id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo al persistir el trade cerrado: {e}") from e

        # Task 2: Actualizar el portafolio de Paper Trading tras el cierre de una posici贸n.
        try:
            await self.portfolio_service.update_paper_portfolio_after_exit(trade)
            logger.info(f"Portafolio de paper trading actualizado para trade {trade.id}.")
        except Exception as e:
            logger.error(f"Error al actualizar el portafolio de paper trading tras cierre de trade {trade.id}: {e}", exc_info=True)

        # Task 3: Enviar notificaciones al usuario sobre la ejecuci贸n de TSL/TP.
        try:
            await self.notification_service.send_paper_trade_exit_notification(trade)
            logger.info(f"Notificaci贸n de cierre de trade simulado enviada para trade {trade.id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificaci贸n de cierre para trade {trade.id}: {e}", exc_info=True)


    async def execute_trade(
        self,
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: float,
        credential_label: str = "default_binance_spot"
    ) -> TradeOrderDetails:
        """
        Ejecuta una operaci贸n de trading, decidiendo entre modo real o paper trading.
        """
        logger.info(f"Solicitud de ejecuci贸n de trade para usuario {user_id}: {side} {quantity} de {symbol}")
        
        try:
            user_config = await self.config_service.get_user_configuration(str(user_id))
            
            if user_config.paperTradingActive:
                logger.info(f"Modo Paper Trading ACTIVO para usuario {user_id}. Simulando orden.")
                order_details = await self.paper_order_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    ocoOrderListId=None # Asegurar que se pasa None
                )
            else:
                logger.info(f"Modo Real Trading ACTIVO para usuario {user_id}. Ejecutando orden real.")
                binance_credential = await self.credential_service.get_credential(
                    user_id=user_id,
                    service_name=ServiceName.BINANCE_SPOT,
                    credential_label=credential_label
                )
                
                if not binance_credential:
                    raise CredentialError(f"No se encontraron credenciales de Binance con la etiqueta '{credential_label}' para el usuario {user_id}.")
                
                api_key = self.credential_service.decrypt_data(binance_credential.encrypted_api_key)
                
                api_secret: Optional[str] = None
                if binance_credential.encrypted_api_secret:
                    api_secret = self.credential_service.decrypt_data(binance_credential.encrypted_api_secret)

                if not api_key or api_secret is None:
                    raise CredentialError(f"API Key o Secret de Binance no pudieron ser desencriptados para la credencial '{credential_label}'.")

                order_details = await self.order_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    api_key=api_key,
                    api_secret=api_secret,
                    ocoOrderListId=None # Asegurar que se pasa None para orden de mercado directa
                )
            
            logger.info(f"Trade ejecutado exitosamente en modo {'PAPER' if user_config.paperTradingActive else 'REAL'}: {order_details.orderId_internal}")
            return order_details

        except ConfigurationError as e:
            logger.error(f"Error de configuraci贸n para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo en el motor de trading debido a error de configuraci贸n: {e}") from e
        except CredentialError as e:
            logger.error(f"Error de credenciales para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo en el motor de trading debido a error de credenciales: {e}") from e
        except OrderExecutionError as e:
            logger.error(f"Error de ejecuci贸n de orden para usuario {user_id}: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error inesperado en el motor de trading para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado en el motor de trading: {e}") from e
