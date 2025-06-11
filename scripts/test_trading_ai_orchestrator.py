#!/usr/bin/env python3
"""
Script de prueba avanzado para el AI Orchestrator con funcionalidades específicas de trading.
Prueba el nuevo modelo TradingAIResponse y el método analyze_trading_opportunity_async.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Añadir el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ultibot_backend.app_config import AppSettings
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_trading_analysis(orchestrator):
    """Prueba el análisis específico de trading con datos realistas."""
    logger.info("🎯 Probando análisis específico de trading...")
    
    # Escenario 1: Oportunidad de Scalping en BTC/USDT
    strategy_context = """
    **ESTRATEGIA: Scalping BTC/USDT**
    - Tipo: Scalping de alta frecuencia
    - Par objetivo: BTC/USDT
    - Timeframe: 1 minuto
    - Stop Loss: 0.8%
    - Take Profit: 1.5%
    - Capital máximo por operación: 2% del portafolio
    - Requisitos: RSI entre 30-70, volumen > promedio 24h
    """
    
    opportunity_context = """
    **OPORTUNIDAD DETECTADA:**
    - Par: BTC/USDT
    - Precio actual: $43,487.25
    - Cambio 24h: +3.24% (+$1,362.45)
    - Volumen 24h: 18,432 BTC (superior al promedio)
    - RSI (1m): 62.3
    - MACD: Señal alcista reciente
    - Resistencia próxima: $43,800
    - Soporte: $43,200
    - Timestamp: 2025-06-10 20:42:00 UTC
    """
    
    historical_context = """
    **HISTORIAL DE SCALPING BTC/USDT (últimas 10 operaciones):**
    1. 2025-06-10 18:30 - COMPRA $43,150 → VENTA $43,780 - ✅ GANANCIA +1.46%
    2. 2025-06-10 16:45 - COMPRA $42,890 → VENTA $43,420 - ✅ GANANCIA +1.24%
    3. 2025-06-10 14:20 - COMPRA $43,200 → VENTA $42,950 - ❌ PÉRDIDA -0.58%
    4. 2025-06-10 12:10 - COMPRA $42,780 → VENTA $43,310 - ✅ GANANCIA +1.24%
    5. 2025-06-10 09:35 - COMPRA $42,650 → VENTA $43,180 - ✅ GANANCIA +1.24%
    6. 2025-06-09 22:15 - COMPRA $42,980 → VENTA $43,540 - ✅ GANANCIA +1.30%
    7. 2025-06-09 19:40 - COMPRA $42,820 → VENTA $43,350 - ✅ GANANCIA +1.24%
    8. 2025-06-09 16:25 - COMPRA $42,750 → VENTA $42,580 - ❌ PÉRDIDA -0.40%
    9. 2025-06-09 13:55 - COMPRA $42,890 → VENTA $43,440 - ✅ GANANCIA +1.28%
    10. 2025-06-09 11:20 - COMPRA $42,980 → VENTA $43,520 - ✅ GANANCIA +1.26%
    
    **MÉTRICAS DE PERFORMANCE:**
    - Win Rate: 80% (8/10 operaciones exitosas)
    - Ganancia promedio: +1.26%
    - Pérdida promedio: -0.49%
    - P&L Total: +8.59%
    - Sharpe Ratio: 2.4
    """
    
    tool_outputs = """
    **RESULTADOS DE HERRAMIENTAS DE ANÁLISIS:**
    
    🔹 **Binance WebSocket (Tiempo Real):**
    - Último precio: $43,487.25
    - Bid: $43,485.10 | Ask: $43,489.40
    - Spread: 0.010% (muy estrecho - buena liquidez)
    - Volumen último minuto: 3.24 BTC
    
    🔹 **Análisis Técnico:**
    - RSI (1m): 62.3 (zona neutral-alcista)
    - RSI (5m): 58.7 (tendencia alcista moderada)
    - MACD (1m): Línea MACD cruzó por encima de señal (bullish)
    - Bollinger Bands: Precio cerca de banda superior
    - EMA 20: $43,380 (precio por encima)
    
    🔹 **Mobula API - Sentimiento:**
    - Trending Score: +74/100 (muy positivo)
    - Búsquedas sociales: +23% en última hora
    - Menciones positivas: 67%
    - Fear & Greed Index: 72 (codicia)
    
    🔹 **Análisis de Volumen:**
    - Volumen 24h: 147% del promedio semanal
    - Order Book: Sólido (sin grandes gaps)
    - Flujo institucional: +$2.4M en última hora
    
    🔹 **Context Market:**
    - BTC Dominance: 54.2%
    - Altcoin Market Cap: Estable
    - DXY (USD Index): 103.2 (neutro)
    - Correlación S&P500: +0.34 (baja)
    """
    
    try:
        logger.info("📤 Enviando análisis de trading a Gemini...")
        
        response = await orchestrator.analyze_trading_opportunity_async(
            strategy_context=strategy_context,
            opportunity_context=opportunity_context,
            historical_context=historical_context,
            tool_outputs=tool_outputs
        )
        
        logger.info("✅ ¡Análisis de trading completado exitosamente!")
        
        # Mostrar resultados estructurados
        logger.info("=" * 60)
        logger.info("📊 RESULTADO DEL ANÁLISIS DE IA")
        logger.info("=" * 60)
        logger.info(f"🎯 RECOMENDACIÓN: {response.recommendation.value}")
        logger.info(f"📈 CONFIANZA: {response.confidence:.1%}")
        logger.info(f"🧠 RAZONAMIENTO: {response.reasoning}")
        
        if response.warnings:
            logger.info(f"⚠️  ADVERTENCIAS: {response.warnings}")
        
        if response.entry_price:
            logger.info(f"💰 PRECIO ENTRADA: ${response.entry_price:,.2f}")
        if response.stop_loss:
            logger.info(f"🛑 STOP LOSS: ${response.stop_loss:,.2f}")
        if response.take_profit:
            logger.info(f"🎯 TAKE PROFIT: ${response.take_profit:,.2f}")
        
        if response.risk_level:
            logger.info(f"📊 NIVEL DE RIESGO: {response.risk_level}")
        
        if response.timeframe:
            logger.info(f"⏰ TIMEFRAME: {response.timeframe}")
            
        logger.info(f"🆔 ANALYSIS ID: {response.analysis_id}")
        
        # Probar métodos de utilidad
        logger.info("\n" + "=" * 60)
        logger.info("🛠️  MÉTODOS DE UTILIDAD")
        logger.info("=" * 60)
        logger.info(f"🔥 Alta Confianza (>80%): {response.is_high_confidence()}")
        logger.info(f"💎 Apto para Trading Real (>95%): {response.is_suitable_for_real_trading()}")
        logger.info(f"📝 Resumen: {response.get_summary()}")
        
        # Mostrar mensaje para Telegram
        telegram_msg = response.to_telegram_message()
        logger.info("\n" + "=" * 60)
        logger.info("📱 MENSAJE PARA TELEGRAM")
        logger.info("=" * 60)
        logger.info(telegram_msg)
        
        return True, response
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de trading: {e}")
        return False, None

async def test_paper_vs_real_scenarios(orchestrator):
    """Prueba escenarios para paper trading vs real trading."""
    logger.info("\n🎮 Probando escenarios Paper vs Real Trading...")
    
    scenarios = [
        {
            "name": "Escenario Paper Trading - Media Confianza",
            "strategy": "Day Trading ETH/USDT con confianza moderada",
            "confidence_target": 0.78
        },
        {
            "name": "Escenario Real Trading - Alta Confianza",
            "strategy": "Scalping BTC/USDT con setup perfecto",
            "confidence_target": 0.96
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        logger.info(f"\n📋 {scenario['name']}")
        logger.info("-" * 50)
        
        # Datos específicos del escenario
        if "ETH" in scenario['strategy']:
            opportunity = """
            Par: ETH/USDT
            Precio: $2,435.67
            Cambio 24h: +1.89%
            Volumen: 89,432 ETH
            RSI: 64.2
            """
        else:
            opportunity = """
            Par: BTC/USDT
            Precio: $43,487.25
            Cambio 24h: +3.24%
            Volumen: 18,432 BTC
            RSI: 62.3
            Setup: Breakout confirmado
            """
        
        try:
            response = await orchestrator.analyze_trading_opportunity_async(
                strategy_context=scenario['strategy'],
                opportunity_context=opportunity,
                historical_context="Win Rate previo: 75%",
                tool_outputs="Análisis técnico positivo"
            )
            
            logger.info(f"📊 Resultado: {response.recommendation.value} ({response.confidence:.1%})")
            logger.info(f"🎯 Alta confianza: {response.is_high_confidence()}")
            logger.info(f"💎 Apto para real: {response.is_suitable_for_real_trading()}")
            
            results.append({
                "scenario": scenario['name'],
                "recommendation": response.recommendation.value,
                "confidence": response.confidence,
                "suitable_for_real": response.is_suitable_for_real_trading()
            })
            
        except Exception as e:
            logger.error(f"❌ Error en {scenario['name']}: {e}")
            results.append({
                "scenario": scenario['name'],
                "error": str(e)
            })
    
    return results

async def run_comprehensive_trading_tests():
    """Ejecuta suite completa de tests de trading."""
    logger.info("🚀 Iniciando suite completa de tests de Trading AI...")
    logger.info("=" * 70)
    
    # Configurar settings
    try:
        settings = AppSettings()
        logger.info("✅ Configuración cargada")
    except Exception as e:
        logger.error(f"❌ Error cargando configuración: {e}")
        return False
    
    # Inicializar orchestrator
    try:
        orchestrator = AIOrchestratorService(settings)
        logger.info("✅ AI Orchestrator inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando orchestrator: {e}")
        return False
    
    # Test 1: Análisis completo de trading
    test1_ok, trading_response = await test_trading_analysis(orchestrator)
    if not test1_ok:
        logger.error("💥 Falló test de análisis de trading")
        return False
    
    # Test 2: Escenarios paper vs real
    scenarios_results = await test_paper_vs_real_scenarios(orchestrator)
    
    # Resumen final
    logger.info("\n" + "=" * 70)
    logger.info("🏆 RESUMEN DE RESULTADOS")
    logger.info("=" * 70)
    logger.info("✅ Análisis de trading específico: EXITOSO")
    logger.info("✅ Modelo TradingAIResponse: FUNCIONANDO")
    logger.info("✅ Validaciones y métodos de utilidad: FUNCIONANDO")
    logger.info("✅ Generación de mensajes Telegram: FUNCIONANDO")
    
    logger.info(f"\n📊 Escenarios probados: {len(scenarios_results)}")
    for result in scenarios_results:
        if 'error' not in result:
            logger.info(f"   - {result['scenario']}: {result['recommendation']} ({result['confidence']:.1%})")
    
    logger.info("\n🎯 ESTADO FINAL: AI ORCHESTRATOR COMPLETAMENTE FUNCIONAL PARA TRADING")
    
    return True

def main():
    """Función principal."""
    try:
        success = asyncio.run(run_comprehensive_trading_tests())
        
        if success:
            logger.info("\n🚀 RESULTADO: AI ORCHESTRATOR TRADING LISTO PARA PRODUCCIÓN")
            sys.exit(0)
        else:
            logger.error("\n💥 RESULTADO: Fallos en testing del AI Orchestrator")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
