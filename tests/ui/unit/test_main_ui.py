import pytest
import sys
import os
from unittest.mock import MagicMock


# Configurar qasync para que use PySide6
os.environ['QT_API'] = 'pyside6'

from unittest.mock import AsyncMock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer

# Asegurarse de que el path de src esté en sys.path para las importaciones relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

# Importar la función a testear
from src.ultibot_ui.main import start_application

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
        # Mockear AppSettings para que no intente cargar .env real
        with patch('src.ultibot_ui.main.AppSettings') as MockAppSettings:
            mock_settings_instance = MockAppSettings.return_value
            mock_settings_instance.CREDENTIAL_ENCRYPTION_KEY = "a_very_secret_key_for_testing_123456789012345678901234567890"
            mock_settings_instance.FIXED_USER_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

            # Mockear SupabasePersistenceService
            with patch('src.ultibot_ui.main.SupabasePersistenceService') as MockPersistenceService:
                mock_persistence_instance = MockPersistenceService.return_value
                mock_persistence_instance.connect = AsyncMock()
                mock_persistence_instance.disconnect = AsyncMock()

                # Mockear CredentialService
                with patch('src.ultibot_ui.main.CredentialService') as MockCredentialService:
                    MockCredentialService.return_value = MagicMock()

                    # Mockear BinanceAdapter
                    with patch('src.ultibot_ui.main.BinanceAdapter') as MockBinanceAdapter:
                        MockBinanceAdapter.return_value = MagicMock()

                        # Mockear MarketDataService
                        with patch('src.ultibot_ui.main.MarketDataService') as MockMarketDataService:
                            MockMarketDataService.return_value = MagicMock()

                            # Mockear ConfigService
                            with patch('src.ultibot_ui.main.ConfigService') as MockConfigService:
                                MockConfigService.return_value = MagicMock()

                                # Mockear MainWindow
                                with patch('src.ultibot_ui.main.MainWindow') as MockMainWindow:
                                    mock_main_window_instance = MockMainWindow.return_value
                                    mock_main_window_instance.show = MagicMock()
                                    mock_main_window_instance.close = MagicMock() # Para asegurar que se pueda cerrar

                                    # Mockear QMessageBox para evitar que aparezcan ventanas emergentes
                                    with patch('src.ultibot_ui.main.QMessageBox.critical') as mock_qmessagebox_critical:
                                        # Ejecutar la aplicación en un hilo separado o con un temporizador
                                        # para permitir que el loop de eventos de Qt se ejecute brevemente
                                        # y luego se cierre.
                                        
                                        # Usar QTimer.singleShot para cerrar la aplicación después de un breve retraso
                                        # Esto es crucial para que el test no se quede colgado esperando la interacción del usuario
                                        QTimer.singleShot(100, qapp.quit) # Cierra la app después de 100ms

                                        with pytest.raises(SystemExit) as excinfo:
                                            await start_application()
                                        assert excinfo.value.code == 0

                                        # Afirmaciones
                                        MockAppSettings.assert_called_once()
                                        MockPersistenceService.assert_called_once()
                                        mock_persistence_instance.connect.assert_awaited_once()
                                        MockCredentialService.assert_called_once()
                                        MockBinanceAdapter.assert_called_once()
                                        MockMarketDataService.assert_called_once()
                                        MockConfigService.assert_called_once()
                                        MockMainWindow.assert_called_once()
                                        mock_main_window_instance.show.assert_called_once()
                                        mock_qmessagebox_critical.assert_not_called() # Asegurarse de que no hubo errores críticos

                                        # Verificar que el disconnect se llamó al salir
                                        # Esto es un poco más complejo debido a app.aboutToQuit.connect
                                        # Para este test básico, nos centraremos en la inicialización.
                                        # Un test más avanzado podría mockear app.aboutToQuit para verificar la conexión.
                                        # Por ahora, asumimos que si no hay errores, el flujo de cleanup se configuró.
