"""
UltiBot Frontend Main Application

Este módulo inicializa y configura la aplicación PyQt5 del frontend UltiBot,
incluyendo la configuración de servicios backend y la interfaz de usuario.

Para ejecutar correctamente la aplicación, use desde la raíz del proyecto:
    poetry run python src/ultibot_ui/main.py
    
O asegúrese de que el directorio raíz del proyecto esté en PYTHONPATH.
"""

import asyncio
import os
import sys
from typing import Optional
from uuid import UUID

from PyQt5.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv

# Importaciones organizadas por grupos
from ..shared.data_types import APICredential, ServiceName, UserConfiguration
from ..ultibot_backend.adapters.binance_adapter import BinanceAdapter
from ..ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ..ultibot_backend.app_config import AppSettings
from ..ultibot_backend.services.config_service import ConfigService
from ..ultibot_backend.services.credential_service import CredentialService
from ..ultibot_backend.services.market_data_service import MarketDataService
from ..ultibot_backend.services.notification_service import NotificationService
from ..ultibot_backend.services.portfolio_service import PortfolioService
from .windows.main_window import MainWindow

# Importar qdarkstyle de forma segura
try:
    import qdarkstyle
    DARK_STYLE_AVAILABLE = True
except ImportError:
    qdarkstyle = None
    DARK_STYLE_AVAILABLE = False
    print("Advertencia: qdarkstyle no está instalado. La aplicación usará el tema por defecto de Qt.")


