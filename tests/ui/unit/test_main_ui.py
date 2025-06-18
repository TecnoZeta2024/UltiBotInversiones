import pytest
import sys
import os

# Configurar qasync para que use PySide6
os.environ['QT_API'] = 'pyside6'

from unittest.mock import MagicMock, AsyncMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt, QCoreApplication

# Asegurarse de que el path de src esté en sys.path para las importaciones relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

# Importar la función a testear
from ultibot_ui.main import main as start_application

@pytest.fixture(scope="session")
def qapp():
    """Fixture para inicializar QApplication una sola vez por sesión de test."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    yield app
    # No cerrar la aplicación aquí, ya que puede ser necesaria para otros tests
    # y pytest-qt maneja el cierre al final de la sesión.

@pytest.mark.asyncio
async def test_start_application_success(qapp):
    """
    Verifica que start_application se ejecuta correctamente con mocks.
    """
    # Mockear las variables de entorno necesarias
    with patch.dict(os.environ, {
        "CREDENTIAL_ENCRYPTION_KEY": "a_very_secret_key_for_testing_123456789012345678901234567890",
        "SUPABASE_URL": "http://mock.supabase.url",
        "SUPABASE_KEY": "mock_supabase_key",
        "FIXED_USER_ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    }):
        # Mockear UltiBotAPIClient y sus métodos
        with patch('ultibot_ui.main.UltiBotAPIClient') as MockAPIClient:
            mock_api_client_instance = MockAPIClient.return_value
            mock_api_client_instance.get_user_configuration = AsyncMock(return_value={
                "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "telegram_chat_id": None,
                "notification_preferences": {},
                "enable_telegram_notifications": True,
                "default_paper_trading_capital": 10000.0,
                "paper_trading_active": True,
                "paper_trading_assets": [],
                "watchlists": [],
                "favorite_pairs": ["BTCUSDT", "ETHUSDT"],
                "risk_profile": "MODERATE",
                "risk_profile_settings": {},
                "real_trading_settings": {
                    "real_trading_mode_active": False,
                    "real_trades_executed_count": 0,
                    "max_concurrent_operations": 5,
                    "daily_loss_limit_absolute": 500.0,
                    "daily_profit_target_absolute": 1000.0,
                    "asset_specific_stop_loss": {},
                    "auto_pause_trading_conditions": {}
                },
                "ai_strategy_configurations": [],
                "ai_analysis_confidence_thresholds": {
                    "paper_trading": 0.6,
                    "real_trading": 0.75
                },
                "mcp_server_preferences": {},
                "selected_theme": "DARK",
                "dashboard_layout_profiles": [],
                "active_dashboard_layout_profile_id": None,
                "dashboard_layout_config": {},
                "cloud_sync_preferences": {},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            })

            # Mockear MainWindow
            with patch('ultibot_ui.main.MainWindow') as MockMainWindow:
                mock_main_window_instance = MockMainWindow.return_value
                mock_main_window_instance.show = MagicMock()
                mock_main_window_instance.close = MagicMock() # Para asegurar que se pueda cerrar

                # Mockear QMessageBox para evitar que aparezcan ventanas emergentes
                with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_qmessagebox_critical:
                    # Mockear httpx.AsyncClient para evitar llamadas de red reales
                    with patch('ultibot_ui.main.httpx.AsyncClient') as MockAsyncClient:
                        MockAsyncClient.return_value.__aenter__.return_value = AsyncMock() # Mockear el context manager

                        # Mockear sys.exit para evitar que el test falle
                        with patch('sys.exit') as mock_exit:
                            # Usar QTimer.singleShot para cerrar la aplicación después de un breve retraso
                            # Esto es crucial para que el test no se quede colgado esperando la interacción del usuario
                            QTimer.singleShot(100, qapp.quit) # Cierra la app después de 100ms

                            # Ejecutar la aplicación
                            start_application()

                            # Verificar que sys.exit fue llamado, indicando un cierre limpio
                            mock_exit.assert_called_once_with(0)

                        # Afirmaciones
                        MockAPIClient.assert_called_once()
                        mock_api_client_instance.get_user_configuration.assert_awaited_once()
                        MockMainWindow.assert_called_once()
                        mock_main_window_instance.show.assert_called_once()
                        mock_qmessagebox_critical.assert_not_called() # Asegurarse de que no hubo errores críticos
                        MockAsyncClient.assert_called_once()
