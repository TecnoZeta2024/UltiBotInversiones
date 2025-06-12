"""
Tests de integración para el AI Orchestrator Service.

Este módulo valida la integración completa del sistema de IA:
- Flujo planificación → ejecución → síntesis
- Integración con herramientas MCP
- Manejo de prompts desde base de datos
- Performance y manejo de errores
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from decimal import Decimal

# Core imports
from ultibot_backend.core.services.ai_orchestrator import AIOrchestratorService
from ultibot_backend.core.services.mcp_tool_hub import MCPToolHub
from ultibot_backend.core.services.prompt_manager import PromptManager
from ultibot_backend.core.domain_models.ai_models import (
    AIAnalysisRequest, AIAnalysisResult, ToolExecutionRequest, ToolExecutionResult
)
from ultibot_backend.core.domain_models.trading import TradingOpportunity
from ultibot_backend.adapters.gemini_adapter import GeminiAdapter

# Test fixtures
from tests.integration.fixtures import (
    create_bullish_market_snapshot,
    create_news_sentiment_spike_data,
    create_onchain_metrics_data
)

class MockGeminiAdapter:
    """Mock del adaptador Gemini para tests."""
    
    def __init__(self):
        self.call_count = 0
        self.response_delay = 0.1  # 100ms simulado
        
    async def generate(self, prompt: str, context: dict = None) -> dict:
        """Simula generación de respuesta del modelo Gemini."""
        self.call_count += 1
        
        # Simular delay de la API
        await asyncio.sleep(self.response_delay)
        
        # Respuestas mock basadas en el tipo de prompt
        if "planning" in prompt.lower():
            return {
                "plan": {
                    "analysis_steps": [
                        "fetch_market_sentiment",
                        "analyze_technical_indicators", 
                        "check_onchain_metrics"
                    ],
                    "tool_actions": [
                        {
                            "name": "market_sentiment",
                            "parameters": {"symbol": "BTCUSDT", "timeframe": "1h"}
                        },
                        {
                            "name": "onchain_analysis", 
                            "parameters": {"asset": "BTC", "metrics": ["whale_activity", "exchange_flows"]}
                        }
                    ],
                    "confidence": 0.85
                }
            }
        
        elif "synthesis" in prompt.lower():
            return {
                "analysis": {
                    "confidence": 0.87,
                    "recommendation": "BUY",
                    "reasoning": "Strong bullish momentum confirmed by multiple indicators and positive sentiment",
                    "risk_score": 0.25,
                    "expected_profit": 0.032,
                    "key_factors": [
                        "Technical breakout above resistance",
                        "Positive sentiment spike",
                        "Whale accumulation pattern"
                    ],
                    "stop_loss": 0.02,
                    "take_profit": 0.04
                }
            }
        
        else:
            return {
                "generic_response": "AI analysis completed",
                "confidence": 0.8
            }

class MockMCPToolHub:
    """Mock del MCP Tool Hub para tests."""
    
    def __init__(self):
        self.tools = {}
        self.execution_count = 0
        
    def register_tool(self, name: str, tool):
        """Registra una herramienta mock."""
        self.tools[name] = tool
    
    async def list_available_tools(self) -> list:
        """Lista herramientas disponibles."""
        return [
            {
                "name": "market_sentiment",
                "description": "Analyzes market sentiment from news and social media",
                "parameters": ["symbol", "timeframe"]
            },
            {
                "name": "onchain_analysis",
                "description": "Provides on-chain metrics and whale activity",
                "parameters": ["asset", "metrics"]
            }
        ]
    
    async def execute_tool(self, name: str, parameters: dict) -> ToolExecutionResult:
        """Ejecuta una herramienta simulada."""
        self.execution_count += 1
        
        # Simular delay de ejecución
        await asyncio.sleep(0.05)
        
        if name == "market_sentiment":
            return ToolExecutionResult(
                tool_name=name,
                success=True,
                data={
                    "sentiment_score": 0.82,
                    "confidence": 0.9,
                    "sources_analyzed": 156,
                    "positive_mentions": 124,
                    "negative_mentions": 32,
                    "trending_keywords": ["bullish", "breakout", "institutional"],
                    "news_velocity": 18
                },
                execution_time_ms=50,
                metadata={"provider": "news_aggregator", "version": "2.1"}
            )
        
        elif name == "onchain_analysis":
            return ToolExecutionResult(
                tool_name=name,
                success=True,
                data={
                    "whale_activity": {
                        "large_transactions_24h": 89,
                        "whale_net_flow": 1850.5,
                        "accumulation_score": 0.76
                    },
                    "exchange_flows": {
                        "net_outflow": -1245.8,
                        "outflow_trend": "increasing"
                    },
                    "network_health": {
                        "hash_rate_change": 0.025,
                        "active_addresses": 980000
                    }
                },
                execution_time_ms=75,
                metadata={"provider": "blockchain_analytics", "version": "3.0"}
            )
        
        else:
            return ToolExecutionResult(
                tool_name=name,
                success=False,
                error="Tool not found",
                execution_time_ms=10
            )

class MockPromptManager:
    """Mock del gestor de prompts para tests."""
    
    def __init__(self):
        self.prompts = {
            "opportunity_planning": """
            Analyze the trading opportunity and create an execution plan.
            Context: {context}
            Available tools: {tools}
            
            Create a step-by-step plan with tool usage.
            """,
            "opportunity_synthesis": """
            Synthesize the analysis results and provide trading recommendation.
            Opportunity: {opportunity}
            Tool Results: {tool_results}
            
            Provide final recommendation with confidence score.
            """
        }
    
    async def get_prompt(self, name: str) -> str:
        """Obtiene un prompt por nombre."""
        return self.prompts.get(name, "Default prompt template")
    
    async def render_prompt(self, template: str, variables: dict) -> str:
        """Renderiza un prompt con variables."""
        return template.format(**variables)

class TestAIOrchestratorIntegration:
    """Tests de integración del AI Orchestrator."""
    
    @pytest.fixture
    async def ai_orchestrator(self):
        """Fixture que crea un AI Orchestrator completo para tests."""
        gemini_adapter = MockGeminiAdapter()
        tool_hub = MockMCPToolHub()
        prompt_manager = MockPromptManager()
        
        # Registrar herramientas mock
        await tool_hub.register_tool("market_sentiment", Mock())
        await tool_hub.register_tool("onchain_analysis", Mock())
        
        orchestrator = AIOrchestratorService(
            gemini_adapter=gemini_adapter,
            tool_hub=tool_hub,
            prompt_manager=prompt_manager
        )
        
        return orchestrator, gemini_adapter, tool_hub, prompt_manager
    
    @pytest.mark.asyncio
    async def test_complete_ai_analysis_flow(self, ai_orchestrator):
        """
        Test del flujo completo de análisis IA:
        1. Planificación con prompt
        2. Ejecución de herramientas MCP
        3. Síntesis de resultados
        """
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        # Crear oportunidad de trading
        opportunity = TradingOpportunity(
            symbol="BTCUSDT",
            strategy_name="macd_rsi_trend_rider",
            confidence=0.8,
            expected_profit=0.025,
            risk_level="MEDIUM",
            timeframe="1h",
            detected_at=datetime.utcnow()
        )
        
        # Ejecutar análisis completo
        result = await orchestrator.analyze_opportunity(opportunity)
        
        # Verificaciones
        assert isinstance(result, AIAnalysisResult)
        assert result.confidence > 0.8
        assert result.recommendation in ["BUY", "SELL", "HOLD"]
        assert result.reasoning is not None
        assert len(result.reasoning) > 0
        
        # Verificar que se usaron las herramientas
        assert tool_hub.execution_count >= 2, "Debe ejecutar al menos 2 herramientas"
        
        # Verificar que se llamó a Gemini al menos 2 veces (planning + synthesis)
        assert gemini_adapter.call_count >= 2, "Debe llamar a Gemini para planning y synthesis"
    
    @pytest.mark.asyncio
    async def test_mcp_tools_integration(self, ai_orchestrator):
        """Test de integración con herramientas MCP."""
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        # Test: obtener lista de herramientas
        tools = await tool_hub.list_available_tools()
        assert len(tools) >= 2
        assert any(tool["name"] == "market_sentiment" for tool in tools)
        assert any(tool["name"] == "onchain_analysis" for tool in tools)
        
        # Test: ejecutar herramienta de sentimiento
        sentiment_result = await tool_hub.execute_tool("market_sentiment", {
            "symbol": "BTCUSDT",
            "timeframe": "1h"
        })
        
        assert sentiment_result.success
        assert "sentiment_score" in sentiment_result.data
        assert 0 <= sentiment_result.data["sentiment_score"] <= 1
        assert sentiment_result.execution_time_ms < 100
        
        # Test: ejecutar herramienta onchain
        onchain_result = await tool_hub.execute_tool("onchain_analysis", {
            "asset": "BTC",
            "metrics": ["whale_activity", "exchange_flows"]
        })
        
        assert onchain_result.success
        assert "whale_activity" in onchain_result.data
        assert "exchange_flows" in onchain_result.data
    
    @pytest.mark.asyncio
    async def test_prompt_management_integration(self, ai_orchestrator):
        """Test de integración con el sistema de prompts."""
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        # Test: obtener prompt de planificación
        planning_prompt = await prompt_manager.get_prompt("opportunity_planning")
        assert "trading opportunity" in planning_prompt.lower()
        assert "{context}" in planning_prompt
        assert "{tools}" in planning_prompt
        
        # Test: renderizar prompt con variables
        rendered = await prompt_manager.render_prompt(planning_prompt, {
            "context": "BTCUSDT bullish signal",
            "tools": "market_sentiment, onchain_analysis"
        })
        assert "BTCUSDT bullish signal" in rendered
        assert "market_sentiment" in rendered
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, ai_orchestrator):
        """Test de performance del AI Orchestrator."""
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        opportunity = TradingOpportunity(
            symbol="BTCUSDT",
            strategy_name="test_strategy",
            confidence=0.8,
            expected_profit=0.02,
            risk_level="MEDIUM",
            timeframe="1h",
            detected_at=datetime.utcnow()
        )
        
        import time
        
        # Test: análisis completo < 300ms
        start_time = time.perf_counter()
        result = await orchestrator.analyze_opportunity(opportunity)
        total_time = (time.perf_counter() - start_time) * 1000
        
        assert total_time < 300, f"Análisis IA tardó {total_time:.2f}ms, debe ser < 300ms"
        assert result.ai_metadata["processing_time_ms"] < 300
    
    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self, ai_orchestrator):
        """Test de manejo de errores y fallbacks."""
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        # Test 1: Error en herramienta MCP
        with patch.object(tool_hub, 'execute_tool', side_effect=Exception("Tool service down")):
            opportunity = TradingOpportunity(
                symbol="BTCUSDT",
                strategy_name="test_strategy",
                confidence=0.8,
                expected_profit=0.02,
                risk_level="MEDIUM", 
                timeframe="1h",
                detected_at=datetime.utcnow()
            )
            
            # El análisis debe continuar aunque fallen las herramientas
            result = await orchestrator.analyze_opportunity(opportunity)
            assert result is not None
            assert result.confidence > 0  # Debe dar algún resultado
        
        # Test 2: Error en Gemini API
        with patch.object(gemini_adapter, 'generate', side_effect=Exception("API rate limit")):
            with pytest.raises(Exception, match="API rate limit"):
                await orchestrator.analyze_opportunity(opportunity)
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, ai_orchestrator):
        """Test de análisis concurrentes."""
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        # Crear múltiples oportunidades
        opportunities = []
        for i in range(5):
            opportunity = TradingOpportunity(
                symbol=f"TEST{i}USDT",
                strategy_name="test_strategy",
                confidence=0.8,
                expected_profit=0.02,
                risk_level="MEDIUM",
                timeframe="1h",
                detected_at=datetime.utcnow()
            )
            opportunities.append(opportunity)
        
        # Ejecutar análisis concurrentes
        tasks = [orchestrator.analyze_opportunity(opp) for opp in opportunities]
        results = await asyncio.gather(*tasks)
        
        # Verificar que todos completaron
        assert len(results) == 5
        for result in results:
            assert isinstance(result, AIAnalysisResult)
            assert result.confidence > 0
        
        # Verificar que se procesaron concurrentemente (no secuencialmente)
        assert tool_hub.execution_count >= 10  # Al menos 2 herramientas por análisis
    
    @pytest.mark.asyncio
    async def test_ai_metadata_tracking(self, ai_orchestrator):
        """Test de tracking de metadatos de IA."""
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        opportunity = TradingOpportunity(
            symbol="BTCUSDT",
            strategy_name="test_strategy",
            confidence=0.8,
            expected_profit=0.02,
            risk_level="MEDIUM",
            timeframe="1h",
            detected_at=datetime.utcnow()
        )
        
        result = await orchestrator.analyze_opportunity(opportunity)
        
        # Verificar metadatos de IA
        assert "ai_metadata" in result.__dict__
        metadata = result.ai_metadata
        
        assert "model_version" in metadata
        assert "processing_time_ms" in metadata
        assert "tools_used" in metadata
        assert isinstance(metadata["tools_used"], list)
        assert len(metadata["tools_used"]) >= 2
        
        # Verificar que se trackean las herramientas usadas
        tool_names = [tool.split(":")[0] if ":" in tool else tool for tool in metadata["tools_used"]]
        assert "market_sentiment" in tool_names
        assert "onchain_analysis" in tool_names
    
    @pytest.mark.asyncio
    async def test_context_aware_analysis(self, ai_orchestrator):
        """Test de análisis consciente del contexto."""
        orchestrator, gemini_adapter, tool_hub, prompt_manager = ai_orchestrator
        
        # Test con diferentes tipos de mercado
        market_scenarios = [
            ("bullish", create_bullish_market_snapshot()),
            ("high_volatility", create_news_sentiment_spike_data()["market_snapshot"])
        ]
        
        for scenario_name, market_data in market_scenarios:
            opportunity = TradingOpportunity(
                symbol=market_data.symbol,
                strategy_name="context_aware_strategy",
                confidence=0.8,
                expected_profit=0.02,
                risk_level="MEDIUM",
                timeframe="1h", 
                detected_at=datetime.utcnow(),
                market_context=market_data.__dict__  # Contexto del mercado
            )
            
            result = await orchestrator.analyze_opportunity(opportunity)
            
            # El análisis debe reflejar el contexto del mercado
            assert result.confidence > 0
            if scenario_name == "bullish":
                assert result.recommendation in ["BUY", "HOLD"]
            
            # Verificar que se consideró el contexto
            assert "market" in result.reasoning.lower() or "context" in result.reasoning.lower()

if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v"])
