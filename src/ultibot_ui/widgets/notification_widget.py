import sys
import asyncio
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QApplication, QAbstractItemView, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon
from typing import List, Optional, Any, Dict
from datetime import datetime
from uuid import UUID, uuid4
import logging

from src.shared.data_types import Notification, NotificationPriority
from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class NotificationWidget(QWidget):
    """
    Widget para mostrar notificaciones del sistema en la UI.
    """
    notification_dismissed = pyqtSignal(str)
    all_notifications_read = pyqtSignal()

    def __init__(self, user_id: UUID, main_window: BaseMainWindow, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.main_window = main_window
        self.api_client = api_client
        self.loop = loop
        self.notifications: List[Notification] = []
        self._is_fetching_notifications = False
        self.init_ui()
        # Se elimina la llamada a _setup_styles() para que los estilos se manejen globalmente en style.qss
        # self._setup_styles()
        self._setup_realtime_updates()

    def _setup_realtime_updates(self):
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(5000)
        self.update_timer.timeout.connect(self._fetch_notifications)
        self.update_timer.start()

    def _fetch_notifications(self):
        if self._is_fetching_notifications:
            return

        self._is_fetching_notifications = True
        
        coroutine_factory = lambda client: client.get_notification_history(limit=20)
        
        self.main_window.submit_task(
            coroutine_factory,
            self._handle_fetch_notifications_result,
            self._handle_fetch_notifications_error
        )

    def _handle_fetch_notifications_result(self, new_notifications_response: List[Dict[str, Any]]):
        try:
            if not isinstance(new_notifications_response, list):
                logger.warning(f"Respuesta inesperada al obtener notificaciones: {type(new_notifications_response)}")
                return

            for notif_data in new_notifications_response:
                if isinstance(notif_data, dict):
                    try:
                        notification = Notification(**notif_data)
                        self.add_notification(notification)
                    except Exception as e:
                        logger.error(f"Error al deserializar notificación: {e} - Datos: {notif_data}")
                else:
                    logger.warning(f"Tipo de notificación desconocido recibido: {type(notif_data)}")
        except Exception as e:
            logger.error(f"Error al procesar resultado de notificaciones: {e}", exc_info=True)
        finally:
            self._is_fetching_notifications = False

    def _handle_fetch_notifications_error(self, error_message: str):
        try:
            logger.error(f"Error API al obtener notificaciones en tiempo real: {error_message}")
        except Exception as e:
            logger.critical(f"Error irrecuperable en el manejador de errores de notificación: {e}", exc_info=True)
        finally:
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
                    logger.warning(f"No se pudo cargar el icono: {icon_path}")
            except Exception as e:
                logger.error(f"Error al cargar icono {icon_path}: {e}")

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
        dismiss_button.setObjectName("dismissButton") # Asignar un objectName para estilizarlo desde QSS
        dismiss_button.clicked.connect(lambda _, n_id=str(notification.id): self._dismiss_notification_by_id(n_id))
        item_layout.addWidget(dismiss_button, alignment=Qt.AlignmentFlag.AlignTop)

        # Asegurar que el widget del ítem ajuste su tamaño para el contenido envuelto
        item_widget.adjustSize() 
        item.setSizeHint(item_widget.sizeHint()) # Recalcular sizeHint después de ajustar el tamaño

        if notification.status in ["read", "archived"]:
            # Estos estilos se manejarán preferentemente desde QSS global si es posible,
            # pero se mantienen aquí para estados específicos que pueden no ser cubiertos por QSS.
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

    def cleanup(self):
        logger.info("NotificationWidget: cleanup called.")
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            logger.info("NotificationWidget: Stopping update timer.")
            self.update_timer.stop()
        logger.info("NotificationWidget: cleanup finished.")

if __name__ == '__main__':
    pass
