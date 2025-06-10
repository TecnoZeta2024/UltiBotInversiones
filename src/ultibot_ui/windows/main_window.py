"""Módulo de ventana principal de UltiBotInversiones.

Este módulo contiene la implementación de la ventana principal de la aplicación,
proporcionando la interfaz de usuario principal con navegación lateral y vistas
intercambiables para diferentes funcionalidades del bot de trading.
"""

import asyncio
import logging
from typing import Optional, List, Callable, Coroutine
from uuid import UUID

from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QAction,
    QTextEdit,
    QVBoxLayout,
    QMenuBar,
    QWidget
)

from src.shared.data_types import UserConfiguration, AiStrategyConfiguration
from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget
from src.ultibot_ui.windows.dashboard_view import DashboardView
from src.ultibot_ui.windows.history_view import HistoryView
from src.ultibot_ui.windows.settings_view import SettingsView
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.services.ui_strategy_service import UIStrategyService
from src.ultibot_ui.views.strategies_view import StrategiesView
from src.ultibot_ui.views.opportunities_view import OpportunitiesView
from src.ultibot_ui.views.portfolio_view import PortfolioView
from src.ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow, BaseMainWindow):
    """Ventana principal de la aplicación UltiBotInversiones."""

    def __init__(
        self,
        user_id: UUID,
        api_client: UltiBotAPIClient,
        loop: asyncio.AbstractEventLoop,
        parent: Optional[QWidget] = None,
    ):
        """Inicializa la ventana principal."""
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.loop = loop
        
        self._initialization_complete = False
        self.active_threads: List[QThread] = []

        self.setWindowTitle("UltiBotInversiones")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1024, 600)

        self.debug_log_widget = QTextEdit()
        self.debug_log_widget.setReadOnly(True)
        self.debug_log_widget.setMaximumHeight(120)
        self.debug_log_widget.setStyleSheet("background-color: #222; color: #0f0; font-family: Consolas, monospace; font-size: 12px;")
        self.debug_log_widget.append("[INFO] UI inicializada. Esperando eventos...")

        self.banner_label = QLabel("🟢 UltiBotInversiones UI cargada correctamente")
        self.banner_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FF8C; padding: 8px; background: #1E1E1E; border-radius: 6px;")

        self.setMenuBar(self._create_menu_bar())
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        status_bar.showMessage("Listo")

        self._main_vbox = QVBoxLayout()
        self._main_vbox.setContentsMargins(0, 0, 0, 0)
        self._main_vbox.setSpacing(0)
        
        self._central_content_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        self._setup_central_widget(parent_widget=self._central_content_widget)
        main_layout.addWidget(self._central_content_widget)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self._log_debug("MainWindow inicializada y visible.")
        
        current_statusbar = self.statusBar()
        if current_statusbar:
            current_statusbar.showMessage("Ventana principal desplegada correctamente.")

    def add_thread(self, thread: QThread):
        """Añade un hilo a la lista de hilos activos para su seguimiento."""
        self.active_threads.append(thread)
        thread.finished.connect(lambda: self.remove_thread(thread))

    def remove_thread(self, thread: QThread):
        """Elimina un hilo de la lista de hilos activos."""
        if thread in self.active_threads:
            self.active_threads.remove(thread)

    def _create_menu_bar(self) -> QMenuBar:
        """Crea y devuelve la barra de menú principal."""
        menu_bar = QMenuBar(self)
        view_menu = menu_bar.addMenu("&View")
        if view_menu:
            theme_menu = view_menu.addMenu("Switch &Theme")
            if theme_menu:
                dark_theme_action = QAction("Dark Theme", self)
                dark_theme_action.triggered.connect(lambda: self._apply_theme_selection("dark"))
                theme_menu.addAction(dark_theme_action)
                
                light_theme_action = QAction("Light Theme", self)
                light_theme_action.triggered.connect(lambda: self._apply_theme_selection("light"))
                theme_menu.addAction(light_theme_action)
        
        return menu_bar

    def _apply_theme_selection(self, theme_name: str):
        """Aplica el tema seleccionado."""
        logger.info(f"MainWindow: User selected {theme_name} theme.")

    def _log_debug(self, msg: str):
        """Agrega un mensaje al panel de logs y al logger."""
        logger.info(msg)

    def _setup_central_widget(self, parent_widget: QWidget):
        """Configura el widget central con navegación y vistas."""
        main_layout = QHBoxLayout(parent_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = SidebarNavigationWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.navigation_requested.connect(self._switch_view)
        main_layout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.dashboard_view = DashboardView(
            user_id=self.user_id,
            main_window=self,
            api_client=self.api_client,
            loop=self.loop
        )
        self.stacked_widget.addWidget(self.dashboard_view)

        self.opportunities_view = OpportunitiesView(
            user_id=self.user_id, 
            main_window=self,
            api_client=self.api_client,
            loop=self.loop
        )
        self.stacked_widget.addWidget(self.opportunities_view)

        self.strategies_view = StrategiesView(
            api_client=self.api_client,
            parent=self
        )
        self.stacked_widget.addWidget(self.strategies_view)

        self.portfolio_view = PortfolioView(
            user_id=self.user_id,
            api_client=self.api_client,
            loop=self.loop
        )
        self.stacked_widget.addWidget(self.portfolio_view)

        self.history_view = HistoryView(
            user_id=self.user_id, 
            main_window=self,
            api_client=self.api_client,
            loop=self.loop
        )
        self.stacked_widget.addWidget(self.history_view)

        self.settings_view = SettingsView(
            user_id=str(self.user_id),
            api_client=self.api_client,
            loop=self.loop
        )
        self.stacked_widget.addWidget(self.settings_view)

        self.view_map = {
            "dashboard": 0, "opportunities": 1, "strategies": 2,
            "portfolio": 3, "history": 4, "settings": 5,
        }

        self.strategy_service = UIStrategyService(
            api_client=self.api_client,
            main_window=self,
            loop=self.loop
        )
        self.strategy_service.strategies_updated.connect(self.strategies_view.update_strategies)
        self.strategy_service.error_occurred.connect(lambda msg: self._log_debug(f"[STRATEGY_SVC_ERR] {msg}"))
        
        self._fetch_strategies()

        dashboard_button = self.sidebar.findChild(QPushButton, "navButton_dashboard")
        if dashboard_button:
            dashboard_button.setChecked(True)
        self.stacked_widget.setCurrentIndex(self.view_map["dashboard"])
        self._log_debug("Central widget y vistas configuradas.")

    def _fetch_strategies(self):
        """
        Initiates fetching strategies using the UIStrategyService.
        """
        self.strategy_service.fetch_strategies()
        self._log_debug("MainWindow: Initiated strategy fetch via UIStrategyService.")

    def _switch_view(self, view_name: str):
        """Cambia a la vista especificada."""
        index = self.view_map.get(view_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)
            if view_name == "strategies":
                self._fetch_strategies()

    def cleanup(self):
        """Limpia los recursos de la ventana."""
        self._log_debug(f"Cleaning up MainWindow resources. Stopping {len(self.active_threads)} active threads...")
        
        for view_widget in [self.dashboard_view, self.history_view, self.opportunities_view, self.portfolio_view, self.settings_view]:
            if hasattr(view_widget, "cleanup"):
                view_widget.cleanup()
        
        for thread in self.active_threads[:]:
            try:
                if thread.isRunning():
                    thread.quit()
                    thread.wait(1000) 
            except RuntimeError:
                logger.warning(f"Thread {thread} was already deleted.")
        
        self.active_threads.clear()
        self._log_debug("MainWindow cleanup finished.")

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.cleanup()
        super().closeEvent(event)
