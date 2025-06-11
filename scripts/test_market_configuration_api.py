#!/usr/bin/env python3
"""
Script de pruebas para validar los nuevos métodos del API Client de configuración de mercado.

Este script prueba la integración entre el frontend y backend para todas las funcionalidades
de configuración avanzada de filtros de mercado implementadas en la Task 11.3.1.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from src.ultibot_ui.services.api_client import UltiBotAPIClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketConfigurationAPITester:
    """Tester para los nuevos métodos del API Client de configuración de mercado."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.api_client = None
        
    async def setup(self):
        """Inicializa el cliente HTTP y API."""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        self.api_client = UltiBotAPIClient(self.client)
        logger.info(f"Cliente API inicializado para {self.base_url}")
        
    async def cleanup(self):
        """Limpia recursos."""
        if self.client:
            await self.client.aclose()
            
    async def test_backend_connectivity(self) -> bool:
        """Verifica conectividad básica con el backend."""
        try:
            logger.info("🔌 Probando conectividad con el backend...")
            trading_mode = await self.api_client.get_trading_mode()
            logger.info(f"✅ Backend conectado. Modo actual: {trading_mode}")
            return True
        except Exception as e:
            logger.error(f"❌ Error de conectividad: {e}")
            return False
    
    async def test_convenience_methods(self):
        """Prueba los métodos de conveniencia para obtener opciones disponibles."""
        logger.info("\n📋 Probando métodos de conveniencia...")
        
        try:
            # Market cap ranges
            ranges = await self.api_client.get_available_market_cap_ranges()
            logger.info(f"✅ Rangos de market cap: {ranges}")
            
            # Volume filters
            volume_filters = await self.api_client.get_available_volume_filters()
            logger.info(f"✅ Filtros de volumen: {volume_filters}")
            
            # Trend directions
            trends = await self.api_client.get_available_trend_directions()
            logger.info(f"✅ Direcciones de tendencia: {trends}")
            
        except Exception as e:
            logger.error(f"❌ Error en métodos de conveniencia: {e}")
            
    async def test_scan_configuration_validation(self):
        """Prueba la validación client-side de configuraciones."""
        logger.info("\n🔍 Probando validación de configuraciones...")
        
        # Configuración válida
        valid_config = {
            "min_price_change_24h_percent": -5.0,
            "max_price_change_24h_percent": 15.0,
            "min_rsi": 30.0,
            "max_rsi": 70.0,
            "min_volume_24h_usd": 1_000_000
        }
        
        validation = await self.api_client.validate_scan_configuration(valid_config)
        logger.info(f"✅ Configuración válida: {validation}")
        
        # Configuración inválida
        invalid_config = {
            "min_price_change_24h_percent": 20.0,  # Mayor que el máximo
            "max_price_change_24h_percent": 10.0,
            "min_rsi": 80.0,  # Mayor que el máximo
            "max_rsi": 30.0,
            "min_volume_24h_usd": 50_000_000  # Muy restrictivo
        }
        
        validation = await self.api_client.validate_scan_configuration(invalid_config)
        logger.info(f"⚠️ Configuración inválida detectada: {validation}")
        
    async def test_system_presets(self):
        """Prueba la obtención de presets del sistema."""
        logger.info("\n🎯 Probando presets del sistema...")
        
        try:
            system_presets = await self.api_client.get_system_presets()
            logger.info(f"✅ Presets del sistema obtenidos: {len(system_presets)} presets")
            
            for preset in system_presets:
                logger.info(f"  📌 Preset: {preset.get('name', 'Sin nombre')} - "
                          f"Tipo: {'Sistema' if preset.get('is_system_preset') else 'Usuario'}")
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo presets del sistema: {e}")
            
    async def test_scan_presets_crud(self):
        """Prueba operaciones CRUD de presets de escaneo."""
        logger.info("\n📝 Probando CRUD de presets...")
        
        # Crear preset de prueba
        test_preset = {
            "name": "Test Preset API Client",
            "description": "Preset creado durante pruebas del API Client",
            "scan_configuration": {
                "min_price_change_24h_percent": -10.0,
                "max_price_change_24h_percent": 25.0,
                "market_cap_ranges": ["SMALL_CAP", "MID_CAP"],
                "volume_filter_type": "ABOVE_AVERAGE",
                "min_volume_24h_usd": 5_000_000,
                "trend_direction": "BULLISH",
                "min_rsi": 40.0,
                "max_rsi": 80.0
            },
            "is_system_preset": False
        }
        
        created_preset = None
        
        try:
            # 1. Crear preset
            logger.info("📌 Creando preset de prueba...")
            created_preset = await self.api_client.create_scan_preset(test_preset)
            preset_id = created_preset.get("id")
            logger.info(f"✅ Preset creado con ID: {preset_id}")
            
            # 2. Obtener preset específico
            logger.info(f"📋 Obteniendo preset {preset_id}...")
            retrieved_preset = await self.api_client.get_scan_preset(preset_id)
            logger.info(f"✅ Preset obtenido: {retrieved_preset.get('name')}")
            
            # 3. Listar todos los presets
            logger.info("📋 Listando todos los presets...")
            all_presets = await self.api_client.get_scan_presets(include_system=True)
            logger.info(f"✅ Total de presets: {len(all_presets)}")
            
            # 4. Actualizar preset
            logger.info(f"🔄 Actualizando preset {preset_id}...")
            updated_data = retrieved_preset.copy()
            updated_data["description"] = "Preset actualizado durante pruebas"
            updated_preset = await self.api_client.update_scan_preset(preset_id, updated_data)
            logger.info(f"✅ Preset actualizado: {updated_preset.get('description')}")
            
            # 5. Eliminar preset
            logger.info(f"🗑️ Eliminando preset {preset_id}...")
            deleted = await self.api_client.delete_scan_preset(preset_id)
            logger.info(f"✅ Preset eliminado: {deleted}")
            
        except Exception as e:
            logger.error(f"❌ Error en CRUD de presets: {e}")
            
            # Limpiar en caso de error
            if created_preset and created_preset.get("id"):
                try:
                    await self.api_client.delete_scan_preset(created_preset["id"])
                    logger.info("🧹 Preset de prueba limpiado")
                except:
                    logger.warning("⚠️ No se pudo limpiar el preset de prueba")
                    
    async def test_execute_preset_scan(self):
        """Prueba la ejecución de escaneos con presets."""
        logger.info("\n🚀 Probando ejecución de escaneos...")
        
        try:
            # Obtener presets del sistema para usar en la prueba
            system_presets = await self.api_client.get_system_presets()
            
            if system_presets:
                preset_id = system_presets[0].get("id")
                preset_name = system_presets[0].get("name")
                
                logger.info(f"🎯 Ejecutando escaneo con preset '{preset_name}' (ID: {preset_id})")
                
                # Ejecutar escaneo
                results = await self.api_client.execute_preset_scan(preset_id)
                logger.info(f"✅ Escaneo completado. Resultados obtenidos: {len(results)}")
                
                # Mostrar algunos resultados si los hay
                for i, result in enumerate(results[:3]):  # Mostrar máximo 3
                    symbol = result.get("symbol", "N/A")
                    price_change = result.get("price_change_24h_percent", "N/A")
                    volume = result.get("volume_24h_usd", "N/A")
                    logger.info(f"  📊 {symbol}: {price_change}% cambio, ${volume:,.0f} volumen" 
                              if isinstance(volume, (int, float)) else f"  📊 {symbol}: {price_change}% cambio")
                    
            else:
                logger.warning("⚠️ No hay presets del sistema disponibles para probar")
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando escaneo: {e}")
            
    async def test_custom_market_scan(self):
        """Prueba la ejecución de escaneos personalizados."""
        logger.info("\n🔧 Probando escaneo personalizado...")
        
        # Configuración de escaneo personalizada
        custom_config = {
            "min_price_change_24h_percent": 5.0,  # Mínimo 5% de subida
            "max_price_change_24h_percent": 50.0,  # Máximo 50% de subida
            "market_cap_ranges": ["SMALL_CAP", "MID_CAP"],
            "volume_filter_type": "HIGH_VOLUME",
            "min_volume_24h_usd": 10_000_000,  # Mínimo $10M volumen
            "trend_direction": "BULLISH"
        }
        
        try:
            logger.info("🔍 Ejecutando escaneo personalizado...")
            results = await self.api_client.execute_market_scan(custom_config)
            logger.info(f"✅ Escaneo personalizado completado. Resultados: {len(results)}")
            
            # Mostrar configuración usada
            logger.info("📋 Configuración utilizada:")
            for key, value in custom_config.items():
                logger.info(f"  • {key}: {value}")
                
        except Exception as e:
            logger.error(f"❌ Error en escaneo personalizado: {e}")
            
    async def test_asset_trading_parameters(self):
        """Prueba las operaciones de parámetros de trading por activo."""
        logger.info("\n💼 Probando parámetros de trading por activo...")
        
        # Parámetros de prueba
        test_parameters = {
            "name": "BTC Test Parameters",
            "symbol": "BTCUSDT",
            "confidence_thresholds": {
                "paper_trading": 0.6,
                "real_trading": 0.95
            },
            "position_sizing": {
                "max_position_size_percent": 10.0,
                "min_position_size_usd": 100.0
            },
            "risk_management": {
                "stop_loss_percent": 5.0,
                "take_profit_percent": 15.0,
                "max_daily_trades": 3
            }
        }
        
        created_params = None
        
        try:
            # 1. Listar parámetros existentes
            logger.info("📋 Listando parámetros existentes...")
            existing_params = await self.api_client.get_asset_trading_parameters()
            logger.info(f"✅ Parámetros existentes: {len(existing_params)}")
            
            # 2. Crear nuevos parámetros
            logger.info("📌 Creando parámetros de prueba...")
            created_params = await self.api_client.create_asset_trading_parameters(test_parameters)
            param_id = created_params.get("id")
            logger.info(f"✅ Parámetros creados con ID: {param_id}")
            
            # 3. Obtener parámetros específicos
            logger.info(f"📋 Obteniendo parámetros {param_id}...")
            retrieved_params = await self.api_client.get_asset_trading_parameter(param_id)
            logger.info(f"✅ Parámetros obtenidos: {retrieved_params.get('name')}")
            
            # 4. Actualizar parámetros
            logger.info(f"🔄 Actualizando parámetros {param_id}...")
            updated_data = retrieved_params.copy()
            updated_data["risk_management"]["stop_loss_percent"] = 3.0
            updated_params = await self.api_client.update_asset_trading_parameters(param_id, updated_data)
            logger.info(f"✅ Parámetros actualizados")
            
            # 5. Eliminar parámetros
            logger.info(f"🗑️ Eliminando parámetros {param_id}...")
            deleted = await self.api_client.delete_asset_trading_parameters(param_id)
            logger.info(f"✅ Parámetros eliminados: {deleted}")
            
        except Exception as e:
            logger.error(f"❌ Error en parámetros de trading: {e}")
            
    async def run_all_tests(self):
        """Ejecuta todas las pruebas del API Client."""
        logger.info("🧪 Iniciando pruebas del API Client de configuración de mercado")
        logger.info("=" * 70)
        
        await self.setup()
        
        try:
            # 1. Verificar conectividad
            if not await self.test_backend_connectivity():
                logger.error("❌ No se puede conectar al backend. Abortando pruebas.")
                return
                
            # 2. Probar métodos de conveniencia
            await self.test_convenience_methods()
            
            # 3. Probar validación
            await self.test_scan_configuration_validation()
            
            # 4. Probar presets del sistema
            await self.test_system_presets()
            
            # 5. Probar CRUD de presets
            await self.test_scan_presets_crud()
            
            # 6. Probar ejecución de escaneos
            await self.test_execute_preset_scan()
            await self.test_custom_market_scan()
            
            # 7. Probar parámetros de trading
            await self.test_asset_trading_parameters()
            
            logger.info("\n" + "=" * 70)
            logger.info("🎉 ¡Todas las pruebas del API Client completadas!")
            
        except Exception as e:
            logger.error(f"❌ Error crítico durante las pruebas: {e}")
            
        finally:
            await self.cleanup()

async def main():
    """Función principal del script de pruebas."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pruebas del API Client de configuración de mercado")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="URL base del backend (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Activar logging verbose"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = MarketConfigurationAPITester(base_url=args.url)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
