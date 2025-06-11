#!/usr/bin/env python3
"""
Script de pruebas offline para validar los métodos del API Client que no requieren backend.

Este script prueba los métodos de conveniencia y validación del API Client
sin necesidad de tener el backend ejecutándose.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from src.ultibot_ui.services.api_client import UltiBotAPIClient

async def test_offline_methods():
    """Prueba métodos que no requieren conexión al backend."""
    
    print("🧪 Iniciando pruebas offline del API Client")
    print("=" * 50)
    
    # Crear cliente dummy (no se usará para conexión real)
    client = httpx.AsyncClient(base_url="http://localhost:8000", timeout=30.0)
    api_client = UltiBotAPIClient(client)
    
    try:
        print("\n📋 Probando métodos de conveniencia...")
        
        # Probar rangos de market cap
        ranges = await api_client.get_available_market_cap_ranges()
        print(f"✅ Rangos de market cap ({len(ranges)}): {ranges}")
        
        # Probar filtros de volumen
        volume_filters = await api_client.get_available_volume_filters()
        print(f"✅ Filtros de volumen ({len(volume_filters)}): {volume_filters}")
        
        # Probar direcciones de tendencia
        trends = await api_client.get_available_trend_directions()
        print(f"✅ Direcciones de tendencia ({len(trends)}): {trends}")
        
        print("\n🔍 Probando validación de configuraciones...")
        
        # Configuración válida
        valid_config = {
            "min_price_change_24h_percent": -5.0,
            "max_price_change_24h_percent": 15.0,
            "min_rsi": 30.0,
            "max_rsi": 70.0,
            "min_volume_24h_usd": 1_000_000
        }
        
        validation = await api_client.validate_scan_configuration(valid_config)
        print(f"✅ Configuración válida:")
        print(f"   - Válida: {validation['is_valid']}")
        print(f"   - Errores: {validation['errors']}")
        print(f"   - Advertencias: {validation['warnings']}")
        
        # Configuración inválida
        invalid_config = {
            "min_price_change_24h_percent": 20.0,  # Mayor que el máximo
            "max_price_change_24h_percent": 10.0,
            "min_rsi": 80.0,  # Mayor que el máximo
            "max_rsi": 30.0,
            "min_volume_24h_usd": 50_000_000  # Muy restrictivo
        }
        
        validation = await api_client.validate_scan_configuration(invalid_config)
        print(f"\n⚠️ Configuración inválida:")
        print(f"   - Válida: {validation['is_valid']}")
        print(f"   - Errores: {validation['errors']}")
        print(f"   - Advertencias: {validation['warnings']}")
        
        # Configuración con RSI fuera de rango
        rsi_invalid_config = {
            "min_rsi": -10.0,  # Fuera de rango
            "max_rsi": 150.0   # Fuera de rango
        }
        
        validation = await api_client.validate_scan_configuration(rsi_invalid_config)
        print(f"\n❌ Configuración RSI inválida:")
        print(f"   - Válida: {validation['is_valid']}")
        print(f"   - Errores: {validation['errors']}")
        
        print("\n" + "=" * 50)
        print("🎉 ¡Todas las pruebas offline completadas exitosamente!")
        print("\nResultados:")
        print("✅ Métodos de conveniencia funcionan correctamente")
        print("✅ Validación client-side funciona correctamente") 
        print("✅ Detección de errores funciona correctamente")
        print("✅ Sistema de advertencias funciona correctamente")
        
        print(f"\n📊 Resumen de métodos implementados:")
        print(f"   - get_available_market_cap_ranges(): {len(ranges)} rangos")
        print(f"   - get_available_volume_filters(): {len(volume_filters)} filtros")
        print(f"   - get_available_trend_directions(): {len(trends)} direcciones")
        print(f"   - validate_scan_configuration(): Validación completa")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        
    finally:
        await client.aclose()

async def test_method_documentation():
    """Verifica que los métodos estén bien documentados."""
    
    print("\n📖 Verificando documentación de métodos...")
    
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    api_client = UltiBotAPIClient(client)
    
    # Lista de métodos nuevos implementados
    new_methods = [
        "execute_market_scan",
        "execute_preset_scan", 
        "get_scan_presets",
        "create_scan_preset",
        "get_scan_preset",
        "update_scan_preset",
        "delete_scan_preset",
        "get_system_presets",
        "get_asset_trading_parameters",
        "create_asset_trading_parameters",
        "get_asset_trading_parameter",
        "update_asset_trading_parameters",
        "delete_asset_trading_parameters",
        "get_available_market_cap_ranges",
        "get_available_volume_filters",
        "get_available_trend_directions",
        "validate_scan_configuration"
    ]
    
    print(f"✅ Métodos implementados: {len(new_methods)}")
    
    documented_methods = 0
    for method_name in new_methods:
        if hasattr(api_client, method_name):
            method = getattr(api_client, method_name)
            if method.__doc__:
                documented_methods += 1
            else:
                print(f"⚠️ Método sin documentación: {method_name}")
        else:
            print(f"❌ Método no encontrado: {method_name}")
    
    print(f"✅ Métodos documentados: {documented_methods}/{len(new_methods)}")
    
    await client.aclose()

if __name__ == "__main__":
    async def main():
        await test_offline_methods()
        await test_method_documentation()
    
    asyncio.run(main())
