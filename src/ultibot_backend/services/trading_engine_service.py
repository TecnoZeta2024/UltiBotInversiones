"""Trading Engine Service for executing trading strategies with AI integration.

This service orchestrates the trading decision process, integrating AI analysis
results with strategy logic to make informed trading decisions.
"""

import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from fastapi import HTTPException

# Use domain models exclusively for internal logic
from ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
)
from ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
)
from ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    AIAnalysis,
    SuggestedAction,
    RecommendedTradeParams,
    DataVerification,
    InitialSignal,
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
    ConfigurationError
)
from shared.data_types import ServiceName

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

        user_config = await self.configuration_service.get_user_configuration()
        if not user_config:
            raise OrderExecutionError(f"User configuration not found for user {opportunity.user_id}")

        # Lógica de reinicio de capital diario
        current_utc_date = datetime.now(timezone.utc).date()
        if user_config.real_trading_settings and user_config.real_trading_settings.last_daily_reset:
            last_reset_date = user_config.real_trading_settings.last_daily_reset.date()
            if last_reset_date < current_utc_date:
                logger.info(f"Daily capital reset triggered for user {opportunity.user_id}. Resetting daily_capital_risked_usd.")
                user_config.real_trading_settings.daily_capital_risked_usd = 0.0
                user_config.real_trading_settings.last_daily_reset = datetime.now(timezone.utc)
                await self.configuration_service.save_user_configuration(user_config)
                logger.info(f"User configuration saved after daily capital reset for user {opportunity.user_id}.")
        elif user_config.real_trading_settings and user_config.real_trading_settings.last_daily_reset is None:
            # Si es la primera vez que se usa, inicializar last_daily_reset
            user_config.real_trading_settings.last_daily_reset = datetime.now(timezone.utc)
            await self.configuration_service.save_user_configuration(user_config)
            logger.info(f"User configuration saved after initializing last_daily_reset for user {opportunity.user_id}.")


        portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(UUID(opportunity.user_id))
        if not portfolio_snapshot:
            raise OrderExecutionError(f"Portfolio snapshot not found for user {opportunity.user_id}")

        current_price = await self.market_data_service.get_latest_price(opportunity.symbol)
        if not current_price:
            raise MarketDataError(f"Could not retrieve current price for {opportunity.symbol}")

        strategies = await self.strategy_service.get_active_strategies(str(opportunity.user_id), "real")
        if not strategies:
            raise OrderExecutionError(f"No active real strategies found for user {opportunity.user_id} to execute confirmed opportunity {opportunity.id}")
        
        strategy = strategies[0]
        logger.warning(f"Using strategy '{strategy.config_name}' as context for confirmed opportunity {opportunity.id}")

        decision = TradingDecision(
            decision="execute_trade",
            confidence=opportunity.ai_analysis.calculated_confidence if opportunity.ai_analysis else 1.0,
            reasoning="Trade executed based on direct user confirmation." + (f" AI analysis: {opportunity.ai_analysis.reasoning_ai}" if opportunity.ai_analysis else ""),
            opportunity_id=str(opportunity.id),
            strategy_id=str(strategy.id),
            mode="real",
            ai_analysis_used=True if opportunity.ai_analysis else False,
            ai_analysis_profile_id=None, # AIAnalysis does not have profile_id directly
            recommended_trade_params=opportunity.initial_signal.model_dump() if opportunity.initial_signal else {}
        )

        trade = await self.create_trade_from_decision(decision, opportunity, strategy)

        if not trade:
            logger.error(f"Failed to create trade from confirmed opportunity {opportunity.id}")
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
                quantity=trade.entryOrder.requestedQuantity,
                trading_mode="real",
                api_key=api_key,
                api_secret=api_secret
            )
            trade.entryOrder = executed_order
            trade.positionStatus = PositionStatus.OPEN.value
            
            logger.info(f"Successfully executed trade {trade.id} from confirmed opportunity.")
            await self.persistence_service.upsert_trade(trade.model_dump())
            
            # Actualizar daily_capital_risked_usd después del trade
            if user_config.real_trading_settings:
                trade_value_usd = executed_order.executedQuantity * executed_order.executedPrice
                if user_config.real_trading_settings.daily_capital_risked_usd is None:
                    user_config.real_trading_settings.daily_capital_risked_usd = 0.0
                user_config.real_trading_settings.daily_capital_risked_usd += trade_value_usd
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
            await self.persistence_service.upsert_trade(trade.model_dump())
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
    ) -> Optional[Trade]:
        if decision.decision != "execute_trade":
            return None

        try:
            trade_side = self._determine_trade_side_from_opportunity(opportunity)
            actual_trade_mode = TradeMode(decision.mode)
            actual_trade_side = TradeSide(trade_side.lower())

            params = decision.recommended_trade_params or {}
            tp_price = params.get("take_profit_target")
            stop_loss_price = params.get("stop_loss_target")
            
            # Lógica para TSL
            # Asumimos un callback rate por defecto si no se especifica
            callback_rate = params.get("trailing_stop_callback_rate", 0.005) 

            trade = Trade(
                user_id=UUID(str(strategy.user_id)),
                mode=actual_trade_mode.value,
                symbol=opportunity.symbol,
                side=actual_trade_side.value,
                entryOrder=self._create_entry_order_from_decision(
                    decision, opportunity
                ),
                positionStatus=PositionStatus.PENDING_ENTRY_CONDITIONS.value,
                strategyId=UUID(str(strategy.id)),
                opportunityId=UUID(str(opportunity.id)),
                aiAnalysisConfidence=(
                    decision.confidence if decision.ai_analysis_used else None
                ),
                pnl_usd=None,
                pnl_percentage=None,
                closingReason=None,
                ocoOrderListId=None,
                takeProfitPrice=float(tp_price) if tp_price else None,
                trailingStopActivationPrice=float(stop_loss_price) if stop_loss_price else None,
                trailingStopCallbackRate=callback_rate,
                currentStopPrice_tsl=float(stop_loss_price) if stop_loss_price else None, # Inicialmente es igual al de activación
                closed_at=None,
            )

            logger.info(f"Created trade {trade.id} from decision {decision.decision_id}")

            await self.persistence_service.upsert_trade(trade.model_dump())
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
        self, decision: TradingDecision, opportunity: Opportunity
    ) -> "TradeOrderDetails":
        params = decision.recommended_trade_params or {}
        entry_price = params.get(
            "entry_price",
            opportunity.initial_signal.entry_price_target
            if opportunity.initial_signal
            else None,
        )
        quantity = params.get("position_size_percentage", 1.0)

        return TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.MARKET.value,
            status=OrderStatus.NEW.value,
            requestedPrice=float(entry_price) if entry_price else None,
            requestedQuantity=float(quantity),
            executedQuantity=0.0,
            executedPrice=0.0,
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

    async def process_opportunity(self, opportunity: Opportunity) -> Optional[Trade]:
        """
        Processes an opportunity, deciding whether to use AI analysis or fallback to autonomous strategy logic.
        """
        logger.info(f"Processing opportunity {opportunity.id} for symbol {opportunity.symbol}")

        if not opportunity.strategy_id:
            logger.error(f"Opportunity {opportunity.id} has no strategy_id. Cannot process.")
            return None

        strategy_config = await self.strategy_service.get_strategy_config(str(opportunity.strategy_id), opportunity.user_id)
        if not strategy_config:
            logger.error(f"Could not find strategy config with ID {opportunity.strategy_id} for opportunity {opportunity.id}")
            return None

        ai_analysis_result = None
        try:
            if strategy_config.ai_analysis_profile_id:
                user_config = await self.configuration_service.get_user_configuration()
                ai_config: Optional[AIStrategyConfiguration] = None
                if user_config and user_config.ai_strategy_configurations:
                    ai_config = next((c for c in user_config.ai_strategy_configurations if c.id == strategy_config.ai_analysis_profile_id), None)

                if ai_config:
                    opportunity_data = OpportunityData(
                        opportunity_id=str(opportunity.id),
                        symbol=opportunity.symbol,
                        initial_signal=opportunity.initial_signal.model_dump(),
                        source_type=opportunity.source_type.value,
                        source_name=opportunity.source_name,
                        source_data=opportunity.source_data,
                        detected_at=opportunity.detected_at,
                    )
                    ai_analysis_result = await self.ai_orchestrator.analyze_opportunity_with_strategy_context_async(
                        opportunity=opportunity_data,
                        strategy=strategy_config,
                        ai_config=ai_config,
                        user_id=opportunity.user_id,
                    )
                else:
                    logger.warning(f"AI profile '{strategy_config.ai_analysis_profile_id}' not found. Skipping AI analysis.")
            
            if ai_analysis_result and ai_analysis_result.suggested_action not in [SuggestedAction.HOLD_NEUTRAL, SuggestedAction.NO_CLEAR_OPPORTUNITY]:
                logger.info(f"AI analysis successful for opportunity {opportunity.id}. Proceeding with AI-driven trade.")
                logger.info(f"AI recommended action: {ai_analysis_result.suggested_action}")
                # Placeholder for creating a trade from the AI decision
                return None
            else:
                if ai_analysis_result:
                    logger.info(f"AI analysis did not recommend a trade for opportunity {opportunity.id}. Reason: {ai_analysis_result.reasoning_ai}")
                # This will trigger the fallback logic
                raise ValueError("AI did not recommend trade or analysis was skipped.")

        except Exception as e:
            logger.warning(f"AI analysis failed or did not recommend trade for opportunity {opportunity.id}: {e}. Checking for autonomous fallback.")
            
            can_operate_autonomously = await self.strategy_service.strategy_can_operate_autonomously(str(opportunity.strategy_id), opportunity.user_id)
            
            if can_operate_autonomously:
                logger.info(f"Strategy {strategy_config.id} can operate autonomously. Proceeding with autonomous logic.")
                # Placeholder for autonomous logic execution
                return None
            else:
                logger.info(f"Strategy {strategy_config.id} cannot operate autonomously. No action taken for opportunity {opportunity.id}.")
                return None
        
    # ... (otros métodos del servicio que no necesitan cambios inmediatos) ...
    # Se omiten por brevedad, pero estarían aquí en el archivo real.
