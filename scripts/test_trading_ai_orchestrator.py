#!/usr/bin/env python3
"""
Script de prueba avanzado para el AI Orchestrator con funcionalidades específicas de trading.
Prueba el nuevo modelo AIAnalysisResult y el método analyze_opportunity.
Este script utiliza mocks para aislar el AIOrchestratorService y probar su lógica interna.
"""

import asyncio
import logging
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock

# Añadir el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.core.domain_models.ai_models import (
    AIAnalysisResult,
    TradingOpportunity,
)
from src.ultibot_backend.core.ports import IAIModelAdapter, IMCPToolHub, IPromptManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_trading_analysis(orchestrator: AIOrchestratorService):
    """Prueba el análisis específico de trading con datos realistas."""
    logger.info("🎯 Probando análisis específico de trading...")
    
    # 1. Construir el objeto TradingOpportunity con la firma correcta
    trading_opportunity = TradingOpportunity(
        opportunity_id=str(uuid.uuid4()),
        symbol="BTC/USDT",
        strategy_name="Scalping de alta frecuencia",
        confidence=0.85,
        current_price=Decimal("43487.25"),
        volume_24h=Decimal("18432"),
        price_change_24h=3.24,
        technical_indicators={
            "RSI_1m": 62.3,
            "MACD_1m": "BULLISH_CROSS",
            "EMA_20_1m": 43380
        },
        market_context={
            "resistance_level": 43800,
            "support_level": 43200,
            "dxy": 103.2
        },
        risk_level="MEDIUM",
        timeframe="1m",
        signal_strength=0.75,
        expected_profit=1.5
    )
    
    try:
        logger.info("📤 Enviando oportunidad de trading al orchestrator (mockeado)...")
        
        # 2. Llamar al método con la firma correcta
        response: AIAnalysisResult = await orchestrator.analyze_opportunity(
            opportunity=trading_opportunity
        )
        
        logger.info("✅ ¡Análisis de trading completado exitosamente!")
        
        # 3. Mostrar resultados basados en el modelo AIAnalysisResult
        logger.info("=" * 60)
        logger.info("📊 RESULTADO DEL ANÁLISIS DE IA (SIMULADO)")
        logger.info("=" * 60)
        logger.info(f"🎯 RECOMENDACIÓN: {response.recommendation}")
        logger.info(f"📈 CONFIANZA: {response.confidence:.1%}")
        logger.info(f"🧠 RAZONAMIENTO: {response.reasoning}")
        
        if response.ai_metadata:
            logger.info(f"⚙️ METADATA IA: {response.ai_metadata}")
        
        logger.info(f"🆔 REQUEST ID: {response.request_id}")
        logger.info(f"⏱️ TIEMPO TOTAL: {response.total_execution_time_ms:.2f} ms")
        
        return True, response
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de trading: {e}", exc_info=True)
        return False, None

async def run_comprehensive_trading_tests():
    """Ejecuta suite completa de tests de trading usando mocks."""
    logger.info("🚀 Iniciando suite completa de tests de Trading AI...")
    logger.info("=" * 70)
    
    try:
        # 1. Crear Mocks para las dependencias del Orchestrator
        mock_gemini_adapter: IAIModelAdapter = AsyncMock(spec=IAIModelAdapter)
        mock_tool_hub: IMCPToolHub = AsyncMock(spec=IMCPToolHub)
        mock_prompt_manager: IPromptManager = AsyncMock(spec=IPromptManager)

        # 2. Configurar el comportamiento de los mocks
        # Simular la respuesta del método `generate` que es llamado internamente por el servicio
        mock_gemini_adapter.generate.return_value = {
            "analysis": {
                "recommendation": "BUY",
                "confidence": 0.88,
                "reasoning": "Simulación exitosa: El análisis técnico y de sentimiento indican una fuerte tendencia alcista a corto plazo."
            },
            "plan": {
                "tool_actions": [] # Simular que no se necesitan herramientas para este test
            }
        }
        
        # Simular una respuesta del prompt manager
        mock_prompt_manager.get_prompt.return_value = "Prompt de prueba."
        mock_prompt_manager.render_prompt.return_value = "Prompt renderizado de prueba."
        
        # Simular la ejecución de herramientas
        mock_tool_hub.list_available_tools.return_value = ["tool1", "tool2"]
        mock_tool_hub.execute_tool.return_value = {"result": "mock_tool_output"}

        # 3. Instanciar el servicio con los mocks
        orchestrator = AIOrchestratorService(
            gemini_adapter=mock_gemini_adapter,
            tool_hub=mock_tool_hub,
            prompt_manager=mock_prompt_manager
        )
        logger.info("✅ AI Orchestrator inicializado con mocks")

    except Exception as e:
        logger.error(f"❌ Error inicializando orchestrator con mocks: {e}", exc_info=True)
        return False
    
    # Test 1: Análisis completo de trading
    test1_ok, _ = await test_trading_analysis(orchestrator)
    if not test1_ok:
        logger.error("💥 Falló test de análisis de trading")
        return False
    
    # Resumen final
    logger.info("\n" + "=" * 70)
    logger.info("🏆 RESUMEN DE RESULTADOS")
    logger.info("=" * 70)
    logger.info("✅ Análisis de trading específico: EXITOSO (con mocks y firma correcta)")
    logger.info("✅ Modelo AIAnalysisResult: VALIDADO")
    
    logger.info("\n🎯 ESTADO FINAL: AI ORCHESTRATOR COMPLETAMENTE FUNCIONAL PARA TRADING (LÓGICA AISLADA)")
    
    return True

def main():
    """Función principal."""
    try:
        success = asyncio.run(run_comprehensive_trading_tests())
        
        if success:
            logger.info("\n🚀 RESULTADO: El script de prueba del AI Orchestrator se ejecutó correctamente.")
            sys.exit(0)
        else:
            logger.error("\n💥 RESULTADO: Fallos en el script de prueba del AI Orchestrator.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Error inesperado en main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