class UltiBotApplication:
    """
    Clase principal para manejar la aplicación UltiBot UI.
    
    Encapsula la inicialización de servicios, configuración y UI.
    """
    
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.settings: Optional[AppSettings] = None
        self.user_id: Optional[UUID] = None
        
        # Servicios backend
        self.persistence_service: Optional[SupabasePersistenceService] = None
        self.credential_service: Optional[CredentialService] = None
        self.market_data_service: Optional[MarketDataService] = None
        self.config_service: Optional[ConfigService] = None
        self.notification_service: Optional[NotificationService] = None
        self.portfolio_service: Optional[PortfolioService] = None
        
        # Adaptadores
        self.binance_adapter: Optional[BinanceAdapter] = None
    
    def setup_qt_application(self) -> QApplication:
        """
        Configura la aplicación PyQt5.
        
        Returns:
            QApplication: Instancia de la aplicación Qt configurada.
        """
        app = QApplication(sys.argv)
        
        # Aplicar el tema oscuro si está disponible
        if DARK_STYLE_AVAILABLE:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        self.app = app
        return app
    
    def load_configuration(self) -> AppSettings:
        """
        Carga la configuración desde variables de entorno.
        
        Returns:
            AppSettings: Configuración de la aplicación.
            
        Raises:
            ValueError: Si faltan configuraciones críticas.
        """
        load_dotenv(override=True)
        
        # Verificar clave de encriptación
        credential_encryption_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        if not credential_encryption_key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY no está configurada en .env file o variables de entorno."
            )
        
        settings = AppSettings(CREDENTIAL_ENCRYPTION_KEY=credential_encryption_key)
        self.settings = settings
        self.user_id = settings.FIXED_USER_ID
        
        return settings
    
    async def initialize_persistence_service(self) -> SupabasePersistenceService:
        """
        Inicializa el servicio de persistencia.
        
        Returns:
            SupabasePersistenceService: Servicio de persistencia inicializado.
            
        Raises:
            Exception: Si falla la conexión a la base de datos.
        """
        persistence_service = SupabasePersistenceService()
        await persistence_service.connect()
        
        # Asegurar que el user_id exista en user_configurations
        await self._ensure_user_exists_in_db(persistence_service)
        
        self.persistence_service = persistence_service
        return persistence_service
    
    async def _ensure_user_exists_in_db(self, persistence_service: SupabasePersistenceService) -> None:
        """
        Asegura que el user_id exista en la tabla user_configurations.
        
        Args:
            persistence_service: Servicio de persistencia para ejecutar SQL.
        """
        try:
            await persistence_service.execute_raw_sql(
                """
                INSERT INTO user_configurations (user_id, selected_theme)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING;
                """,
                (self.user_id, "dark")
            )
            print(f"Asegurado que user_id {self.user_id} existe en user_configurations.")
            await asyncio.sleep(0.1)  # Pequeño retraso para consistencia de BD
        except Exception as e:
            raise Exception(f"Error al asegurar la existencia del usuario en la base de datos: {str(e)}")
    
    async def initialize_core_services(self) -> None:
        """
        Inicializa los servicios core de la aplicación.
        
        Raises:
            Exception: Si falla la inicialización de algún servicio crítico.
        """
        if not self.settings or not self.persistence_service:
            raise RuntimeError("Configuración o servicio de persistencia no inicializados")
        
        # Inicializar CredentialService
        self.credential_service = CredentialService(
            encryption_key=self.settings.CREDENTIAL_ENCRYPTION_KEY
        )
        
        # Inicializar adaptadores
        self.binance_adapter = BinanceAdapter()
        
        # Inicializar MarketDataService
        self.market_data_service = MarketDataService(
            self.credential_service,
            self.binance_adapter
        )
        
        # Inicializar PortfolioService
        self.portfolio_service = PortfolioService(
            self.market_data_service,
            self.persistence_service
        )
        
        # Inicializar ConfigService
        self.config_service = ConfigService(
            self.persistence_service,
            credential_service=self.credential_service,
            portfolio_service=self.portfolio_service
        )
        
        # Inicializar NotificationService
        self.notification_service = NotificationService(
            self.credential_service,
            self.persistence_service,
            self.config_service
        )
        
        # Inyectar NotificationService en ConfigService
        self.config_service.set_notification_service(self.notification_service)
    
    async def ensure_user_configuration(self) -> None:
        """
        Asegura que exista una configuración de usuario válida.
        
        Raises:
            Exception: Si falla la carga/creación de la configuración.
        """
        if not self.config_service:
            raise RuntimeError("ConfigService no inicializado")
        
        try:
            existing_config = await self.config_service.get_user_configuration(str(self.user_id))
            print(f"Configuración de usuario para {self.user_id} cargada exitosamente.")
        except Exception as e:
            raise Exception(f"Error al cargar configuración de usuario: {str(e)}")
    
    async def setup_binance_credentials(self) -> None:
        """
        Configura las credenciales de Binance desde variables de entorno.
        
        Raises:
            ValueError: Si faltan las credenciales de Binance.
            Exception: Si falla el guardado de credenciales.
        """
        binance_api_key = os.getenv("BINANCE_API_KEY")
        binance_api_secret = os.getenv("BINANCE_API_SECRET")
        
        if not binance_api_key or not binance_api_secret:
            raise ValueError(
                "BINANCE_API_KEY o BINANCE_API_SECRET no encontradas en .env o variables de entorno."
            )
        
        try:
            # Verificar si ya existen credenciales
            existing_credential = await self.credential_service.get_credential(
                user_id=self.user_id,
                service_name=ServiceName.BINANCE_SPOT,
                credential_label="default"
            )
            
            print("Guardando/actualizando credenciales de Binance desde .env...")
            
            # Encriptar credenciales
            encrypted_api_key = self.credential_service.encrypt_data(binance_api_key)
            encrypted_api_secret = self.credential_service.encrypt_data(binance_api_secret)
            
            # Crear credencial
            binance_credential = APICredential(
                id=self.settings.FIXED_BINANCE_CREDENTIAL_ID,
                user_id=self.user_id,
                service_name=ServiceName.BINANCE_SPOT,
                credential_label="default",
                encrypted_api_key=encrypted_api_key,
                encrypted_api_secret=encrypted_api_secret
            )
            
            # Asegurar que service_name sea Enum
            if isinstance(binance_credential.service_name, str):
                binance_credential.service_name = ServiceName(binance_credential.service_name)
            
            await self.credential_service.save_encrypted_credential(binance_credential)
            print("Credenciales de Binance guardadas/actualizadas exitosamente.")
            
        except Exception as e:
            raise Exception(f"Error al guardar/actualizar credenciales de Binance: {str(e)}")
    
    def create_main_window(self) -> MainWindow:
        """
        Crea y configura la ventana principal.
        
        Returns:
            MainWindow: Instancia de la ventana principal configurada.
            
        Raises:
            RuntimeError: Si los servicios requeridos no están inicializados.
        """
        required_services = [
            self.user_id, self.market_data_service, self.config_service,
            self.notification_service, self.persistence_service
        ]
        
        if any(service is None for service in required_services):
            raise RuntimeError("Servicios requeridos no están inicializados")
        
        main_window = MainWindow(
            self.user_id,
            self.market_data_service,
            self.config_service,
            self.notification_service,
            self.persistence_service
        )
        
        self.main_window = main_window
        return main_window
    
    async def cleanup_resources(self) -> None:
        """
        Limpia todos los recursos asíncronos.
        """
        print("Iniciando limpieza de recursos asíncronos...")
        
        cleanup_tasks = [
            ("PersistenceService", self.persistence_service),
            ("MarketDataService", self.market_data_service),
        ]
        
        for service_name, service in cleanup_tasks:
            if service:
                try:
                    print(f"Limpiando {service_name}...")
                    if hasattr(service, 'disconnect'):
                        await service.disconnect()
                    elif hasattr(service, 'close'):
                        await service.close()
                    print(f"{service_name} limpiado correctamente.")
                except Exception as e:
                    print(f"Error durante la limpieza de {service_name}: {e}")
        
        print("Limpieza de recursos asíncronos completada.")
    
    def show_error_and_exit(self, title: str, message: str, exit_code: int = 1) -> None:
        """
        Muestra un mensaje de error y termina la aplicación.
        
        Args:
            title: Título del mensaje de error.
            message: Mensaje de error detallado.
            exit_code: Código de salida de la aplicación.
        """
        if self.app:
            QMessageBox.critical(None, title, f"{message}\\n\\nLa aplicación se cerrará.")
        else:
            print(f"ERROR - {title}: {message}")
        sys.exit(exit_code)


