"""Trading Engine Service for executing trading strategies with AI integration.

This service orchestrates the trading decision process, integrating AI analysis
results with strategy logic to make informed trading decisions.
"""

import logging
from uuid import UUID
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from fastapi import HTTPException

# Use domain models exclusively for internal logic
from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
)
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
)
from src.ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    AIAnalysis,
    SuggestedAction,
    RecommendedTradeParams,
    DataVerification,
    InitialSignal,
)
from src.ultibot_backend.core.domain_models.ai import AIResponse
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.core.domain_models.trade_models import (
    Trade,
    AIInfluenceDetails,
    PositionStatus,
    OrderType,
    TradeOrderDetails,
    OrderStatus,
    TradeMode, 
    TradeSide
)
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import MarketDataError, BinanceAPIError, OrderExecutionError
from src.shared.data_types import ServiceName
from src.ultibot_backend.app_config import AppSettings

# Conditional imports for type checking to avoid circular dependencies
if TYPE_CHECKING:
    from src.ultibot_backend.services.strategy_service import StrategyService
    from src.ultibot_backend.services.config_service import ConfigurationService
    from src.ultibot_backend.services.notification_service import NotificationService
    from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
    from src.ultibot_backend.services.portfolio_service import PortfolioService

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
        self.ai_analysis_used = ai_analysis_used
        self.ai_analysis_profile_id = ai_analysis_profile_id
        self.recommended_trade_params = recommended_trade_params
        self.risk_assessment = risk_assessment
        self.warnings = warnings or []
        self.timestamp = datetime.now(timezone.utc)
        self.decision_id = str(UUID())


