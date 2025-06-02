import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QMessageBox
from uuid import UUID
from typing import Optional
import os # Importar os

from dotenv import load_dotenv
from src.ultibot_backend.app_config import AppSettings
from src.shared.data_types import APICredential, ServiceName # Importar APICredential y ServiceName

# Importar la MainWindow
from src.ultibot_ui.windows.main_window import MainWindow

# Importar servicios de backend
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService
from src.shared.data_types import UserConfiguration # Importar UserConfiguration

# --- Importar qdarkstyle de forma segura ---
try:
    import qdarkstyle
except ImportError:
    qdarkstyle = None
    print("Advertencia: qdarkstyle no está instalado. La aplicación usará el tema por defecto de Qt.")

async def start_application():
    # --- Application Configuration ---
    # This application relies on a .env file in its working directory for essential
    # configurations such as database connection strings, API keys, and encryption keys.
    # Ensure a valid .env file is present. See .env.example for a template.
    # The AppSettings object will load these configurations.
    # ---

    app = QApplication(sys.argv)
    # Apply the dark theme early so QMessageBox is styled.
    if qdarkstyle:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    else:
        print("qdarkstyle no disponible, usando tema por defecto.")

    settings = None
    persistence_service = None
    credential_service = None
    market_data_service = None
    config_service = None
    notification_service = None # Añadir notification_service
    user_id = None

    try:
        load_dotenv(override=True)
        # Obtener la clave de encriptación desde el entorno
        credential_encryption_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        if not credential_encryption_key:
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY is not set in .env file or environment.")
        settings = AppSettings(CREDENTIAL_ENCRYPTION_KEY=credential_encryption_key)

        user_id = settings.FIXED_USER_ID # Set user_id after settings are loaded

        # Initialize PersistenceService
        persistence_service = SupabasePersistenceService()
        await persistence_service.connect() # Connection attempt

        # --- Asegurar que el user_id exista en user_configurations antes de cualquier otra operación ---
        # Esto es una medida de contingencia para la clave foránea.
        try:
            await persistence_service.execute_raw_sql(
                """
                INSERT INTO user_configurations (user_id, selected_theme)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (user_id, "dark") # Usar un tema por defecto
            )
            print(f"Asegurado que user_id {user_id} existe en user_configurations.")
            await asyncio.sleep(1) # Añadir un pequeño retraso para la consistencia de la base de datos
        except Exception as e:
            QMessageBox.critical(None, "Error de Inicialización de Usuario", f"Error al asegurar la existencia del usuario en la base de datos: {str(e)}\n\nLa aplicación se cerrará.")
            sys.exit(1)
        # --- Fin de la inicialización de user_id ---

        # Initialize CredentialService
        credential_service = CredentialService(encryption_key=settings.CREDENTIAL_ENCRYPTION_KEY)

        # Other services
        binance_adapter = BinanceAdapter() # Assumes AppSettings is used internally
        market_data_service = MarketDataService(credential_service, binance_adapter)
        # Inicializar PortfolioService para pasar a ConfigService
        from src.ultibot_backend.services.portfolio_service import PortfolioService
        portfolio_service = PortfolioService(market_data_service, persistence_service)
        config_service = ConfigService(
            persistence_service,
            credential_service=credential_service,
            portfolio_service=portfolio_service
        )
        notification_service = NotificationService(credential_service, persistence_service, config_service) # Corregido: pasar config_service
        config_service.set_notification_service(notification_service)

        # --- Asegurar que la configuración de usuario por defecto exista ---
        existing_user_config = await config_service.get_user_configuration(str(user_id)) # Corregido: pasar str(user_id)
        print(f"Configuración de usuario para {user_id} cargada o creada exitosamente.")
        # --- Fin de la lógica de configuración de usuario ---

        # --- Cargar y guardar credenciales de Binance si no existen ---
        binance_api_key = os.getenv("BINANCE_API_KEY")
        binance_api_secret = os.getenv("BINANCE_API_SECRET")

        if not binance_api_key or not binance_api_secret:
            raise ValueError("BINANCE_API_KEY or BINANCE_API_SECRET not found in .env file or environment.")

        try:
            existing_binance_credential = await credential_service.get_credential(
                user_id=user_id,
                service_name=ServiceName.BINANCE_SPOT, # Corregido a ServiceName.BINANCE_SPOT
                credential_label="default"
            )
            print("Intentando guardar/actualizar credenciales de Binance desde .env...")
            
            encrypted_api_key = credential_service.encrypt_data(binance_api_key)
            encrypted_api_secret = credential_service.encrypt_data(binance_api_secret)

            binance_credential = APICredential( # Usar APICredential
                id=settings.FIXED_BINANCE_CREDENTIAL_ID, # Pasar el UUID directamente
                user_id=user_id, # Corregido a user_id
                service_name=ServiceName.BINANCE_SPOT, # Corregido a ServiceName.BINANCE_SPOT
                credential_label="default", # Corregido a credential_label
                encrypted_api_key=encrypted_api_key, # Usar clave encriptada
                encrypted_api_secret=encrypted_api_secret # Usar clave secreta encriptada
            )
            # Forzar que service_name sea Enum antes de guardar
            if isinstance(binance_credential.service_name, str):
                binance_credential.service_name = ServiceName(binance_credential.service_name)
            await credential_service.save_encrypted_credential(binance_credential) # Usar el nuevo método
            print("Credenciales de Binance guardadas/actualizadas exitosamente desde .env.")
        except Exception as e:
            QMessageBox.critical(None, "Error de Credenciales", f"Error al guardar/actualizar credenciales de Binance: {str(e)}\n\nLa aplicación se cerrará.")
            sys.exit(1)
        # --- Fin de la lógica de credenciales de Binance ---

    except ValueError as ve: # Specifically for missing key or other ValueErrors during setup
        QMessageBox.critical(None, "Configuration Error", f"A configuration error occurred: {str(ve)}\n\nPlease check your .env file or environment variables.\nThe application will now exit.")
        sys.exit(1)
    except Exception as e: # Catch other potential errors during service init (e.g., DB connection, malformed keys)
        QMessageBox.critical(None, "Service Initialization Error", f"Failed to initialize critical services: {str(e)}\n\nLa aplicación se cerrará.")
        sys.exit(1)

    # Ensure persistence_service is available for cleanup, even if MainWindow creation fails
    # (though unlikely if services initialized correctly)
    
    # Crear y mostrar la ventana principal, pasando los servicios
    main_window = MainWindow(user_id, market_data_service, config_service, notification_service, persistence_service) # Pasar persistence_service
    main_window.show()

    # Ejecutar el loop de eventos de Qt
    exit_code = app.exec_()

    # --- Limpieza de recursos después de que la aplicación Qt haya terminado ---
    print("Iniciando limpieza de recursos asíncronos...")
    if persistence_service:
        try:
            print("Desconectando persistence service...")
            await persistence_service.disconnect()
            print("Persistence service desconectado.")
        except Exception as e:
            print(f"Error durante la desconexión de persistence_service: {e}")

    if market_data_service: # Asegurarse de que market_data_service se inicializó
        try:
            print("Cerrando market_data_service...")
            await market_data_service.close()
            print("Market_data_service cerrado.")
        except Exception as e:
            print(f"Error durante el cierre de market_data_service: {e}")
    
    print("Limpieza de recursos asíncronos completada.")
    # --- Fin de la limpieza ---

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
    # Fix for Windows ProactorEventLoop issue with psycopg
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # Ejecutar la aplicación asíncrona
    asyncio.run(start_application())
