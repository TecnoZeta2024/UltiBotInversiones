"""Trading Engine Service for executing trading strategies with AI integration.

This service orchestrates the trading decision process, integrating AI analysis
results with strategy logic to make informed trading decisions.
"""

import logging
from uuid import UUID # Importar UUID explícitamente
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING # Añadir TYPE_CHECKING

from fastapi import HTTPException

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
    RecommendedTradeParams, # Añadir importación
    DataVerification, # Añadir importación
    InitialSignal, # Añadir importación
)
from src.ultibot_backend.services.ai_orchestrator_service import (
    AIOrchestrator,
    AIAnalysisResult,
    OpportunityData,
)
from src.ultibot_backend.core.domain_models.trade_models import (
    Trade,
    AIInfluenceDetails,
    PositionStatus, # Corregido de TradeStatus
    OrderType, # Añadido
    TradeOrderDetails, # Añadido para la creación de la orden de salida
    OrderStatus, # Añadido
)
from src.ultibot_backend.services.market_data_service import MarketDataService # Añadido
from src.ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService # Añadido
from src.ultibot_backend.services.credential_service import CredentialService # Añadido
from src.ultibot_backend.services.notification_service import NotificationService # Añadido para Tarea 1.4.2
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Añadido para Tarea 1.4.2
from src.ultibot_backend.core.domain_models.trade_models import TradeMode, TradeSide # Añadido para enums
from src.ultibot_backend.core.exceptions import MarketDataError, BinanceAPIError # Añadido BinanceAPIError
from src.shared.data_types import ServiceName # Añadido


logger = logging.getLogger(__name__)


