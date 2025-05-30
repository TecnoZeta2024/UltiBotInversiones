import sys
import qdarkstyle
import asyncio
from PyQt5.QtWidgets import QApplication
from uuid import UUID
from qasync.qt import QEventLoopPolicy # Importar QEventLoopPolicy de qasync.qt
from qasync import run # Importar run de qasync

# Importar la MainWindow
from ultibot_ui.windows.main_window import MainWindow

# Importar servicios de backend
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService as BackendMarketDataService # Alias para claridad
from src.ultibot_backend.services.config_service import ConfigService as BackendConfigService # Alias para claridad

# Importar UI service wrappers
from src.ultibot_ui.services import UIMarketDataService # Importar el wrapper
from src.ultibot_ui.services import UIConfigService # Importar el wrapper

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
    
    # Inicializar servicios de backend
    credential_service = CredentialService()
    binance_adapter = BinanceAdapter()
    # Renombrar instancias de backend para evitar confusión
    backend_market_data_service = BackendMarketDataService(credential_service, binance_adapter)
    backend_config_service = BackendConfigService(persistence_service)

    # Inicializar UI service wrappers, pasando los servicios de backend
    ui_market_data_service = UIMarketDataService(backend_market_data_service=backend_market_data_service)
    ui_config_service = UIConfigService(backend_config_service=backend_config_service)

    # Crear y mostrar la ventana principal, pasando los UI service wrappers
    main_window = MainWindow(user_id, ui_market_data_service, ui_config_service) # Actualizado aquí
    main_window.show()

    # qasync se encarga de ejecutar el loop de eventos de Qt y asyncio
    # No es necesario sys.exit(app.exec_()) aquí, qasync.run lo maneja.
    # El retorno de run() es el resultado de la corrutina, que en este caso no se usa.
    return app.exec_() # Retornar el código de salida de la aplicación Qt

if __name__ == "__main__":
    # Establecer la política del bucle de eventos de asyncio a QEventLoopPolicy
    asyncio.set_event_loop_policy(QEventLoopPolicy())
    # Ejecutar la aplicación asíncrona con qasync
    run(start_application())
