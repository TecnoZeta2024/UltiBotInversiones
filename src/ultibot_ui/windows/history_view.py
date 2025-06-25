"""
Vista de historial que integra la visualización de resultados de Paper Trading.
"""

import logging
from typing import Optional
from uuid import UUID

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ultibot_ui.models import BaseMainWindow
from ultibot_ui.widgets.paper_trading_report_widget import PaperTradingReportWidget
from ultibot_ui.services.api_client import UltiBotAPIClient

logger = logging.getLogger(__name__)

class HistoryView(QWidget):
    """
    Vista principal para mostrar el historial de trading.
    
    Incluye tanto paper trading como trading real en pestañas separadas.
    """
    
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, parent=None):
        super().__init__(parent)
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client
        self.main_window = main_window
        
        self.setup_ui()
        logger.info("HistoryView inicializada.")
        
    def set_user_id(self, user_id: UUID):
        """Establece el user_id y activa la carga de datos."""
        self.user_id = user_id
        logger.info(f"HistoryView: User ID set to {user_id}. Loading data.")
        if hasattr(self, 'paper_trading_report_widget'):
            self.paper_trading_report_widget.set_user_id(user_id)
            self.paper_trading_report_widget.load_data() # Cargar datos una vez que el user_id esté disponible

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título principal
        title_label = QLabel("Historial de Trading")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Descripción
        description_label = QLabel(
            "Revisa el rendimiento histórico de tus operaciones de trading, "
            "incluyendo métricas detalladas y análisis de resultados."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description_label)
        
        # Pestañas para diferentes tipos de trading
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # === PESTAÑA 1: PAPER TRADING ===
        # Pasar api_client y main_window, user_id se establecerá después
        self.paper_trading_report_widget = PaperTradingReportWidget(
            api_client=self.api_client,
            main_window=self.main_window
        )
        self.paper_trading_tab = QWidget()
        paper_layout = QVBoxLayout(self.paper_trading_tab)
        paper_layout.setContentsMargins(5, 5, 5, 5)
        paper_layout.addWidget(self.paper_trading_report_widget)
        self.tab_widget.addTab(self.paper_trading_tab, "📊 Paper Trading")
        
        # === PESTAÑA 2: TRADING REAL (PLACEHOLDER POR AHORA) ===
        self.real_trading_tab = self.create_real_trading_tab()
        self.tab_widget.addTab(self.real_trading_tab, "💰 Trading Real")
        
        # Configurar pestaña inicial
        self.tab_widget.setCurrentIndex(0)  # Comenzar con Paper Trading
        
    def create_real_trading_tab(self) -> QWidget:
        """Crea la pestaña de Trading Real (placeholder por ahora)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Placeholder para futuras implementaciones
        placeholder_label = QLabel(
            "Vista de Trading Real\n\n"
            "Esta sección mostrará el historial y rendimiento "
            "de las operaciones de trading real una vez que "
            "se implementen las funcionalidades correspondientes."
        )
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #666;
                background-color: #f5f5f5;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px;
            }
        """)
        layout.addWidget(placeholder_label)
        
        return tab
        
    def refresh_data(self):
        """Refresca los datos de todas las pestañas."""
        if hasattr(self, 'paper_trading_report_widget') and self.user_id:
            self.paper_trading_report_widget.load_data()
            logger.info("Datos del historial de paper trading refrescados")
        
        # Aquí se podría agregar lógica para refrescar otros tabs cuando se implementen
        
    def cleanup(self):
        """Limpia recursos al cerrar la vista."""
        if hasattr(self, 'paper_trading_report_widget'):
            self.paper_trading_report_widget.cleanup()
        logger.info("HistoryView cleanup completado")
