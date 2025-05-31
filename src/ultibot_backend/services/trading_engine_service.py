import logging
from uuid import UUID, uuid4 # Importar uuid4
from datetime import datetime # Importar datetime
from typing import Optional
import asyncio # Importar asyncio

from src.shared.data_types import TradeOrderDetails, ServiceName, Opportunity, Trade, PortfolioSnapshot, OpportunityStatus # Importar OpportunityStatus
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService, PaperOrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService # Importar MarketDataService
from src.ultibot_backend.services.portfolio_service import PortfolioService # Importar PortfolioService para Task 2
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Importar PersistenceService para Task 1.6
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService para Task 3
from src.ultibot_backend.core.exceptions import OrderExecutionError, ConfigurationError, CredentialError, MarketDataError, PortfolioError # Importar PortfolioError

logger = logging.getLogger(__name__)

class TradingEngineService:
    """
    Servicio central del motor de trading que decide si ejecutar órdenes
    en modo real o paper trading, basándose en la configuración del usuario.
    """
    def __init__(
        self,
        config_service: ConfigService,
        order_execution_service: OrderExecutionService,
        paper_order_execution_service: PaperOrderExecutionService,
        credential_service: CredentialService,
        market_data_service: MarketDataService, # Añadir MarketDataService
        portfolio_service: PortfolioService, # Añadir PortfolioService
        persistence_service: SupabasePersistenceService, # Añadir PersistenceService
        notification_service: NotificationService # Añadir NotificationService
    ):
        self.config_service = config_service
        self.order_execution_service = order_execution_service
        self.paper_order_execution_service = paper_order_execution_service
        self.credential_service = credential_service
        self.market_data_service = market_data_service # Asignar
        self.portfolio_service = portfolio_service # Asignar
        self.persistence_service = persistence_service # Asignar
        self.notification_service = notification_service # Asignar
        self._monitor_task: Optional[asyncio.Task] = None # Para controlar la tarea de monitoreo

    async def start_paper_trading_monitor(self):
        """
        Inicia el monitoreo continuo de trades abiertos en Paper Trading.
        """
        if self._monitor_task and not self._monitor_task.done():
            logger.info("El monitor de Paper Trading ya está en ejecución.")
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
        MONITOR_INTERVAL_SECONDS = 5 # Monitorear cada 5 segundos

        while True:
            try:
                logger.debug("Ejecutando ciclo de monitoreo de Paper Trading...")
                # Subtask 1.4: Obtener trades abiertos en Paper Trading
                open_paper_trades = await self.persistence_service.get_open_paper_trades()
                
                if not open_paper_trades:
                    logger.debug("No hay trades abiertos en Paper Trading para monitorear.")
                
                for trade in open_paper_trades:
                    # Subtask 1.5: Dentro del monitoreo, obtener el precio de mercado actual
                    # Subtask 1.6: Implementar la lógica para ajustar el TSL
                    # Subtask 1.7: Implementar la lógica para detectar si el precio alcanza el TSL o TP
                    # Subtask 1.8: Si se alcanza TSL/TP, simular el cierre de la posición
                    await self.monitor_and_manage_paper_trade_exit(trade)
                
            except Exception as e:
                logger.error(f"Error en el bucle de monitoreo de Paper Trading: {e}", exc_info=True)
            
            await asyncio.sleep(MONITOR_INTERVAL_SECONDS)

    async def simulate_paper_entry_order(self, opportunity: Opportunity) -> Trade:
        """
        Simula la ejecución de una orden de entrada en modo Paper Trading
        para una oportunidad de trading validada por la IA.
        """
        logger.info(f"Simulando orden de entrada para oportunidad {opportunity.id} ({opportunity.symbol})")
        user_id = opportunity.user_id
        symbol = opportunity.symbol
        side = opportunity.ai_analysis.suggestedAction if opportunity.ai_analysis else None

        if not symbol or not side:
            logger.error(f"Oportunidad {opportunity.id} no tiene símbolo o acción sugerida. No se puede simular.")
            raise OrderExecutionError(f"Oportunidad inválida para simulación: {opportunity.id}")

        # Subtask 1.2: Obtener el precio de mercado actual
        try:
            current_price = await self.market_data_service.get_latest_price(symbol)
            logger.info(f"Precio actual de {symbol}: {current_price}")
        except MarketDataError as e:
            logger.error(f"Error al obtener precio de mercado para {symbol}: {e}", exc_info=True)
            raise OrderExecutionError(f"No se pudo obtener el precio de mercado para {symbol}.") from e

        # Subtask 1.3: Calcular el tamaño de la posición (quantity)
        user_config = await self.config_service.get_user_configuration(user_id)
        
        # Obtener el capital disponible del portafolio de paper trading
        portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(user_id)
        available_capital = portfolio_snapshot.paper_trading.available_balance_usdt

        # Reglas de gestión de capital (FR3.1 - no más del 50% del capital diario, FR3.2 - ajuste dinámico al 25%)
        # Simplificación: Usaremos perTradeCapitalRiskPercentage sobre el capital disponible para esta simulación.
        # La lógica de "capital diario" es más compleja y podría requerir un seguimiento de trades diarios.
        per_trade_risk_percentage = user_config.riskProfileSettings.perTradeCapitalRiskPercentage if user_config.riskProfileSettings else None
        
        if not per_trade_risk_percentage:
            logger.warning(f"No se encontró 'perTradeCapitalRiskPercentage' para usuario {user_id}. Usando 0.01 (1%).")
            per_trade_risk_percentage = 0.01 # Valor por defecto si no está configurado

        capital_to_invest = available_capital * per_trade_risk_percentage
        
        if capital_to_invest <= 0:
            logger.warning(f"Capital a invertir es cero o negativo para {user_id}. No se puede simular la orden.")
            raise OrderExecutionError("Capital insuficiente para simular la orden.")

        # Calcular la cantidad (quantity)
        # Asumimos que el precio es en USDT y la cantidad es del activo base (ej. BTC en BTCUSDT)
        quantity = capital_to_invest / current_price
        
        # TODO: Considerar la precisión de los símbolos (pasos de cantidad y precio) de Binance para redondear correctamente.
        # Esto requeriría obtener información de los símbolos de Binance, lo cual puede ser una tarea futura o una mejora.
        # Por ahora, usaremos la cantidad calculada directamente.
        logger.info(f"Calculado: Capital disponible={available_capital}, % riesgo por trade={per_trade_risk_percentage}, Capital a invertir={capital_to_invest}, Cantidad={quantity}")

        # Subtask 1.4: Crear una instancia de TradeOrderDetails
        simulated_order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            type='market',
            status='filled',
            requestedQuantity=quantity,
            executedQuantity=quantity,
            executedPrice=current_price,
            timestamp=datetime.utcnow(),
            exchangeOrderId=None, # Añadir explícitamente None
            commission=None,      # Añadir explícitamente None
            commissionAsset=None, # Añadir explícitamente None
            rawResponse=None      # Añadir explícitamente None
        )
        logger.info(f"Orden simulada creada: {simulated_order_details.orderId_internal}")

        # Subtask 1.2: Calcular los niveles iniciales de TSL y TP (AC1)
        # Usaremos porcentajes fijos para la v1.0
        TP_PERCENTAGE = 0.02  # 2% de ganancia
        TSL_PERCENTAGE = 0.01  # 1% de pérdida inicial
        TSL_CALLBACK_RATE = 0.005 # 0.5% de retroceso para TSL

        take_profit_price = current_price * (1 + TP_PERCENTAGE) if side == 'BUY' else current_price * (1 - TP_PERCENTAGE)
        trailing_stop_activation_price = current_price * (1 - TSL_PERCENTAGE) if side == 'BUY' else current_price * (1 + TSL_PERCENTAGE)
        current_stop_price_tsl = trailing_stop_activation_price # Inicialmente, el stop es el precio de activación

        logger.info(f"Calculado para {symbol} ({side}): TP={take_profit_price:.4f}, TSL Act.={trailing_stop_activation_price:.4f}, TSL Callback={TSL_CALLBACK_RATE}, Current TSL={current_stop_price_tsl:.4f}")

        # Subtask 1.5: Crear una nueva instancia de Trade
        new_trade = Trade(
            id=uuid4(),
            user_id=user_id,
            mode='paper',
            symbol=symbol,
            side=side,
            entryOrder=simulated_order_details,
            exitOrders=[], # Asegurar que sea una lista vacía por defecto
            positionStatus='open',
            opportunityId=opportunity.id,
            aiAnalysisConfidence=opportunity.ai_analysis.calculatedConfidence if opportunity.ai_analysis else None,
            pnl_usd=None,
            pnl_percentage=None,
            closingReason=None,
            takeProfitPrice=take_profit_price,
            trailingStopActivationPrice=trailing_stop_activation_price,
            trailingStopCallbackRate=TSL_CALLBACK_RATE,
            currentStopPrice_tsl=current_stop_price_tsl,
            riskRewardAdjustments=[], # Asegurar que sea una lista vacía por defecto
            created_at=datetime.utcnow(),
            opened_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
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
        # Esto se hará en PortfolioService, pero lo llamamos desde aquí.
        try:
            await self.portfolio_service.update_paper_portfolio_after_entry(new_trade)
            logger.info(f"Portafolio de paper trading actualizado para trade {new_trade.id}.")
        except Exception as e:
            logger.error(f"Error al actualizar el portafolio de paper trading para trade {new_trade.id}: {e}", exc_info=True)
            # No relanzamos el error aquí para no bloquear la creación del trade, pero lo logueamos.
            # Podríamos considerar un mecanismo de reintento o compensación.

        # Task 3: Enviar notificaciones al usuario (Subtasks 3.1 - 3.2)
        try:
            await self.notification_service.send_paper_trade_entry_notification(new_trade)
            logger.info(f"Notificación de trade simulado enviada para trade {new_trade.id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificación para trade {new_trade.id}: {e}", exc_info=True)
            # Similar al portafolio, no bloqueamos la operación principal por un fallo en la notificación.

        return new_trade

    async def process_opportunity_for_real_trading(self, opportunity: Opportunity):
        """
        Procesa una oportunidad de trading analizada por la IA para determinar
        si es una candidata de muy alta confianza para operativa real.
        """
        logger.info(f"Procesando oportunidad {opportunity.id} para posible operativa real.")

        user_id = opportunity.user_id
        user_config = await self.config_service.get_user_configuration(user_id)

        # Acceder a realTradingSettings de forma segura
        real_trading_settings = user_config.realTradingSettings
        if not real_trading_settings or not real_trading_settings.real_trading_mode_active:
            logger.info(f"Modo de operativa real no activo para usuario {user_id}. Oportunidad {opportunity.id} no considerada para real trading.")
            return

        if not opportunity.ai_analysis or opportunity.ai_analysis.calculatedConfidence is None:
            logger.warning(f"Oportunidad {opportunity.id} no tiene análisis de IA o confianza calculada. No se puede procesar para real trading.")
            return

        # Subtask 1.1: Filtrar oportunidades basándose en aiAnalysis.calculatedConfidence > 0.95
        confidence_threshold = 0.95 # Valor por defecto
        if user_config.aiAnalysisConfidenceThresholds and user_config.aiAnalysisConfidenceThresholds.realTrading is not None:
            confidence_threshold = user_config.aiAnalysisConfidenceThresholds.realTrading
        
        if opportunity.ai_analysis.calculatedConfidence <= confidence_threshold:
            logger.info(f"Confianza de IA ({opportunity.ai_analysis.calculatedConfidence:.2f}) para oportunidad {opportunity.id} no supera el umbral de {confidence_threshold:.2f}. No es candidata para operativa real.")
            return

        # Subtask 1.3: Verificar el real_trades_executed_count
        real_trades_executed_count = real_trading_settings.real_trades_executed_count if real_trading_settings.real_trades_executed_count is not None else 0
        max_real_trades = real_trading_settings.max_real_trades if real_trading_settings.max_real_trades is not None else 5 # Límite por defecto de 5

        if real_trades_executed_count >= max_real_trades:
            logger.warning(f"Límite de operaciones reales ({max_real_trades}) alcanzado para usuario {user_id}. Oportunidad {opportunity.id} no presentada para operativa real.")
            # TODO: Considerar enviar una notificación al usuario si el límite se ha alcanzado y se detecta una oportunidad de alta confianza.
            return

        # Subtask 1.4: Actualizar el status de la Opportunity a PENDING_USER_CONFIRMATION_REAL
        opportunity.status = OpportunityStatus.PENDING_USER_CONFIRMATION_REAL # Usar el miembro del Enum
        opportunity.updated_at = datetime.utcnow()
        try:
            await self.persistence_service.upsert_opportunity(opportunity.user_id, opportunity.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info(f"Oportunidad {opportunity.id} actualizada a 'pending_user_confirmation_real' y persistida.")
        except Exception as e:
            logger.error(f"Error al persistir la oportunidad {opportunity.id} con estado 'pending_user_confirmation_real': {e}", exc_info=True)
            # Si falla la persistencia, no podemos continuar con la notificación/presentación.
            return

        # Subtask 4.2: Disparar notificación prioritaria
        try:
            await self.notification_service.send_high_confidence_opportunity_notification(opportunity)
            logger.info(f"Notificación de oportunidad de alta confianza enviada para {opportunity.id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificación de alta confianza para oportunidad {opportunity.id}: {e}", exc_info=True)
            # No bloqueamos el flujo principal si la notificación falla.

        logger.info(f"Oportunidad {opportunity.id} es una candidata de muy alta confianza para operativa real y ha sido marcada para confirmación del usuario.")

    async def execute_real_trade(self, opportunity_id: UUID, user_id: UUID) -> Trade:
        """
        Ejecuta una orden real en Binance basada en una oportunidad confirmada por el usuario.
        """
        logger.info(f"Iniciando ejecución de orden REAL para oportunidad {opportunity_id} y usuario {user_id}.")

        # 2.2: Recuperar la Opportunity completa de la base de datos
        opportunity = await self.persistence_service.get_opportunity_by_id(opportunity_id)
        if not opportunity:
            logger.error(f"Oportunidad {opportunity_id} no encontrada para ejecución real.")
            raise OrderExecutionError(f"Oportunidad {opportunity_id} no encontrada.")

        if opportunity.status != OpportunityStatus.PENDING_USER_CONFIRMATION_REAL:
            logger.error(f"Oportunidad {opportunity_id} no está en estado PENDING_USER_CONFIRMATION_REAL. Estado actual: {opportunity.status.value}")
            raise OrderExecutionError(f"Oportunidad {opportunity_id} no está lista para ejecución real.")

        if not opportunity.symbol or not opportunity.ai_analysis or not opportunity.ai_analysis.suggestedAction:
            logger.error(f"Oportunidad {opportunity_id} carece de símbolo o acción sugerida por IA.")
            raise OrderExecutionError(f"Oportunidad {opportunity_id} incompleta para ejecución real.")

        symbol = opportunity.symbol
        side = opportunity.ai_analysis.suggestedAction
        
        # 2.3: Calcular la cantidad a operar (requestedQuantity)
        user_config = await self.config_service.get_user_configuration(user_id)
        if not user_config or not user_config.realTradingSettings or not user_config.riskProfileSettings:
            logger.error(f"Configuración de usuario o de trading real/riesgo no encontrada para {user_id}.")
            raise ConfigurationError("Configuración de usuario incompleta para operativa real.")

        real_trading_settings = user_config.realTradingSettings
        risk_profile_settings = user_config.riskProfileSettings

        # Verificar cupos disponibles de nuevo (doble chequeo)
        if real_trading_settings.real_trades_executed_count >= real_trading_settings.max_real_trades:
            logger.error(f"Límite de operaciones reales ({real_trading_settings.max_real_trades}) alcanzado para usuario {user_id}.")
            raise OrderExecutionError("Límite de operaciones reales alcanzado.")

        # Obtener el saldo real disponible
        try:
            portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(user_id)
            available_capital = portfolio_snapshot.real_trading.available_balance_usdt
            logger.info(f"Saldo real disponible para {user_id}: {available_capital} USDT.")
        except PortfolioError as e:
            logger.error(f"Error al obtener el saldo real para {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"No se pudo obtener el saldo real: {e}") from e

        per_trade_capital_risk_percentage = risk_profile_settings.perTradeCapitalRiskPercentage
        if per_trade_capital_risk_percentage is None:
            logger.warning(f"perTradeCapitalRiskPercentage no configurado para {user_id}. Usando 0.01 (1%).")
            per_trade_capital_risk_percentage = 0.01

        capital_to_invest = available_capital * per_trade_capital_risk_percentage
        if capital_to_invest <= 0:
            logger.error(f"Capital a invertir es cero o negativo para {user_id}. Capital disponible: {available_capital}.")
            raise OrderExecutionError("Capital insuficiente para la operación real.")

        # Obtener el precio de mercado actual para calcular la cantidad
        try:
            current_price = await self.market_data_service.get_latest_price(symbol)
            logger.info(f"Precio actual de {symbol}: {current_price}")
        except MarketDataError as e:
            logger.error(f"Error al obtener precio de mercado para {symbol}: {e}", exc_info=True)
            raise OrderExecutionError(f"No se pudo obtener el precio de mercado para {symbol}.") from e

        requested_quantity = capital_to_invest / current_price
        logger.info(f"Calculado para orden real: Capital a invertir={capital_to_invest:.2f}, Cantidad={requested_quantity:.8f}")

        # 2.4: Utilizar el BinanceAdapter para enviar la orden real a Binance
        # Obtener credenciales de Binance
        binance_credential = await self.credential_service.get_credential(
            user_id=user_id,
            service_name=ServiceName.BINANCE_SPOT, # Asumimos SPOT por ahora
            credential_label="default_binance_spot" # Asumimos etiqueta por defecto
        )
        
        if not binance_credential:
            logger.error(f"No se encontraron credenciales de Binance para el usuario {user_id}.")
            raise CredentialError(f"No se encontraron credenciales de Binance para el usuario {user_id}.")
        
        api_key = self.credential_service.decrypt_data(binance_credential.encrypted_api_key)
        api_secret: Optional[str] = None
        if binance_credential.encrypted_api_secret:
            api_secret = self.credential_service.decrypt_data(binance_credential.encrypted_api_secret)

        if not api_key or api_secret is None:
            logger.error(f"API Key o Secret de Binance no pudieron ser desencriptados para {user_id}.")
            raise CredentialError("API Key o Secret de Binance no válidos.")

        trade_order_details: Optional[TradeOrderDetails] = None
        try:
            trade_order_details = await self.order_execution_service.execute_market_order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=requested_quantity,
                api_key=api_key,
                api_secret=api_secret
            )
            logger.info(f"Orden real enviada a Binance: {trade_order_details.orderId_internal}")
            # 2.9: Disparar notificación de orden enviada
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Orden real enviada para {symbol} ({side}). Estado: {trade_order_details.status}", "INFO"
            )
        except OrderExecutionError as e:
            logger.error(f"Fallo al enviar orden real a Binance para oportunidad {opportunity_id}: {e}", exc_info=True)
            # 2.8: Manejar errores de Binance y actualizar estado de la oportunidad
            await self.persistence_service.update_opportunity_status(
                opportunity_id, OpportunityStatus.EXECUTION_FAILED, f"Fallo al enviar orden real: {str(e)}"
            )
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error al enviar orden real para {symbol} ({side}): {str(e)}", "ERROR"
            )
            raise # Re-lanzar para que el endpoint pueda manejarlo

        # 2.5: Registrar la orden enviada y su estado inicial en la base de datos (creando una nueva entidad Trade)
        new_trade = Trade(
            id=uuid4(),
            user_id=user_id,
            mode='real',
            symbol=symbol,
            side=side,
            entryOrder=trade_order_details,
            exitOrders=[],
            positionStatus='open', # Asumimos que la orden de entrada abre la posición
            opportunityId=opportunity_id,
            aiAnalysisConfidence=opportunity.ai_analysis.calculatedConfidence if opportunity.ai_analysis else None,
            pnl_usd=None,
            pnl_percentage=None,
            closingReason=None,
            takeProfitPrice=None, # Estos se establecerán en el monitoreo de trades reales
            trailingStopActivationPrice=None,
            trailingStopCallbackRate=None,
            currentStopPrice_tsl=None,
            created_at=datetime.utcnow(),
            opened_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            closed_at=None
        )
        try:
            await self.persistence_service.upsert_trade(new_trade.user_id, new_trade.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info(f"Trade real {new_trade.id} persistido exitosamente.")
        except Exception as e:
            logger.error(f"Error al persistir el trade real {new_trade.id}: {e}", exc_info=True)
            # Si falla la persistencia del trade, es un problema crítico.
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Error crítico: Orden real enviada pero fallo al registrar el trade {new_trade.id}: {str(e)}", "CRITICAL"
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
            # Esto es un problema de consistencia de datos, pero la orden ya se envió.
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Advertencia: Orden real enviada, pero fallo al actualizar estado de oportunidad {opportunity_id}: {str(e)}", "WARNING"
            )

        # 2.7: Decrementar el real_trades_executed_count en UserConfiguration.realTradingSettings
        try:
            user_config.realTradingSettings.real_trades_executed_count += 1
            await self.config_service.save_user_configuration(user_config)
            logger.info(f"Contador de trades reales decrementado para usuario {user_id}. Nuevo conteo: {user_config.realTradingSettings.real_trades_executed_count}")
        except Exception as e:
            logger.error(f"Error al decrementar el contador de trades reales para usuario {user_id}: {e}", exc_info=True)
            await self.notification_service.send_real_trade_status_notification(
                user_id, f"Advertencia: Orden real enviada, pero fallo al actualizar contador de trades reales para {user_id}: {str(e)}", "WARNING"
            )
        
        # 2.8: Manejar las respuestas de Binance (éxito, error, rechazo) y actualizar el estado de la TradeOrderDetails y la Trade en consecuencia.
        # Esto se haría en un proceso de monitoreo de órdenes o a través de webhooks de Binance.
        # Por ahora, asumimos que trade_order_details ya refleja el estado inicial de la orden.
        # Las actualizaciones posteriores (ej. 'filled', 'partial_fill') se manejarían en un servicio de monitoreo de órdenes.
        # La lógica de TSL/TP para trades reales también iría en un monitor similar al de paper trading.

        # 2.9: Disparar notificaciones (a través de NotificationService) sobre el estado de la orden.
        # Ya se envió una notificación inicial. Notificaciones posteriores se harían en el monitor.

        return new_trade

    async def monitor_and_manage_paper_trade_exit(self, trade: Trade):
        """
        Monitorea y gestiona las órdenes de salida (TSL/TP) para un trade en Paper Trading.
        Este método será llamado después de que un trade de paper trading se abra.
        """
        logger.info(f"Monitoreando TSL/TP para trade {trade.id} ({trade.symbol})")

        # Subtask 1.5: Obtener el precio de mercado actual
        try:
            current_price = await self.market_data_service.get_latest_price(trade.symbol)
            logger.debug(f"Precio actual de {trade.symbol}: {current_price}")
        except MarketDataError as e:
            logger.error(f"Error al obtener precio de mercado para {trade.symbol} en monitoreo: {e}", exc_info=True)
            return # No podemos procesar este trade sin precio actual

        # Subtask 1.6: Implementar la lógica para ajustar el TSL si el precio se mueve favorablemente (AC3)
        # Solo ajustamos TSL si la posición está abierta
        if trade.positionStatus == 'open':
            if trade.trailingStopCallbackRate is None or trade.currentStopPrice_tsl is None:
                logger.warning(f"Trade {trade.id} no tiene TSL configurado correctamente. Saltando ajuste de TSL.")
                return

            if trade.side == 'BUY':
                # Para BUY, TSL sube si el precio sube
                if current_price > trade.entryOrder.executedPrice: # Solo si el precio actual es mayor que el de entrada
                    # Calcular el nuevo stop potencial basado en el precio actual y el callback rate
                    new_potential_stop = current_price * (1 - trade.trailingStopCallbackRate)
                    # Si el nuevo stop potencial es mayor que el stop actual, actualizamos
                    if new_potential_stop > trade.currentStopPrice_tsl:
                        trade.currentStopPrice_tsl = new_potential_stop
                        trade.updated_at = datetime.utcnow()
                        logger.info(f"TSL para {trade.symbol} (BUY) ajustado a {trade.currentStopPrice_tsl:.4f} (precio actual: {current_price:.4f})")
                        # Opcional: registrar ajuste en riskRewardAdjustments
                        trade.riskRewardAdjustments.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "type": "TSL_ADJUSTMENT",
                            "new_stop_price": new_potential_stop,
                            "current_price": current_price
                        })
                        await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
                        logger.info(f"Trade {trade.id} con TSL actualizado persistido.")
            elif trade.side == 'SELL':
                # Para SELL, TSL baja si el precio baja
                if current_price < trade.entryOrder.executedPrice: # Solo si el precio actual es menor que el de entrada
                    # Calcular el nuevo stop potencial basado en el precio actual y el callback rate
                    new_potential_stop = current_price * (1 + trade.trailingStopCallbackRate)
                    # Si el nuevo stop potencial es menor que el stop actual, actualizamos
                    if new_potential_stop < trade.currentStopPrice_tsl:
                        trade.currentStopPrice_tsl = new_potential_stop
                        trade.updated_at = datetime.utcnow()
                        logger.info(f"TSL para {trade.symbol} (SELL) ajustado a {trade.currentStopPrice_tsl:.4f} (precio actual: {current_price:.4f})")
                        # Opcional: registrar ajuste en riskRewardAdjustments
                        trade.riskRewardAdjustments.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "type": "TSL_ADJUSTMENT",
                            "new_stop_price": new_potential_stop,
                            "current_price": current_price
                        })
                        await self.persistence_service.upsert_trade(trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True))
                        logger.info(f"Trade {trade.id} con TSL actualizado persistido.")

            # Subtask 1.7: Implementar la lógica para detectar si el precio alcanza el TSL o TP (AC4)
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
                # Subtask 1.8: Si se alcanza TSL/TP, simular el cierre de la posición
                await self._close_paper_trade(trade, current_price, closing_reason)

    async def _close_paper_trade(self, trade: Trade, executed_price: float, closing_reason: str):
        """
        Simula el cierre de una posición en Paper Trading.
        """
        logger.info(f"Cerrando trade {trade.id} por {closing_reason} a precio {executed_price:.4f}")

        # Subtask 1.8.1: Crear una instancia de TradeOrderDetails para la orden de salida simulada
        exit_order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            type='trailing_stop_loss' if closing_reason == 'SL_HIT' else 'take_profit',
            status='filled',
            requestedQuantity=trade.entryOrder.executedQuantity, # Cantidad total de la posición
            executedQuantity=trade.entryOrder.executedQuantity,
            executedPrice=executed_price,
            timestamp=datetime.utcnow(),
            exchangeOrderId=None, # Añadir explícitamente None
            commission=None,      # Añadir explícitamente None
            commissionAsset=None, # Añadir explícitamente None
            rawResponse=None      # Añadir explícitamente None
        )
        trade.exitOrders.append(exit_order_details) # Añadir a la lista de órdenes de salida

        # Subtask 1.8.2: Actualizar el Trade con la orden de salida, P&L y estado
        trade.positionStatus = 'closed'
        trade.closingReason = closing_reason
        trade.closed_at = datetime.utcnow()

        # Calcular P&L
        entry_value = trade.entryOrder.executedQuantity * trade.entryOrder.executedPrice
        exit_value = exit_order_details.executedQuantity * exit_order_details.executedPrice

        if trade.side == 'BUY':
            trade.pnl_usd = exit_value - entry_value
        elif trade.side == 'SELL':
            trade.pnl_usd = entry_value - exit_value # Para ventas, si el precio baja, se gana

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
            # Considerar un mecanismo de reintento o alerta si la persistencia falla aquí.
            raise OrderExecutionError(f"Fallo al persistir el trade cerrado: {e}") from e

        # Task 2: Actualizar el portafolio de Paper Trading tras el cierre de una posición.
        try:
            await self.portfolio_service.update_paper_portfolio_after_exit(trade)
            logger.info(f"Portafolio de paper trading actualizado para trade {trade.id}.")
        except Exception as e:
            logger.error(f"Error al actualizar el portafolio de paper trading tras cierre de trade {trade.id}: {e}", exc_info=True)
            # No relanzamos el error aquí para no bloquear la operación principal, pero lo logueamos.

        # Task 3: Enviar notificaciones al usuario sobre la ejecución de TSL/TP.
        try:
            await self.notification_service.send_paper_trade_exit_notification(trade)
            logger.info(f"Notificación de cierre de trade simulado enviada para trade {trade.id}.")
        except Exception as e:
            logger.error(f"Error al enviar notificación de cierre para trade {trade.id}: {e}", exc_info=True)
            # Similar al portafolio, no bloqueamos la operación principal por un fallo en la notificación.

    async def execute_trade(
        self,
        user_id: UUID,
        symbol: str,
        side: str, # 'BUY' o 'SELL'
        quantity: float,
        credential_label: str = "default_binance_spot" # Etiqueta de la credencial de Binance a usar
    ) -> TradeOrderDetails:
        """
        Ejecuta una operación de trading, decidiendo entre modo real o paper trading.
        """
        logger.info(f"Solicitud de ejecución de trade para usuario {user_id}: {side} {quantity} de {symbol}")
        
        try:
            user_config = await self.config_service.get_user_configuration(user_id)
            
            if user_config.paperTradingActive:
                logger.info(f"Modo Paper Trading ACTIVO para usuario {user_id}. Simulando orden.")
                order_details = await self.paper_order_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity
                )
            else:
                logger.info(f"Modo Real Trading ACTIVO para usuario {user_id}. Ejecutando orden real.")
                # Obtener credenciales de Binance
                binance_credential = await self.credential_service.get_credential(
                    user_id=user_id,
                    service_name=ServiceName.BINANCE_SPOT, # Asumimos SPOT por ahora
                    credential_label=credential_label
                )
                
                if not binance_credential:
                    raise CredentialError(f"No se encontraron credenciales de Binance con la etiqueta '{credential_label}' para el usuario {user_id}.")
                
                # Desencriptar credenciales para pasarlas al servicio de ejecución real
                api_key = self.credential_service.decrypt_data(binance_credential.encrypted_api_key)
                
                api_secret: Optional[str] = None
                if binance_credential.encrypted_api_secret:
                    api_secret = self.credential_service.decrypt_data(binance_credential.encrypted_api_secret)

                if not api_key or api_secret is None: # api_secret puede ser una cadena vacía si no hay secret
                    raise CredentialError(f"API Key o Secret de Binance no pudieron ser desencriptados para la credencial '{credential_label}'.")

                order_details = await self.order_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    api_key=api_key,
                    api_secret=api_secret
                )
            
            logger.info(f"Trade ejecutado exitosamente en modo {'PAPER' if user_config.paperTradingActive else 'REAL'}: {order_details.orderId_internal}")
            return order_details

        except ConfigurationError as e:
            logger.error(f"Error de configuración para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo en el motor de trading debido a error de configuración: {e}") from e
        except CredentialError as e:
            logger.error(f"Error de credenciales para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo en el motor de trading debido a error de credenciales: {e}") from e
        except OrderExecutionError as e:
            logger.error(f"Error de ejecución de orden para usuario {user_id}: {e}", exc_info=True)
            raise # Re-lanzar el error de ejecución de orden
        except Exception as e:
            logger.error(f"Error inesperado en el motor de trading para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado en el motor de trading: {e}") from e
