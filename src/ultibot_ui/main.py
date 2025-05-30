import sys
import qdarkstyle
import asyncio
from PyQt5.QtWidgets import QApplication
from uuid import UUID, uuid4 # Importar uuid4
from qasync import run # Importar run de qasync
from typing import List, Dict, Any, Optional # Importar tipos de typing
from datetime import datetime, timedelta # Importar datetime y timedelta

# Importar la MainWindow
from ultibot_ui.windows.main_window import MainWindow

# Importar servicios de backend
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService

# Importar modelos de datos compartidos
from src.shared.data_types import Notification, NotificationPriority, NotificationAction

# --- Mocks para desarrollo local y pruebas ---
class MockNotificationService:
    """
    Mock del NotificationService para desarrollo de UI.
    Simula el historial de notificaciones y la capacidad de marcarlas como leídas.
    """
    def __init__(self):
        self._notifications: List[Dict[str, Any]] = []
        self._populate_mock_notifications()

    def _populate_mock_notifications(self):
        # Notificación de error crítico
        self._notifications.append(Notification(
            id=uuid4(),
            eventType="SYSTEM_ERROR",
            channel="ui",
            title="Error Crítico de Conexión",
            message="No se pudo establecer conexión con la API de Binance. Revise sus credenciales.",
            priority=NotificationPriority.CRITICAL,
            createdAt=datetime.utcnow() - timedelta(minutes=5)
        ).model_dump()) # Usar model_dump para obtener un dict

        # Notificación de éxito de operación
        self._notifications.append(Notification(
            id=uuid4(),
            eventType="REAL_TRADE_EXECUTED",
            channel="ui",
            title="Operación Exitosa",
            message="Compra de BTC/USDT ejecutada con éxito. Cantidad: 0.001 BTC, Precio: 60,000 USDT.",
            priority=NotificationPriority.HIGH,
            createdAt=datetime.utcnow() - timedelta(minutes=2)
        ).model_dump())

        # Notificación de advertencia
        self._notifications.append(Notification(
            id=uuid4(),
            eventType="RISK_ALERT",
            channel="ui",
            title="Advertencia de Riesgo",
            message="El drawdown actual de su portafolio de paper trading ha superado el 5%.",
            priority=NotificationPriority.MEDIUM,
            createdAt=datetime.utcnow() - timedelta(minutes=1)
        ).model_dump())

        # Notificación de información
        self._notifications.append(Notification(
            id=uuid4(),
            eventType="INFO",
            channel="ui",
            title="Actualización del Sistema",
            message="Los datos de mercado se han actualizado correctamente.",
            priority=NotificationPriority.LOW,
            createdAt=datetime.utcnow()
        ).model_dump())

        # Notificación con acción (ejemplo)
        self._notifications.append(Notification(
            id=uuid4(),
            eventType="OPPORTUNITY_ANALYZED",
            channel="ui",
            title="Nueva Oportunidad Detectada",
            message="Se ha detectado una oportunidad de compra para ETH/USDT con alta confianza.",
            priority=NotificationPriority.HIGH,
            createdAt=datetime.utcnow() + timedelta(seconds=10),
            actions=[
                NotificationAction(label="Ver Detalles", actionType="NAVIGATE", actionValue="/opportunity/123"),
                NotificationAction(label="Ejecutar en Paper", actionType="API_CALL", actionValue={"endpoint": "/trade/paper/execute", "method": "POST"})
            ]
        ).model_dump())

    async def get_notification_history(self, user_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """Simula la obtención del historial de notificaciones."""
        print(f"MockNotificationService: Obteniendo historial para {user_id}")
        # Devolver las últimas 'limit' notificaciones
        return self._notifications[:limit]

    async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID):
        """Simula marcar una notificación como leída."""
        print(f"MockNotificationService: Marcando notificación {notification_id} como leída para {user_id}")
        # En un mock, no hacemos nada real, pero podríamos cambiar el estado interno
        for notif in self._notifications:
            if notif["id"] == str(notification_id):
                notif["status"] = "read"
                notif["readAt"] = datetime.utcnow().isoformat() + "Z"
                break

    async def mark_all_notifications_as_read(self, user_id: UUID):
        """Simula marcar todas las notificaciones como leídas."""
        print(f"MockNotificationService: Marcando todas las notificaciones como leídas para {user_id}")
        for notif in self._notifications:
            notif["status"] = "read"
            notif["readAt"] = datetime.utcnow().isoformat() + "Z"
        self._notifications = [] # Limpiar el historial del mock

    async def send_notification(self, user_id: UUID, title: str, message: str, channel: str = "telegram", event_type: str = "SYSTEM_MESSAGE") -> bool:
        """Simula el envío de una notificación."""
        print(f"MockNotificationService: Enviando notificación a {channel} para {user_id}: {title} - {message}")
        # En un mock, simplemente la añadimos al historial si es para UI
        if channel == "ui":
            new_notif = Notification(
                id=uuid4(),
                eventType=event_type,
                channel=channel,
                title=title,
                message=message,
                createdAt=datetime.utcnow()
            )
            self._notifications.insert(0, new_notif.model_dump())
        return True

    async def close(self):
        """Simula el cierre del servicio."""
        print("MockNotificationService: Cerrando.")
        pass

async def start_application():
    app = QApplication(sys.argv)

    # Aplicar el tema oscuro
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # Inicializar servicios de backend
    # Para un entorno de desarrollo/prueba, puedes usar un UUID fijo
    # En un entorno de producción, el user_id se obtendría de la autenticación
    user_id = UUID("00000000-0000-0000-0000-000000000001") 

    # Inicializar PersistenceService (requiere configuración de Supabase)
    persistence_service = SupabasePersistenceService()
    
    credential_service = CredentialService() # CredentialService no necesita persistence_service en su constructor
    binance_adapter = BinanceAdapter()
    market_data_service = MarketDataService(credential_service, binance_adapter)
    config_service = ConfigService(persistence_service)
    
    # Instanciar el MockNotificationService
    notification_service = MockNotificationService() # type: ignore # Ignorar error de Pylance para el mock

    # Crear y mostrar la ventana principal, pasando los servicios
    main_window = MainWindow(user_id, market_data_service, config_service, notification_service) # type: ignore # Pasar notification_service
    main_window.show()

    # qasync se encarga de ejecutar el loop de eventos de Qt y asyncio
    return app.exec_() # Retornar el código de salida de la aplicación Qt

if __name__ == "__main__":
    # Ejecutar la aplicación asíncrona con qasync
    run(start_application())
