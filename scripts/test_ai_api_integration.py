#!/usr/bin/env python3
"""
Script de prueba de integración completa del AI Orchestrator a través de la API.
Demuestra que el orquestrador está activado y accesible desde la UI.
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
import httpx

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de la API
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

async def test_ai_health_check():
    """Verifica que el servicio de IA esté saludable."""
    logger.info("🔍 Verificando salud del servicio de IA...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/ai/health")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Servicio de IA: {data['status']}")
                logger.info(f"   - Modelo: {data.get('model', 'N/A')}")
                logger.info(f"   - Configurado: {data.get('configured', False)}")
                return True, data
            else:
                logger.error(f"❌ Health check falló: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error en health check: {e}")
            return False, None

async def test_ai_models_info():
    """Obtiene información sobre los modelos de IA."""
    logger.info("🔍 Obteniendo información de modelos de IA...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/ai/models/info")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Información de modelos obtenida:")
                logger.info(f"   - Proveedor: {data['primary_model']['provider']}")
                logger.info(f"   - Modelo: {data['primary_model']['name']}")
                logger.info(f"   - Capacidades: {data['capabilities']}")
                return True, data
            else:
                logger.error(f"❌ Fallo al obtener info de modelos: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo info de modelos: {e}")
            return False, None

async def test_ai_trading_analysis():
    """Prueba el análisis completo de trading a través de la API."""
    logger.info("🎯 Probando análisis de trading a través de API...")
    
    # Datos de prueba realistas
    request_data = {
        "strategy_context": """
        ESTRATEGIA: Scalping BTC/USDT
        - Tipo: Scalping de alta frecuencia
        - Timeframe: 1 minuto
        - Stop Loss: 0.8%
        - Take Profit: 1.5%
        - Capital por operación: 2% del portafolio
        """,
        "opportunity_context": """
        OPORTUNIDAD DETECTADA:
        - Par: BTC/USDT
        - Precio actual: $43,520.75
        - Cambio 24h: +2.87%
        - Volumen 24h: 16,890 BTC
        - RSI (1m): 58.4
        - MACD: Señal alcista confirmada
        - Tendencia: Alcista de corto plazo
        """,
        "historical_context": """
        HISTORIAL RECIENTE:
        - Win Rate: 82% (últimas 10 operaciones)
        - P&L promedio: +1.24%
        - Sharpe Ratio: 2.1
        - Última operación: ÉXITO (+1.67%)
        """,
        "tool_outputs": """
        DATOS DE HERRAMIENTAS:
        - Binance WebSocket: Datos en tiempo real ✅
        - Análisis técnico: Señales alcistas confirmadas
        - Mobula API: Sentimiento positivo (+71/100)
        - Volume Profile: Liquidez adecuada
        """,
        "trading_mode": "paper"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/ai/analyze/trading",
                json=request_data,
                headers=HEADERS
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Análisis de trading completado!")
                logger.info("=" * 50)
                logger.info("📊 RESULTADO DEL ANÁLISIS")
                logger.info("=" * 50)
                logger.info(f"🎯 RECOMENDACIÓN: {data['recommendation']}")
                logger.info(f"📈 CONFIANZA: {data['confidence']:.1%}")
                logger.info(f"🧠 RAZONAMIENTO: {data['reasoning'][:100]}...")
                
                if data.get('warnings'):
                    logger.info(f"⚠️  ADVERTENCIAS: {data['warnings'][:100]}...")
                
                if data.get('entry_price'):
                    logger.info(f"💰 PRECIO ENTRADA: ${data['entry_price']:,.2f}")
                if data.get('stop_loss'):
                    logger.info(f"🛑 STOP LOSS: ${data['stop_loss']:,.2f}")
                if data.get('take_profit'):
                    logger.info(f"🎯 TAKE PROFIT: ${data['take_profit']:,.2f}")
                
                logger.info(f"🔥 Alta Confianza: {data['is_high_confidence']}")
                logger.info(f"💎 Apto para Real: {data['is_suitable_for_real_trading']}")
                logger.info(f"📝 Resumen: {data['summary']}")
                logger.info(f"🆔 Analysis ID: {data['analysis_id']}")
                
                return True, data
            else:
                logger.error(f"❌ Análisis falló: {response.status_code}")
                logger.error(f"   Respuesta: {response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error en análisis de trading: {e}")
            return False, None

async def test_ai_quick_analysis():
    """Prueba el análisis rápido a través de la API."""
    logger.info("⚡ Probando análisis rápido...")
    
    request_data = {
        "symbol": "BTC/USDT",
        "current_price": 43520.75,
        "strategy_type": "scalping",
        "timeframe": "1m"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/ai/analyze/quick",
                json=request_data,
                headers=HEADERS
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Análisis rápido completado!")
                logger.info(f"📊 Resultado: {data['recommendation']} ({data['confidence']:.1%})")
                logger.info(f"📝 Resumen: {data['summary']}")
                return True, data
            else:
                logger.error(f"❌ Análisis rápido falló: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error en análisis rápido: {e}")
            return False, None

async def test_telegram_message_format(analysis_data):
    """Verifica el formato del mensaje de Telegram."""
    logger.info("📱 Verificando formato de mensaje Telegram...")
    
    if 'telegram_message' in analysis_data:
        telegram_msg = analysis_data['telegram_message']
        logger.info("✅ Mensaje de Telegram generado:")
        logger.info("-" * 50)
        logger.info(telegram_msg)
        logger.info("-" * 50)
        return True
    else:
        logger.error("❌ No se encontró mensaje de Telegram")
        return False

async def run_comprehensive_api_tests():
    """Ejecuta todos los tests de integración de la API."""
    logger.info("🚀 Iniciando tests de integración completa de AI API...")
    logger.info("=" * 70)
    
    results = {
        "health_check": False,
        "models_info": False,
        "trading_analysis": False,
        "quick_analysis": False,
        "telegram_format": False
    }
    
    try:
        # Test 1: Health Check
        health_ok, health_data = await test_ai_health_check()
        results["health_check"] = health_ok
        
        if not health_ok:
            logger.error("💥 Health check falló - abortando tests")
            return False, results
        
        # Test 2: Models Info
        models_ok, models_data = await test_ai_models_info()
        results["models_info"] = models_ok
        
        # Test 3: Trading Analysis (el más importante)
        analysis_ok, analysis_data = await test_ai_trading_analysis()
        results["trading_analysis"] = analysis_ok
        
        if analysis_ok and analysis_data:
            # Test 4: Telegram Message Format
            telegram_ok = await test_telegram_message_format(analysis_data)
            results["telegram_format"] = telegram_ok
        
        # Test 5: Quick Analysis
        quick_ok, quick_data = await test_ai_quick_analysis()
        results["quick_analysis"] = quick_ok
        
        # Resumen de resultados
        logger.info("\n" + "=" * 70)
        logger.info("🏆 RESUMEN DE TESTS DE INTEGRACIÓN")
        logger.info("=" * 70)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} - {test_name.replace('_', ' ').title()}")
        
        logger.info(f"\n📊 RESULTADO: {passed_tests}/{total_tests} tests pasaron")
        
        if passed_tests == total_tests:
            logger.info("🎉 ¡TODOS LOS TESTS DE INTEGRACIÓN PASARON!")
            logger.info("🚀 AI ORCHESTRATOR COMPLETAMENTE ACTIVADO Y ACCESIBLE VÍA API")
            return True, results
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} tests fallaron")
            return False, results
            
    except Exception as e:
        logger.error(f"💥 Error inesperado en tests: {e}")
        return False, results

def main():
    """Función principal."""
    logger.info("🎯 Test de Integración Completa - AI Orchestrator API")
    logger.info("=" * 70)
    
    try:
        success, results = asyncio.run(run_comprehensive_api_tests())
        
        if success:
            logger.info("\n🎊 RESULTADO FINAL: ¡AI ORCHESTRATOR COMPLETAMENTE FUNCIONAL!")
            logger.info("✅ El orquestrador de IA está activado y listo para dar consejos de trading")
            logger.info("✅ Accesible a través de la API REST")
            logger.info("✅ Integrado con modelos de trading especializados")
            logger.info("✅ Preparado para integración con la UI")
            sys.exit(0)
        else:
            logger.error("\n💥 RESULTADO FINAL: Algunos tests fallaron")
            logger.error("❌ Revisar configuración y dependencias")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
