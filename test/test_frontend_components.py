#!/usr/bin/env python3
"""
Script específico para probar componentes del frontend/UI.
"""

import sys
import os
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_ui_imports():
    """Prueba imports del frontend"""
    print("🔍 Probando imports del frontend...")
    
    imports_to_test = [
        ("ultibot_ui.main", "main"),
        ("ultibot_ui.app_config", "UIAppConfig"),
        ("ultibot_ui.models", None),
        ("ultibot_ui.workers", None),
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

def test_ui_windows():
    """Prueba ventanas principales del UI"""
    print("🪟 Probando ventanas del UI...")
    
    windows = [
        ("ultibot_ui.windows.main_window", "MainWindow"),
        ("ultibot_ui.windows.dashboard_view", "DashboardView"),
        ("ultibot_ui.windows.history_view", "HistoryView"),
        ("ultibot_ui.windows.settings_view", "SettingsView"),
    ]
    
    for module_name, class_name in windows:
        try:
            module = __import__(module_name, fromlist=[class_name])
            window_class = getattr(module, class_name)
            print(f"✅ {class_name} importado correctamente")
        except Exception as e:
            print(f"❌ {class_name} - Error: {e}")
            return False
    
    return True

def test_ui_widgets():
    """Prueba widgets del UI"""
    print("🧩 Probando widgets del UI...")
    
    widgets = [
        ("ultibot_ui.widgets.portfolio_widget", "PortfolioWidget"),
        ("ultibot_ui.widgets.chart_widget", "ChartWidget"),
        ("ultibot_ui.widgets.market_data_widget", "MarketDataWidget"),
        ("ultibot_ui.widgets.notification_widget", "NotificationWidget"),
        ("ultibot_ui.widgets.order_form_widget", "OrderFormWidget"),
        ("ultibot_ui.widgets.trading_mode_selector", "TradingModeSelector"),
    ]
    
    for module_name, class_name in widgets:
        try:
            module = __import__(module_name, fromlist=[class_name])
            widget_class = getattr(module, class_name)
            print(f"✅ {class_name} importado correctamente")
        except Exception as e:
            print(f"❌ {class_name} - Error: {e}")
            return False
    
    return True

def test_ui_dialogs():
    """Prueba diálogos del UI"""
    print("💬 Probando diálogos del UI...")
    
    dialogs = [
        ("ultibot_ui.dialogs.login_dialog", "LoginDialog"),
        ("ultibot_ui.dialogs.strategy_config_dialog", "StrategyConfigDialog"),
    ]
    
    for module_name, class_name in dialogs:
        try:
            module = __import__(module_name, fromlist=[class_name])
            dialog_class = getattr(module, class_name)
            print(f"✅ {class_name} importado correctamente")
        except Exception as e:
            print(f"❌ {class_name} - Error: {e}")
            return False
    
    return True

def test_ui_services():
    """Prueba servicios del UI"""
    print("⚙️ Probando servicios del UI...")
    
    services = [
        ("ultibot_ui.services.api_client", "APIClient"),
        ("ultibot_ui.services.trading_mode_service", "TradingModeService"),
        ("ultibot_ui.services.trading_mode_state", "TradingModeState"),
        ("ultibot_ui.services.ui_config_service", "UIConfigService"),
        ("ultibot_ui.services.ui_market_data_service", "UIMarketDataService"),
        ("ultibot_ui.services.ui_strategy_service", "UIStrategyService"),
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

def test_ui_views():
    """Prueba vistas del UI"""
    print("👁️ Probando vistas del UI...")
    
    views = [
        ("ultibot_ui.views.opportunities_view", "OpportunitiesView"),
        ("ultibot_ui.views.portfolio_view", "PortfolioView"),
        ("ultibot_ui.views.strategies_view", "StrategiesView"),
        ("ultibot_ui.views.strategy_management_view", "StrategyManagementView"),
    ]
    
    for module_name, class_name in views:
        try:
            module = __import__(module_name, fromlist=[class_name])
            view_class = getattr(module, class_name)
            print(f"✅ {class_name} importado correctamente")
        except Exception as e:
            print(f"❌ {class_name} - Error: {e}")
            return False
    
    return True

def test_qt_availability():
    """Prueba disponibilidad de Qt"""
    print("🎨 Probando disponibilidad de Qt...")
    
    try:
        import PyQt5
        print("✅ PyQt5 disponible")
        qt_available = True
    except ImportError:
        try:
            import PySide2
            print("✅ PySide2 disponible")
            qt_available = True
        except ImportError:
            try:
                import PyQt6
                print("✅ PyQt6 disponible")
                qt_available = True
            except ImportError:
                try:
                    import PySide6
                    print("✅ PySide6 disponible")
                    qt_available = True
                except ImportError:
                    print("❌ No se encontró ninguna biblioteca Qt")
                    qt_available = False
    
    if qt_available:
        try:
            # Intentar importar QApplication sin inicializarla
            from PyQt5.QtWidgets import QApplication
            print("✅ QApplication importada correctamente")
        except ImportError:
            try:
                from PySide2.QtWidgets import QApplication
                print("✅ QApplication importada correctamente")
            except ImportError:
                try:
                    from PyQt6.QtWidgets import QApplication
                    print("✅ QApplication importada correctamente")
                except ImportError:
                    try:
                        from PySide6.QtWidgets import QApplication
                        print("✅ QApplication importada correctamente")
                    except ImportError:
                        print("❌ No se pudo importar QApplication")
                        return False
    
    return qt_available

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de componentes del frontend")
    print("=" * 60)
    
    tests = [
        ("Disponibilidad de Qt", test_qt_availability),
        ("Imports del frontend", test_ui_imports),
        ("Ventanas del UI", test_ui_windows),
        ("Widgets del UI", test_ui_widgets),
        ("Diálogos del UI", test_ui_dialogs),
        ("Servicios del UI", test_ui_services),
        ("Vistas del UI", test_ui_views),
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
    print("📊 REPORTE FINAL - COMPONENTES FRONTEND")
    print("=" * 60)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"Total de pruebas: {total}")
    print(f"Pruebas exitosas: {passed}")
    print(f"Pruebas fallidas: {total - passed}")
    
    if passed == total:
        print("🎉 ¡TODAS LAS PRUEBAS DEL FRONTEND PASARON!")
        return True
    else:
        print("⚠️ Algunas pruebas del frontend fallaron")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
