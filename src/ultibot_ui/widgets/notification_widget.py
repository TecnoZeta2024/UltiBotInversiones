import sys
import asyncio # Importar asyncio
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QApplication, QAbstractItemView, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon
from typing import List, Optional, Any # Importar Any
from datetime import datetime
from uuid import UUID, uuid4 # Importar UUID y uuid4

from src.shared.data_types import Notification, NotificationPriority, NotificationAction # Importar los tipos de datos

class NotificationWidget(QWidget):
    """
    Widget para mostrar notificaciones del sistema en la UI.
    """
    notification_dismissed = pyqtSignal(str) # Emite el ID de la notificación descartada
    all_notifications_read = pyqtSignal() # Emite cuando todas las notificaciones se marcan como leídas

    def __init__(self, notification_service: Any, user_id: UUID, parent: Optional[QWidget] = None): # Añadir notification_service y user_id
        super().__init__(parent)
        self.notification_service = notification_service
        self.user_id = user_id
        self.notifications: List[Notification] = [] # Almacena las notificaciones activas
        self.init_ui()
        self._setup_styles()
        self._setup_realtime_updates() # Configurar actualizaciones en tiempo real

    def _setup_realtime_updates(self):
        """
        Configura un temporizador para buscar nuevas notificaciones periódicamente.
        """
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(5000)  # Actualizar cada 5 segundos (ajustable)
        self.update_timer.timeout.connect(self._fetch_notifications)
        self.update_timer.start()

    def _fetch_notifications(self):
        """
        Obtiene las notificaciones pendientes del servicio y las añade al widget.
        """
        # Ejecutar la llamada asíncrona en un hilo separado o usar un executor
        # Para simplificar, usaremos un enfoque que no bloquee la UI directamente.
        # En una aplicación real, esto podría usar QThreadPool o un enfoque más robusto.
        
        # Aquí se asume que notification_service.get_notification_history es un método asíncrono.
        # Para llamarlo desde un contexto síncrono de Qt, necesitamos un bucle de eventos asyncio.
        # Dado que la aplicación principal ya usa asyncio.run, podemos usar asyncio.create_task
        # para programar la corrutina.
        
        async def fetch_and_add():
            try:
                # Obtener solo las notificaciones no leídas o activas
                # Asumiendo que get_notification_history puede filtrar por estado o que
                # solo queremos las más recientes y el widget maneja los duplicados.
                # Para este ejemplo, obtendremos las últimas 20 notificaciones.
                # El filtrado por 'status' debe hacerse en el lado del cliente si el servicio no lo soporta,
                # o el servicio debe ser actualizado para soportarlo. Por ahora, eliminamos el argumento.
                new_notifications = await self.notification_service.get_notification_history(
                    user_id=self.user_id, limit=20
                )
                for notif in new_notifications:
                    self.add_notification(notif)
            except Exception as e:
                print(f"Error al obtener notificaciones en tiempo real: {e}")

        # Programar la corrutina para que se ejecute en el bucle de eventos existente
        # Esto requiere que el bucle de eventos de asyncio esté corriendo, lo cual es cierto
        # porque main.py usa asyncio.run().
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                # Esto no debería ocurrir si main.py está configurado correctamente
                # para ejecutar el bucle de eventos.
                print("Advertencia: El bucle de eventos de asyncio no está corriendo. No se pueden obtener notificaciones.")
                return
            asyncio.create_task(fetch_and_add())
        except RuntimeError:
            # Esto puede ocurrir si el bucle de eventos ya se cerró o no se ha iniciado.
            print("Error: No se pudo obtener el bucle de eventos de asyncio para las notificaciones.")


    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Título del panel
        title_label = QLabel("Notificaciones del Sistema")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0f0f0;")
        main_layout.addWidget(title_label)

        # Lista de notificaciones
        self.notification_list = QListWidget()
        self.notification_list.setAlternatingRowColors(True)
        self.notification_list.setSelectionMode(QAbstractItemView.NoSelection) # No permitir selección
        self.notification_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel) # Desplazamiento suave
        self.notification_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.notification_list)

        # Controles (descartar, marcar como leídas)
        controls_layout = QHBoxLayout()
        self.dismiss_selected_button = QPushButton("Descartar Seleccionada")
        self.dismiss_selected_button.clicked.connect(self._dismiss_selected_notification)
        self.dismiss_selected_button.setEnabled(False) # Deshabilitado hasta que haya selección

        self.mark_all_read_button = QPushButton("Marcar Todas como Leídas")
        self.mark_all_read_button.clicked.connect(self._mark_all_as_read)
        self.mark_all_read_button.setEnabled(False) # Deshabilitado hasta que haya notificaciones

        controls_layout.addWidget(self.dismiss_selected_button)
        controls_layout.addWidget(self.mark_all_read_button)
        controls_layout.addStretch(1) # Empuja los botones a la izquierda

        main_layout.addLayout(controls_layout)

        # Conectar la señal de cambio de selección para habilitar/deshabilitar el botón de descartar
        self.notification_list.itemSelectionChanged.connect(self._update_dismiss_button_state)

    def _setup_styles(self):
        self.setStyleSheet("""
            NotificationWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QListWidget {
                background-color: #222;
                border: 1px solid #333;
                border-radius: 3px;
                color: #f0f0f0;
            }
            QListWidget::item {
                padding: 8px;
                margin-bottom: 2px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:alternate {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #0056b3; /* Color de selección */
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #bbb;
            }
        """)

    def add_notification(self, notification: Notification):
        """
        Añade una nueva notificación al panel.
        Las notificaciones más nuevas aparecen en la parte superior.
        """
        # Evitar duplicados si ya existe una notificación con el mismo ID
        if any(n.id == notification.id for n in self.notifications):
            return

        self.notifications.insert(0, notification) # Añadir al principio para que sea la más nueva
        self._update_notification_list_ui()
        self._update_control_buttons_state()

    def _update_notification_list_ui(self):
        """
        Actualiza la QListWidget con las notificaciones actuales.
        """
        self.notification_list.clear()
        for notification in self.notifications:
            item = QListWidgetItem(self.notification_list)
            
            # Crear un widget personalizado para cada elemento de la lista
            notification_item_widget = self._create_notification_item_widget(notification)
            item.setSizeHint(notification_item_widget.sizeHint()) # Ajustar altura del item
            self.notification_list.setItemWidget(item, notification_item_widget)

    def _create_notification_item_widget(self, notification: Notification) -> QWidget:
        """
        Crea un widget personalizado para representar una notificación individual.
        """
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 5, 5, 5)
        item_layout.setSpacing(10)

        # Icono (AC3)
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24) # Tamaño fijo para el icono
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("border-radius: 12px;") # Fondo circular para el icono
        
        icon_path, bg_color = self._get_icon_and_color_for_priority(notification.priority)
        if icon_path:
            icon_label.setPixmap(QIcon(icon_path).pixmap(20, 20))
        icon_label.setStyleSheet(f"background-color: {bg_color}; border-radius: 12px;")
        item_layout.addWidget(icon_label)

        # Contenido de la notificación (AC4)
        content_layout = QVBoxLayout()
        
        # Título y Timestamp
        header_layout = QHBoxLayout()
        title_label = QLabel(notification.title)
        title_label.setStyleSheet("font-weight: bold; color: #f0f0f0;")
        
        timestamp_label = QLabel(notification.createdAt.strftime("%Y-%m-%d %H:%M:%S"))
        timestamp_label.setStyleSheet("font-size: 10px; color: #888;")
        timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(timestamp_label)
        content_layout.addLayout(header_layout)

        # Mensaje
        message_label = QLabel(notification.message)
        message_label.setWordWrap(True) # Ajustar texto
        message_label.setStyleSheet("color: #cccccc;")
        content_layout.addWidget(message_label)

        item_layout.addLayout(content_layout)

        # Botón de descartar individual (AC6)
        dismiss_button = QPushButton("X")
        dismiss_button.setFixedSize(24, 24)
        dismiss_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        # Conectar el botón a un slot que descarte esta notificación específica
        dismiss_button.clicked.connect(lambda _, n_id=str(notification.id): self._dismiss_notification_by_id(n_id)) # Convertir UUID a str
        item_layout.addWidget(dismiss_button, alignment=Qt.AlignmentFlag.AlignTop)

        # Marcar como leída si el estado es 'read' o 'archived'
        if notification.status in ["read", "archived"]:
            item_widget.setStyleSheet("background-color: #3a3a3a; color: #888;") # Atenuar visualmente
            title_label.setStyleSheet("font-weight: bold; color: #888;")
            message_label.setStyleSheet("color: #666;")
            dismiss_button.setEnabled(False) # No se puede descartar si ya está leída/archivada

        return item_widget

    def _get_icon_and_color_for_priority(self, priority: Optional[NotificationPriority]):
        """
        Devuelve la ruta del icono y el color de fondo según la prioridad.
        """
        # TODO: Usar iconos reales. Por ahora, placeholders.
        # Los iconos deberían estar en src/ultibot_ui/assets/icons/
        base_path = "src/ultibot_ui/assets/icons/" # Asegurarse de que esta ruta sea correcta
        
        if priority == NotificationPriority.CRITICAL:
            return f"{base_path}error.png", "#dc3545" # Rojo
        elif priority == NotificationPriority.HIGH:
            return f"{base_path}warning.png", "#ffc107" # Amarillo
        elif priority == NotificationPriority.MEDIUM:
            return f"{base_path}info.png", "#007bff" # Azul
        elif priority == NotificationPriority.LOW:
            return f"{base_path}info.png", "#6c757d" # Gris
        else: # Default
            return f"{base_path}info.png", "#007bff"

    def _dismiss_selected_notification(self):
        """
        Descartar la notificación seleccionada actualmente.
        """
        selected_items = self.notification_list.selectedItems()
        if selected_items:
            # Asumimos que solo se puede seleccionar un item a la vez o que queremos el primero
            item = selected_items[0]
            row = self.notification_list.row(item)
            if 0 <= row < len(self.notifications):
                notification_id = self.notifications[row].id
                self._dismiss_notification_by_id(str(notification_id)) # Convertir UUID a str

    def _dismiss_notification_by_id(self, notification_id: str):
        """
        Descartar una notificación por su ID.
        Esto la remueve de la lista visible y emite una señal.
        """
        self.notifications = [n for n in self.notifications if str(n.id) != notification_id]
        self._update_notification_list_ui()
        self._update_control_buttons_state()
        self.notification_dismissed.emit(notification_id) # Notificar al backend o servicio

    def _mark_all_as_read(self):
        """
        Marca todas las notificaciones como leídas y las descarta visualmente.
        """
        # En una implementación real, esto también notificaría al backend para actualizar el estado
        self.notifications = [] # Limpiar todas las notificaciones visibles
        self._update_notification_list_ui()
        self._update_control_buttons_state()
        self.all_notifications_read.emit() # Notificar al backend o servicio

    def _update_dismiss_button_state(self):
        """
        Actualiza el estado del botón 'Descartar Seleccionada' basado en la selección.
        """
        self.dismiss_selected_button.setEnabled(len(self.notification_list.selectedItems()) > 0)

    def _update_control_buttons_state(self):
        """
        Actualiza el estado de los botones de control (Marcar Todas como Leídas).
        """
        has_notifications = len(self.notifications) > 0
        self.mark_all_read_button.setEnabled(has_notifications)
        self.dismiss_selected_button.setEnabled(has_notifications and len(self.notification_list.selectedItems()) > 0)

    def cleanup(self):
        """
        Limpia los recursos utilizados por NotificationWidget.
        Principalmente, detiene el temporizador de actualización.
        """
        print("NotificationWidget: cleanup called.")
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            print("NotificationWidget: Stopping update timer.")
            self.update_timer.stop()
        print("NotificationWidget: cleanup finished.")


