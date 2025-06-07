"""AI Orchestrator Service for Gemini analysis integration.

This service handles the orchestration of AI analysis using Google Gemini,
including dynamic prompt generation based on trading strategies and opportunities.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
)
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
)
from src.ultibot_backend.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)


class AIAnalysisResult:
    """Result of AI analysis for an opportunity."""
    
    def __init__(
        self,
        analysis_id: str,
        calculated_confidence: float,
        suggested_action: str,
        reasoning_ai: str,
        recommended_trade_strategy_type: Optional[str] = None,
        recommended_trade_params: Optional[Dict[str, Any]] = None,
        data_verification: Optional[Dict[str, Any]] = None,
        processing_time_ms: Optional[int] = None,
        ai_warnings: Optional[List[str]] = None,
        model_used: Optional[str] = None,
    ):
        """Initialize AI analysis result.
        
        Args:
            analysis_id: Unique identifier for this analysis.
            calculated_confidence: Confidence score (0-1).
            suggested_action: Action suggestion ('strong_buy', 'buy', 'hold_neutral', etc.).
            reasoning_ai: AI's reasoning for the recommendation.
            recommended_trade_strategy_type: Recommended trade strategy type.
            recommended_trade_params: Recommended trade parameters.
            data_verification: Data verification results.
            processing_time_ms: Processing time in milliseconds.
            ai_warnings: List of warnings from AI.
            model_used: AI model used for analysis.
        """
        self.analysis_id = analysis_id
        self.calculated_confidence = calculated_confidence
        self.suggested_action = suggested_action
        self.reasoning_ai = reasoning_ai
        self.recommended_trade_strategy_type = recommended_trade_strategy_type
        self.recommended_trade_params = recommended_trade_params
        self.data_verification = data_verification
        self.processing_time_ms = processing_time_ms
        self.ai_warnings = ai_warnings or []
        self.model_used = model_used
        self.analyzed_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage."""
        return {
            "analysisId": self.analysis_id,
            "analyzedAt": self.analyzed_at.isoformat(),
            "modelUsed": self.model_used,
            "calculatedConfidence": self.calculated_confidence,
            "suggestedAction": self.suggested_action,
            "recommendedTradeStrategyType": self.recommended_trade_strategy_type,
            "recommendedTradeParams": self.recommended_trade_params,
            "reasoning_ai": self.reasoning_ai,
            "dataVerification": self.data_verification,
            "processingTimeMs": self.processing_time_ms,
            "aiWarnings": self.ai_warnings,
        }


class OpportunityData:
    """Data structure for opportunity information."""
    
    def __init__(
        self,
        opportunity_id: str,
        symbol: str,
        initial_signal: Dict[str, Any],
        source_type: str,
        source_name: Optional[str] = None,
        source_data: Optional[Dict[str, Any]] = None,
        detected_at: Optional[datetime] = None,
    ):
        """Initialize opportunity data.
        
        Args:
            opportunity_id: Unique opportunity identifier.
            symbol: Trading symbol (e.g., 'BTC/USDT').
            initial_signal: Initial signal data.
            source_type: Type of source that detected the opportunity.
            source_name: Name of the specific source.
            source_data: Additional source data.
            detected_at: When the opportunity was detected.
        """
        self.opportunity_id = opportunity_id
        self.symbol = symbol
        self.initial_signal = initial_signal
        self.source_type = source_type
        self.source_name = source_name
        self.source_data = source_data
        self.detected_at = detected_at or datetime.now(timezone.utc)


