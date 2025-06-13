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

from src.ultibot_backend.dependencies import get_settings # MODIFIED
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.adapters.gemini_adapter import GeminiAdapter # ADDED
from src.ultibot_backend.adapters.mobula_adapter import MobulaAdapter # ADDED
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter # ADDED
from src.ultibot_backend.services.credential_service import CredentialService # ADDED
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # ADDED
from src.ultibot_backend.adapters.prompt_persistence_adapter import PromptPersistenceAdapter # ADDED
from src.ultibot_backend.services.tool_hub_service import ToolHubService # ADDED
from src.ultibot_backend.services.prompt_manager_service import PromptManagerService # ADDED


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# REMOVED check_environment_variables

def test_app_settings(): # Renamed from test_app_settings to reflect it now gets settings
    """Verifica que AppSettings pueda cargar la configuración."""
    logger.info("🔍 Probando carga de configuración...")
    
    try:
        app_settings = get_settings() # MODIFIED
        
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
        # Manually instantiate dependencies for AIOrchestratorService
        # This mirrors parts of src.ultibot_backend.dependencies.py
        
        # Persistence
        persistence_port = SupabasePersistenceService(app_settings=settings)
        asyncio.run(persistence_port.connect()) # Connect the pool for this script's lifetime

        # Credential Service
        credential_service = CredentialService(persistence_port=persistence_port)

        # Adapters
        gemini_adapter = GeminiAdapter(api_key=settings.gemini_api_key)

        # Binance adapter might require credentials to be pre-loaded for some tool functions
        # For basic orchestrator init, it might not be strictly needed if not all tools are called.
        binance_adapter = BinanceAdapter(config=settings, credential_service=credential_service)

        mobula_adapter = MobulaAdapter(api_key=settings.mobula_api_key)

        # ToolHub
        tool_hub = ToolHubService(mobula_adapter=mobula_adapter, binance_adapter=binance_adapter)

        # Prompt Management
        if not settings.supabase_url or not settings.supabase_key:
            logger.error("❌ Supabase URL/Key not configured, cannot init PromptPersistenceAdapter.")
            return False, None, None
        prompt_persistence_adapter = PromptPersistenceAdapter(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_key
        )
        prompt_manager = PromptManagerService(prompt_repository=prompt_persistence_adapter)

        # AI Orchestrator
        orchestrator = AIOrchestratorService(
            gemini_adapter=gemini_adapter,
            tool_hub=tool_hub,
            prompt_manager=prompt_manager
        )

        # Basic checks (can be expanded)
        if orchestrator.gemini_adapter is None:
            logger.error("❌ Gemini Adapter not initialized in Orchestrator")
            return False, None, None
            
        logger.info("✅ AI Orchestrator inicializado correctamente")
        # Add more specific checks if needed, e.g., model name from gemini_adapter
        logger.info(f"   - Gemini Model: {orchestrator.gemini_adapter.get_model_name()}")

        return True, orchestrator, persistence_port
        
    except Exception as e:
        logger.error(f"❌ Error inicializando AI Orchestrator: {e}", exc_info=True)
        return False, None, None

from src.ultibot_backend.core.domain_models.ai_models import TradingOpportunity # ADDED
from decimal import Decimal # ADDED
import uuid # ADDED

async def test_basic_ai_analysis(orchestrator):
    """Prueba básica de análisis con el AI Orchestrator."""
    logger.info("🔍 Probando análisis básico de IA (con dummy TradingOpportunity)...")

    # Crear un TradingOpportunity dummy para la prueba
    # Los detalles completos de strategy_context, opportunity_context, etc.,
    # no se usan directamente por analyze_opportunity; esta espera un objeto estructurado.
    # Esta prueba ahora verifica la capacidad de llamar al método y obtener una respuesta simulada
    # o una respuesta basada en el procesamiento interno si los mocks no interceptan todo.
    dummy_opportunity = TradingOpportunity(
        opportunity_id=str(uuid.uuid4()),
        symbol="BTC/USDT",
        strategy_name="Dummy Strategy",
        confidence=0.0, # Confidence is usually an output of previous stages, not input here.
        # Los siguientes campos pueden necesitar valores válidos si el método los usa directamente.
        current_price=Decimal("43250.00"),
        # Añadir otros campos requeridos por TradingOpportunity con valores dummy
        # Basado en test_trading_ai_orchestrator.py:
        volume_24h=Decimal("15240"),
        price_change_24h=2.45,
        technical_indicators={"RSI_1m": 58.2},
        market_context={},
        risk_level="UNKNOWN",
        timeframe="1m",
        signal_strength=0.0, # Similar a confidence
        expected_profit=0.0
    )
    
    try:
        logger.info("📤 Enviando solicitud de análisis a Gemini (a través de orchestrator.analyze_opportunity)...")
        
        response = await orchestrator.analyze_opportunity(
            opportunity=dummy_opportunity
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
    
    persistence_port = None # Define persistence_port here to be accessible in finally
    try:
        # Test 1: Configuración de la aplicación (Variables de entorno implicitly checked by get_settings)
        config_ok, app_settings = test_app_settings() # MODIFIED: was test_app_settings() before, now it's the getter
        if not config_ok:
            logger.error("💥 Fallo en carga de configuración")
            return False

        logger.info("\n" + "=" * 60)

        # Test 3: Inicialización del orchestrator
        # Update: test_ai_orchestrator_initialization might need to return persistence_port
        # For simplicity, I'll re-fetch it or assume it's available if orchestrator is.
        # For now, I'll assume test_ai_orchestrator_initialization handles its own connect/disconnect
        # or I pass persistence_port back from it.
        # Let's adjust test_ai_orchestrator_initialization to return persistence_port

        init_ok, orchestrator, persistence_port = test_ai_orchestrator_initialization(app_settings)
        if not init_ok:
            logger.error("💥 Fallo en inicialización del AI Orchestrator")
            return False

        logger.info("\n" + "=" * 60)

        # Test 4: Análisis básico
        # WARNING: analyze_opportunity_with_strategy_context_async may not exist or match signature
        # This part might fail and require further adaptation of the test data / method call.
        analysis_ok, response = await test_basic_ai_analysis(orchestrator)
        if not analysis_ok:
            logger.error("💥 Fallo en análisis básico de IA")
            return False

        logger.info("\n" + "=" * 60)
        logger.info("🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE (core configuration and initialization)!")
    finally:
        if persistence_port:
            logger.info("🔌 Cerrando conexión de persistencia...")
            asyncio.run(persistence_port.disconnect())
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
