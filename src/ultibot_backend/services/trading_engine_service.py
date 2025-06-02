"""Trading Engine Service for executing trading strategies with AI integration.

This service orchestrates the trading decision process, integrating AI analysis
results with strategy logic to make informed trading decisions.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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
)
from src.ultibot_backend.services.ai_orchestrator_service import (
    AIOrchestrator,
    AIAnalysisResult,
    OpportunityData,
)
from src.ultibot_backend.core.domain_models.trade_models import (
    Trade,
    AIInfluenceDetails,
)

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
        self.opportunity_id = opportunity_id
        self.strategy_id = strategy_id
        self.ai_analysis_used = ai_analysis_used
        self.ai_analysis_profile_id = ai_analysis_profile_id
        self.recommended_trade_params = recommended_trade_params
        self.risk_assessment = risk_assessment
        self.warnings = warnings or []
        self.timestamp = datetime.now(timezone.utc)
        self.decision_id = str(uuid.uuid4())


class TradingEngine:
    """Service for executing trading strategies with AI integration."""
    
    def __init__(
        self,
        strategy_service: 'StrategyService',
        configuration_service: 'ConfigurationService',
        ai_orchestrator: Optional[AIOrchestrator] = None,
    ):
        """Initialize the trading engine.
        
        Args:
            strategy_service: Strategy service for accessing strategy configurations.
            configuration_service: Configuration service for user settings.
            ai_orchestrator: AI orchestrator for AI analysis (optional).
        """
        self.strategy_service = strategy_service
        self.configuration_service = configuration_service
        self.ai_orchestrator = ai_orchestrator or AIOrchestrator()
    
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
                    opportunity_id=opportunity.id,
                    strategy_id=strategy.id,
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
            opportunity_id=opportunity.id,
            strategy_id=strategy.id,
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
        
        if hasattr(params, 'profit_target_percentage'):
            profit_target_pct = params.profit_target_percentage
            stop_loss_pct = params.stop_loss_percentage
        else:
            # Default scalping parameters
            profit_target_pct = 0.01  # 1%
            stop_loss_pct = 0.005  # 0.5%
        
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
            opportunity_id=opportunity.id,
            strategy_id=strategy.id,
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
        return OpportunityData(
            opportunity_id=opportunity.id,
            symbol=opportunity.symbol,
            initial_signal=opportunity.initial_signal.dict() if hasattr(opportunity.initial_signal, 'dict') else opportunity.initial_signal,
            source_type=opportunity.source_type.value,
            source_name=opportunity.source_name,
            source_data=opportunity.source_data,
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
        ai_analysis = AIAnalysis(
            analysis_id=ai_result.analysis_id,
            analyzed_at=ai_result.analyzed_at,
            model_used=ai_result.model_used,
            calculated_confidence=ai_result.calculated_confidence,
            suggested_action=ai_result.suggested_action,
            recommended_trade_strategy_type=ai_result.recommended_trade_strategy_type,
            recommended_trade_params=ai_result.recommended_trade_params,
            reasoning_ai=ai_result.reasoning_ai,
            data_verification=ai_result.data_verification,
            processing_time_ms=ai_result.processing_time_ms,
            ai_warnings=ai_result.ai_warnings,
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
            # Create basic trade structure
            trade = Trade(
                id=str(uuid.uuid4()),
                user_id=strategy.user_id,
                mode="paper",  # Default to paper mode for now
                symbol=opportunity.symbol,
                side="buy",  # Default side, should be determined from opportunity/strategy
                strategy_id=strategy.id,
                opportunity_id=opportunity.id,
                position_status="pending_entry_conditions",
                entry_order=self._create_entry_order_from_decision(decision, opportunity),
                notes=f"Trade created from decision {decision.decision_id}. {decision.reasoning}",
                created_at=datetime.now(timezone.utc),
            )
            
            # Add AI influence details if AI was used
            if decision.ai_analysis_used and decision.ai_analysis_profile_id:
                await self._add_ai_influence_to_trade(trade, decision, opportunity)
            
            # Log trade creation with AI influence information
            logger.info(f"Created trade {trade.id} from decision {decision.decision_id}")
            logger.info(trade.get_trade_summary_for_logging())
            
            # TODO: Save trade to database via persistence service
            
            return trade
            
        except Exception as e:
            logger.error(f"Error creating trade from decision {decision.decision_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create trade: {str(e)}"
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
        else:
            entry_price = opportunity.initial_signal.entry_price_target
        
        return TradeOrderDetails(
            order_id_internal=str(uuid.uuid4()),
            type=OrderType.MARKET,  # Default to market order
            status=OrderStatus.NEW,
            requested_price=entry_price,
            requested_quantity=1.0,  # Default quantity, should be calculated based on position sizing
            timestamp=datetime.now(timezone.utc),
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
        if hasattr(strategy.parameters, 'dict'):
            params = strategy.parameters.dict()
        elif isinstance(strategy.parameters, dict):
            params = strategy.parameters
        else:
            return "No parameters"
        
        # Log only key parameters to avoid verbosity
        key_params = {}
        for key, value in params.items():
            if 'percentage' in key.lower() or 'price' in key.lower() or 'threshold' in key.lower():
                key_params[key] = value
            elif len(key_params) < 5:  # Limit to 5 key parameters
                key_params[key] = value
        
        return ", ".join([f"{k}={v}" for k, v in key_params.items()])
    
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
