#!/usr/bin/env python3
"""
Script de validación para el AI Orchestrator Service de UltiBotInversiones.
Verifica la configuración básica y conexión con Gemini API.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Añadir el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ultibot_backend.app_config import get_app_settings
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Verifica que las variables de entorno necesarias estén configuradas."""
    logger.info("🔍 Verificando variables de entorno...")
    
    required_vars = [
        'GEMINI_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'CREDENTIAL_ENCRYPTION_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            logger.info(f"✅ {var}: Configurada")
    
    if missing_vars:
        logger.error(f"❌ Variables faltantes: {missing_vars}")
        return False
    
    logger.info("✅ Todas las variables de entorno requeridas están configuradas")
    return True

def test_app_settings():
    """Verifica que AppSettings pueda cargar la configuración."""
    logger.info("🔍 Probando carga de configuración...")
    
    try:
        app_settings = get_app_settings()
        
        # Verificar campos críticos
        if not app_settings.gemini_api_key:
            logger.error("❌ GEMINI_API_KEY no está disponible en AppSettings")
            return False, None
            
        if not app_settings.supabase_url:
            logger.error("❌ SUPABASE_URL no está disponible en AppSettings")
            return False, None
            
        logger.info(f"✅ Configuración cargada correctamente")
        logger.info(f"   - Gemini API Key: {'*' * (len(app_settings.gemini_api_key) - 4) + app_settings.gemini_api_key[-4:]}")
        logger.info(f"   - Supabase URL: {app_settings.supabase_url}")
        logger.info(f"   - Fixed User ID: {app_settings.fixed_user_id}")
        
        return True, app_settings
        
    except Exception as e:
        logger.error(f"❌ Error cargando configuración: {e}")
        return False, None

def test_ai_orchestrator_initialization(settings):
    """Verifica que el AI Orchestrator se pueda inicializar."""
    logger.info("🔍 Probando inicialización del AI Orchestrator...")
    
    try:
        orchestrator = AIOrchestratorService(settings)
        
        if orchestrator.llm is None:
            logger.error("❌ LLM no se inicializó correctamente")
            return False, None
            
        if orchestrator.parser is None:
            logger.error("❌ Parser no se inicializó correctamente")
            return False, None
            
        if orchestrator.prompt_template is None:
            logger.error("❌ Prompt template no se inicializó correctamente")
            return False, None
            
        logger.info("✅ AI Orchestrator inicializado correctamente")
        logger.info(f"   - Modelo LLM: {orchestrator.llm.model}")
        logger.info(f"   - Temperatura: {orchestrator.llm.temperature}")
        
        return True, orchestrator
        
    except Exception as e:
        logger.error(f"❌ Error inicializando AI Orchestrator: {e}")
        return False, None

async def test_basic_ai_analysis(orchestrator):
    """Prueba básica de análisis con el AI Orchestrator."""
    logger.info("🔍 Probando análisis básico de IA...")
    
    # Datos de prueba
    strategy_context = """
    Estrategia: Scalping en BTC/USDT
    Parámetros: 
    - Stop Loss: 1%
    - Take Profit: 2%
    - Timeframe: 1m
    """
    
    opportunity_context = """
    Par: BTC/USDT
    Precio actual: $43,250.00
    Cambio 24h: +2.45%
    Volumen 24h: 15,240 BTC
    RSI: 58.2
    """
    
    historical_context = """
    Últimas 5 operaciones:
    1. COMPRA a $42,800 - ÉXITO (+1.8%)
    2. VENTA a $43,100 - ÉXITO (+1.2%)
    3. COMPRA a $42,950 - PÉRDIDA (-0.8%)
    4. VENTA a $43,200 - ÉXITO (+1.5%)
    5. COMPRA a $43,000 - ÉXITO (+2.1%)
    Win Rate: 80%
    """
    
    tool_outputs = """
    Binance API: Datos de mercado actualizados
    Mobula API: BTC trending positivamente (+15% en búsquedas)
    Análisis técnico: Tendencia alcista de corto plazo
    """
    
    try:
        logger.info("📤 Enviando solicitud de análisis a Gemini...")
        
        response = await orchestrator.analyze_opportunity_with_strategy_context_async(
            strategy_context=strategy_context,
            opportunity_context=opportunity_context,
            historical_context=historical_context,
            tool_outputs=tool_outputs
        )
        
        logger.info("✅ Análisis completado exitosamente!")
        logger.info(f"📊 Respuesta de IA:")
        logger.info(f"   - Contenido: {response.content[:200]}...")
        
        if response.metadata:
            logger.info(f"   - Metadata: {response.metadata}")
            
        if response.error:
            logger.warning(f"   - Error reportado: {response.error}")
        
        return True, response
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de IA: {e}")
        return False, None

async def run_validation_tests():
    """Ejecuta todos los tests de validación."""
    logger.info("🚀 Iniciando validación del AI Orchestrator...")
    logger.info("=" * 60)
    
    # Test 1: Variables de entorno
    if not check_environment_variables():
        logger.error("💥 Fallo en verificación de variables de entorno")
        return False
    
    logger.info("\n" + "=" * 60)
    
    # Test 2: Configuración de la aplicación
    config_ok, app_settings = test_app_settings()
    if not config_ok:
        logger.error("💥 Fallo en carga de configuración")
        return False
    
    logger.info("\n" + "=" * 60)
    
    # Test 3: Inicialización del orchestrator
    init_ok, orchestrator = test_ai_orchestrator_initialization(app_settings)
    if not init_ok:
        logger.error("💥 Fallo en inicialización del AI Orchestrator")
        return False
    
    logger.info("\n" + "=" * 60)
    
    # Test 4: Análisis básico
    analysis_ok, response = await test_basic_ai_analysis(orchestrator)
    if not analysis_ok:
        logger.error("💥 Fallo en análisis básico de IA")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
    logger.info("✅ El AI Orchestrator está correctamente configurado y funcionando")
    logger.info("🚀 Listo para dar consejos de trading e inversiones")
    
    return True

def main():
    """Función principal."""
    try:
        # Ejecutar tests asincrónicos
        success = asyncio.run(run_validation_tests())
        
        if success:
            logger.info("\n🎯 RESULTADO: AI Orchestrator ACTIVADO y FUNCIONAL")
            sys.exit(0)
        else:
            logger.error("\n💥 RESULTADO: Fallo en activación del AI Orchestrator")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
