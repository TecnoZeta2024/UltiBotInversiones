import sys
import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QApplication, QAbstractItemView, QSizePolicy
)
from PySide6.QtCore import Qt, Signal as pyqtSignal, QTimer
from PySide6.QtGui import QColor, QFont, QIcon
from typing import List, Optional, Any, Dict # Importar Dict
from datetime import datetime
from uuid import UUID, uuid4

from shared.data_types import Notification, NotificationPriority
from ultibot_ui.models import BaseMainWindow
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError

class NotificationWidget(QWidget):
    """
    Widget para mostrar notificaciones del sistema en la UI.
    """
    notification_dismissed = pyqtSignal(str)
    all_notifications_read = pyqtSignal()

    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.api_client = api_client # Usar la instancia de api_client
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.main_window = main_window
        self.notifications: List[Notification] = []
        self._is_fetching_notifications = False
        self.update_timer: Optional[QTimer] = None
        self.init_ui()
        self._setup_styles()
        # No iniciar _setup_realtime_updates aquí, se iniciará después de set_user_id

    def set_user_id(self, user_id: UUID):
        """Establece el user_id y activa las actualizaciones de notificaciones."""
        self.user_id = user_id
        print(f"NotificationWidget: User ID set to {user_id}. Starting real-time updates.")
        self._setup_realtime_updates() # Iniciar actualizaciones una vez que el user_id esté disponible

    def _setup_realtime_updates(self):
        if self.update_timer is None: # Asegurarse de que el timer se inicialice una sola vez
            self.update_timer = QTimer(self)
            self.update_timer.setInterval(5000)
            self.update_timer.timeout.connect(self._fetch_notifications)
        if not self.update_timer.isActive():
            self.update_timer.start()

    def _fetch_notifications(self):
        if self._is_fetching_notifications:
            return
        asyncio.create_task(self._fetch_notifications_async())

    async def _fetch_notifications_async(self):
        if self._is_fetching_notifications:
            return
        self._is_fetching_notifications = True
        try:
            notifications_data = await self.api_client.get_notification_history(limit=20)
            self._handle_fetch_notifications_result(notifications_data)
        except Exception as e:
            self._handle_fetch_notifications_error(e)
        finally:
            self._is_fetching_notifications = False

    def _handle_fetch_notifications_result(self, new_notifications_response: Any):
        try:
            if not isinstance(new_notifications_response, list):
                print(f"Respuesta inesperada al obtener notificaciones: {type(new_notifications_response)}")
                return

            for notif_data in new_notifications_response:
                try:
                    notification = Notification.model_validate(notif_data)
                    self.add_notification(notification)
                except Exception as e:
                    print(f"Error de validación de notificación: {e} para datos: {notif_data}")
        except Exception as e:
            print(f"Error al procesar resultado de notificaciones: {e}")
        finally:
            self._is_fetching_notifications = False

    def _handle_fetch_notifications_error(self, error_message: Any):
        actual_message = error_message.message if isinstance(error_message, APIError) else str(error_message)
        
        if isinstance(error_message, APIError):
            print(f"Error API al obtener notificaciones en tiempo real: {actual_message}")
        else:
            print(f"Error al obtener notificaciones en tiempo real: {actual_message}")
        self._is_fetching_notifications = False

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        title_label = QLabel("Notificaciones del Sistema")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0f0f0;")
        main_layout.addWidget(title_label)

        self.notification_list = QListWidget()
        self.notification_list.setAlternatingRowColors(True)
        self.notification_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.notification_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.notification_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.notification_list)

        controls_layout = QHBoxLayout()
        self.dismiss_selected_button = QPushButton("Descartar Seleccionada")
        self.dismiss_selected_button.clicked.connect(self._dismiss_selected_notification)
        self.dismiss_selected_button.setEnabled(False)

        self.mark_all_read_button = QPushButton("Marcar Todas como Leídas")
        self.mark_all_read_button.clicked.connect(self._mark_all_as_read)
        self.mark_all_read_button.setEnabled(False)

        controls_layout.addWidget(self.dismiss_selected_button)
        controls_layout.addWidget(self.mark_all_read_button)
        controls_layout.addStretch(1)

        main_layout.addLayout(controls_layout)
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
                background-color: #0056b3;
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
        if any(n.id == notification.id for n in self.notifications):
            return
        self.notifications.insert(0, notification)
        self._update_notification_list_ui()
        self._update_control_buttons_state()

    def _update_notification_list_ui(self):
        self.notification_list.clear()
        for notification in self.notifications:
            item = QListWidgetItem(self.notification_list)
            notification_item_widget = self._create_notification_item_widget(notification)
            item.setSizeHint(notification_item_widget.sizeHint())
            self.notification_list.setItemWidget(item, notification_item_widget)

    def _create_notification_item_widget(self, notification: Notification) -> QWidget:
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 5, 5, 5)
        item_layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("border-radius: 12px;")
        
        icon_path, bg_color = self._get_icon_and_color_for_priority(notification.priority)
        if icon_path:
            try:
                q_icon = QIcon(icon_path)
                if not q_icon.isNull():
                    icon_label.setPixmap(q_icon.pixmap(20, 20))
                else:
                    print(f"Advertencia: No se pudo cargar el icono: {icon_path}")
            except Exception as e:
                print(f"Error al cargar icono {icon_path}: {e}")

        icon_label.setStyleSheet(f"background-color: {bg_color}; border-radius: 12px;")
        item_layout.addWidget(icon_label)

        content_layout = QVBoxLayout()
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

        message_label = QLabel(notification.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #cccccc;")
        content_layout.addWidget(message_label)
        item_layout.addLayout(content_layout)

        dismiss_button = QPushButton("X")
        dismiss_button.setFixedSize(24, 24)
        dismiss_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545; color: white; border: none;
                border-radius: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        dismiss_button.clicked.connect(lambda _, n_id=str(notification.id): self._dismiss_notification_by_id(n_id))
        item_layout.addWidget(dismiss_button, alignment=Qt.AlignmentFlag.AlignTop)

        if notification.status in ["read", "archived"]:
            item_widget.setStyleSheet("background-color: #3a3a3a; color: #888;")
            title_label.setStyleSheet("font-weight: bold; color: #888;")
            message_label.setStyleSheet("color: #666;")
            dismiss_button.setEnabled(False)
        return item_widget

    def _get_icon_and_color_for_priority(self, priority: Optional[NotificationPriority]):
        base_path = "src/ultibot_ui/assets/icons/"
        default_icon = f"{base_path}info.png"
        default_color = "#007bff"

        if priority == NotificationPriority.CRITICAL:
            return f"{base_path}error.png", "#dc3545"
        elif priority == NotificationPriority.HIGH:
            return f"{base_path}warning.png", "#ffc107"
        elif priority == NotificationPriority.MEDIUM:
            return default_icon, default_color
        elif priority == NotificationPriority.LOW:
            return f"{base_path}info_low.png", "#6c757d"
        else:
            return default_icon, default_color

    def _dismiss_selected_notification(self):
        selected_items = self.notification_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            row = self.notification_list.row(item)
            if 0 <= row < len(self.notifications):
                notification_id = self.notifications[row].id
                self._dismiss_notification_by_id(str(notification_id))

    def _dismiss_notification_by_id(self, notification_id: str):
        self.notifications = [n for n in self.notifications if str(n.id) != notification_id]
        self._update_notification_list_ui()
        self._update_control_buttons_state()
        self.notification_dismissed.emit(notification_id)

    def _mark_all_as_read(self):
        self.notifications = []
        self._update_notification_list_ui()
        self._update_control_buttons_state()
        self.all_notifications_read.emit()

    def _update_dismiss_button_state(self):
        self.dismiss_selected_button.setEnabled(len(self.notification_list.selectedItems()) > 0)

    def _update_control_buttons_state(self):
        has_notifications = len(self.notifications) > 0
        self.mark_all_read_button.setEnabled(has_notifications)
        self.dismiss_selected_button.setEnabled(has_notifications and len(self.notification_list.selectedItems()) > 0)

    def start_updates(self):
        """Inicia la actualización de notificaciones en tiempo real."""
        self._setup_realtime_updates() # Asegura que el timer esté configurado y activo
        self._fetch_notifications() # Fetch immediately on start

    def stop_updates(self):
        """Detiene la actualización de notificaciones en tiempo real."""
        if self.update_timer and self.update_timer.isActive():
            self.update_timer.stop()

    def cleanup(self):
        print("NotificationWidget: cleanup called.")
        self.stop_updates()
        print("NotificationWidget: cleanup finished.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget { background-color: #222; color: #f0f0f0; font-family: "Segoe UI", sans-serif; }
        QLabel { color: #f0f0f0; }
        QPushButton { background-color: #007bff; color: white; border: none; padding: 8px 15px; border-radius: 5px; }
        QPushButton:hover { background-color: #0056b3; }
        QPushButton:disabled { background-color: #555; color: #bbb; }
    """)

    main_window_widget = QWidget()
    main_layout = QVBoxLayout(main_window_widget)
    main_window_widget.setLayout(main_layout)

    class MockUltiBotAPIClient(UltiBotAPIClient): # Heredar de UltiBotAPIClient
        async def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]: # Retornar Dict[str, Any]
            from datetime import timedelta
            return [
                {"id": str(uuid4()), "userId": str(uuid4()), "eventType": "MOCK_INFO", "channel": "ui", "title": "Notificación de Prueba 1", "message": "Este es un mensaje de prueba para el historial.", "createdAt": (datetime.utcnow() - timedelta(minutes=10)).isoformat()},
                {"id": str(uuid4()), "userId": str(uuid4()), "eventType": "MOCK_WARNING", "channel": "ui", "title": "Notificación de Prueba 2", "message": "Otro mensaje de prueba para el historial.", "createdAt": (datetime.utcnow() - timedelta(minutes=20)).isoformat()}
            ]

    test_user_id = uuid4()
    
    class MockMainWindow(BaseMainWindow):
        def add_thread(self, thread): # No se necesita QThread aquí
            print(f"MockMainWindow: Thread '{thread.objectName()}' added for tracking.")

    mock_main_window = MockMainWindow()

    notification_widget = NotificationWidget(MockUltiBotAPIClient(base_url="http://mock"), mock_main_window) # Pasar base_url
    notification_widget.set_user_id(test_user_id) # Establecer user_id
    main_layout.addWidget(notification_widget)
    
    # Añadir algunas notificaciones de ejemplo para visualización
    from datetime import timedelta
    notification_widget.add_notification(Notification(id=uuid4(), userId=test_user_id, eventType="SYSTEM_ERROR", channel="ui", title="Error Crítico de Conexión", message="No se pudo establecer conexión con la API de Binance.", priority=NotificationPriority.CRITICAL, createdAt=datetime.utcnow() - timedelta(minutes=5)))
    notification_widget.add_notification(Notification(id=uuid4(), userId=test_user_id, eventType="REAL_TRADE_EXECUTED", channel="ui", title="Operación Exitosa", message="Compra de BTC/USDT ejecutada.", priority=NotificationPriority.HIGH, createdAt=datetime.utcnow() - timedelta(minutes=2)))
    notification_widget.add_notification(Notification(id=uuid4(), userId=test_user_id, eventType="INFO", channel="ui", title="Actualización del Sistema", message="La versión 1.2.0 ha sido desplegada con éxito.", priority=NotificationPriority.MEDIUM, createdAt=datetime.utcnow() - timedelta(minutes=1)))

    main_window_widget.show()
    sys.exit(app.exec_())
