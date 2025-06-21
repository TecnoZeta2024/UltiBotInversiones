"""Trading Engine Service for executing trading strategies with AI integration.

This service orchestrates the trading decision process, integrating AI analysis
results with strategy logic to make informed trading decisions.
"""

import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from decimal import Decimal # Importar Decimal

from fastapi import HTTPException

# Use domain models exclusively for internal logic
from ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
)
from ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
    UserConfiguration, # Importar UserConfiguration
    RealTradingSettings # Importar RealTradingSettings
)
from ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    AIAnalysis,
    SuggestedAction,
    RecommendedTradeParams,
    DataVerification,
    InitialSignal,
    SourceType,
)
from ultibot_backend.services.ai_orchestrator_service import (
    AIOrchestrator,
    AIAnalysisResult,
    OpportunityData,
)
from ultibot_backend.core.domain_models.trade_models import (
    Trade,
    AIInfluenceDetails,
    PositionStatus,
    OrderType,
    TradeOrderDetails,
    OrderStatus,
    TradeMode,
    TradeSide,
    OrderCategory,
)
from ultibot_backend.services.market_data_service import MarketDataService
from ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService
from ultibot_backend.services.credential_service import CredentialService
from ultibot_backend.core.exceptions import (
    MarketDataError,
    BinanceAPIError,
    OrderExecutionError,
    ConfigurationError,
)
from shared.data_types import ServiceName, PortfolioSnapshot

# Conditional imports for type checking to avoid circular dependencies
if TYPE_CHECKING:
    from ultibot_backend.services.strategy_service import StrategyService
    from ultibot_backend.services.config_service import ConfigurationService
    from ultibot_backend.services.notification_service import NotificationService
    from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
    from ultibot_backend.services.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)


