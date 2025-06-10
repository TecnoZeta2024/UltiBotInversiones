#!/usr/bin/env python3
"""
Script de prueba para verificar la integración completa del Sistema de Configuración Avanzada
en la ventana principal de UltiBotInversiones.

Este script valida:
1. Importaciones correctas de todos los diálogos
2. Compilación sin errores de sintaxis
3. Instanciación correcta de componentes principales
"""

import sys
import os
import asyncio
from pathlib import Path
from uuid import UUID, uuid4

# Agregar el directorio raíz al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Prueba que todas las importaciones necesarias funcionen correctamente."""
    print("🔍 Probando importaciones...")
    
    try:
        # Importar main window con todas las dependencias
        from src.ultibot_ui.windows.main_window import MainWindow
        print("✅ MainWindow importado correctamente")
        
        # Importar diálogos de configuración avanzada
        from src.ultibot_ui.dialogs.market_scan_config_dialog import MarketScanConfigDialog
        from src.ultibot_ui.dialogs.preset_management_dialog import PresetManagementDialog
        from src.ultibot_ui.dialogs.asset_config_dialog import AssetTradingParametersDialog
        print("✅ Diálogos de configuración avanzada importados correctamente")
        
        # Importar widgets especializados
        from src.ultibot_ui.widgets.market_filter_widgets import (
            PriceRangeWidget, PercentageChangeWidget, VolumeFilterWidget,
            MarketCapRangeWidget, TechnicalAnalysisWidget, TrendDirectionWidget,
            ExclusionCriteriaWidget, ConfidenceThresholdsWidget
        )
        from src.ultibot_ui.widgets.preset_selector_widget import (
            PresetSelectorWidget, ScanResultsWidget, PresetQuickActionWidget, PresetScannerWidget
        )
        print("✅ Widgets especializados importados correctamente")
        
        # Importar API client y dependencias
        from src.ultibot_ui.services.api_client import UltiBotAPIClient
        from src.ultibot_ui.services.trading_mode_state import TradingModeStateManager
        print("✅ Servicios y dependencias importados correctamente")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado en importaciones: {e}")
        return False

def test_compilation():
    """Prueba que todos los archivos principales se compilen sin errores."""
    print("\n🔍 Probando compilación de archivos...")
    
    files_to_test = [
        "src/ultibot_ui/windows/main_window.py",
        "src/ultibot_ui/dialogs/market_scan_config_dialog.py",
        "src/ultibot_ui/dialogs/preset_management_dialog.py", 
        "src/ultibot_ui/dialogs/asset_config_dialog.py",
        "src/ultibot_ui/widgets/market_filter_widgets.py",
        "src/ultibot_ui/widgets/preset_selector_widget.py"
    ]
    
    all_compiled = True
    
    for file_path in files_to_test:
        try:
            full_path = project_root / file_path
            if full_path.exists():
                import py_compile
                py_compile.compile(str(full_path), doraise=True)
                print(f"✅ {file_path} compilado correctamente")
            else:
                print(f"⚠️  {file_path} no encontrado")
                all_compiled = False
        except py_compile.PyCompileError as e:
            print(f"❌ Error de compilación en {file_path}: {e}")
            all_compiled = False
        except Exception as e:
            print(f"❌ Error inesperado compilando {file_path}: {e}")
            all_compiled = False
    
    return all_compiled

def test_dialog_instantiation():
    """Prueba que los diálogos se puedan instanciar correctamente (sin mostrar)."""
    print("\n🔍 Probando instanciación de diálogos...")
    
    try:
        # Importar Qt
        from PyQt5.QtWidgets import QApplication
        import sys
        
        # Crear aplicación Qt si no existe
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Mock API Client básico
        class MockAPIClient:
            def __init__(self):
                pass
                
        # Mock loop asyncio
        loop = asyncio.new_event_loop()
        
        # Probar instanciación de diálogos (sin mostrar)
        from src.ultibot_ui.dialogs.market_scan_config_dialog import MarketScanConfigDialog
        from src.ultibot_ui.dialogs.preset_management_dialog import PresetManagementDialog
        from src.ultibot_ui.dialogs.asset_config_dialog import AssetTradingParametersDialog
        
        api_client = MockAPIClient()
        
        # Instanciar cada diálogo
        market_dialog = MarketScanConfigDialog(api_client=api_client, loop=loop, parent=None)
        print("✅ MarketScanConfigDialog instanciado correctamente")
        
        preset_dialog = PresetManagementDialog(api_client=api_client, loop=loop, parent=None)
        print("✅ PresetManagementDialog instanciado correctamente")
        
        asset_dialog = AssetTradingParametersDialog(api_client=api_client, loop=loop, parent=None)
        print("✅ AssetTradingParametersDialog instanciado correctamente")
        
        # Limpiar
        market_dialog.deleteLater()
        preset_dialog.deleteLater()
        asset_dialog.deleteLater()
        
        return True
        
    except Exception as e:
        print(f"❌ Error en instanciación de diálogos: {e}")
        return False

def test_menu_integration():
    """Prueba que los métodos de integración del menú existan y sean accesibles."""
    print("\n🔍 Probando integración de menús...")
    
    try:
        from src.ultibot_ui.windows.main_window import MainWindow
        
        # Verificar que los métodos requeridos existen
        required_methods = [
            'open_market_scan_config',
            'open_preset_management', 
            'open_asset_trading_parameters',
            '_show_about_dialog'
        ]
        
        for method_name in required_methods:
            if hasattr(MainWindow, method_name):
                print(f"✅ Método {method_name} encontrado en MainWindow")
            else:
                print(f"❌ Método {method_name} NO encontrado en MainWindow")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando integración de menús: {e}")
        return False

def main():
    """Función principal de prueba."""
    print("🚀 Iniciando pruebas de integración del Sistema de Configuración Avanzada")
    print("=" * 80)
    
    tests = [
        ("Importaciones", test_imports),
        ("Compilación", test_compilation), 
        ("Instanciación de Diálogos", test_dialog_instantiation),
        ("Integración de Menús", test_menu_integration)
    ]
    
    all_passed = True
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Ejecutando prueba: {test_name}")
        print("-" * 50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ Error ejecutando prueba {test_name}: {e}")
            results.append((test_name, False))
            all_passed = False
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name:<30} {status}")
    
    print("-" * 80)
    if all_passed:
        print("🎉 TODAS LAS PRUEBAS PASARON - Sistema de Configuración Avanzada integrado correctamente")
        print("🚀 Ready for production deployment!")
    else:
        print("⚠️  ALGUNAS PRUEBAS FALLARON - Revisar errores arriba")
    
    print("=" * 80)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