# Ejemplo de uso para pruebas locales
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            background-color: #222;
            color: #f0f0f0;
            font-family: "Segoe UI", sans-serif;
        }
        QLabel {
            color: #f0f0f0;
        }
        QPushButton {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:disabled {
            background-color: #555;
            color: #bbb;
        }
    """)

    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)
    main_window.setLayout(main_layout)

    # Mock simple para NotificationService para la prueba
    class MockNotificationService:
        async def get_notification_history(self, user_id: UUID, limit: int = 50) -> List[Notification]:
            # Devuelve algunas notificaciones de prueba
            return [
                Notification(
                    id=uuid4(),
                    userId=user_id,
                    eventType="MOCK_INFO",
                    channel="ui",
                    title="Notificación de Prueba 1",
                    message="Este es un mensaje de prueba para el historial.",
                    createdAt=datetime.utcnow() - timedelta(minutes=10)
                ),
                Notification(
                    id=uuid4(),
                    userId=user_id,
                    eventType="MOCK_WARNING",
                    channel="ui",
                    title="Notificación de Prueba 2",
                    message="Otro mensaje de prueba para el historial.",
                    createdAt=datetime.utcnow() - timedelta(minutes=20)
                )
            ]
        
        async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
            print(f"Mock: Notificación {notification_id} marcada como leída.")
            return None # No implementado para el mock

        async def save_notification(self, notification: Notification) -> Notification:
            print(f"Mock: Notificación {notification.id} guardada.")
            return notification

    test_user_id = uuid4()
    notification_widget = NotificationWidget(MockNotificationService(), test_user_id)
    main_layout.addWidget(notification_widget)

    # Añadir algunas notificaciones de prueba
    from datetime import datetime, timedelta

    # Notificación de error crítico
    notification_widget.add_notification(Notification(
        id=uuid4(),
        eventType="SYSTEM_ERROR",
        channel="ui",
        title="Error Crítico de Conexión",
        message="No se pudo establecer conexión con la API de Binance. Revise sus credenciales.",
        priority=NotificationPriority.CRITICAL,
        createdAt=datetime.utcnow() - timedelta(minutes=5)
    ))

    # Notificación de éxito de operación
    notification_widget.add_notification(Notification(
        id=uuid4(),
        eventType="REAL_TRADE_EXECUTED",
        channel="ui",
        title="Operación Exitosa",
        message="Compra de BTC/USDT ejecutada con éxito. Cantidad: 0.001 BTC, Precio: 60,000 USDT.",
        priority=NotificationPriority.HIGH,
        createdAt=datetime.utcnow() - timedelta(minutes=2)
    ))

    # Notificación de advertencia
    notification_widget.add_notification(Notification(
        id=uuid4(),
        eventType="RISK_ALERT",
        channel="ui",
        title="Advertencia de Riesgo",
        message="El drawdown actual de su portafolio de paper trading ha superado el 5%.",
        priority=NotificationPriority.MEDIUM,
        createdAt=datetime.utcnow() - timedelta(minutes=1)
    ))

    # Notificación de información
    notification_widget.add_notification(Notification(
        id=uuid4(),
        eventType="INFO",
        channel="ui",
        title="Actualización del Sistema",
        message="Los datos de mercado se han actualizado correctamente.",
        priority=NotificationPriority.LOW,
        createdAt=datetime.utcnow()
    ))

    # Notificación con acción (ejemplo)
    notification_widget.add_notification(Notification(
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
    ))

    main_window.show()
    sys.exit(app.exec_())