class TradingDecision:
    """Result of trading decision analysis."""
    
    def __init__(
        self,
        decision: str,  # "execute_trade", "reject_opportunity", "requires_investigation"
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
        """Initialize trading decision.
        
        Args:
            decision: The decision made ("execute_trade", "reject_opportunity", etc.).
            confidence: Confidence in the decision (0-1).
            reasoning: Reasoning for the decision.
            opportunity_id: ID of the opportunity.
            strategy_id: ID of the strategy used.
            ai_analysis_used: Whether AI analysis was used.
            ai_analysis_profile_id: AI analysis profile ID if used.
            recommended_trade_params: Recommended trade parameters.
            risk_assessment: Risk assessment results.
            warnings: Any warnings or concerns.
        """
        self.decision = decision
        self.confidence = confidence
        self.reasoning = reasoning
        self.opportunity_id = opportunity_id if opportunity_id is not None else "UNKNOWN_OPPORTUNITY_ID"
        self.strategy_id = strategy_id if strategy_id is not None else "UNKNOWN_STRATEGY_ID"
        self.ai_analysis_used = ai_analysis_used
        self.ai_analysis_profile_id = ai_analysis_profile_id
        self.recommended_trade_params = recommended_trade_params
        self.risk_assessment = risk_assessment
        self.warnings = warnings or []
        self.timestamp = datetime.now(timezone.utc)
        self.decision_id = str(UUID().hex) # Usar UUID importado y generar un string


class TradingEngine:
    """Service for executing trading strategies with AI integration."""
    
    def __init__(
        self,
        persistence_service: "SupabasePersistenceService",
        market_data_service: MarketDataService,
        unified_order_execution_service: UnifiedOrderExecutionService,
        credential_service: CredentialService,
        notification_service: "NotificationService",
        ai_orchestrator: Optional[AIOrchestrator] = None,
        strategy_service: Optional["StrategyService"] = None,
        configuration_service: Optional["ConfigurationService"] = None,
        portfolio_service: Optional["PortfolioService"] = None,
    ):
        """Initialize the trading engine.
        
        Args:
            persistence_service: Service for data persistence.
            market_data_service: Service for fetching market data.
            unified_order_execution_service: Service for executing orders.
            credential_service: Service for managing user credentials.
            notification_service: Service for sending notifications.
            ai_orchestrator: AI orchestrator for AI analysis (optional).
            strategy_service: Strategy service for accessing strategy configurations (optional).
            configuration_service: Configuration service for user settings (optional).
            portfolio_service: Service for portfolio management (optional).
        """
        self.strategy_service = strategy_service
        self.configuration_service = configuration_service
        self.market_data_service = market_data_service
        self.unified_order_execution_service = unified_order_execution_service
        self.credential_service = credential_service
        self.notification_service = notification_service
        self.persistence_service = persistence_service
        self.ai_orchestrator = ai_orchestrator or AIOrchestrator()
        self.portfolio_service = portfolio_service

if TYPE_CHECKING:
    from src.ultibot_backend.services.strategy_service import StrategyService
    from src.ultibot_backend.services.configuration_service import ConfigurationService
    from src.ultibot_backend.services.notification_service import NotificationService # Added
    from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Added
    from src.ultibot_backend.services.portfolio_service import PortfolioService
    
    async def evaluate_opportunity_with_strategy(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str = "paper",  # "paper" or "real"
    ) -> TradingDecision:
        """Evaluate an opportunity using a specific strategy.
        
        Args:
            opportunity: The opportunity to evaluate.
            strategy: The trading strategy to use.
            mode: Trading mode ("paper" or "real").
            
        Returns:
            TradingDecision with the evaluation result.
            
        Raises:
            HTTPException: If evaluation fails.
        """
        try:
            logger.info(
                f"Evaluating opportunity {opportunity.id} with strategy {strategy.config_name} "
                f"in {mode} mode"
            )
            
            # Check if strategy requires AI analysis
            requires_ai = await self.strategy_service.strategy_requires_ai_analysis(strategy)
            
            if requires_ai:
                # Perform AI analysis
                decision = await self._evaluate_with_ai_analysis(
                    opportunity, strategy, mode
                )
            else:
                # Perform autonomous strategy evaluation
                decision = await self._evaluate_autonomously(
                    opportunity, strategy, mode
                )
            
            logger.info(
                f"Completed evaluation for opportunity {opportunity.id}. "
                f"Decision: {decision.decision}, Confidence: {decision.confidence:.2f}"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error evaluating opportunity {opportunity.id} with strategy {strategy.id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Trading evaluation failed: {str(e)}"
            )
    
    async def _evaluate_with_ai_analysis(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
    ) -> TradingDecision:
        """Evaluate opportunity with AI analysis integration.
        
        Args:
            opportunity: The opportunity to evaluate.
            strategy: The trading strategy to use.
            mode: Trading mode ("paper" or "real").
            
        Returns:
            TradingDecision with AI analysis integration.
        """
        # Get AI configuration for the strategy
        ai_config = await self.strategy_service.get_ai_configuration_for_strategy(strategy)
        if not ai_config:
            logger.warning(
                f"Strategy {strategy.id} requires AI but configuration not found. "
                "Falling back to autonomous evaluation."
            )
            return await self._evaluate_autonomously(opportunity, strategy, mode)
        
        # Convert opportunity to OpportunityData format for AI analysis
        opportunity_data = self._convert_opportunity_to_data(opportunity)
        
        # Perform AI analysis
        try:
            ai_result = await self.ai_orchestrator.analyze_opportunity_with_strategy_context_async(
                opportunity_data, strategy, ai_config, strategy.user_id
            )
            
            # Log detailed AI invocation information for auditing
            await self.log_ai_invocation_details(strategy, opportunity, ai_config, ai_result)
            
        except Exception as e:
            logger.error(f"AI analysis failed for opportunity {opportunity.id}: {e}")
            # Decide whether to fall back to autonomous evaluation or reject
            if await self.strategy_service.strategy_can_operate_autonomously(strategy):
                logger.info("Falling back to autonomous evaluation due to AI failure")
                return await self._evaluate_autonomously(opportunity, strategy, mode)
            else:
                return TradingDecision(
                    decision="reject_opportunity",
                    confidence=0.0,
                    reasoning=f"AI analysis failed and strategy cannot operate autonomously: {e}",
                    opportunity_id=str(opportunity.id) if opportunity.id is not None else "UNKNOWN_OPPORTUNITY_ID",
                    strategy_id=str(strategy.id) if strategy.id is not None else "UNKNOWN_STRATEGY_ID",
                    ai_analysis_used=False,
                    warnings=[f"AI analysis failed: {e}"],
                )
        
        # Get effective confidence thresholds
        confidence_thresholds = await self.strategy_service.get_effective_confidence_thresholds_for_strategy(strategy)
        threshold = self._get_confidence_threshold_for_mode(confidence_thresholds, mode)
        
        # Make decision based on AI analysis
        decision = self._make_decision_from_ai_analysis(
            ai_result, opportunity, strategy, mode, threshold
        )
        
        # Update opportunity with AI analysis
        await self._update_opportunity_with_ai_analysis(opportunity, ai_result)
        
        return decision
    
    async def _evaluate_autonomously(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
    ) -> TradingDecision:
        """Evaluate opportunity using autonomous strategy logic.
        
        Args:
            opportunity: The opportunity to evaluate.
            strategy: The trading strategy to use.
            mode: Trading mode ("paper" or "real").
            
        Returns:
            TradingDecision based on autonomous strategy logic.
        """
        logger.info(f"Performing autonomous evaluation for strategy {strategy.config_name}")
        
        # Perform strategy-specific autonomous evaluation
        decision_result = self._evaluate_strategy_autonomously(opportunity, strategy, mode)
        
        return TradingDecision(
            decision=decision_result["decision"],
            confidence=decision_result["confidence"],
            reasoning=decision_result["reasoning"],
            opportunity_id=str(opportunity.id) if opportunity.id is not None else "UNKNOWN_OPPORTUNITY_ID",
            strategy_id=str(strategy.id) if strategy.id is not None else "UNKNOWN_STRATEGY_ID",
            ai_analysis_used=False,
            recommended_trade_params=decision_result.get("trade_params"),
            risk_assessment=decision_result.get("risk_assessment"),
            warnings=decision_result.get("warnings", []),
        )
    
    def _evaluate_strategy_autonomously(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
    ) -> Dict[str, Any]:
        """Perform autonomous evaluation based on strategy type.
        
        Args:
            opportunity: The opportunity to evaluate.
            strategy: The trading strategy to use.
            mode: Trading mode ("paper" or "real").
            
        Returns:
            Dictionary with evaluation results.
        """
        # Get strategy-specific evaluation based on type
        if strategy.base_strategy_type == BaseStrategyType.SCALPING:
            return self._evaluate_scalping_strategy(opportunity, strategy, mode)
        elif strategy.base_strategy_type == BaseStrategyType.DAY_TRADING:
            return self._evaluate_day_trading_strategy(opportunity, strategy, mode)
        elif strategy.base_strategy_type == BaseStrategyType.ARBITRAGE_SIMPLE:
            return self._evaluate_arbitrage_strategy(opportunity, strategy, mode)
        else:
            # Default evaluation for other strategy types
            return self._evaluate_default_strategy(opportunity, strategy, mode)
    
    def _evaluate_scalping_strategy(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
    ) -> Dict[str, Any]:
        """Evaluate opportunity using scalping strategy logic.
        
        Args:
            opportunity: The opportunity to evaluate.
            strategy: The trading strategy configuration.
            mode: Trading mode.
            
        Returns:
            Evaluation results dictionary.
        """
        # Get scalping parameters
        params = strategy.parameters
        
        # Basic scalping evaluation logic
        signal = opportunity.initial_signal
        confidence = 0.7  # Base confidence for scalping
        
        # Check if we have entry price target
        if not signal.entry_price_target:
            return {
                "decision": "reject_opportunity",
                "confidence": 0.0,
                "reasoning": "Scalping strategy requires entry price target",
                "warnings": ["No entry price target provided"],
            }
        
        # Calculate stop loss and take profit based on scalping parameters
        entry_price = signal.entry_price_target
        
        # Acceso seguro a parámetros
        profit_target_pct = getattr(params, 'profit_target_percentage', 0.01) if hasattr(params, 'profit_target_percentage') else params.get('profit_target_percentage', 0.01) if isinstance(params, dict) else 0.01
        stop_loss_pct = getattr(params, 'stop_loss_percentage', 0.005) if hasattr(params, 'stop_loss_percentage') else params.get('stop_loss_percentage', 0.005) if isinstance(params, dict) else 0.005
        
        # Calculate trade parameters
        if signal.direction_sought == "buy":
            take_profit = entry_price * (1 + profit_target_pct)
            stop_loss = entry_price * (1 - stop_loss_pct)
        else:
            take_profit = entry_price * (1 - profit_target_pct)
            stop_loss = entry_price * (1 + stop_loss_pct)
        
        trade_params = {
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": [take_profit],
            "position_size_percentage": 2.0,  # Default 2% position size for scalping
        }
        
        reasoning = (
            f"Scalping strategy evaluation: Entry at {entry_price}, "
            f"TP at {take_profit:.2f} ({profit_target_pct*100:.1f}%), "
            f"SL at {stop_loss:.2f} ({stop_loss_pct*100:.1f}%)"
        )
        
        return {
            "decision": "execute_trade",
            "confidence": confidence,
            "reasoning": reasoning,
            "trade_params": trade_params,
            "risk_assessment": {
                "risk_reward_ratio": profit_target_pct / stop_loss_pct,
                "max_loss_percentage": stop_loss_pct,
            },
        }
    
    def _evaluate_day_trading_strategy(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
    ) -> Dict[str, Any]:
        """Evaluate opportunity using day trading strategy logic."""
        # Mock day trading evaluation
        confidence = 0.65
        
        return {
            "decision": "execute_trade",
            "confidence": confidence,
            "reasoning": "Day trading strategy sees favorable conditions",
            "trade_params": {
                "entry_price": opportunity.initial_signal.entry_price_target,
                "stop_loss": opportunity.initial_signal.stop_loss_target,
                "take_profit": opportunity.initial_signal.take_profit_target,
                "position_size_percentage": 3.0,
            },
        }
    
    def _evaluate_arbitrage_strategy(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
    ) -> Dict[str, Any]:
        """Evaluate opportunity using arbitrage strategy logic."""
        # Mock arbitrage evaluation
        confidence = 0.8
        
        return {
            "decision": "execute_trade",
            "confidence": confidence,
            "reasoning": "Arbitrage opportunity identified with acceptable spread",
            "trade_params": {
                "entry_price": opportunity.initial_signal.entry_price_target,
                "position_size_percentage": 5.0,
            },
        }
    
    def _evaluate_default_strategy(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
    ) -> Dict[str, Any]:
        """Default evaluation for unknown strategy types."""
        return {
            "decision": "requires_investigation",
            "confidence": 0.5,
            "reasoning": f"Strategy type {strategy.base_strategy_type} requires manual evaluation",
            "warnings": ["Unknown strategy type - manual review required"],
        }
    
    def _make_decision_from_ai_analysis(
        self,
        ai_result: AIAnalysisResult,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
        confidence_threshold: float,
    ) -> TradingDecision:
        """Make trading decision based on AI analysis results.
        
        Args:
            ai_result: AI analysis results.
            opportunity: The opportunity being evaluated.
            strategy: The trading strategy.
            mode: Trading mode.
            confidence_threshold: Confidence threshold for the mode.
            
        Returns:
            TradingDecision based on AI analysis.
        """
        # Check confidence against threshold
        if ai_result.calculated_confidence < confidence_threshold:
            decision = "reject_opportunity"
            reasoning = (
                f"AI confidence {ai_result.calculated_confidence:.2f} below threshold "
                f"{confidence_threshold:.2f} for {mode} mode"
            )
        elif ai_result.suggested_action in [SuggestedAction.STRONG_BUY, SuggestedAction.BUY]:
            decision = "execute_trade"
            reasoning = f"AI recommends {ai_result.suggested_action} with confidence {ai_result.calculated_confidence:.2f}"
        elif ai_result.suggested_action == SuggestedAction.FURTHER_INVESTIGATION_NEEDED:
            decision = "requires_investigation"
            reasoning = f"AI recommends further investigation: {ai_result.reasoning_ai}"
        else:
            decision = "reject_opportunity"
            reasoning = f"AI recommends {ai_result.suggested_action}: {ai_result.reasoning_ai}"
        
        return TradingDecision(
            decision=decision,
            confidence=ai_result.calculated_confidence,
            reasoning=reasoning,
            opportunity_id=str(opportunity.id) if opportunity.id is not None else "UNKNOWN_OPPORTUNITY_ID",
            strategy_id=str(strategy.id) if strategy.id is not None else "UNKNOWN_STRATEGY_ID",
            ai_analysis_used=True,
            ai_analysis_profile_id=strategy.ai_analysis_profile_id,
            recommended_trade_params=ai_result.recommended_trade_params,
            warnings=ai_result.ai_warnings,
        )
    
    def _convert_opportunity_to_data(self, opportunity: Opportunity) -> OpportunityData:
        """Convert Opportunity model to OpportunityData for AI analysis.
        
        Args:
            opportunity: The opportunity model.
            
        Returns:
            OpportunityData for AI analysis.
        """
        initial_signal_data: Dict[str, Any]

        if opportunity.initial_signal is None:
            logger.warning(f"Initial signal is None for opportunity {opportunity.id}. Using empty dict.")
            initial_signal_data = {}
        elif isinstance(opportunity.initial_signal, dict):
            initial_signal_data = opportunity.initial_signal
        elif hasattr(opportunity.initial_signal, 'model_dump'):  # Pydantic v2+
            initial_signal_data = opportunity.initial_signal.model_dump()
        elif hasattr(opportunity.initial_signal, 'dict'):  # Pydantic v1
            initial_signal_data = opportunity.initial_signal.dict()
        else:
            try:
                # Intento de conversión genérica si no es Pydantic ni dict
                initial_signal_data = dict(opportunity.initial_signal)
                logger.warning(f"Initial_signal for opportunity {opportunity.id} was converted to dict using generic dict(). Type was {type(opportunity.initial_signal)}")
            except (TypeError, ValueError) as e:
                logger.error(f"Could not convert initial_signal to dict for opportunity {opportunity.id}. Type: {type(opportunity.initial_signal)}. Error: {e}")
                initial_signal_data = {}  # Fallback a dict vacío

        return OpportunityData(
            opportunity_id=str(opportunity.id) if opportunity.id is not None else "UNKNOWN_OPPORTUNITY_ID", # Usar un ID por defecto más descriptivo
            symbol=opportunity.symbol,
            initial_signal=initial_signal_data, # Esto debe ser un Dict[str, Any]
            source_type=opportunity.source_type.value if opportunity.source_type else "UNKNOWN", # Manejar Optional
            source_name=opportunity.source_name if opportunity.source_name else "UNKNOWN", # Manejar Optional
            source_data=opportunity.source_data if opportunity.source_data else {}, # Manejar Optional
            detected_at=opportunity.detected_at,
        )
    
    async def _update_opportunity_with_ai_analysis(
        self,
        opportunity: Opportunity,
        ai_result: AIAnalysisResult,
    ) -> None:
        """Update opportunity with AI analysis results.
        
        Args:
            opportunity: The opportunity to update.
            ai_result: AI analysis results.
        """
        # Convert AI result to AIAnalysis model
        # Asegurarse que los tipos coinciden con el modelo AIAnalysis
        
        # Convertir suggested_action a Enum si es string
        action_enum = ai_result.suggested_action
        if isinstance(action_enum, str):
            try:
                action_enum = SuggestedAction(action_enum)
            except ValueError:
                logger.error(f"Invalid suggested_action string: {ai_result.suggested_action}. Cannot convert to Enum.")
                # Manejar el error, por ejemplo, usando un valor por defecto o levantando una excepción
                action_enum = SuggestedAction.FURTHER_INVESTIGATION_NEEDED # O alguna otra acción por defecto

        # Asegurar que recommended_trade_params y data_verification son instancias de sus modelos o None
        
        parsed_rec_params: Optional[RecommendedTradeParams] = None
        if isinstance(ai_result.recommended_trade_params, RecommendedTradeParams):
            parsed_rec_params = ai_result.recommended_trade_params
        elif isinstance(ai_result.recommended_trade_params, dict):
            try:
                parsed_rec_params = RecommendedTradeParams(**ai_result.recommended_trade_params)
            except Exception as e_rec:
                logger.warning(f"Could not parse recommended_trade_params dict into model: {e_rec}. Params: {ai_result.recommended_trade_params}")
        elif ai_result.recommended_trade_params is not None:
            logger.warning(f"recommended_trade_params is not a dict, None, or RecommendedTradeParams instance. Type: {type(ai_result.recommended_trade_params)}. Setting to None.")

        parsed_data_ver: Optional[DataVerification] = None
        if isinstance(ai_result.data_verification, DataVerification):
            parsed_data_ver = ai_result.data_verification
        elif isinstance(ai_result.data_verification, dict):
            try:
                parsed_data_ver = DataVerification(**ai_result.data_verification)
            except Exception as e_data:
                logger.warning(f"Could not parse data_verification dict into model: {e_data}. Data: {ai_result.data_verification}")
        elif ai_result.data_verification is not None:
            logger.warning(f"data_verification is not a dict, None, or DataVerification instance. Type: {type(ai_result.data_verification)}. Setting to None.")
            
        ai_analysis = AIAnalysis(
            analysis_id=ai_result.analysis_id, # str
            analyzed_at=ai_result.analyzed_at, # datetime
            model_used=ai_result.model_used, # Optional[str]
            calculated_confidence=ai_result.calculated_confidence, # float
            suggested_action=action_enum, # SuggestedAction (Enum)
            recommended_trade_strategy_type=ai_result.recommended_trade_strategy_type, # Optional[str]
            recommended_trade_params=parsed_rec_params, # Optional[RecommendedTradeParams]
            reasoning_ai=ai_result.reasoning_ai, # str
            data_verification=parsed_data_ver, # Optional[DataVerification]
            processing_time_ms=ai_result.processing_time_ms, # Optional[int]
            ai_warnings=ai_result.ai_warnings, # Optional[List[str]]
        )
        
        # Update opportunity
        opportunity.ai_analysis = ai_analysis
        opportunity.status = OpportunityStatus.ANALYSIS_COMPLETE
        opportunity.updated_at = datetime.now(timezone.utc)
    
    def _get_confidence_threshold_for_mode(
        self,
        confidence_thresholds: Optional[ConfidenceThresholds],
        mode: str,
    ) -> float:
        """Get confidence threshold for specific trading mode.
        
        Args:
            confidence_thresholds: Confidence thresholds configuration.
            mode: Trading mode ("paper" or "real").
            
        Returns:
            Confidence threshold value.
        """
        if confidence_thresholds:
            if mode == "paper" and confidence_thresholds.paper_trading:
                return confidence_thresholds.paper_trading
            elif mode == "real" and confidence_thresholds.real_trading:
                return confidence_thresholds.real_trading
        
        # Default thresholds
        return 0.6 if mode == "paper" else 0.8
    
    async def get_trading_decisions_for_user(
        self,
        user_id: str,
        mode: str = "paper",
        limit: int = 10,
    ) -> List[TradingDecision]:
        """Get recent trading decisions for a user.
        
        Args:
            user_id: The user identifier.
            mode: Trading mode filter.
            limit: Maximum number of decisions to return.
            
        Returns:
            List of recent trading decisions.
        """
        # TODO: Implement persistence and retrieval of trading decisions
        # For now, return empty list
        return []
    
    async def log_trading_decision(self, decision: TradingDecision) -> None:
        """Log a trading decision for auditing and analysis.
        
        Args:
            decision: The trading decision to log.
        """
        logger.info(
            f"Trading Decision {decision.decision_id}: {decision.decision} for opportunity "
            f"{decision.opportunity_id} with strategy {decision.strategy_id}. "
            f"Confidence: {decision.confidence:.2f}, AI used: {decision.ai_analysis_used}"
        )
        
        if decision.ai_analysis_used and decision.ai_analysis_profile_id:
            logger.info(
                f"AI Analysis Profile used: {decision.ai_analysis_profile_id}"
            )
        
        if decision.warnings:
            logger.warning(
                f"Decision warnings for {decision.decision_id}: {'; '.join(decision.warnings)}"
            )
    
    async def process_opportunity_with_active_strategies(
        self,
        opportunity: Opportunity,
        user_id: str,
        mode: str = "paper",  # "paper" or "real"
    ) -> List[TradingDecision]:
        """Process an opportunity using only active and applicable strategies.
        
        This is the main method implementing Story 5.4 - it ensures that only
        active strategies are considered for opportunity evaluation.
        
        Args:
            opportunity: The opportunity to process.
            user_id: The user identifier.
            mode: Trading mode ("paper" or "real").
            
        Returns:
            List of trading decisions from applicable active strategies.
            
        Raises:
            HTTPException: If processing fails.
        """
        try:
            logger.info(
                f"Processing opportunity {opportunity.id} for user {user_id} in {mode} mode"
            )
            
            # AC1: Query active strategies before processing any opportunity
            active_strategies = await self.strategy_service.get_active_strategies(user_id, mode)
            
            if not active_strategies:
                logger.info(f"No active {mode} strategies found for user {user_id}")
                await self._update_opportunity_status(
                    opportunity, 
                    OpportunityStatus.REJECTED_BY_AI,
                    "no_active_strategies",
                    f"No active strategies configured for {mode} mode"
                )
                return []
            
            logger.info(f"Found {len(active_strategies)} active {mode} strategies")
            
            # AC2: Filter and determine applicable strategies
            applicable_strategies = await self._filter_applicable_strategies(
                opportunity, active_strategies
            )
            
            if not applicable_strategies:
                logger.info(f"No applicable strategies found for opportunity {opportunity.id}")
                await self._update_opportunity_status(
                    opportunity,
                    OpportunityStatus.REJECTED_BY_AI,
                    "no_applicable_strategies",
                    "No active strategies are applicable to this opportunity"
                )
                return []
            
            logger.info(f"Found {len(applicable_strategies)} applicable strategies")
            
            # AC3: Process opportunity with each applicable strategy
            trading_decisions = []
            for strategy in applicable_strategies:
                try:
                    logger.info(f"Processing opportunity with strategy {strategy.config_name}")
                    
                    decision = await self.evaluate_opportunity_with_strategy(
                        opportunity, strategy, mode
                    )
                    
                    trading_decisions.append(decision)
                    
                    # Log the trading decision for auditing
                    await self.log_trading_decision(decision)
                    
                except Exception as e:
                    logger.error(f"Error processing strategy {strategy.id}: {e}")
                    # Continue with other strategies even if one fails
                    continue
            
            # AC4: Consolidate decisions and determine execution
            execution_results = await self._consolidate_and_execute_decisions(
                trading_decisions, opportunity, mode, user_id
            )
            
            logger.info(
                f"Completed processing opportunity {opportunity.id}. "
                f"Generated {len(trading_decisions)} decisions, "
                f"executed {len(execution_results)} trades"
            )
            
            return trading_decisions
            
        except Exception as e:
            logger.error(f"Error processing opportunity {opportunity.id}: {e}")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.ERROR_IN_PROCESSING,
                "processing_error",
                f"Error during processing: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process opportunity: {str(e)}"
            )
    
    async def _filter_applicable_strategies(
        self,
        opportunity: Opportunity,
        strategies: List[TradingStrategyConfig],
    ) -> List[TradingStrategyConfig]:
        """Filter strategies to find those applicable to the opportunity.
        
        Args:
            opportunity: The opportunity to evaluate.
            strategies: List of active strategies to filter.
            
        Returns:
            List of strategies applicable to the opportunity.
        """
        applicable_strategies = []
        
        for strategy in strategies:
            try:
                is_applicable = await self._is_strategy_applicable_to_opportunity(
                    opportunity, strategy
                )
                
                if is_applicable:
                    applicable_strategies.append(strategy)
                    logger.debug(f"Strategy {strategy.config_name} is applicable to {opportunity.symbol}")
                else:
                    logger.debug(f"Strategy {strategy.config_name} is not applicable to {opportunity.symbol}")
                    
            except Exception as e:
                logger.warning(f"Error evaluating applicability of strategy {strategy.id}: {e}")
                continue
        
        return applicable_strategies
    
    async def _is_strategy_applicable_to_opportunity(
        self,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
    ) -> bool:
        """Check if a strategy is applicable to an opportunity.
        
        Args:
            opportunity: The opportunity to check.
            strategy: The strategy to evaluate.
            
        Returns:
            True if strategy is applicable, False otherwise.
        """
        # If no applicability rules defined, strategy applies to all opportunities
        if not strategy.applicability_rules:
            logger.debug(f"Strategy {strategy.config_name} has no applicability rules - applies to all")
            return True
        
        rules = strategy.applicability_rules
        
        # Check explicit pairs
        if hasattr(rules, 'explicit_pairs') and rules.explicit_pairs:
            if opportunity.symbol not in rules.explicit_pairs:
                logger.debug(f"Symbol {opportunity.symbol} not in explicit pairs for {strategy.config_name}")
                return False
        
        # Check include all spot (if pair is spot)
        if hasattr(rules, 'include_all_spot') and rules.include_all_spot:
            # For now, assume all symbols are spot (future enhancement: detect futures/options)
            logger.debug(f"Strategy {strategy.config_name} includes all spot pairs")
            return True
        
        # Check dynamic filters if defined
        if hasattr(rules, 'dynamic_filter') and rules.dynamic_filter:
            # For v1.0, implement basic dynamic filtering
            # Future enhancement: integrate with market data service for real-time filtering
            logger.debug(f"Dynamic filtering not fully implemented for strategy {strategy.config_name}")
            return True
        
        # If we get here and explicit_pairs was defined but didn't match, reject
        if hasattr(rules, 'explicit_pairs') and rules.explicit_pairs:
            return False
        
        # Default: strategy is applicable
        return True
    
    async def _consolidate_and_execute_decisions(
        self,
        trading_decisions: List[TradingDecision],
        opportunity: Opportunity,
        mode: str,
        user_id: str,
    ) -> List[Trade]:
        """Consolidate trading decisions and execute approved trades.
        
        Args:
            trading_decisions: List of decisions from applicable strategies.
            opportunity: The opportunity being processed.
            mode: Trading mode ("paper" or "real").
            user_id: The user identifier.
            
        Returns:
            List of executed trades.
        """
        executed_trades = []
        
        # Filter decisions that recommend execution
        execution_decisions = [
            decision for decision in trading_decisions 
            if decision.decision == "execute_trade"
        ]
        
        if not execution_decisions:
            logger.info(f"No strategies recommended execution for opportunity {opportunity.id}")
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "no_execution_signals",
                "No active strategies generated execution signals"
            )
            return []
        
        # AC4: Check confidence thresholds and execute trades
        for decision in execution_decisions:
            try:
                # Get the strategy that made this decision
                strategy = await self.strategy_service.get_strategy_config(
                    decision.strategy_id, user_id
                )
                
                if not strategy:
                    logger.warning(f"Strategy {decision.strategy_id} not found")
                    continue
                
                # Check confidence threshold
                confidence_thresholds = await self.strategy_service.get_effective_confidence_thresholds_for_strategy(strategy)
                threshold = self._get_confidence_threshold_for_mode(confidence_thresholds, mode)
                
                if decision.confidence < threshold:
                    logger.info(
                        f"Decision {decision.decision_id} confidence {decision.confidence:.3f} "
                        f"below threshold {threshold:.3f} for {mode} mode"
                    )
                    continue
                
                # AC4.3: Execute based on mode
                trade = await self._execute_decision_by_mode(
                    decision, opportunity, strategy, mode, user_id
                )
                
                if trade:
                    executed_trades.append(trade)
                    
            except Exception as e:
                logger.error(f"Error executing decision {decision.decision_id}: {e}")
                continue
        
        # Update opportunity status based on execution results
        if executed_trades:
            if mode == "paper":
                await self._update_opportunity_status(
                    opportunity,
                    OpportunityStatus.CONVERTED_TO_TRADE_PAPER,
                    "trades_executed",
                    f"Executed {len(executed_trades)} paper trades"
                )
            else:
                await self._update_opportunity_status(
                    opportunity,
                    OpportunityStatus.CONVERTED_TO_TRADE_REAL,
                    "trades_executed", 
                    f"Executed {len(executed_trades)} real trades"
                )
        else:
            await self._update_opportunity_status(
                opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "confidence_too_low",
                "All strategy decisions below confidence threshold"
            )
        
        return executed_trades
    
    async def _execute_decision_by_mode(
        self,
        decision: TradingDecision,
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
        mode: str,
        user_id: str,
    ) -> Optional[Trade]:
        """Execute a trading decision based on the mode (paper or real).
        
        Args:
            decision: The trading decision to execute.
            opportunity: The opportunity being processed.
            strategy: The strategy that generated the decision.
            mode: Trading mode ("paper" or "real").
            user_id: The user identifier.
            
        Returns:
            Created Trade if executed, None otherwise.
        """
        if mode == "paper":
            # Paper trading: Create trade directly
            trade = await self.create_trade_from_decision(decision, opportunity, strategy)
            if trade:
                logger.info(f"Created paper trade {trade.id} from decision {decision.decision_id}")
            return trade
        
        else:  # mode == "real"
            # Real trading: Check if user confirmation is required
            user_config = await self.configuration_service.get_user_configuration(user_id)
            requires_confirmation = self._requires_user_confirmation_for_real_trade(user_config)
            
            if requires_confirmation:
                # Update opportunity to pending confirmation
                await self._update_opportunity_status(
                    opportunity,
                    OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
                    "awaiting_user_confirmation",
                    f"Real trade requires user confirmation for strategy {strategy.config_name}"
                )
                
                # TODO: Notify UI about pending confirmation
                logger.info(f"Real trade requires user confirmation for opportunity {opportunity.id}")
                return None
            
            else:
                # Execute real trade directly
                trade = await self.create_trade_from_decision(decision, opportunity, strategy)
                if trade:
                    # TODO: Send to OrderExecutionService for real execution
                    logger.info(f"Created real trade {trade.id} from decision {decision.decision_id}")
                return trade
    
    def _requires_user_confirmation_for_real_trade(self, user_config) -> bool:
        """Check if user confirmation is required for real trades.
        
        Args:
            user_config: User configuration object.
            
        Returns:
            True if confirmation is required, False otherwise.
        """
        if not user_config or not hasattr(user_config, 'real_trading_settings'):
            return True  # Default to requiring confirmation
        
        real_settings = user_config.real_trading_settings
        if not real_settings:
            return True
        
        # For v1.0, always require confirmation for safety
        # Future enhancement: make this configurable
        return True
    
    async def _update_opportunity_status(
        self,
        opportunity: Opportunity,
        status: OpportunityStatus,
        reason_code: str,
        reason_text: str,
    ) -> None:
        """Update opportunity status with reason.
        
        Args:
            opportunity: The opportunity to update.
            status: New status.
            reason_code: Reason code for the status change.
            reason_text: Human-readable reason for the status change.
        """
        opportunity.status = status
        opportunity.status_reason_code = reason_code
        opportunity.status_reason_text = reason_text
        opportunity.updated_at = datetime.now(timezone.utc)
        
        logger.info(
            f"Updated opportunity {opportunity.id} status to {status.value}: {reason_text}"
        )
        
        try:
            await self.persistence_service.update_opportunity_status(
                opportunity_id=opportunity.id,
                user_id=opportunity.user_id, # Asumiendo que opportunity.user_id está disponible y es correcto
                new_status=status,
                status_reason=reason_text 
            )
            logger.info(f"Persisted status update for opportunity {opportunity.id}")
        except Exception as e_persist:
            logger.error(f"Failed to persist status update for opportunity {opportunity.id}: {e_persist}", exc_info=True)
            # Considerar cómo manejar este error. ¿Reintentar? ¿Marcar la oportunidad de alguna manera?

    async def create_trade_from_decision(
        self, 
        decision: TradingDecision, 
        opportunity: Opportunity,
        strategy: TradingStrategyConfig,
    ) -> Optional[Trade]:
        """Create a trade from a trading decision.
        
        Args:
            decision: The trading decision.
            opportunity: The opportunity that generated the decision.
            strategy: The strategy used for the decision.
            
        Returns:
            Created Trade if decision is to execute trade, None otherwise.
        """
        if decision.decision != "execute_trade":
            logger.info(f"Decision {decision.decision_id} is not to execute trade: {decision.decision}")
            return None
        
        try:
            # Determine trade side from opportunity signal
            trade_side = self._determine_trade_side_from_opportunity(opportunity)
            
            # Determine trade mode from decision context or default to paper
            trade_mode = getattr(decision, 'mode', 'paper')
            
            # Create basic trade structure
            
            # Convertir trade_mode y trade_side a sus respectivos Enums
            # from src.ultibot_backend.core.domain_models.trade_models import TradeMode, TradeSide # Ya importados arriba
            
            try:
                actual_trade_mode = TradeMode(trade_mode)
            except ValueError:
                logger.error(f"Invalid trade_mode value: {trade_mode}. Defaulting to PAPER.")
                actual_trade_mode = TradeMode.PAPER

            try:
                actual_trade_side = TradeSide(trade_side)
            except ValueError:
                logger.error(f"Invalid trade_side value: {trade_side}. Cannot create trade.")
                return None # O lanzar una excepción más específica

            # Manejo seguro de take_profit_price
            tp_price = None
            if decision.recommended_trade_params:
                tp_value = decision.recommended_trade_params.get("take_profit")
                if isinstance(tp_value, list) and len(tp_value) > 0:
                    tp_price = tp_value[0]
                elif isinstance(tp_value, (float, int)): # Si es un solo valor
                    tp_price = float(tp_value)
                # Asegurar que tp_price es float o None
                if tp_price is not None and not isinstance(tp_price, (float, int)):
                    logger.warning(f"take_profit_price is not float or int: {tp_price}. Setting to None.")
                    tp_price = None


            trade = Trade(
                id=str(UUID().hex),
                user_id=str(strategy.user_id),
                mode=actual_trade_mode,
                symbol=opportunity.symbol,
                side=actual_trade_side,
                strategy_id=str(strategy.id) if strategy.id else "UNKNOWN_STRATEGY_ID",
                opportunity_id=str(opportunity.id) if opportunity.id else "UNKNOWN_OPPORTUNITY_ID",
                position_status=PositionStatus.PENDING_ENTRY_CONDITIONS,
                entry_order=self._create_entry_order_from_decision(decision, opportunity),
                ai_analysis_confidence=decision.confidence if decision.ai_analysis_used else None,
                strategy_execution_instance_id=None,
                exit_orders=None,
                initial_risk_quote_amount=None,
                initial_reward_to_risk_ratio=None,
                risk_reward_adjustments=None,
                current_risk_quote_amount=None,
                current_reward_to_risk_ratio=None,
                pnl=None,
                pnl_percentage=None,
                closing_reason=None,
                stop_loss_price=decision.recommended_trade_params.get("stop_loss") if decision.recommended_trade_params else None,
                take_profit_price=tp_price,
                exit_order_oco_id=None,
                exit_price=None,
                market_context_snapshots=None,
                external_event_or_analysis_link=None,
                backtest_details=None,
                ai_influence_details=None,  # Se añade después a través de add_ai_influence_to_trade
                notes=f"Trade created from strategy '{strategy.config_name}' (ID: {str(strategy.id) if strategy.id else 'UNKNOWN_STRATEGY_ID'}) via decision {decision.decision_id}. {decision.reasoning}",
                created_at=datetime.now(timezone.utc),
                opened_at=None,
                closed_at=None,
                updated_at=datetime.now(timezone.utc)
            )
            
            # Add AI influence details if AI was used
            if decision.ai_analysis_used and decision.ai_analysis_profile_id:
                await self._add_ai_influence_to_trade(trade, decision, opportunity)
            
            # Log trade creation with AI influence information
            logger.info(f"Created trade {trade.id} from decision {decision.decision_id}")
            logger.info(trade.get_trade_summary_for_logging())

            # Persistir el trade inicial antes de intentar ejecutar órdenes
            try:
                await self.persistence_service.save_trade(trade) # Asumiendo que existe save_trade
                logger.info(f"Trade {trade.id} inicial guardado antes de la ejecución.")
            except Exception as e_persist:
                logger.error(f"Error al guardar trade inicial {trade.id} antes de la ejecución: {e_persist}", exc_info=True)
                # Podríamos decidir no continuar si no se puede persistir el trade inicial.
                # Por ahora, se loguea y se intenta continuar con la ejecución.
                # Considerar lanzar una excepción aquí si la persistencia inicial es crítica.

            # Intentar ejecutar la orden de entrada y potencialmente OCO
            if trade.mode == TradeMode.REAL: # Solo para trades reales por ahora
                try:
                    logger.info(f"Attempting to place entry order for real trade {trade.id}")
                    # Aquí se debería llamar a UnifiedOrderExecutionService para colocar la orden de entrada
                    # y si la estrategia lo requiere, la orden OCO.
                    # Esta parte necesita una implementación más detallada de cómo se colocan las OCOs.
                    # Por ahora, simularemos un intento y un posible fallo para la Tarea 1.4.2.

                    # Ejemplo de cómo se podría intentar colocar una OCO (requiere que OrderExecutionService/BinanceAdapter lo soporten)
                    # if strategy.requires_oco_exit: # Suponiendo que la estrategia tiene esta info
                    #     oco_details = await self.unified_order_execution_service.create_oco_order_for_trade(trade, user_id=UUID(trade.user_id))
                    #     trade.exit_order_oco_id = oco_details.get("listClientOrderId") # o el campo correspondiente
                    # else:
                    #     # Colocar solo la orden de entrada
                    #     executed_entry_order = await self.unified_order_execution_service.execute_order(
                    #         order_details=trade.entry_order,
                    #         user_id=UUID(trade.user_id),
                    #         trading_mode=trade.mode,
                    #         symbol=trade.symbol,
                    #         side=trade.side.value, # Asegurar que es string 'buy' o 'sell'
                    #         # api_key y api_secret se obtendrían de CredentialService
                    #     )
                    #     trade.entry_order = executed_entry_order # Actualizar con detalles de ejecución
                    
                    # SIMULACIÓN DE FALLO OCO para Tarea 1.4.2 - ESTO DEBERÍA SER REAL
                    # En un flujo real, la excepción vendría de unified_order_execution_service o binance_adapter
                    if opportunity.symbol == "FAIL_OCO_SYMBOL_TEST": # Condición de prueba para simular fallo
                        raise BinanceAPIError(message="Simulated OCO placement failure for test.", status_code=400, response_data={"code": -2010, "msg": "OCO order placement failed due to margin."})

                    # Si la ejecución fue exitosa (simulado por ahora, no hay fallo)
                    trade.position_status = PositionStatus.OPEN # O PENDING_EXECUTION si la orden no es market o no se llena de inmediato
                    trade.opened_at = datetime.now(timezone.utc)
                    logger.info(f"Real trade {trade.id} entry order placed/simulated successfully.")

                except BinanceAPIError as e_oco: # Capturar específicamente el error de la API de Binance
                    logger.error(f"CRITICAL: Failed to place OCO or entry order for real trade {trade.id} for symbol {trade.symbol}. Error: {e_oco.message}", exc_info=True)
                    trade.notes = (trade.notes or "") + f" | CRITICAL: OCO/Entry order placement failed: {e_oco.message}. Manual intervention required."
                    trade.position_status = PositionStatus.ERROR # Usar estado de error genérico
                    
                    # Enviar notificación de error crítico
                    await self.notification_service.send_real_trade_status_notification(
                        user_id=UUID(trade.user_id),
                        message=f"Fallo CRÍTICO al colocar orden OCO/entrada para {trade.symbol} (Trade ID: {trade.id}). Se requiere intervención manual. Error: {e_oco.message}",
                        status_level="CRITICAL",
                        symbol=trade.symbol,
                        trade_id=UUID(trade.id)
                    )
                except Exception as e_exec: # Capturar otros errores de ejecución
                    logger.error(f"CRITICAL: Unexpected error during order execution for real trade {trade.id} for symbol {trade.symbol}. Error: {e_exec}", exc_info=True)
                    trade.notes = (trade.notes or "") + f" | CRITICAL: Unexpected error during order execution: {str(e_exec)}. Manual intervention required."
                    trade.position_status = PositionStatus.ERROR # Usar estado de error genérico
                    
                    await self.notification_service.send_real_trade_status_notification(
                        user_id=UUID(trade.user_id),
                        message=f"Fallo CRÍTICO inesperado durante ejecución de orden para {trade.symbol} (Trade ID: {trade.id}). Se requiere intervención manual. Error: {str(e_exec)}",
                        status_level="CRITICAL",
                        symbol=trade.symbol,
                        trade_id=UUID(trade.id)
                    )
                finally:
                    # Siempre persistir el estado final del trade después del intento de ejecución
                    try:
                        await self.persistence_service.save_trade(trade)
                        logger.info(f"Trade {trade.id} estado final ({trade.position_status.value}) guardado después del intento de ejecución.")
                    except Exception as e_persist_final:
                        logger.error(f"Error al guardar estado final del trade {trade.id}: {e_persist_final}", exc_info=True)
                        # Aquí podría ser necesario un mecanismo de alerta adicional si la persistencia falla críticamente.
            
            return trade
            
        except Exception as e: # Captura de errores en la creación del objeto Trade en sí
            logger.error(f"Error creating trade object from decision {decision.decision_id}: {e}", exc_info=True)
            # No se puede enviar notificación sobre un trade_id si el objeto trade no se pudo crear.
            # Se podría enviar una notificación genérica si es relevante.
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create trade object: {str(e)}"
            )
    
    async def _add_ai_influence_to_trade(
        self, 
        trade: Trade, 
        decision: TradingDecision,
        opportunity: Opportunity,
    ) -> None:
        """Add AI influence details to a trade.
        
        Args:
            trade: The trade to add AI influence to.
            decision: The trading decision with AI information.
            opportunity: The opportunity with AI analysis.
        """
        if not decision.ai_analysis_used or not decision.ai_analysis_profile_id:
            return
        
        ai_analysis = opportunity.ai_analysis
        if not ai_analysis:
            logger.warning(f"Decision {decision.decision_id} claims AI analysis used but opportunity {opportunity.id} has no AI analysis")
            return
        
        # Add detailed AI influence information
        trade.add_ai_influence_details(
            ai_analysis_profile_id=decision.ai_analysis_profile_id,
            ai_confidence=decision.confidence,
            ai_suggested_action=ai_analysis.suggested_action.value,
            ai_reasoning_summary=ai_analysis.reasoning_ai[:500],  # Truncate for storage
            ai_model_used=ai_analysis.model_used,
            ai_processing_time_ms=ai_analysis.processing_time_ms,
            ai_warnings=ai_analysis.ai_warnings,
        )
        
        # Update trade notes with AI information
        ai_note = (
            f" | AI Analysis: {ai_analysis.suggested_action} with {decision.confidence:.2f} confidence "
            f"using profile {decision.ai_analysis_profile_id}"
        )
        trade.notes = (trade.notes or "") + ai_note
        
        # Log detailed AI influence
        logger.info(
            f"Trade {trade.id} influenced by AI: "
            f"Profile={decision.ai_analysis_profile_id}, "
            f"Confidence={decision.confidence:.3f}, "
            f"Action={ai_analysis.suggested_action}, "
            f"Model={ai_analysis.model_used}"
        )
        
        if ai_analysis.ai_warnings:
            logger.warning(
                f"Trade {trade.id} AI warnings: {'; '.join(ai_analysis.ai_warnings)}"
            )
    
    def _create_entry_order_from_decision(
        self, 
        decision: TradingDecision,
        opportunity: Opportunity,
    ) -> 'TradeOrderDetails':
        """Create entry order details from trading decision.
        
        Args:
            decision: The trading decision.
            opportunity: The opportunity.
            
        Returns:
            TradeOrderDetails for the entry order.
        """
        # Import here to avoid circular imports
        from src.ultibot_backend.core.domain_models.trade_models import (
            TradeOrderDetails, 
            OrderType, 
            OrderStatus
        )
        
        # Use recommended trade params if available, otherwise use opportunity signal
        if decision.recommended_trade_params:
            entry_price = decision.recommended_trade_params.get("entry_price")
            # Aquí también se debería obtener la cantidad de los parámetros recomendados si es posible
            requested_quantity = decision.recommended_trade_params.get("position_size_percentage", 1.0) # Ejemplo, ajustar
        else:
            entry_price = opportunity.initial_signal.entry_price_target
            requested_quantity = 1.0 # Default quantity
        
        # Asegurar que todos los campos requeridos por TradeOrderDetails se proveen
        # y que los tipos son correctos.
        
        # Convertir entry_price a float si no es None, de lo contrario, None.
        actual_entry_price: Optional[float] = None
        if entry_price is not None:
            try:
                actual_entry_price = float(entry_price)
            except (ValueError, TypeError):
                logger.warning(f"Could not convert entry_price '{entry_price}' to float. Setting to None.")
        
        # Asegurar que requested_quantity es float.
        actual_requested_quantity: float
        try:
            actual_requested_quantity = float(requested_quantity)
        except (ValueError, TypeError):
            logger.error(f"Could not convert requested_quantity '{requested_quantity}' to float. Defaulting to 1.0.")
            actual_requested_quantity = 1.0


        return TradeOrderDetails(
            order_id_internal=str(UUID().hex),
            type=OrderType.MARKET, # Asumiendo MARKET para la entrada inicial basada en decisión
            status=OrderStatus.NEW,
            requested_price=actual_entry_price, # Puede ser None para MARKET, pero lo pasamos si está disponible
            requested_quantity=actual_requested_quantity,
            timestamp=datetime.now(timezone.utc),
            # Todos los demás campos son Optional y Pydantic los manejará con sus defaults (None)
            # si no se proveen explícitamente.
            order_id_exchange=None,
            client_order_id_exchange=None,
            exchange_status_raw=None,
            rejection_reason_code=None,
            rejection_reason_message=None,
            stop_price=None,
            executed_price=None,
            slippage_amount=None,
            slippage_percentage=None,
            executed_quantity=None,
            cumulative_quote_qty=None,
            commissions=None,
            submitted_at=None,
            last_update_timestamp=None,
            fill_timestamp=None,
            trailing_stop_activation_price=None,
            trailing_stop_callback_rate=None,
            current_stop_price_tsl=None,
            oco_group_id_exchange=None
        )
    
    async def log_ai_invocation_details(
        self, 
        strategy: TradingStrategyConfig,
        opportunity: Opportunity,
        ai_config: AIStrategyConfiguration,
        ai_result: AIAnalysisResult,
    ) -> None:
        """Log detailed AI invocation information for auditing.
        
        Args:
            strategy: Strategy that invoked AI.
            opportunity: Opportunity being analyzed.
            ai_config: AI configuration used.
            ai_result: AI analysis results.
        """
        logger.info(
            f"AI Invocation Details: "
            f"Strategy={strategy.config_name} ({strategy.id}), "
            f"Opportunity={opportunity.id} ({opportunity.symbol}), "
            f"AI_Profile={ai_config.name} ({ai_config.id}), "
            f"User={strategy.user_id}"
        )
        
        # Log strategy parameters that influenced the AI prompt
        strategy_params_summary = self._summarize_strategy_params_for_logging(strategy)
        logger.info(f"Strategy Parameters for AI: {strategy_params_summary}")
        
        # Log opportunity signal that influenced the AI prompt  
        signal_summary = self._summarize_opportunity_signal_for_logging(opportunity)
        logger.info(f"Opportunity Signal for AI: {signal_summary}")
        
        # Log AI configuration details
        ai_config_summary = self._summarize_ai_config_for_logging(ai_config)
        logger.info(f"AI Configuration Used: {ai_config_summary}")
        
        # Log final AI response summary
        logger.info(
            f"AI Response Summary: "
            f"Confidence={ai_result.calculated_confidence:.3f}, "
            f"Action={ai_result.suggested_action}, "
            f"Processing_Time={ai_result.processing_time_ms}ms, "
            f"Model={ai_result.model_used}"
        )
    
    def _summarize_strategy_params_for_logging(self, strategy: TradingStrategyConfig) -> str:
        """Summarize strategy parameters for logging."""
        params_to_log: Dict[str, Any] = {}
        
        if isinstance(strategy.parameters, dict):
            # If parameters is already a dict, use it directly
            params_dict = strategy.parameters
        elif hasattr(strategy.parameters, 'model_dump'): # Pydantic v2+
            params_dict = strategy.parameters.model_dump()
        elif hasattr(strategy.parameters, 'dict'): # Pydantic v1
            params_dict = strategy.parameters.dict()
        else:
            # Fallback if parameters is not a dict or Pydantic model
            logger.warning(f"Strategy parameters for {strategy.config_name} are not a dict or Pydantic model. Type: {type(strategy.parameters)}")
            return "Parameters not in expected format"

        if not params_dict:
            return "No parameters"
            
        # Log only key parameters to avoid verbosity
        for key, value in params_dict.items():
            if 'percentage' in key.lower() or 'price' in key.lower() or 'threshold' in key.lower():
                params_to_log[key] = value
            elif len(params_to_log) < 5:  # Limit to 5 key parameters
                params_to_log[key] = value
        
        if not params_to_log:
            return "No key parameters to log"
            
        return ", ".join([f"{k}={v}" for k, v in params_to_log.items()])
    
    def _summarize_opportunity_signal_for_logging(self, opportunity: Opportunity) -> str:
        """Summarize opportunity signal for logging."""
        signal = opportunity.initial_signal
        
        summary_parts = []
        if signal.direction_sought:
            summary_parts.append(f"direction={signal.direction_sought}")
        if signal.entry_price_target:
            summary_parts.append(f"entry={signal.entry_price_target}")
        if signal.confidence_source:
            summary_parts.append(f"source_confidence={signal.confidence_source:.2f}")
        if signal.timeframe:
            summary_parts.append(f"timeframe={signal.timeframe}")
        
        return ", ".join(summary_parts) if summary_parts else "No signal details"
    
    def _summarize_ai_config_for_logging(self, ai_config: AIStrategyConfiguration) -> str:
        """Summarize AI configuration for logging."""
        summary_parts = []
        summary_parts.append(f"name={ai_config.name}")
        
        if ai_config.tools_available_to_gemini:
            tools = ", ".join(ai_config.tools_available_to_gemini[:3])  # Limit to first 3 tools
            if len(ai_config.tools_available_to_gemini) > 3:
                tools += "..."
            summary_parts.append(f"tools=[{tools}]")
        
        if ai_config.confidence_thresholds:
            thresholds = ai_config.confidence_thresholds
            if thresholds.paper_trading or thresholds.real_trading:
                summary_parts.append(f"thresholds=paper:{thresholds.paper_trading},real:{thresholds.real_trading}")
        
        if ai_config.max_context_window_tokens:
            summary_parts.append(f"max_tokens={ai_config.max_context_window_tokens}")
        
        return ", ".join(summary_parts)
    
    def _determine_trade_side_from_opportunity(self, opportunity: Opportunity) -> str:
        """Determine trade side (buy/sell) from opportunity signal.
        
        Args:
            opportunity: The opportunity with initial signal.
            
        Returns:
            Trade side ("buy" or "sell").
        """
        if opportunity.initial_signal and hasattr(opportunity.initial_signal, 'direction_sought'):
            direction = opportunity.initial_signal.direction_sought
            if direction in ["buy", "long"]:
                return "buy"
            elif direction in ["sell", "short"]:
                return "sell"
        
        # Default to buy if direction not specified or unclear
        logger.warning(f"Could not determine trade side from opportunity {opportunity.id}, defaulting to 'buy'")
        return "buy"

    async def monitor_and_manage_real_trade_exit(
        self, 
        trade: Trade, 
        user_id: str
    ) -> None:
        """
        Monitors a real trade and executes a market order if TSL or TP is hit,
        especially for trades not managed by OCO orders.

        Args:
            trade: The trade object to monitor.
            user_id: The ID of the user owning the trade.
        """
        if trade.mode != "real" or trade.position_status != PositionStatus.OPEN: # Corregido a PositionStatus.OPEN
            logger.debug(f"Trade {trade.id} is not an active real trade (Status: {trade.position_status}). Skipping exit monitoring.")
            return

        # Asumimos que si no hay exit_order_oco_id, no está gestionado por OCO.
        # O podríamos añadir un flag explícito `is_oco_managed` al modelo Trade.
        is_oco_managed = bool(trade.exit_order_oco_id) 
        if is_oco_managed:
            logger.debug(f"Trade {trade.id} is OCO managed. Skipping manual exit monitoring.")
            return

        logger.info(f"Monitoring non-OCO real trade {trade.id} for TSL/TP.")

        try:
            current_price: float
            try:
                current_price = await self.market_data_service.get_latest_price(trade.symbol)
            except MarketDataError as e:
                logger.warning(f"Could not fetch current price for {trade.symbol} for trade {trade.id}: {e}")
                return
            
            logger.info(f"Trade {trade.id} ({trade.symbol}): Current Price = {current_price}, SL = {trade.stop_loss_price}, TP = {trade.take_profit_price}")

            exit_reason = None
            exit_price = None

            if trade.side == "buy": # Long position
                if trade.stop_loss_price and current_price <= trade.stop_loss_price:
                    exit_reason = "stop_loss_hit"
                    exit_price = trade.stop_loss_price
                    logger.info(f"Trade {trade.id}: Stop Loss triggered at {current_price} (SL: {trade.stop_loss_price}).")
                elif trade.take_profit_price and current_price >= trade.take_profit_price:
                    exit_reason = "take_profit_hit"
                    exit_price = trade.take_profit_price
                    logger.info(f"Trade {trade.id}: Take Profit triggered at {current_price} (TP: {trade.take_profit_price}).")
            
            elif trade.side == "sell": # Short position
                if trade.stop_loss_price and current_price >= trade.stop_loss_price:
                    exit_reason = "stop_loss_hit"
                    exit_price = trade.stop_loss_price
                    logger.info(f"Trade {trade.id}: Stop Loss triggered at {current_price} (SL: {trade.stop_loss_price}).")
                elif trade.take_profit_price and current_price <= trade.take_profit_price:
                    exit_reason = "take_profit_hit"
                    exit_price = trade.take_profit_price
                    logger.info(f"Trade {trade.id}: Take Profit triggered at {current_price} (TP: {trade.take_profit_price}).")

            if exit_reason:
                logger.info(f"Trade {trade.id}: {exit_reason}. Attempting to close position with market order.")
                
                # Determinar la cantidad a cerrar. Asumimos que es la cantidad abierta del trade.
                # El modelo Trade debería tener `open_quantity` o similar.
                # Por ahora, usaremos `entry_order.executed_quantity` si existe.
                quantity_to_close = trade.entry_order.executed_quantity if trade.entry_order and trade.entry_order.executed_quantity else None
                
                if not quantity_to_close:
                    logger.error(f"Cannot determine quantity to close for trade {trade.id}. Aborting market exit.")
                    # Podríamos actualizar el estado del trade a un estado de error aquí.
                    return

                exit_order_details = TradeOrderDetails(
                    order_id_internal=str(UUID().hex), # Usar UUID importado
                    type=OrderType.MARKET, # OrderType Enum
                    status=OrderStatus.NEW, # OrderStatus Enum
                    requested_quantity=quantity_to_close, # float
                    timestamp=datetime.now(timezone.utc), # datetime
                    # Campos opcionales con None por defecto si no se especifican
                    order_id_exchange=None, # Optional[str]
                    client_order_id_exchange=None, # Optional[str]
                    exchange_status_raw=None, # Optional[str]
                    rejection_reason_code=None, # Optional[str]
                    rejection_reason_message=None, # Optional[str]
                    requested_price=None, # Market order no tiene requested_price # Optional[float]
                    stop_price=None, # Optional[float]
                    executed_price=None, # Optional[float]
                    slippage_amount=None, # Optional[float]
                    slippage_percentage=None, # Optional[float]
                    executed_quantity=None, # Optional[float]
                    cumulative_quote_qty=None, # Optional[float]
                    commissions=None, # Optional[List[Commission]]
                    submitted_at=None, # Optional[datetime]
                    last_update_timestamp=None, # Optional[datetime]
                    fill_timestamp=None, # Optional[datetime]
                    trailing_stop_activation_price=None, # Optional[float]
                    trailing_stop_callback_rate=None, # Optional[float]
                    current_stop_price_tsl=None, # Optional[float]
                    oco_group_id_exchange=None # Optional[str]
                )
                # Las notas sobre la orden deberían ir en el Trade o en un log separado.
                # El TradeOrderDetails en sí no tiene un campo 'notes'.
                # El 'side' y 'symbol' se infieren del trade al que se asocia la orden.
                
                # TODO: El `execute_order` del UnifiedOrderExecutionService necesita ser definido/revisado.
                # Asumiendo que toma TradeOrderDetails, user_id, trade_mode.
                # Necesitamos asegurar que UnifiedOrderExecutionService tiene un método `execute_order`
                # que puede manejar esto.

                # Obtener credenciales para modo real
                api_key: Optional[str] = None
                api_secret: Optional[str] = None
                if trade.mode == TradeMode.REAL: # Usar Enum
                    try:
                        # Convertir user_id a UUID si es string. Asumimos que user_id ya es UUID o compatible.
                        # Si user_id viene como string, se debe convertir: user_uuid = UUID(user_id)
                        # Por ahora, asumimos que user_id es del tipo correcto para el servicio.
                        credential = await self.credential_service.get_credential(
                            user_id=UUID(user_id), # Asegurar que user_id es UUID
                            service_name=ServiceName.BINANCE_SPOT, # Asumir Spot por ahora
                            credential_label="default" # Asumir default
                        )
                        if credential:
                            # Las credenciales ya deberían estar desencriptadas por el CredentialService
                            api_key = credential.api_key 
                            api_secret = credential.secret_key
                        else:
                            logger.error(f"No se encontraron credenciales para user {user_id} para cerrar trade {trade.id}")
                            # Marcar el trade para intervención manual si no hay credenciales
                            trade.notes = (trade.notes or "") + f" | CRITICAL: No credentials found to auto-close on {exit_reason}. Manual intervention required."
                            # TODO: Persist trade update with error note.
                            return 
                    except Exception as cred_exc:
                        logger.error(f"Error obteniendo credenciales para user {user_id} para cerrar trade {trade.id}: {cred_exc}")
                        trade.notes = (trade.notes or "") + f" | CRITICAL: Credential error during auto-close on {exit_reason}. Manual intervention required."
                        # TODO: Persist trade update with error note.
                        return
                
                # Determinar el lado de la orden de salida
                exit_order_side = TradeSide.SELL if trade.side == TradeSide.BUY else TradeSide.BUY

                executed_order = await self.unified_order_execution_service.execute_order(
                    order_details=exit_order_details,
                    user_id=UUID(user_id), # Asegurar que user_id es UUID
                    trading_mode=trade.mode,
                    symbol=trade.symbol, # Pasar el símbolo
                    side=exit_order_side.value, # Pasar el lado correcto de la orden de salida
                    api_key=api_key, # Pasar api_key
                    api_secret=api_secret # Pasar api_secret
                )

                if executed_order and executed_order.status == OrderStatus.FILLED:
                    if trade.exit_orders is None:
                        trade.exit_orders = []
                    trade.exit_orders.append(executed_order)
                    trade.position_status = PositionStatus.CLOSED # Corregido
                    trade.exit_price = executed_order.executed_price
                    trade.closing_reason = exit_reason # Corregido
                    trade.closed_at = datetime.now(timezone.utc)
                    logger.info(f"Trade {trade.id} closed successfully via market order at {executed_order.executed_price}.")
                    # TODO: Persist trade update
                else:
                    logger.error(f"Failed to execute market exit order for trade {trade.id} or order not filled. Status: {executed_order.status if executed_order else 'None'}")
                    # TODO: Implement robust error reporting and alerts (Task 1.4.2)
                    # Marcar el trade para intervención manual.
                    trade.notes = (trade.notes or "") + f" | CRITICAL: Failed to auto-close on {exit_reason}. Manual intervention required."
                    # TODO: Persist trade update with error note.
                    # TODO: Send notification (Task 1.4.2)

        except Exception as e:
            logger.error(f"Error in monitor_and_manage_real_trade_exit for trade {trade.id}: {e}", exc_info=True)
            # TODO: Considerar cómo manejar errores aquí, ¿reintentar? ¿alertar?
            trade.notes = (trade.notes or "") + f" | ERROR during exit monitoring: {str(e)[:100]}" # Truncate error
            # TODO: Persist trade update with error note.
            # TODO: Send notification (Task 1.4.2)