class TradingDecision:
    """Result of trading decision analysis."""
    
    def __init__(
        self,
        decision: str,
        confidence: float,
        reasoning: str,
        opportunity_id: str,
        strategy_id: str,
        mode: str = "paper",
        ai_analysis_used: bool = False,
        ai_analysis_profile_id: Optional[str] = None,
        recommended_trade_params: Optional[Dict[str, Any]] = None,
        risk_assessment: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.decision = decision
        self.confidence = confidence
        self.reasoning = reasoning
        self.opportunity_id = opportunity_id
        self.strategy_id = strategy_id
        self.mode = mode
        self.ai_analysis_used = ai_analysis_used
        self.ai_analysis_profile_id = ai_analysis_profile_id
        self.recommended_trade_params = recommended_trade_params
        self.risk_assessment = risk_assessment
        self.warnings = warnings or []
        self.timestamp = datetime.now(timezone.utc)
        self.decision_id = str(uuid4())


class TradingEngine:
    """Service for executing trading strategies with AI integration."""
    
    def __init__(
        self,
        persistence_service: "SupabasePersistenceService",
        market_data_service: MarketDataService,
        unified_order_execution_service: UnifiedOrderExecutionService,
        credential_service: CredentialService,
        notification_service: "NotificationService",
        strategy_service: "StrategyService",
        configuration_service: "ConfigurationService",
        portfolio_service: "PortfolioService",
        ai_orchestrator: Optional[AIOrchestrator] = None,
    ):
        self.persistence_service = persistence_service
        self.market_data_service = market_data_service
        self.unified_order_execution_service = unified_order_execution_service
        self.credential_service = credential_service
        self.notification_service = notification_service
        self.strategy_service = strategy_service
        self.configuration_service = configuration_service
        self.portfolio_service = portfolio_service
        self.ai_orchestrator = ai_orchestrator or AIOrchestrator(market_data_service=market_data_service)

    async def execute_trade_from_confirmed_opportunity(self, opportunity: Opportunity) -> Optional[Trade]:
        logger.info(f"Executing trade directly from confirmed opportunity {opportunity.id}")

        user_config = await self.configuration_service.get_user_configuration(str(opportunity.user_id))
        if not user_config:
            raise OrderExecutionError(f"User configuration not found for user {opportunity.user_id}")

        # Lógica de reinicio de capital diario
        current_utc_date = datetime.now(timezone.utc).date()
        if user_config.real_trading_settings and user_config.real_trading_settings.last_daily_reset:
            last_reset_date = user_config.real_trading_settings.last_daily_reset.date()
            if last_reset_date < current_utc_date:
                logger.info(f"Daily capital reset triggered for user {opportunity.user_id}. Resetting daily_capital_risked_usd.")
                user_config.real_trading_settings.daily_capital_risked_usd = Decimal("0.0") # Asegurar tipo Decimal
                user_config.real_trading_settings.last_daily_reset = datetime.now(timezone.utc)
                await self.configuration_service.save_user_configuration(user_config)
                logger.info(f"User configuration saved after daily capital reset for user {opportunity.user_id}.")
        elif user_config.real_trading_settings and user_config.real_trading_settings.last_daily_reset is None:
            # Si es la primera vez que se usa, inicializar last_daily_reset
            user_config.real_trading_settings.last_daily_reset = datetime.now(timezone.utc)
            await self.configuration_service.save_user_configuration(user_config)
            logger.info(f"User configuration saved after initializing last_daily_reset for user {opportunity.user_id}.")
        elif user_config.real_trading_settings is None: # Asegurar que real_trading_settings no sea None
            user_config.real_trading_settings = RealTradingSettings(
                real_trading_mode_active=True, # Asumir activo si se llega aquí
                real_trades_executed_count=0,
                max_concurrent_operations=5,
                daily_loss_limit_absolute=None, # Valor por defecto
                daily_profit_target_absolute=None, # Valor por defecto
                asset_specific_stop_loss=None, # Valor por defecto
                auto_pause_trading_conditions=None, # Valor por defecto
                daily_capital_risked_usd=Decimal("0.0"),
                last_daily_reset=datetime.now(timezone.utc)
            )
            await self.configuration_service.save_user_configuration(user_config)
            logger.info(f"User configuration saved after initializing real_trading_settings for user {opportunity.user_id}.")

        # --- Lógica de Validación de Capital ---
        if not user_config.risk_profile_settings or not user_config.risk_profile_settings.daily_capital_risk_percentage or not user_config.risk_profile_settings.per_trade_capital_risk_percentage:
            raise ConfigurationError("Risk profile settings are not fully configured.")

        portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(UUID(opportunity.user_id))
        if not portfolio_snapshot:
            raise OrderExecutionError(f"Portfolio snapshot not found for user {opportunity.user_id}")

        portfolio_value_for_risk_calc = Decimal(str(portfolio_snapshot.real_trading.total_portfolio_value_usd))

        # Calculate potential risk for this trade
        per_trade_risk_percentage = Decimal(str(user_config.risk_profile_settings.per_trade_capital_risk_percentage))
        potential_risk_usd = portfolio_value_for_risk_calc * per_trade_risk_percentage

        # Check against daily limit
        daily_risk_limit_percentage = Decimal(str(user_config.risk_profile_settings.daily_capital_risk_percentage))
        daily_risk_limit_usd = portfolio_value_for_risk_calc * daily_risk_limit_percentage

        current_daily_risked = user_config.real_trading_settings.daily_capital_risked_usd or Decimal("0.0")

        if (current_daily_risked + potential_risk_usd) > daily_risk_limit_usd:
            error_msg = f"Límite de riesgo de capital diario excedido. Límite: {daily_risk_limit_usd}, Arriesgado: {current_daily_risked}, Nuevo Trade: {potential_risk_usd}"
            logger.error(error_msg)
            await self._update_opportunity_status(opportunity, OpportunityStatus.ERROR_IN_PROCESSING, "daily_capital_limit_exceeded", error_msg)
            raise OrderExecutionError(error_msg)
        # --- Fin de la Lógica de Validación de Capital ---
        
        current_price_raw = await self.market_data_service.get_latest_price(opportunity.symbol)
        if not current_price_raw:
            raise MarketDataError(f"Could not retrieve current price for {opportunity.symbol}")
        current_price = Decimal(str(current_price_raw))

        strategies = await self.strategy_service.get_active_strategies(str(opportunity.user_id), "real")
        if not strategies:
            raise OrderExecutionError(f"No active real strategies found for user {opportunity.user_id} to execute confirmed opportunity {opportunity.id}")
        
        strategy = strategies[0]
        logger.warning(f"Using strategy '{strategy.config_name}' as context for confirmed opportunity {opportunity.id}")

        recommended_params = opportunity.initial_signal.model_dump() if opportunity.initial_signal else {}

        decision = TradingDecision(
            decision="execute_trade",
            confidence=opportunity.ai_analysis.calculated_confidence if opportunity.ai_analysis else 1.0,
            reasoning="Trade executed based on direct user confirmation." + (f" AI analysis: {opportunity.ai_analysis.reasoning_ai}" if opportunity.ai_analysis else ""),
            opportunity_id=str(opportunity.id),
            strategy_id=str(strategy.id),
            mode="real",
            ai_analysis_used=True if opportunity.ai_analysis else False,
            ai_analysis_profile_id=None, # AIAnalysis does not have profile_id directly
            recommended_trade_params=recommended_params,
        )

        trade = await self.create_trade_from_decision(
            decision,
            opportunity,
            strategy,
            user_config,
            current_price,
            portfolio_snapshot,
        )

        if not trade:
            logger.error(
                f"Failed to create trade from confirmed opportunity {opportunity.id}"
            )
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.ERROR_IN_PROCESSING,
                "trade_creation_failed",
                "Failed to create trade object after user confirmation."
            )
            return None

        try:
            # Get credentials for execution
            credential = await self.credential_service.get_credential(
                service_name=ServiceName.BINANCE_SPOT,
                credential_label="default_binance_spot"
            )
            if not credential:
                raise ConfigurationError("No active credentials found for trade execution.")

            api_key = self.credential_service.decrypt_data(credential.encrypted_api_key)
            api_secret = self.credential_service.decrypt_data(credential.encrypted_api_secret) if credential.encrypted_api_secret else None

            # Execute the trade
            executed_order = await self.unified_order_execution_service.execute_market_order(
                user_id=trade.user_id,
                symbol=trade.symbol,
                side=trade.side.upper(),
                quantity=trade.entryOrder.requestedQuantity, # Mantener como Decimal
                trading_mode="real",
                api_key=api_key,
                api_secret=api_secret
            )
            # Asegurar que executed_order sea un objeto TradeOrderDetails
            if isinstance(executed_order, TradeOrderDetails):
                trade.entryOrder = executed_order
            else:
                trade.entryOrder = TradeOrderDetails(**executed_order)
            trade.positionStatus = PositionStatus.OPEN.value
            logger.info(f"Successfully executed trade {trade.id} from confirmed opportunity.")
            
            # Usar trade.entryOrder para la notificación ya que executed_order podría ser un objeto
            executed_qty = trade.entryOrder.executedQuantity if trade.entryOrder else "N/A"
            executed_price = trade.entryOrder.executedPrice if trade.entryOrder else "N/A"
            
            await self.notification_service.send_real_trade_status_notification(
                user_config=user_config,
                message=f"Trade {trade.symbol} ({trade.side}) ejecutado exitosamente. Cantidad: {executed_qty}, Precio: {executed_price}",
                status_level="INFO",
                symbol=trade.symbol,
                trade_id=trade.id
            )

            # Create OCO order for TSL/TP if applicable
            if trade.takeProfitPrice and trade.trailingStopActivationPrice:
                try:
                    if trade.side == TradeSide.BUY.value:
                        oco_side = TradeSide.SELL.value
                    elif trade.side == TradeSide.SELL.value:
                        oco_side = TradeSide.BUY.value
                    else:
                        logger.error(f"Unexpected trade side: {trade.side}")
                        raise ValueError(f"Invalid trade side: {trade.side}")
                    logger.debug(f"Trade side: {trade.side}, OCO side calculated: {oco_side}")
                    oco_order_result = await self.unified_order_execution_service.create_oco_order(
                        user_id=trade.user_id,
                        symbol=trade.symbol,
                        side=oco_side,
                        quantity=trade.entryOrder.executedQuantity,
                        price=trade.takeProfitPrice,
                        stop_price=trade.trailingStopActivationPrice,
                        limit_price=trade.takeProfitPrice, # Usar takeProfitPrice como limit_price para la orden OCO
                        trading_mode="real",
                        api_key=api_key,
                        api_secret=api_secret,
                    )
                    if oco_order_result:
                        # oco_order_result es un diccionario, no un objeto TradeOrderDetails
                        trade.ocoOrderListId = oco_order_result.get("listClientOrderId") if isinstance(oco_order_result, dict) else str(oco_order_result)
                        logger.info(
                            f"Successfully created OCO order for trade {trade.id}. OCO List ID: {trade.ocoOrderListId}"
                        )
                except Exception as oco_e:
                    logger.error(
                        f"Failed to create OCO order for trade {trade.id}: {oco_e}",
                        exc_info=True,
                    )
                    trade.closingReason = (
                        f"Position opened, but OCO creation failed: {str(oco_e)}"
                    )

            await self.persistence_service.upsert_trade(
                trade
            )  # Persist trade with updated status and OCO ID

            # Actualizar daily_capital_risked_usd después del trade
            if user_config.real_trading_settings:
                # Asegurar que daily_capital_risked_usd se inicialice si es None ANTES de usarlo
                if user_config.real_trading_settings.daily_capital_risked_usd is None:
                    user_config.real_trading_settings.daily_capital_risked_usd = Decimal("0.0")

                trade_value_usd: Decimal
                # Usar trade.entryOrder que ya es un objeto TradeOrderDetails
                if trade.entryOrder and isinstance(trade.entryOrder.executedQuantity, Decimal) and isinstance(trade.entryOrder.executedPrice, Decimal):
                    trade_value_usd = trade.entryOrder.executedQuantity * trade.entryOrder.executedPrice
                else:
                    logger.error(f"Invalid executed_order details for trade {trade.id}. Quantity: {getattr(trade.entryOrder, 'executedQuantity', 'N/A')}, Price: {getattr(trade.entryOrder, 'executedPrice', 'N/A')}")
                    trade_value_usd = Decimal("0.0") # Default to 0 to avoid further errors

                current_risked = user_config.real_trading_settings.daily_capital_risked_usd or Decimal("0.0")
                user_config.real_trading_settings.daily_capital_risked_usd = current_risked + trade_value_usd
                
                # Asegurar que real_trades_executed_count se inicialice si es None
                if user_config.real_trading_settings.real_trades_executed_count is None:
                    user_config.real_trading_settings.real_trades_executed_count = 0
                user_config.real_trading_settings.real_trades_executed_count += 1 # Incrementar el contador de trades ejecutados
                await self.configuration_service.save_user_configuration(user_config)
                logger.info(f"Updated daily_capital_risked_usd for user {opportunity.user_id} to {user_config.real_trading_settings.daily_capital_risked_usd}.")

            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.CONVERTED_TO_TRADE_REAL,
                "trade_executed_by_confirmation",
                f"Trade {trade.id} executed based on user confirmation."
            )
            return trade
        except Exception as e:
            logger.error(f"Failed to execute trade for opportunity {opportunity.id}: {e}", exc_info=True)
            trade.positionStatus = PositionStatus.ERROR.value
            trade.closingReason = str(e)
            await self.persistence_service.upsert_trade(trade) # Pasar el objeto Trade directamente
            await self.notification_service.send_real_trade_status_notification(
                user_config=user_config,
                message=f"Error al ejecutar trade para {opportunity.symbol}: {e}",
                status_level="ERROR",
                symbol=opportunity.symbol,
                trade_id=trade.id
            )
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.ERROR_IN_PROCESSING,
                "trade_execution_failed",
                f"Failed to execute trade: {e}"
            )
            return trade

    async def create_trade_from_decision(
        self,
        decision: TradingDecision,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        user_config: UserConfiguration,
        current_price: Decimal,
        portfolio_snapshot: PortfolioSnapshot,
    ) -> Optional[Trade]:
        if decision.decision != "execute_trade":
            return None

        try:
            trade_side = self._determine_trade_side_from_opportunity(opportunity)
            actual_trade_mode = TradeMode(decision.mode)
            actual_trade_side = TradeSide(trade_side.lower())

            params = decision.recommended_trade_params or {}
            tp_price_raw = params.get("take_profit_target")
            stop_loss_price_raw = params.get("stop_loss_target")

            # Asegurar que tp_price y stop_loss_price sean Decimal o None
            tp_price = (
                tp_price_raw[0]
                if isinstance(tp_price_raw, list) and tp_price_raw
                else tp_price_raw
            )
            stop_loss_price = (
                stop_loss_price_raw[0]
                if isinstance(stop_loss_price_raw, list) and stop_loss_price_raw
                else stop_loss_price_raw
            )

            # Lógica para TSL
            # Asumimos un callback rate por defecto si no se especifica
            callback_rate = params.get("trailing_stop_callback_rate", Decimal("0.005"))

            trade = Trade(
                user_id=UUID(str(strategy.user_id)),
                mode=actual_trade_mode.value,
                symbol=opportunity.symbol,
                side=actual_trade_side.value,
                entryOrder=self._create_entry_order_from_decision(
                    decision,
                    opportunity,
                    user_config,
                    current_price,
                    portfolio_snapshot,
                ),
                positionStatus=PositionStatus.PENDING_ENTRY_CONDITIONS.value,
                strategyId=UUID(str(strategy.id)),
                opportunityId=UUID(str(opportunity.id)),
                aiAnalysisConfidence=(
                    Decimal(str(decision.confidence)) if decision.ai_analysis_used else None
                ),
                pnl_usd=None,
                pnl_percentage=None,
                closingReason=None,
                ocoOrderListId=None,
                takeProfitPrice=Decimal(str(tp_price)) if tp_price is not None else None,
                trailingStopActivationPrice=Decimal(str(stop_loss_price)) if stop_loss_price is not None else None,
                trailingStopCallbackRate=Decimal(str(callback_rate)) if callback_rate is not None else None,
                currentStopPrice_tsl=Decimal(str(stop_loss_price)) if stop_loss_price is not None else None, # Inicialmente es igual al de activación
                closed_at=None,
            )

            logger.info(f"Created trade {trade.id} from decision {decision.decision_id}")

            await self.persistence_service.upsert_trade(trade) # Pasar el objeto Trade directamente
            logger.info(f"Trade {trade.id} persisted before execution.")

            return trade
        except Exception as e:
            logger.error(
                f"Error creating trade object from decision {decision.decision_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to create trade object: {str(e)}"
            )

    def _create_entry_order_from_decision(
        self,
        decision: TradingDecision,
        opportunity: Opportunity,
        user_config: UserConfiguration,
        current_price: Decimal,
        portfolio_snapshot: PortfolioSnapshot,
    ) -> "TradeOrderDetails":
        params = decision.recommended_trade_params or {}
        entry_price = params.get(
            "entry_price",
            opportunity.initial_signal.entry_price_target
            if opportunity.initial_signal
            else None,
        )

        # --- Lógica de cálculo de cantidad movida aquí ---
        if (
            not user_config.risk_profile_settings
            or user_config.risk_profile_settings.per_trade_capital_risk_percentage
            is None
        ):
            raise ConfigurationError(
                "Risk profile settings or per-trade risk percentage is not configured."
            )

        if not portfolio_snapshot:
            raise OrderExecutionError(
                f"Portfolio snapshot not found for user {user_config.user_id}"
            )

        portfolio_value_for_risk_calc = Decimal(
            str(portfolio_snapshot.real_trading.total_portfolio_value_usd)
        )
        risk_percentage = Decimal(
            str(user_config.risk_profile_settings.per_trade_capital_risk_percentage)
        )
        capital_to_invest = portfolio_value_for_risk_calc * risk_percentage

        if current_price <= 0:
            raise MarketDataError(
                "Current price must be positive to calculate quantity."
            )

        quantity = capital_to_invest / current_price
        # --- Fin de la lógica de cálculo de cantidad ---

        return TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.MARKET.value,
            status=OrderStatus.NEW.value,
            requestedPrice=Decimal(str(entry_price)) if entry_price is not None else None,
            requestedQuantity=quantity,
            executedQuantity=Decimal("0.0"),
            executedPrice=Decimal("0.0"),
            orderId_exchange=None,
            clientOrderId_exchange=None,
            cumulativeQuoteQty=None,
            commissions=None,
            commission=None,
            commissionAsset=None,
            submittedAt=None,
            fillTimestamp=None,
            rawResponse=None,
            ocoOrderListId=None,
        )

    async def _update_opportunity_status(self, opportunity: Opportunity, status: OpportunityStatus, reason_code: str, reason_text: str) -> None:
        opportunity.status = status
        opportunity.status_reason_code = reason_code
        opportunity.status_reason_text = reason_text
        opportunity.updated_at = datetime.now(timezone.utc)
        logger.info(f"Updated opportunity {opportunity.id} status to {status.value}: {reason_text}")
        try:
            await self.persistence_service.update_opportunity_status(
                opportunity_id=UUID(opportunity.id), 
                new_status=status, 
                status_reason=reason_text
            )
            logger.info(f"Persisted status update for opportunity {opportunity.id}")
        except Exception as e_persist:
            logger.error(f"Failed to persist status update for opportunity {opportunity.id}: {e_persist}", exc_info=True)

    def _determine_trade_side_from_opportunity(self, opportunity: Opportunity) -> str:
        if opportunity.initial_signal and hasattr(opportunity.initial_signal, 'direction_sought'):
            direction = opportunity.initial_signal.direction_sought
            if direction in ["buy", "long"]:
                return "buy"
            elif direction in ["sell", "short"]:
                return "sell"
        logger.warning(f"Could not determine trade side from opportunity {opportunity.id}, defaulting to 'buy'")
        return "buy"

    async def process_opportunity(self, opportunity: Opportunity) -> List[TradingDecision]:
        """
        Processes an opportunity by evaluating it against all applicable active strategies.
        """
        logger.info(f"Processing opportunity {opportunity.id} for symbol {opportunity.symbol}")
        
        user_id_str = str(opportunity.user_id)
        user_config = await self.configuration_service.get_user_configuration(user_id_str)
        if not user_config:
            logger.error(f"User configuration not found for user {user_id_str}. Cannot process opportunity.")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.ERROR_IN_PROCESSING,
                "user_config_not_found",
                f"User configuration not found for user {user_id_str}"
            )
            return []

        mode = "paper" if user_config.paper_trading_active else "real"
        active_strategies = await self.strategy_service.get_active_strategies(user_id_str, mode)
        
        if not active_strategies:
            logger.warning(f"No active strategies found for user {user_id_str} in {mode} mode.")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.REJECTED_BY_SYSTEM,
                "no_active_strategies",
                f"No active {mode} strategies found for user."
            )
            return []

        applicable_strategies = []
        for s in active_strategies:
            if await self.strategy_service.is_strategy_applicable_to_symbol(str(s.id), user_id_str, opportunity.symbol):
                applicable_strategies.append(s)

        if not applicable_strategies:
            logger.warning(f"No active and applicable strategies found for opportunity {opportunity.id} with symbol {opportunity.symbol}.")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.REJECTED_BY_SYSTEM,
                "no_applicable_strategies",
                "No active strategies are applicable to this opportunity's symbol."
            )
            return []

        decisions: List[TradingDecision] = []
        for strategy in applicable_strategies:
            try:
                decision = await self._evaluate_strategy_for_opportunity(strategy, opportunity, user_config, mode)
                if decision:
                    decisions.append(decision)
            except Exception as e:
                logger.error(f"Error evaluating strategy {strategy.id} for opportunity {opportunity.id}: {e}", exc_info=True)

        if not decisions:
            logger.info(f"No affirmative trading decisions made for opportunity {opportunity.id}.")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.REJECTED_BY_SYSTEM,
                "no_affirmative_decision",
                "All applicable strategies evaluated, but none resulted in a decision to trade."
            )
        else:
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.UNDER_EVALUATION,
                "strategies_evaluated",
                f"{len(decisions)} potential trade decision(s) generated."
            )

        return decisions

    async def _evaluate_strategy_for_opportunity(
        self, 
        strategy: TradingStrategyConfig, 
        opportunity: Opportunity, 
        user_config: UserConfiguration,
        mode: str
    ) -> Optional[TradingDecision]:
        """Evaluates a single strategy (AI or autonomous) for a given opportunity."""
        
        user_id_str = str(opportunity.user_id)

        # Validar el tipo de estrategia. Si es desconocido, recomendar investigación.
        if strategy.base_strategy_type not in [member.value for member in BaseStrategyType]:
            logger.warning(f"Unknown strategy type '{strategy.base_strategy_type}' for strategy {strategy.id}. Recommending investigation.")
            return TradingDecision(
                decision="investigate",
                confidence=0.0, # Baja confianza para tipo desconocido
                reasoning=f"Strategy type '{strategy.base_strategy_type}' is unknown. Requires manual investigation.",
                opportunity_id=str(opportunity.id),
                strategy_id=str(strategy.id),
                mode=mode,
                ai_analysis_used=False,
                warnings=["UNKNOWN_STRATEGY_TYPE"]
            )

        # 1. AI-Driven Path
        if strategy.ai_analysis_profile_id and self.ai_orchestrator:
            ai_config = None
            if user_config.ai_strategy_configurations:
                ai_config = next((c for c in user_config.ai_strategy_configurations if c.id == strategy.ai_analysis_profile_id), None)
            
            if not ai_config:
                logger.warning(f"AI profile '{strategy.ai_analysis_profile_id}' for strategy {strategy.id} not found. Skipping AI analysis.")
            else:
                try:
                    # Defensive coding to handle string or Enum for source_type
                    source_type_val = opportunity.source_type
                    if isinstance(source_type_val, str):
                        try:
                            # Attempt to convert string to Enum member
                            source_type_val = SourceType(source_type_val).value
                        except ValueError:
                            logger.warning(f"Invalid source_type string '{source_type_val}' for opportunity {opportunity.id}. Defaulting to UNKNOWN.")
                            source_type_val = SourceType.UNKNOWN.value
                    elif isinstance(source_type_val, SourceType):
                        source_type_val = source_type_val.value

                    opportunity_data = OpportunityData(
                        opportunity_id=str(opportunity.id), symbol=opportunity.symbol,
                        initial_signal=opportunity.initial_signal.model_dump() if opportunity.initial_signal else {},
                        source_type=source_type_val,
                        source_name=opportunity.source_name, source_data=opportunity.source_data, detected_at=opportunity.detected_at,
                    )
                    ai_result = await self.ai_orchestrator.analyze_opportunity_with_strategy_context_async(
                        opportunity=opportunity_data, strategy=strategy, ai_config=ai_config, user_id=user_id_str
                    )
                    
                    if ai_result and ai_result.suggested_action not in [SuggestedAction.HOLD_NEUTRAL, SuggestedAction.NO_CLEAR_OPPORTUNITY]:
                        thresholds = ai_config.confidence_thresholds
                        confidence_threshold = 0.0
                        if thresholds:
                            threshold_value = thresholds.paper_trading if mode == "paper" else thresholds.real_trading
                            if threshold_value is not None:
                                confidence_threshold = threshold_value
                        else:
                            logger.warning(f"Confidence thresholds not set for AI profile {ai_config.id}. Using default 0.0")
                        
                        if ai_result.calculated_confidence >= confidence_threshold:
                            return TradingDecision(
                                decision="execute_trade", confidence=ai_result.calculated_confidence,
                                reasoning=ai_result.reasoning_ai, opportunity_id=str(opportunity.id),
                                strategy_id=str(strategy.id), mode=mode, ai_analysis_used=True,
                                ai_analysis_profile_id=ai_config.id, 
                                recommended_trade_params=ai_result.recommended_trade_params if ai_result.recommended_trade_params else None,
                                warnings=ai_result.ai_warnings
                            )
                        else:
                            logger.info(f"AI confidence {ai_result.calculated_confidence} for strategy {strategy.id} is below threshold {confidence_threshold}.")
                except Exception as e:
                    logger.error(f"AI analysis for strategy {strategy.id} failed: {e}. Checking for autonomous fallback.", exc_info=True)

        # 2. Autonomous Fallback/Default Path
        can_operate_autonomously = await self.strategy_service.strategy_can_operate_autonomously(str(strategy.id), user_id_str)
        if can_operate_autonomously:
            logger.info(f"Strategy {strategy.id} can operate autonomously. Proceeding with autonomous logic.")
            return TradingDecision(
                decision="execute_trade", confidence=0.75,
                reasoning=f"Autonomous strategy '{strategy.config_name}' triggered based on its internal logic.",
                opportunity_id=str(opportunity.id), strategy_id=str(strategy.id),
                mode=mode, ai_analysis_used=False
            )
        
        logger.info(f"Strategy {strategy.id} did not produce a decision for opportunity {opportunity.id}.")
        return None
        
    # ... (otros métodos del servicio que no necesitan cambios inmediatos) ...
    # Se omiten por brevedad, pero estarían aquí en el archivo real.
