import sys
import qdarkstyle
import asyncio
from PyQt5.QtWidgets import QApplication
from uuid import UUID

# Importar la MainWindow
from ultibot_ui.windows.main_window import MainWindow

# Importar servicios de backend
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService

async def start_application():
    app = QApplication(sys.argv)

    # Aplicar el tema oscuro
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # Inicializar servicios de backend
    # Para un entorno de desarrollo/prueba, puedes usar un UUID fijo
    # En un entorno de producción, el user_id se obtendría de la autenticación
    user_id = UUID("00000000-0000-0000-0000-000000000001") 

    # Inicializar PersistenceService (requiere configuración de Supabase)
    # Para este ejemplo, asumimos que SupabasePersistenceService puede inicializarse sin conexión activa
    # o que la conexión se establecerá de forma perezosa cuando sea necesaria.
    # En un entorno real, se podría inyectar una instancia ya conectada.
    persistence_service = SupabasePersistenceService()
    
    credential_service = CredentialService() # CredentialService no necesita persistence_service en su constructor
    binance_adapter = BinanceAdapter()
    market_data_service = MarketDataService(credential_service, binance_adapter)
    config_service = ConfigService(persistence_service)

    # Crear y mostrar la ventana principal, pasando los servicios
    main_window = MainWindow(user_id, market_data_service, config_service)
    main_window.show()

    # Ejecutar el loop de eventos de Qt
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Ejecutar la aplicación asíncrona
    asyncio.run(start_application())
