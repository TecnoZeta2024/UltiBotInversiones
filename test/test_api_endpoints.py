#!/usr/bin/env python3
"""
Script específico para probar endpoints de la API REST.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_fastapi_imports():
    """Prueba imports de FastAPI"""
    print("🔍 Probando imports de FastAPI...")
    
    imports_to_test = [
        ("fastapi", "FastAPI"),
        ("fastapi.testclient", "TestClient"),
        ("uvicorn", None),
        ("pydantic", "BaseModel"),
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

def test_api_models():
    """Prueba modelos de la API"""
    print("📋 Probando modelos de la API...")
    
    models_to_test = [
        ("ultibot_backend.api.v1.models.strategy_models", "StrategyResponse"),
        ("ultibot_backend.api.v1.models.performance_models", "PerformanceMetrics"),
    ]
    
    for module_name, class_name in models_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            model_class = getattr(module, class_name)
            print(f"✅ {class_name} importado correctamente")
        except Exception as e:
            print(f"❌ {class_name} - Error: {e}")
            return False
    
    return True

def test_api_endpoints_imports():
    """Prueba imports de endpoints"""
    print("🌐 Probando imports de endpoints...")
    
    endpoints_to_test = [
        "ultibot_backend.api.v1.endpoints.config",
        "ultibot_backend.api.v1.endpoints.strategies", 
        "ultibot_backend.api.v1.endpoints.portfolio",
        "ultibot_backend.api.v1.endpoints.market_data",
        "ultibot_backend.api.v1.endpoints.trades",
        "ultibot_backend.api.v1.endpoints.performance",
        "ultibot_backend.api.v1.endpoints.notifications",
        "ultibot_backend.api.v1.endpoints.opportunities",
    ]
    
    for endpoint_module in endpoints_to_test:
        try:
            __import__(endpoint_module)
            print(f"✅ {endpoint_module}")
        except Exception as e:
            print(f"❌ {endpoint_module} - Error: {e}")
            return False
    
    return True

def create_mock_app():
    """Crea una aplicación FastAPI mock para pruebas"""
    try:
        from fastapi import FastAPI
        
        app = FastAPI(title="UltiBot Test API", version="1.0.0")
        
        # Endpoints básicos de prueba
        @app.get("/health")
        async def health_check():
            return {"status": "ok", "service": "ultibot-api"}
        
        @app.get("/api/v1/test")
        async def test_endpoint():
            return {"message": "API funcionando correctamente"}
        
        return app
        
    except Exception as e:
        print(f"❌ Error creando app mock: {e}")
        return None

def test_mock_api():
    """Prueba API mock básica"""
    print("🧪 Probando API mock...")
    
    try:
        from fastapi.testclient import TestClient
        
        app = create_mock_app()
        if not app:
            return False
        
        client = TestClient(app)
        
        # Probar endpoint de health
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Endpoint /health funciona")
        else:
            print(f"❌ Endpoint /health falló: {response.status_code}")
            return False
        
        # Probar endpoint de test
        response = client.get("/api/v1/test")
        if response.status_code == 200:
            print("✅ Endpoint /api/v1/test funciona")
        else:
            print(f"❌ Endpoint /api/v1/test falló: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando API mock: {e}")
        return False

def test_main_app_creation():
    """Prueba creación de la aplicación principal"""
    print("🏗️ Probando creación de la aplicación principal...")
    
    try:
        # Intentar importar la aplicación principal
        from ultibot_backend.main import app
        
        print("✅ Aplicación principal importada correctamente")
        
        # Verificar que es una instancia de FastAPI
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            print("✅ Aplicación es instancia válida de FastAPI")
            return True
        else:
            print("❌ Aplicación no es instancia de FastAPI")
            return False
            
    except Exception as e:
        print(f"❌ Error importando aplicación principal: {e}")
        return False

def test_main_app_with_testclient():
    """Prueba la aplicación principal con TestClient"""
    print("🔬 Probando aplicación principal con TestClient...")
    
    try:
        from ultibot_backend.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Endpoints básicos que deberían existir
        test_endpoints = [
            ("/", "Endpoint raíz"),
            ("/health", "Health check"),
            ("/docs", "Documentación API"),
        ]
        
        successful_tests = 0
        for endpoint, description in test_endpoints:
            try:
                response = client.get(endpoint)
                if response.status_code < 500:  # Acepta códigos que no sean errores del servidor
                    print(f"✅ {description} ({endpoint}) - Status: {response.status_code}")
                    successful_tests += 1
                else:
                    print(f"⚠️ {description} ({endpoint}) - Status: {response.status_code}")
            except Exception as e:
                print(f"❌ {description} ({endpoint}) - Error: {e}")
        
        if successful_tests > 0:
            print(f"✅ {successful_tests}/{len(test_endpoints)} endpoints respondieron")
            return True
        else:
            print("❌ Ningún endpoint respondió correctamente")
            return False
            
    except Exception as e:
        print(f"❌ Error probando aplicación con TestClient: {e}")
        return False

def test_app_config():
    """Prueba configuración de la aplicación"""
    print("⚙️ Probando configuración de la aplicación...")
    
    try:
        from ultibot_backend.app_config import AppConfig
        
        # Intentar crear instancia de configuración
        config = AppConfig()
        print("✅ AppConfig instanciado correctamente")
        
        # Verificar que tiene atributos básicos
        expected_attrs = ['debug', 'host', 'port']
        found_attrs = []
        
        for attr in expected_attrs:
            if hasattr(config, attr):
                found_attrs.append(attr)
                print(f"✅ Atributo {attr} encontrado")
            else:
                print(f"⚠️ Atributo {attr} no encontrado")
        
        if found_attrs:
            print(f"✅ Configuración tiene {len(found_attrs)}/{len(expected_attrs)} atributos esperados")
            return True
        else:
            print("❌ Configuración no tiene atributos esperados")
            return False
            
    except Exception as e:
        print(f"❌ Error probando AppConfig: {e}")
        return False

def test_dependencies():
    """Prueba módulo de dependencias"""
    print("🔗 Probando módulo de dependencias...")
    
    try:
        import ultibot_backend.dependencies
        print("✅ Módulo de dependencias importado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error importando dependencias: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de endpoints API")
    print("=" * 60)
    
    tests = [
        ("Imports de FastAPI", test_fastapi_imports),
        ("Modelos de la API", test_api_models),
        ("Imports de endpoints", test_api_endpoints_imports),
        ("API mock", test_mock_api),
        ("Configuración de app", test_app_config),
        ("Módulo de dependencias", test_dependencies),
        ("Creación de app principal", test_main_app_creation),
        ("App principal con TestClient", test_main_app_with_testclient),
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
    print("📊 REPORTE FINAL - ENDPOINTS API")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"Total de pruebas: {total}")
    print(f"Pruebas exitosas: {passed}")
    print(f"Pruebas fallidas: {total - passed}")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS DE API PASARON!")
        return True
    else:
        print("⚠️ Algunas pruebas de API fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