async def run_application() -> None:
    """
    Función principal para ejecutar la aplicación UltiBot.
    """
    ultibot_app = UltiBotApplication()
    
    try:
        # 1. Configurar aplicación PyQt5
        qt_app = ultibot_app.setup_qt_application()
        
        # 2. Cargar configuración
        settings = ultibot_app.load_configuration()
        
        # 3. Inicializar servicio de persistencia
        await ultibot_app.initialize_persistence_service()
        
        # 4. Inicializar servicios core
        await ultibot_app.initialize_core_services()
        
        # 5. Asegurar configuración de usuario
        await ultibot_app.ensure_user_configuration()
        
        # 6. Configurar credenciales de Binance
        await ultibot_app.setup_binance_credentials()
        
        # 7. Crear y mostrar ventana principal
        main_window = ultibot_app.create_main_window()
        main_window.show()
        
        # 8. Ejecutar loop de eventos de Qt
        exit_code = qt_app.exec_()
        
        # 9. Limpieza de recursos
        await ultibot_app.cleanup_resources()
        
        sys.exit(exit_code)
        
    except ValueError as ve:
        ultibot_app.show_error_and_exit(
            "Error de Configuración",
            f"Error de configuración: {str(ve)}\\n\\nPor favor verifique su archivo .env o variables de entorno."
        )
    
    except Exception as e:
        ultibot_app.show_error_and_exit(
            "Error de Inicialización de Servicios",
            f"Falló la inicialización de servicios críticos: {str(e)}"
        )


def main() -> None:
    """
    Punto de entrada principal de la aplicación.
    
    Configura el event loop apropiado para Windows y ejecuta la aplicación.
    """
    # Solución para Windows ProactorEventLoop con psycopg
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Ejecutar la aplicación asíncrona
    asyncio.run(run_application())


if __name__ == "__main__":
    main()
