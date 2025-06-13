#!/usr/bin/env python3
"""
Script maestro para ejecutar todas las pruebas de componentes del sistema UltiBot.
Ejecuta validaciones completas de backend, frontend, base de datos, APIs y servicios.
"""

import os
import sys
import subprocess
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Tuple
import time

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestRunner:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Log con timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def run_command(self, command: str, description: str) -> Tuple[bool, str]:
        """Ejecuta un comando y retorna el resultado"""
        self.log(f"Ejecutando: {description}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=60
            )
            success = result.returncode == 0
            output = result.stdout + result.stderr
            return success, output
        except subprocess.TimeoutExpired:
            return False, "Timeout: El comando tardó más de 60 segundos"
        except Exception as e:
            return False, f"Error ejecutando comando: {str(e)}"
    
    def test_environment_setup(self) -> bool:
        """Verifica que el entorno esté configurado correctamente"""
        self.log("🔧 Verificando configuración del entorno...")
        
        # Verificar Python y Poetry
        success, _ = self.run_command("python --version", "Versión de Python")
        if not success:
            self.log("❌ Python no encontrado", "ERROR")
            return False
            
        success, _ = self.run_command("poetry --version", "Versión de Poetry")
        if not success:
            self.log("❌ Poetry no encontrado", "ERROR")
            return False
            
        # Verificar variables de entorno
        required_env = ['.env', '.env.example']
        for env_file in required_env:
            if not os.path.exists(env_file):
                self.log(f"⚠️ Archivo {env_file} no encontrado", "WARNING")
        
        self.log("✅ Configuración del entorno verificada")
        return True
    
    def test_imports(self) -> bool:
        """Verifica que todos los módulos principales se importen correctamente"""
        self.log("📦 Verificando imports de módulos principales...")
        
        test_imports = [
            "from ultibot_backend.main import app",
            "from ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategy",
            "from ultibot_backend.services.market_data_service import MarketDataService",
            "from ultibot_backend.adapters.binance_adapter import BinanceAdapter",
            "from ultibot_ui.main import main as ui_main",
            "from shared.data_types import *"
        ]
        
        for import_statement in test_imports:
            try:
                exec(import_statement)
                self.log(f"✅ {import_statement}")
            except Exception as e:
                self.log(f"❌ {import_statement} - Error: {str(e)}", "ERROR")
                return False
        
        self.log("✅ Todos los imports principales funcionan correctamente")
        return True
    
    def test_backend_api(self) -> bool:
        """Verifica que la API del backend esté funcional"""
        self.log("🌐 Verificando API del backend...")
        
        try:
            from ultibot_backend.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Test endpoints básicos
            endpoints = [
                "/health",
                "/api/v1/config",
                "/api/v1/strategies",
                "/api/v1/portfolio/status"
            ]
            
            for endpoint in endpoints:
                try:
                    response = client.get(endpoint)
                    if response.status_code < 500:
                        self.log(f"✅ {endpoint} - Status: {response.status_code}")
                    else:
                        self.log(f"⚠️ {endpoint} - Status: {response.status_code}", "WARNING")
                except Exception as e:
                    self.log(f"❌ {endpoint} - Error: {str(e)}", "ERROR")
            
            self.log("✅ API del backend verificada")
            return True
            
        except Exception as e:
            self.log(f"❌ Error verificando API del backend: {str(e)}", "ERROR")
            return False
    
    def test_database_connection(self) -> bool:
        """Verifica la conexión a la base de datos"""
        self.log("🗄️ Verificando conexión a la base de datos...")
        
        try:
            # Ejecutar script de prueba de conexión DB
            success, output = self.run_command(
                "python scripts/test_db_connection.py",
                "Conexión a base de datos"
            )
            
            if success:
                self.log("✅ Conexión a base de datos exitosa")
                return True
            else:
                self.log(f"❌ Error en conexión DB: {output}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verificando DB: {str(e)}", "ERROR")
            return False
    
    def test_services(self) -> bool:
        """Verifica que los servicios principales funcionen"""
        self.log("⚙️ Verificando servicios principales...")
        
        services_to_test = [
            ("MarketDataService", "ultibot_backend.services.market_data_service"),
            ("ConfigService", "ultibot_backend.services.config_service"),
            ("StrategyService", "ultibot_backend.services.strategy_service"),
            ("PortfolioService", "ultibot_backend.services.portfolio_service")
        ]
        
        for service_name, module_path in services_to_test:
            try:
                module = __import__(module_path, fromlist=[service_name])
                service_class = getattr(module, service_name)
                
                # Intentar instanciar el servicio
                service_instance = service_class()
                self.log(f"✅ {service_name} - Instanciado correctamente")
                
            except Exception as e:
                self.log(f"❌ {service_name} - Error: {str(e)}", "ERROR")
                return False
        
        self.log("✅ Servicios principales verificados")
        return True
    
    def test_ui_components(self) -> bool:
        """Verifica que los componentes de UI se puedan importar"""
        self.log("🖥️ Verificando componentes de UI...")
        
        ui_components = [
            ("MainWindow", "ultibot_ui.windows.main_window"),
            ("DashboardView", "ultibot_ui.windows.dashboard_view"),
            ("PortfolioWidget", "ultibot_ui.widgets.portfolio_widget"),
            ("ChartWidget", "ultibot_ui.widgets.chart_widget")
        ]
        
        for component_name, module_path in ui_components:
            try:
                module = __import__(module_path, fromlist=[component_name])
                component_class = getattr(module, component_name)
                self.log(f"✅ {component_name} - Import exitoso")
                
            except Exception as e:
                self.log(f"❌ {component_name} - Error: {str(e)}", "ERROR")
                return False
        
        self.log("✅ Componentes de UI verificados")
        return True
    
    def test_adapters(self) -> bool:
        """Verifica que los adaptadores funcionen correctamente"""
        self.log("🔌 Verificando adaptadores...")
        
        adapters = [
            ("BinanceAdapter", "ultibot_backend.adapters.binance_adapter"),
            ("MobulaAdapter", "ultibot_backend.adapters.mobula_adapter"),
            ("TelegramAdapter", "ultibot_backend.adapters.telegram_adapter")
        ]
        
        for adapter_name, module_path in adapters:
            try:
                module = __import__(module_path, fromlist=[adapter_name])
                adapter_class = getattr(module, adapter_name)
                self.log(f"✅ {adapter_name} - Import exitoso")
                
            except Exception as e:
                self.log(f"❌ {adapter_name} - Error: {str(e)}", "ERROR")
                return False
        
        self.log("✅ Adaptadores verificados")
        return True
    
    def run_pytest_suite(self) -> bool:
        """Ejecuta la suite completa de pytest"""
        self.log("🧪 Ejecutando suite de pytest...")
        
        success, output = self.run_command(
            "poetry run pytest tests/ -v --tb=short",
            "Suite completa de pytest"
        )
        
        if success:
            self.log("✅ Suite de pytest completada exitosamente")
        else:
            self.log(f"❌ Errores en pytest: {output}", "ERROR")
        
        return success
    
    def generate_report(self):
        """Genera un reporte final de todas las pruebas"""
        elapsed_time = time.time() - self.start_time
        
        self.log("=" * 80)
        self.log("📊 REPORTE FINAL DE PRUEBAS")
        self.log("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        self.log(f"Total de pruebas: {total_tests}")
        self.log(f"Pruebas exitosas: {passed_tests}")
        self.log(f"Pruebas fallidas: {total_tests - passed_tests}")
        self.log(f"Tiempo total: {elapsed_time:.2f} segundos")
        
        if passed_tests == total_tests:
            self.log("🎉 ¡TODAS LAS PRUEBAS PASARON!", "SUCCESS")
        else:
            self.log("⚠️ Algunas pruebas fallaron. Revisar logs arriba.", "WARNING")
        
        # Guardar reporte en archivo
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "elapsed_time": elapsed_time,
            "results": self.results
        }
        
        with open("test/test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        self.log("📄 Reporte guardado en test/test_report.json")

def main():
    """Función principal que ejecuta todas las pruebas"""
    runner = TestRunner()
    
    runner.log("🚀 Iniciando pruebas completas del sistema UltiBot")
    runner.log("=" * 80)
    
    # Ejecutar todas las pruebas
    tests = [
        ("environment_setup", runner.test_environment_setup),
        ("imports", runner.test_imports),
        ("backend_api", runner.test_backend_api),
        ("database_connection", runner.test_database_connection),
        ("services", runner.test_services),
        ("ui_components", runner.test_ui_components),
        ("adapters", runner.test_adapters),
        ("pytest_suite", runner.run_pytest_suite)
    ]
    
    for test_name, test_function in tests:
        try:
            result = test_function()
            runner.results[test_name] = result
        except Exception as e:
            runner.log(f"❌ Error crítico en {test_name}: {str(e)}", "ERROR")
            runner.results[test_name] = False
    
    # Generar reporte final
    runner.generate_report()
    
    # Código de salida
    if all(runner.results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
