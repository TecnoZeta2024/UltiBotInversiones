import sys
import qdarkstyle
import asyncio
from PyQt5.QtWidgets import QApplication, QMessageBox
from uuid import UUID
from typing import Optional

from dotenv import load_dotenv
from src.ultibot_backend.app_config import AppSettings

# Importar la MainWindow
from src.ultibot_ui.windows.main_window import MainWindow

# Importar servicios de backend
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService

async def start_application():
    # --- Application Configuration ---
    # This application relies on a .env file in its working directory for essential
    # configurations such as database connection strings, API keys, and encryption keys.
    # Ensure a valid .env file is present. See .env.example for a template.
    # The AppSettings object will load these configurations.
    # ---

    app = QApplication(sys.argv)
    # Apply the dark theme early so QMessageBox is styled.
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    settings = None
    persistence_service = None
    credential_service = None
    market_data_service = None
    config_service = None
    notification_service = None # Añadir notification_service
    user_id = None

    try:
        load_dotenv(override=True)
        settings = AppSettings()

        if not settings.CREDENTIAL_ENCRYPTION_KEY:
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY is not set in .env file or environment.")
        
        user_id = settings.FIXED_USER_ID # Set user_id after settings are loaded

        # Initialize PersistenceService
        persistence_service = SupabasePersistenceService()
        await persistence_service.connect() # Connection attempt

        # Initialize CredentialService
        credential_service = CredentialService(encryption_key=settings.CREDENTIAL_ENCRYPTION_KEY)

        # Other services
        binance_adapter = BinanceAdapter() # Assumes AppSettings is used internally
        market_data_service = MarketDataService(credential_service, binance_adapter)
        config_service = ConfigService(persistence_service)
        notification_service = NotificationService(credential_service, persistence_service) # Inicializar NotificationService

    except ValueError as ve: # Specifically for missing key or other ValueErrors during setup
        QMessageBox.critical(None, "Configuration Error", f"A configuration error occurred: {str(ve)}\n\nPlease check your .env file or environment variables.\nThe application will now exit.")
        sys.exit(1)
    except Exception as e: # Catch other potential errors during service init (e.g., DB connection, malformed keys)
        QMessageBox.critical(None, "Service Initialization Error", f"Failed to initialize critical services: {str(e)}\n\nThe application will now exit.")
        sys.exit(1)

    # Ensure persistence_service is available for cleanup, even if MainWindow creation fails
    # (though unlikely if services initialized correctly)
    
    # Crear y mostrar la ventana principal, pasando los servicios
    # This part is reached only if all initializations were successful
    main_window = MainWindow(user_id, market_data_service, config_service, notification_service) # Pasar notification_service
    main_window.show()

    # Configurar limpieza de recursos al salir
    # persistence_service might be None if initialization failed before it was set.
    if persistence_service:
        async def cleanup_resources(ps_service: SupabasePersistenceService):
            if ps_service: # Double check, though outer 'if' should cover
                print("Disconnecting persistence service...")
                await ps_service.disconnect()
                print("Persistence service disconnected.")

        def _cleanup_sync_wrapper(ps_service_to_clean: SupabasePersistenceService):
            # Wrapper to ensure the correct persistence_service instance is used
            def _cleanup_sync():
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    loop.run_until_complete(cleanup_resources(ps_service_to_clean))
                except Exception as e:
                    print(f"Error during cleanup: {e}")
                finally:
                    if 'loop' in locals() and loop is not asyncio.get_event_loop() and not loop.is_closed():
                         # This logic for closing a potentially new loop needs care.
                         # If the main event loop was closed, and we started a new one for cleanup,
                         # it should ideally be closed. However, get_event_loop() behavior can be tricky.
                         # For now, let's assume the loop management is sufficient.
                         pass
            return _cleanup_sync

        app.aboutToQuit.connect(_cleanup_sync_wrapper(persistence_service))

    # Ejecutar el loop de eventos de Qt
    exit_code = app.exec_()
    
    # Final cleanup check (safeguard)
    # This check needs to be careful if persistence_service was never initialized.
    # Eliminar la lógica de verificación de is_connected, ya que app.aboutToQuit.connect es el método preferido
    # para la limpieza y el atributo is_connected no existe en SupabasePersistenceService.

    sys.exit(exit_code)

if __name__ == "__main__":
    # --- Running the Application ---
    # This UI application is part of a larger project structure within the 'src' directory.
    # To ensure all internal imports (e.g., from 'src.ultibot_backend' or 'ultibot_ui.windows')
    # resolve correctly, it's recommended to run this script using Poetry from the
    # project root directory:
    #
    #   poetry run python src/ultibot_ui/main.py
    #
    # If not using Poetry, ensure the project root directory (containing 'src')
    # is in your PYTHONPATH, or run the script from the project root directory, e.g.:
    #
    #   python -m src.ultibot_ui.main
    #
    # or ensure your current working directory is the project root when running:
    #   python src/ultibot_ui/main.py
    # ---
    # Ejecutar la aplicación asíncrona
    asyncio.run(start_application())
