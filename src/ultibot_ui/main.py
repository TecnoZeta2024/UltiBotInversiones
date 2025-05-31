import sys
import qdarkstyle
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
        config_service = ConfigService(persistence_service)
        notification_service = NotificationService(credential_service, persistence_service) # Inicializar NotificationService

        # --- Asegurar que la configuración de usuario por defecto exista ---
        # Esto es necesario porque api_credentials tiene una clave foránea a user_configurations.
        existing_user_config = await config_service.load_user_configuration(user_id) # Cambiado a load_user_configuration
        if not existing_user_config or existing_user_config.id != user_id: # Verificar si la configuración es realmente para este user_id
            print(f"Configuración de usuario para {user_id} no encontrada o no válida. Creando configuración por defecto...")
            default_user_config = UserConfiguration(
                id=user_id,
                user_id=user_id,
                defaultPaperTradingCapital=10000.0, # Capital inicial para paper trading
                enableTelegramNotifications=False,
                selectedTheme="dark"
            )
            print("DEBUG: Antes de config_service.save_user_configuration") # Log de depuración
            # logger.info("DEBUG: Antes de config_service.save_user_configuration") # Comentado para evitar dependencia de logger aquí
            await config_service.save_user_configuration(user_id, default_user_config) # Pasar user_id como primer argumento
            print("DEBUG: Después de config_service.save_user_configuration") # Log de depuración
            # logger.info("DEBUG: Después de config_service.save_user_configuration") # Comentado
            print("Configuración de usuario por defecto creada exitosamente.")
        else:
            print(f"Configuración de usuario para {user_id} ya existe.")
        # --- Fin de la lógica de configuración de usuario ---

        # --- Cargar y guardar credenciales de Binance si no existen ---
        # Esto asegura que las credenciales de Binance estén disponibles en la base de datos
        # para el CredentialService, que las recupera de allí.
        binance_api_key = os.getenv("BINANCE_API_KEY")
        binance_api_secret = os.getenv("BINANCE_API_SECRET")

        if not binance_api_key or not binance_api_secret:
            raise ValueError("BINANCE_API_KEY or BINANCE_API_SECRET not found in .env file or environment.")

        try:
            # Intentar obtener las credenciales para ver si ya están guardadas
            existing_binance_credential = await credential_service.get_credential(
                user_id=user_id,
                service_name=ServiceName.BINANCE_SPOT, # Corregido a ServiceName.BINANCE_SPOT
                credential_label="default"
            )
            # Se elimina la condición 'if not existing_binance_credential:' para forzar la actualización
            # de las credenciales desde .env en cada inicio, aprovechando el ON CONFLICT DO UPDATE.
            print("Intentando guardar/actualizar credenciales de Binance desde .env...")
            
            # Encriptar las claves antes de guardarlas
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
            await credential_service.save_encrypted_credential(binance_credential) # Usar el nuevo método
            print("Credenciales de Binance guardadas/actualizadas exitosamente desde .env.")
            # Ya no se necesita el 'else' porque siempre se intenta guardar/actualizar.
        except Exception as e:
            QMessageBox.critical(None, "Error de Credenciales", f"Error al guardar/actualizar credenciales de Binance: {str(e)}\n\nLa aplicación se cerrará.")
            sys.exit(1)
        # --- Fin de la lógica de credenciales de Binance ---

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
