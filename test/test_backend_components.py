#!/usr/bin/env python3
"""
Script específico para probar componentes del backend.
"""

import sys
import os
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_backend_imports():
    """Prueba imports del backend"""
    print("🔍 Probando imports del backend...")
    
    imports_to_test = [
        ("ultibot_backend.main", "app"),
        ("ultibot_backend.app_config", "AppConfig"),
        ("ultibot_backend.dependencies", None),
        ("ultibot_backend.core.exceptions", "UltiBotException"),
        ("ultibot_backend.core.domain_models.trading_strategy_models", "TradingStrategy"),
        ("ultibot_backend.core.domain_models.trade_models", "Trade"),
        ("ultibot_backend.core.domain_models.user_configuration_models", "UserConfiguration"),
    ]
    
    for module_name, class_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name] if class_name else [])
            if class_name:
                getattr(module, class_name)
            print(f"✅ {module_name}.{class_name if class_name else ''}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name if class_name else ''} - Error: {e}")
            return False
    
    return True

def test_backend_services():
    """Prueba servicios del backend"""
    print("⚙️ Probando servicios del backend...")
    
    services = [
        ("ultibot_backend.services.config_service", "ConfigService"),
        ("ultibot_backend.services.market_data_service", "MarketDataService"),
        ("ultibot_backend.services.strategy_service", "StrategyService"),
        ("ultibot_backend.services.portfolio_service", "PortfolioService"),
        ("ultibot_backend.services.notification_service", "NotificationService"),
        ("ultibot_backend.services.performance_service", "PerformanceService"),
    ]
    
    for module_name, class_name in services:
        try:
            module = __import__(module_name, fromlist=[class_name])
            service_class = getattr(module, class_name)
            print(f"✅ {class_name} importado correctamente")
        except Exception as e:
            print(f"❌ {class_name} - Error: {e}")
            return False
    
    return True

def test_backend_adapters():
    """Prueba adaptadores del backend"""
    print("🔌 Probando adaptadores del backend...")
    
    adapters = [
        ("ultibot_backend.adapters.binance_adapter", "BinanceAdapter"),
        ("ultibot_backend.adapters.mobula_adapter", "MobulaAdapter"),
        ("ultibot_backend.adapters.telegram_adapter", "TelegramAdapter"),
        ("ultibot_backend.adapters.persistence_service", "PersistenceService"),
    ]
    
    for module_name, class_name in adapters:
        try:
            module = __import__(module_name, fromlist=[class_name])
            adapter_class = getattr(module, class_name)
            print(f"✅ {class_name} importado correctamente")
        except Exception as e:
            print(f"❌ {class_name} - Error: {e}")
            return False
    
    return True

def test_api_endpoints():
    """Prueba endpoints de la API"""
    print("🌐 Probando endpoints de la API...")
    
    endpoints = [
        "ultibot_backend.api.v1.endpoints.config",
        "ultibot_backend.api.v1.endpoints.strategies",
        "ultibot_backend.api.v1.endpoints.portfolio",
        "ultibot_backend.api.v1.endpoints.market_data",
        "ultibot_backend.api.v1.endpoints.trades",
        "ultibot_backend.api.v1.endpoints.performance",
    ]
    
    for endpoint_module in endpoints:
        try:
            __import__(endpoint_module)
            print(f"✅ {endpoint_module}")
        except Exception as e:
            print(f"❌ {endpoint_module} - Error: {e}")
            return False
    
    return True

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de componentes del backend")
    print("=" * 60)
    
    tests = [
        ("Imports del backend", test_backend_imports),
        ("Servicios del backend", test_backend_services),
        ("Adaptadores del backend", test_backend_adapters),  
        ("Endpoints de la API", test_api_endpoints),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                print(f"✅ {test_name} - EXITOSO")
            else:
                print(f"❌ {test_name} - FALLÓ")
        except Exception as e:
            print(f"❌ {test_name} - ERROR CRÍTICO: {e}")
            results[test_name] = False
    
    # Reporte final
    print("\n" + "=" * 60)
    print("📊 REPORTE FINAL - COMPONENTES BACKEND")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"Total de pruebas: {total}")
    print(f"Pruebas exitosas: {passed}")
    print(f"Pruebas fallidas: {total - passed}")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS DEL BACKEND PASARON!")
        return True
    else:
        print("⚠️ Algunas pruebas del backend fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