class TradingEngineService:
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
        ai_orchestrator: Optional[AIOrchestratorService] = None,
        app_settings: Optional[AppSettings] = None,
    ):
        self.persistence_service = persistence_service
        self.market_data_service = market_data_service
        self.unified_order_execution_service = unified_order_execution_service
        self.credential_service = credential_service
        self.notification_service = notification_service
        self.strategy_service = strategy_service
        self.configuration_service = configuration_service
        self.portfolio_service = portfolio_service
        if ai_orchestrator:
            self.ai_orchestrator = ai_orchestrator
        elif app_settings:
            self.ai_orchestrator = AIOrchestratorService(app_settings=app_settings)
        else:
            logger.warning("AIOrchestratorService not initialized because neither an instance nor app_settings were provided.")
            self.ai_orchestrator = None


    async def execute_trade_from_confirmed_opportunity(self, opportunity: Opportunity) -> Optional[Trade]:
        logger.info(f"Executing trade directly from confirmed opportunity {opportunity.id}")

        strategies = await self.strategy_service.list_strategy_configs(UUID(opportunity.user_id))
        active_strategies = [s for s in strategies if s.is_active_real_mode]

        if not active_strategies:
            raise OrderExecutionError(f"No active real strategies found for user {opportunity.user_id} to execute confirmed opportunity {opportunity.id}")
        
        strategy = active_strategies[0]
        logger.warning(f"Using strategy '{strategy.config_name}' as context for confirmed opportunity {opportunity.id}")

        decision = TradingDecision(
            decision="execute_trade",
            confidence=1.0,
            reasoning="Trade executed based on direct user confirmation.",
            opportunity_id=str(opportunity.id),
            strategy_id=str(strategy.id),
            ai_analysis_used=False,
            recommended_trade_params=opportunity.initial_signal.model_dump() if opportunity.initial_signal else {}
        )

        trade = await self.create_trade_from_decision(decision, opportunity, strategy)

        if trade:
            logger.info(f"Successfully created trade {trade.id} from confirmed opportunity.")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.CONVERTED_TO_TRADE_REAL,
                "trade_executed_by_confirmation",
                f"Trade {trade.id} executed based on user confirmation."
            )
        else:
            logger.error(f"Failed to create trade from confirmed opportunity {opportunity.id}")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.ERROR_IN_PROCESSING,
                "trade_creation_failed",
                "Failed to create trade object after user confirmation."
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
            trade_mode_str = getattr(decision, 'mode', 'paper')
            
            actual_trade_mode = TradeMode(trade_mode_str)
            actual_trade_side = TradeSide(trade_side)

            tp_price = None
            if decision.recommended_trade_params:
                tp_value = decision.recommended_trade_params.get("take_profit")
                if isinstance(tp_value, list) and tp_value:
                    tp_price = float(tp_value[0])
                elif isinstance(tp_value, (float, int)):
                    tp_price = float(tp_value)

            trade = Trade(
                id=UUID(),
                user_id=UUID(strategy.user_id),
                mode=actual_trade_mode,
                symbol=opportunity.symbol,
                side=actual_trade_side,
                strategy_id=UUID(strategy.id),
                opportunity_id=UUID(opportunity.id),
                position_status=PositionStatus.PENDING_ENTRY_CONDITIONS,
                entry_order=self._create_entry_order_from_decision(decision, opportunity),
                ai_analysis_confidence=decision.confidence if decision.ai_analysis_used else None,
                notes=f"Trade from strategy '{strategy.config_name}': {decision.reasoning}",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                stop_loss_price=decision.recommended_trade_params.get("stop_loss") if decision.recommended_trade_params else None,
                take_profit_price=tp_price,
                exit_orders=[],
                initial_risk_quote_amount=None,
                initial_reward_to_risk_ratio=None,
                risk_reward_adjustments=[],
                current_risk_quote_amount=None,
                current_reward_to_risk_ratio=None,
                pnl=None,
                pnl_percentage=None,
                closing_reason=None,
                exit_order_oco_id=None,
                exit_price=None,
                market_context_snapshots=None,
                external_event_or_analysis_link=None,
                backtest_details=None,
                ai_influence_details=None,
                opened_at=None,
                closed_at=None,
                strategy_execution_instance_id=None
            )
            
            if decision.ai_analysis_used and decision.ai_analysis_profile_id:
                trade.add_ai_influence_details(
                    ai_analysis_profile_id=decision.ai_analysis_profile_id,
                    ai_confidence=decision.confidence,
                    ai_suggested_action=opportunity.ai_analysis.suggested_action.value if opportunity.ai_analysis else "UNKNOWN",
                    ai_reasoning_summary=opportunity.ai_analysis.reasoning_ai[:500] if opportunity.ai_analysis else "N/A",
                )

            logger.info(f"Created trade {trade.id} from decision {decision.decision_id}")
            
            await self.persistence_service.upsert_trade(trade.model_dump())
            logger.info(f"Trade {trade.id} persisted before execution.")

            return trade
        except Exception as e:
            logger.error(f"Error creating trade object from decision {decision.decision_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create trade object: {str(e)}")

    def _create_entry_order_from_decision(self, decision: TradingDecision, opportunity: Opportunity) -> 'TradeOrderDetails':
        params = decision.recommended_trade_params or {}
        entry_price = params.get("entry_price", opportunity.initial_signal.entry_price_target if opportunity.initial_signal else None)
        quantity = params.get("position_size_percentage", 1.0)

        return TradeOrderDetails(
            order_id_internal=UUID(),
            type=OrderType.MARKET,
            status=OrderStatus.NEW,
            requested_price=float(entry_price) if entry_price else None,
            requested_quantity=float(quantity),
            timestamp=datetime.now(timezone.utc)
        )

    async def _update_opportunity_status(self, opportunity: Opportunity, status: OpportunityStatus, reason_code: str, reason_text: str) -> None:
        opportunity.status = status
        opportunity.status_reason_code = reason_code
        opportunity.status_reason_text = reason_text
        opportunity.updated_at = datetime.now(timezone.utc)
        logger.info(f"Updated opportunity {opportunity.id} status to {status.value}: {reason_text}")
        try:
            if opportunity.id is None:
                logger.error("Cannot update opportunity status without an ID.")
                return
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
        
    # ... (otros métodos del servicio que no necesitan cambios inmediatos) ...
    # Se omiten por brevedad, pero estarían aquí en el archivo real.
