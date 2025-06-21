"""AI Orchestrator Service for Gemini analysis integration.

This service handles the orchestration of AI analysis using Google Gemini,
including dynamic prompt generation based on trading strategies and opportunities.
"""

import logging
import time
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

# LangChain imports for structured output
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser

from ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
)
from ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
)
from ultibot_backend.services.market_data_service import MarketDataService
from ultibot_backend.app_config import get_app_settings

logger = logging.getLogger(__name__)

# --- Pydantic Models for Structured LLM Output ---

class TradeParameters(BaseModel):
    entry_price: Optional[float] = Field(None, description="Suggested entry price for the trade.")
    stop_loss: Optional[float] = Field(None, description="Suggested stop-loss price.")
    take_profit: Optional[List[float]] = Field(None, description="List of suggested take-profit price levels.")
    position_size_percentage: Optional[float] = Field(None, description="Suggested position size as a percentage of capital.")

class DataVerification(BaseModel):
    price_check: str = Field(..., description="Status of price verification (e.g., 'verified', 'discrepancy_found').")
    volume_check: str = Field(..., description="Status of volume verification (e.g., 'sufficient', 'low_liquidity').")

class AIResponse(BaseModel):
    """Defines the structured JSON output expected from the AI."""
    confidence: float = Field(..., ge=0.0, le=1.0, description="The AI's confidence level in its analysis.")
    action: str = Field(..., description="The recommended action (e.g., 'strong_buy', 'hold_neutral', 'sell').")
    reasoning: str = Field(..., description="Detailed reasoning behind the recommended action.")
    trade_params: Optional[TradeParameters] = Field(None, description="Specific trade parameters, if applicable.")
    warnings: Optional[List[str]] = Field(None, description="A list of any warnings or risks identified.")
    data_verification: Optional[DataVerification] = Field(None, description="Results of data verification checks.")


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
        self.market_data_service = market_data_service
        self.model_name = "gemini-1.5-pro-latest"
        
        app_settings = get_app_settings()
        gemini_api_key = app_settings.GEMINI_API_KEY
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")

        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=gemini_api_key,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        self.output_parser = PydanticOutputParser(pydantic_object=AIResponse)
        self.robust_parser = OutputFixingParser.from_llm(parser=self.output_parser, llm=self.llm)
        logger.info(f"AIOrchestrator initialized with {self.model_name} and PydanticOutputParser.")
    
    async def analyze_opportunity_with_strategy_context_async(
        self,
        opportunity: OpportunityData,
        strategy: TradingStrategyConfig,
        ai_config: AIStrategyConfiguration,
        user_id: str,
    ) -> AIAnalysisResult:
        start_time = time.time()
        analysis_id = f"ai_analysis_{opportunity.opportunity_id}_{int(start_time)}"
        
        try:
            historical_data = await self.market_data_service.get_candlestick_data(
                symbol=opportunity.symbol,
                interval='1h',
                limit=200
            )

            prompt_template_str = self._build_dynamic_prompt_template(ai_config)
            prompt = PromptTemplate(
                template=prompt_template_str,
                input_variables=["strategy_type", "strategy_name", "strategy_params", "opportunity_details", "historical_data", "symbol", "tools_available", "confidence_threshold_paper", "confidence_threshold_real"],
                partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
            )

            strategy_params = self._format_strategy_parameters(strategy)
            opportunity_details = self._format_opportunity_details(opportunity)
            historical_data_details = self._format_historical_data(historical_data)
            tools_description = self._format_tools_description(ai_config.tools_available_to_gemini or [])

            chain = prompt | self.llm
            
            logger.info(f"Starting AI analysis {analysis_id} for opportunity {opportunity.opportunity_id}")
            
            llm_response = await chain.ainvoke({
                "strategy_type": strategy.base_strategy_type.value,
                "strategy_name": strategy.config_name,
                "strategy_params": strategy_params,
                "opportunity_details": opportunity_details,
                "historical_data": historical_data_details,
                "symbol": opportunity.symbol,
                "tools_available": tools_description,
                "confidence_threshold_paper": self._get_confidence_threshold(ai_config, "paper"),
                "confidence_threshold_real": self._get_confidence_threshold(ai_config, "real"),
            })

            llm_content_str = str(llm_response.content)
            try:
                parsed_response: AIResponse = self.output_parser.parse(llm_content_str)
            except Exception:
                logger.warning(f"PydanticOutputParser failed for analysis {analysis_id}. Attempting to fix with OutputFixingParser.")
                parsed_response: AIResponse = self.robust_parser.parse(llm_content_str)

            analysis_result = self._create_analysis_result(analysis_id, parsed_response, self.model_name)
            
            processing_time = int((time.time() - start_time) * 1000)
            analysis_result.processing_time_ms = processing_time
            
            self._log_ai_analysis_results(analysis_result, ai_config)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in AI analysis for opportunity {opportunity.opportunity_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

    def _create_analysis_result(self, analysis_id: str, parsed_response: AIResponse, model_used: str) -> AIAnalysisResult:
        trade_params_dict = parsed_response.trade_params.model_dump() if parsed_response.trade_params else None
        data_verification_dict = parsed_response.data_verification.model_dump() if parsed_response.data_verification else None

        return AIAnalysisResult(
            analysis_id=analysis_id,
            calculated_confidence=parsed_response.confidence,
            suggested_action=parsed_response.action,
            reasoning_ai=parsed_response.reasoning,
            recommended_trade_params=trade_params_dict,
            data_verification=data_verification_dict,
            ai_warnings=parsed_response.warnings,
            model_used=model_used,
        )

    def _build_dynamic_prompt_template(self, ai_config: AIStrategyConfiguration) -> str:
        """Builds the prompt template, incorporating format instructions."""
        base_template = ai_config.gemini_prompt_template or self._get_default_prompt_template()
        return base_template + "\n\n{format_instructions}\n"

    def _format_historical_data(self, historical_data: List[Dict[str, Any]]) -> str:
        if not historical_data:
            return "No historical data available."
        
        formatted_lines = ["Timestamp, Open, High, Low, Close, Volume"]
        for kline in historical_data[-20:]:
            dt_object = datetime.fromtimestamp(kline['open_time'] / 1000)
            formatted_lines.append(
                f"{dt_object.strftime('%Y-%m-%d %H:%M')},{kline['open']},{kline['high']},{kline['low']},{kline['close']},{kline['volume']}"
            )
        return "\n".join(formatted_lines)

    def _get_default_prompt_template(self) -> str:
        return """
Analyze this trading opportunity for {symbol} using the {strategy_type} strategy '{strategy_name}'.

**Strategy Configuration:**
{strategy_params}

**Opportunity Details:**
{opportunity_details}

**Recent Market Data (last 20 hours, CSV format):**
{historical_data}

**Available Analysis Tools:**
{tools_available}

**Task:**
Based on all the information provided, perform a comprehensive analysis and provide a structured JSON response. Your analysis must be rigorous, considering the strategy's parameters, market data, and potential risks.

**Confidence Thresholds:**
- Paper Trading Minimum Confidence: {confidence_threshold_paper:.2f}
- Real Trading Minimum Confidence: {confidence_threshold_real:.2f}

**Output Format:**
You MUST respond ONLY with a valid JSON object that conforms to the schema provided in the format instructions below. Do not include any text or markdown formatting before or after the JSON object.
"""
    
    def _format_strategy_parameters(self, strategy: TradingStrategyConfig) -> str:
        params_dict = {}
        # Explicitly check if it's a Pydantic model instance
        if isinstance(strategy.parameters, BaseModel):
            params_dict = strategy.parameters.model_dump()
        # Else, if it's a dictionary, use it directly
        elif isinstance(strategy.parameters, dict):
            params_dict = strategy.parameters

        return "\n".join([f"- {key}: {value}" for key, value in params_dict.items()]) or "No specific parameters."
    
    def _format_opportunity_details(self, opportunity: OpportunityData) -> str:
        details = [
            f"- Symbol: {opportunity.symbol}",
            f"- Source: {opportunity.source_type}",
            f"- Detected At: {opportunity.detected_at.isoformat()}"
        ]
        if opportunity.source_name:
            details.append(f"- Source Name: {opportunity.source_name}")
        if opportunity.initial_signal:
            details.append("- Initial Signal:")
            details.extend([f"  - {key}: {value}" for key, value in opportunity.initial_signal.items()])
        return "\n".join(details)
    
    def _format_tools_description(self, tools: List[str]) -> str:
        if not tools:
            return "No specific tools configured."
        
        tool_descriptions = {
            "MobulaChecker": "Real-time price and market data verification.",
            "BinanceMarketReader": "Binance market data and order book analysis.",
            "TechnicalIndicators": "Technical analysis indicators (RSI, MACD, etc.).",
            "NewsAnalyzer": "Recent news sentiment analysis.",
            "VolumeAnalyzer": "Trading volume pattern analysis.",
        }
        return "\n".join([f"- {tool_descriptions.get(tool, f'Tool: {tool}')}" for tool in tools])
    
    def _get_confidence_threshold(self, ai_config: AIStrategyConfiguration, mode: str) -> float:
        if ai_config.confidence_thresholds:
            if mode == "paper":
                return ai_config.confidence_thresholds.paper_trading or 0.6
            elif mode == "real":
                return ai_config.confidence_thresholds.real_trading or 0.8
        return 0.6 if mode == "paper" else 0.8
    
    def _log_ai_analysis_results(self, ai_result: AIAnalysisResult, ai_config: AIStrategyConfiguration) -> None:
        logger.info(
            f"AI Analysis Results {ai_result.analysis_id}: "
            f"Profile={ai_config.id} ({ai_config.name}), "
            f"Model={ai_result.model_used}, "
            f"Confidence={ai_result.calculated_confidence:.3f}, "
            f"Action={ai_result.suggested_action}, "
            f"Processing={ai_result.processing_time_ms}ms"
        )
        reasoning_preview = ai_result.reasoning_ai[:200] + "..." if len(ai_result.reasoning_ai) > 200 else ai_result.reasoning_ai
        logger.info(f"AI Reasoning {ai_result.analysis_id}: {reasoning_preview}")
        if ai_result.ai_warnings:
            logger.warning(f"AI Warnings {ai_result.analysis_id}: {'; '.join(ai_result.ai_warnings)}")
        if ai_result.recommended_trade_params:
            params_summary = ", ".join([f"{k}={v}" for k, v in ai_result.recommended_trade_params.items()])
            logger.info(f"AI Trade Params {ai_result.analysis_id}: {params_summary}")
        if ai_result.data_verification:
            verification_summary = ", ".join([f"{k}={v}" for k, v in ai_result.data_verification.items()])
            logger.info(f"AI Data Verification {ai_result.analysis_id}: {verification_summary}")
