import logging
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QBarSeries, QBarSet
from PySide6.QtGui import QPainter

from ultibot_ui.workers import PerformanceWorker
from ultibot_ui.services.api_client import UltiBotAPIClient

logger = logging.getLogger(__name__)

import logging
import logging
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QBarSeries, QBarSet
from PySide6.QtGui import QPainter
from typing import Optional
from uuid import UUID

from ultibot_ui.workers import PerformanceWorker
from ultibot_ui.services.api_client import UltiBotAPIClient
from ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow

logger = logging.getLogger(__name__)

class PerformanceView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Global Performance")
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client
        self.main_window = main_window # Guardar referencia a MainWindow
        self.worker_thread: Optional[QThread] = None
        self.worker: Optional[PerformanceWorker] = None
        
        self._layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Global Portfolio Performance")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self.title_label)
        
        charts_layout = QHBoxLayout()
        
        self.portfolio_chart_view = QChartView()
        self.portfolio_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        charts_layout.addWidget(self.portfolio_chart_view)
        
        self.pnl_chart_view = QChartView()
        self.pnl_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        charts_layout.addWidget(self.pnl_chart_view)
        
        self._layout.addLayout(charts_layout)
        
        self.metrics_layout = self._setup_metrics({})
        self._layout.addLayout(self.metrics_layout)
        
        self.setLayout(self._layout)
        
        # Initialize with empty data
        self._setup_portfolio_chart([])
        self._setup_pnl_chart([])
        
        # No llamar a load_performance_data aquí, se llamará después de set_user_id
        
        logger.info("PerformanceView initialized.")

    def set_user_id(self, user_id: UUID):
        """Establece el user_id y activa la carga de datos de rendimiento."""
        self.user_id = user_id
        logger.info(f"PerformanceView: User ID set to {user_id}. Loading performance data.")
        self.load_performance_data()

    def _setup_metrics(self, metrics: dict):
        """Creates and returns a layout with key performance metrics."""
        # Clear previous metrics if any
        if hasattr(self, 'metrics_layout'):
            while self.metrics_layout.count():
                child = self.metrics_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        metrics_layout = QHBoxLayout()
        
        sharpe_ratio = metrics.get("sharpe_ratio", "N/A")
        max_drawdown = metrics.get("max_drawdown", "N/A")
        win_rate = metrics.get("win_rate", "N/A")
        
        metrics_layout.addWidget(self._create_metric_widget("Sharpe Ratio", sharpe_ratio))
        metrics_layout.addWidget(self._create_metric_widget("Max Drawdown", max_drawdown))
        metrics_layout.addWidget(self._create_metric_widget("Win Rate", win_rate))
        
        return metrics_layout

    def _create_metric_widget(self, name: str, value: str) -> QWidget:
        """Helper to create a consistent widget for a single metric."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 12px; color: gray;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        layout.addWidget(name_label)
        layout.addWidget(value_label)
        
        widget.setLayout(layout)
        return widget

    def _setup_portfolio_chart(self, data_points: list):
        """Sets up the portfolio evolution chart."""
        series = QLineSeries()
        series.setName("Portfolio Value")
        
        for point in data_points:
            series.append(point[0], point[1])
            
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Portfolio Value Over Time")
        chart.createDefaultAxes()
        chart.legend().setVisible(True)
        
        self.portfolio_chart_view.setChart(chart)

    def _setup_pnl_chart(self, pnl_data: list):
        """Sets up the P&L by period chart."""
        bar_set = QBarSet("P&L")
        bar_set.append(pnl_data)

        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("P&L by Period")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        chart.createDefaultAxes()
        chart.legend().setVisible(False)

        self.pnl_chart_view.setChart(chart)

    def load_performance_data(self):
        """Initializes and runs the worker to load performance data."""
        if self.user_id is None:
            logger.warning("PerformanceView: user_id no está disponible. No se pueden cargar los datos de rendimiento.")
            QMessageBox.warning(self, "Error", "Configuración de usuario no cargada. No se pueden mostrar los datos de rendimiento.")
            return

        logger.info("Starting PerformanceWorker...")
        self.worker_thread = QThread()
        self.worker = PerformanceWorker(self.api_client, self.user_id) # Pasar user_id
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.performance_data_ready.connect(self.update_performance_data)
        self.worker.error_occurred.connect(self.on_worker_error)
        
        # Conectar la señal finished del worker para que el hilo se cierre
        self.worker.finished.connect(self.worker_thread.quit)
        
        # Conectar la señal finished del hilo para limpiar el worker y el hilo
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        # Añadir el hilo a la ventana principal para su seguimiento
        self.main_window.add_thread(self.worker_thread)
        
        self.worker_thread.start()

    def update_performance_data(self, data: dict):
        """Slot to update the UI with data from the worker."""
        logger.info("Updating performance data in the UI.")
        self._setup_portfolio_chart(data.get("portfolio_evolution", []))
        self._setup_pnl_chart(data.get("pnl_by_period", []))
        
        # Re-create metrics layout with new data
        self.metrics_layout = self._setup_metrics(data.get("metrics", {}))
        self._layout.addLayout(self.metrics_layout)

    def on_worker_error(self, error_message: str):
        """Handles errors reported by the worker."""
        logger.error(f"An error occurred in PerformanceWorker: {error_message}")
        QMessageBox.critical(self, "Error", f"Failed to load performance data:\n{error_message}")

    def cleanup(self):
        """Detiene el worker de rendimiento y limpia los recursos."""
        logger.info("PerformanceView: Iniciando limpieza de tareas.")
        if self.worker_thread and self.worker_thread.isRunning():
            logger.info("PerformanceView: Solicitando detención del worker de rendimiento.")
            self.worker_thread.quit()
            if not self.worker_thread.wait(5000): # Esperar hasta 5 segundos
                logger.warning("PerformanceView: El hilo del worker de rendimiento no terminó correctamente.")
        
        # Limpiar los gráficos
        if self.portfolio_chart_view.chart():
            self.portfolio_chart_view.chart().deleteLater()
        if self.pnl_chart_view.chart():
            self.pnl_chart_view.chart().deleteLater()
        
        # Limpiar el layout de métricas
        if hasattr(self, 'metrics_layout'):
            while self.metrics_layout.count():
                item = self.metrics_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            # No eliminar el layout en sí, ya que es parte del layout principal de la vista
        
        logger.info("PerformanceView: Limpieza completada.")