class AIOrchestrator:
    """Service for orchestrating AI analysis using Google Gemini."""
    
    def __init__(self, market_data_service: MarketDataService):
        """Initialize the AI Orchestrator service."""
        self.market_data_service = market_data_service
        self.gemini_client = None # Placeholder for the actual client
        logger.info("AIOrchestrator initialized (using MOCK implementation for Gemini).")
    
    async def analyze_opportunity_with_strategy_context_async(
        self,
        opportunity: OpportunityData,
        strategy: TradingStrategyConfig,
        ai_config: AIStrategyConfiguration,
        user_id: str,
    ) -> AIAnalysisResult:
        """Analyze an opportunity with strategy context using AI.
        
        Args:
            opportunity: The opportunity data to analyze.
            strategy: The trading strategy configuration.
            ai_config: The AI configuration to use.
            user_id: The user identifier.
            
        Returns:
            AIAnalysisResult with the analysis.
            
        Raises:
            HTTPException: If analysis fails.
        """
        start_time = time.time()
        
        try:
            analysis_id = f"ai_analysis_{opportunity.opportunity_id}_{int(start_time)}"
            
            historical_data = await self.market_data_service.get_candlestick_data(
                symbol=opportunity.symbol,
                interval='1h', # Or make this configurable
                limit=200
            )

            prompt = self._build_dynamic_prompt(opportunity, strategy, ai_config, historical_data)
            
            logger.info(
                f"Starting AI analysis {analysis_id} for opportunity {opportunity.opportunity_id} "
                f"with strategy {strategy.config_name} using AI profile {ai_config.id}"
            )
            
            self.log_prompt_summary(prompt, analysis_id)
            
            analysis_result = await self._mock_gemini_analysis(
                analysis_id, prompt, opportunity, strategy, ai_config
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            analysis_result.processing_time_ms = processing_time
            
            self._log_ai_analysis_results(analysis_result, ai_config)
            
            logger.info(
                f"Completed AI analysis {analysis_id} in {processing_time}ms. "
                f"Confidence: {analysis_result.calculated_confidence:.2f}, "
                f"Action: {analysis_result.suggested_action}"
            )
            
            return analysis_result
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(
                f"Error in AI analysis for opportunity {opportunity.opportunity_id}: {e}. "
                f"Processing time: {processing_time}ms"
            )
            raise HTTPException(
                status_code=500,
                detail=f"AI analysis failed: {str(e)}"
            )
    
    def _build_dynamic_prompt(
        self,
        opportunity: OpportunityData,
        strategy: TradingStrategyConfig,
        ai_config: AIStrategyConfiguration,
        historical_data: List[Dict[str, Any]]
    ) -> str:
        """Build a dynamic prompt based on opportunity, strategy, and AI configuration.
        
        Args:
            opportunity: The opportunity data.
            strategy: The trading strategy configuration.
            ai_config: The AI configuration.
            historical_data: Historical market data.
            
        Returns:
            The generated prompt string.
        """
        template = ai_config.gemini_prompt_template or self._get_default_prompt_template()
        
        strategy_params = self._format_strategy_parameters(strategy)
        opportunity_details = self._format_opportunity_details(opportunity)
        historical_data_details = self._format_historical_data(historical_data)
        
        available_tools = ai_config.tools_available_to_gemini or []
        tools_description = self._format_tools_description(available_tools)
        
        prompt = template.format(
            strategy_type=strategy.base_strategy_type.value,
            strategy_name=strategy.config_name,
            strategy_params=strategy_params,
            opportunity_details=opportunity_details,
            historical_data=historical_data_details,
            symbol=opportunity.symbol,
            tools_available=tools_description,
            confidence_threshold_paper=self._get_confidence_threshold(ai_config, "paper"),
            confidence_threshold_real=self._get_confidence_threshold(ai_config, "real"),
        )
        
        return prompt

    def _format_historical_data(self, historical_data: List[Dict[str, Any]]) -> str:
        """Formats historical data for prompt inclusion."""
        if not historical_data:
            return "No historical data available."
        
        formatted_lines = ["Timestamp, Open, High, Low, Close, Volume"]
        for kline in historical_data[-20:]: # Limit to last 20 records for prompt brevity
            dt_object = datetime.fromtimestamp(kline['open_time'] / 1000)
            formatted_lines.append(
                f"{dt_object.strftime('%Y-%m-%d %H:%M')}, {kline['open']}, {kline['high']}, {kline['low']}, {kline['close']}, {kline['volume']}"
            )
        return "\n".join(formatted_lines)

    def _get_default_prompt_template(self) -> str:
        """Get the default prompt template for AI analysis.
        
        Returns:
            Default prompt template string.
        """
        return """
Analyze this trading opportunity for {symbol} using the {strategy_type} strategy '{strategy_name}'.

Strategy Configuration:
{strategy_params}

Opportunity Details:
{opportunity_details}

Recent Market Data (last 20 hours):
{historical_data}

Available Analysis Tools:
{tools_available}

Please provide:
1. Your confidence level (0.0 to 1.0) for this opportunity
2. Recommended action (strong_buy, buy, hold_neutral, sell, strong_sell, further_investigation_needed)
3. Detailed reasoning for your recommendation based on the provided historical data and strategy.
4. Suggested trade parameters if applicable
5. Any warnings or risk factors to consider

Consider the strategy's specific parameters and risk profile when making your recommendation.
For paper trading, minimum confidence threshold is {confidence_threshold_paper:.2f}.
For real trading, minimum confidence threshold is {confidence_threshold_real:.2f}.

Respond in JSON format:
{{
    "confidence": <float 0.0-1.0>,
    "action": "<action_string>",
    "reasoning": "<detailed_reasoning>",
    "trade_params": {{
        "entry_price": <float>,
        "stop_loss": <float>,
        "take_profit": [<float>, ...],
        "position_size_percentage": <float>
    }},
    "warnings": ["<warning1>", "<warning2>"],
    "data_verification": {{
        "price_check": "verified",
        "volume_check": "verified"
    }}
}}
"""
    
    def _format_strategy_parameters(self, strategy: TradingStrategyConfig) -> str:
        """Format strategy parameters for prompt inclusion.
        
        Args:
            strategy: The trading strategy configuration.
            
        Returns:
            Formatted string of strategy parameters.
        """
        params_dict = {}

        if hasattr(strategy.parameters, 'dict'):
            params_dict = strategy.parameters.dict()  # type: ignore
        elif isinstance(strategy.parameters, dict):
            params_dict = strategy.parameters

        formatted_params = []
        for key, value in params_dict.items():
            formatted_params.append(f"- {key}: {value}")
        
        return "\n".join(formatted_params) if formatted_params else "No specific parameters configured"
    
    def _format_opportunity_details(self, opportunity: OpportunityData) -> str:
        """Format opportunity details for prompt inclusion.
        
        Args:
            opportunity: The opportunity data.
            
        Returns:
            Formatted string of opportunity details.
        """
        details = []
        details.append(f"- Symbol: {opportunity.symbol}")
        details.append(f"- Source: {opportunity.source_type}")
        if opportunity.source_name:
            details.append(f"- Source Name: {opportunity.source_name}")
        details.append(f"- Detected At: {opportunity.detected_at.isoformat()}")
        
        # Format initial signal
        signal = opportunity.initial_signal
        if signal:
            details.append("- Initial Signal:")
            for key, value in signal.items():
                details.append(f"  - {key}: {value}")
        
        return "\n".join(details)
    
    def _format_tools_description(self, tools: List[str]) -> str:
        """Format available tools description.
        
        Args:
            tools: List of available tool names.
            
        Returns:
            Formatted string describing available tools.
        """
        if not tools:
            return "No specific tools configured"
        
        tool_descriptions = {
            "MobulaChecker": "Real-time price and market data verification",
            "BinanceMarketReader": "Binance market data and order book analysis",
            "TechnicalIndicators": "Technical analysis indicators (RSI, MACD, etc.)",
            "NewsAnalyzer": "Recent news sentiment analysis",
            "VolumeAnalyzer": "Trading volume pattern analysis",
        }
        
        descriptions = []
        for tool in tools:
            desc = tool_descriptions.get(tool, f"Tool: {tool}")
            descriptions.append(f"- {desc}")
        
        return "\n".join(descriptions)
    
    def _get_confidence_threshold(self, ai_config: AIStrategyConfiguration, mode: str) -> float:
        """Get confidence threshold for a specific mode.
        
        Args:
            ai_config: The AI configuration.
            mode: The trading mode ('paper' or 'real').
            
        Returns:
            Confidence threshold value.
        """
        if ai_config.confidence_thresholds:
            if mode == "paper":
                return ai_config.confidence_thresholds.paper_trading or 0.6
            elif mode == "real":
                return ai_config.confidence_thresholds.real_trading or 0.8
        
        # Default thresholds
        return 0.6 if mode == "paper" else 0.8
    
    async def _mock_gemini_analysis(
        self,
        analysis_id: str,
        prompt: str,
        opportunity: OpportunityData,
        strategy: TradingStrategyConfig,
        ai_config: AIStrategyConfiguration,
    ) -> AIAnalysisResult:
        """Mock Gemini analysis for testing purposes.
        
        This method provides realistic mock responses until actual Gemini integration is complete.
        
        Args:
            analysis_id: The analysis identifier.
            prompt: The generated prompt.
            opportunity: The opportunity data.
            strategy: The trading strategy configuration.
            ai_config: The AI configuration.
            
        Returns:
            Mock AIAnalysisResult.
        """
        # Simulate analysis based on strategy type and opportunity
        confidence = 0.75  # Mock confidence
        
        if strategy.base_strategy_type == BaseStrategyType.SCALPING:
            action = "buy"
            reasoning = (
                f"Based on the scalping strategy parameters and the {opportunity.symbol} opportunity, "
                "I detect a favorable short-term price movement pattern. The entry signal shows "
                "good momentum with acceptable risk parameters."
            )
            trade_params = {
                "entry_price": 30000.0,
                "stop_loss": 29700.0,
                "take_profit": [30300.0],
                "position_size_percentage": 2.0,
            }
        elif strategy.base_strategy_type == BaseStrategyType.DAY_TRADING:
            action = "hold_neutral"
            confidence = 0.65
            reasoning = (
                f"The day trading indicators for {opportunity.symbol} show mixed signals. "
                "While there's some bullish momentum, the volume doesn't strongly support "
                "a high-confidence entry at this time."
            )
            trade_params = {
                "entry_price": 30050.0,
                "stop_loss": 29500.0,
                "take_profit": [30800.0, 31200.0],
                "position_size_percentage": 3.0,
            }
        else:
            action = "further_investigation_needed"
            confidence = 0.5
            reasoning = (
                f"The opportunity for {opportunity.symbol} requires additional analysis. "
                "The current market conditions and strategy parameters don't provide "
                "sufficient clarity for a confident recommendation."
            )
            trade_params = None
        
        return AIAnalysisResult(
            analysis_id=analysis_id,
            calculated_confidence=confidence,
            suggested_action=action,
            reasoning_ai=reasoning,
            recommended_trade_strategy_type="simple_entry",
            recommended_trade_params=trade_params,
            data_verification={
                "mobulaCheckStatus": "success",
                "binanceDataCheck": "verified",
            },
            ai_warnings=["This is a mock analysis for development purposes"],
            model_used="Gemini-1.5-Pro (Mock)",
        )
    
    def log_prompt_summary(self, prompt: str, analysis_id: str) -> None:
        """Log a summary of the prompt for debugging and auditing.
        
        Args:
            prompt: The full prompt sent to AI.
            analysis_id: The analysis identifier.
        """
        # Log only a summary to avoid verbosity and potential data exposure
        prompt_length = len(prompt)
        first_100_chars = prompt[:100].replace('\n', ' ')
        
        logger.info(
            f"AI Analysis {analysis_id}: Prompt sent (length: {prompt_length} chars). "
            f"Preview: {first_100_chars}..."
        )
    
    def _log_ai_analysis_results(self, ai_result: AIAnalysisResult, ai_config: AIStrategyConfiguration) -> None:
        """Log detailed AI analysis results for auditing.
        
        Args:
            ai_result: AI analysis results.
            ai_config: AI configuration used.
        """
        logger.info(
            f"AI Analysis Results {ai_result.analysis_id}: "
            f"Profile={ai_config.id} ({ai_config.name}), "
            f"Model={ai_result.model_used}, "
            f"Confidence={ai_result.calculated_confidence:.3f}, "
            f"Action={ai_result.suggested_action}, "
            f"Processing={ai_result.processing_time_ms}ms"
        )
        
        # Log reasoning summary (truncated to avoid excessive verbosity)
        reasoning_preview = ai_result.reasoning_ai[:200] + "..." if len(ai_result.reasoning_ai) > 200 else ai_result.reasoning_ai
        logger.info(f"AI Reasoning {ai_result.analysis_id}: {reasoning_preview}")
        
        # Log any warnings
        if ai_result.ai_warnings:
            logger.warning(f"AI Warnings {ai_result.analysis_id}: {'; '.join(ai_result.ai_warnings)}")
        
        # Log trade parameters if provided
        if ai_result.recommended_trade_params:
            params_summary = ", ".join([f"{k}={v}" for k, v in ai_result.recommended_trade_params.items() if k in ["entry_price", "stop_loss", "take_profit"]])
            logger.info(f"AI Trade Params {ai_result.analysis_id}: {params_summary}")
        
        # Log data verification status
        if ai_result.data_verification:
            verification_summary = ", ".join([f"{k}={v}" for k, v in ai_result.data_verification.items()])
            logger.info(f"AI Data Verification {ai_result.analysis_id}: {verification_summary}")
