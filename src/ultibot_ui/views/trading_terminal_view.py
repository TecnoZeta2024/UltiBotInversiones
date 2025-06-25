import logging
from collections import deque
from PySide6.QtCore import QThread, Slot, QPointF
from PySide6 import QtCore
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGroupBox,
                               QFormLayout, QComboBox, QLineEdit,
                               QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtGui import QPainter

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.workers import TradingTerminalWorker, ApiWorker
from ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow

logger = logging.getLogger(__name__)

class TradingTerminalView(QWidget):
    """
    Vista para la ejecución de órdenes manuales y visualización de datos de mercado.
    """
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terminal de Trading")
        
        self.api_client = api_client
        self.main_window = main_window
        self._layout = QVBoxLayout(self)
        
        self.price_worker = None
        self.price_data = deque(maxlen=60)
        app_instance = QtCore.QCoreApplication.instance()
        self.main_event_loop = None
        if app_instance:
            self.main_event_loop = app_instance.property("asyncio_event_loop")
        
        if not self.main_event_loop:
            logger.error("TradingTerminalView: No se encontró el bucle de eventos de asyncio principal. La funcionalidad de feed de precios puede no funcionar correctamente.")
            # Aquí podrías deshabilitar la funcionalidad de feed de precios o mostrar un mensaje al usuario.
            # Por ahora, el worker manejará la ausencia del bucle.

        self.title_label = QLabel("Terminal de Trading")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self.title_label)
        
        self._setup_trading_controls()
        
        self._setup_price_chart()
        
        self._layout.addStretch()
        
        self.setLayout(self._layout)
        
        self.symbol_combo.currentTextChanged.connect(self.initialize_view_data)
        
        logger.info("TradingTerminalView initialized.")

    def initialize_view_data(self):
        """
        Initializes and runs the worker to load price feed data asynchronously
        on a dedicated QThread. This method is called after MainWindow is fully
        initialized and visible.
        """
        logger.info("TradingTerminalView: Initializing view data (starting price feed)...")
        self.start_price_feed(self.symbol_combo.currentText())

    def _setup_trading_controls(self):
        """Configura los widgets para la entrada de órdenes."""
        controls_group = QGroupBox("Panel de Órdenes")
        group_layout = QVBoxLayout(controls_group)
        
        form_layout = QFormLayout()
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["BTC/USDT", "ETH/USDT", "SOL/USDT"])
        form_layout.addRow("Símbolo:", self.symbol_combo)
        
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["Market", "Limit"])
        form_layout.addRow("Tipo de Orden:", self.order_type_combo)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Ej: 0.01")
        form_layout.addRow("Cantidad:", self.amount_input)
        
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Ej: 50000.0")
        self.price_label = QLabel("Precio:")
        form_layout.addRow(self.price_label, self.price_input)
        
        self.order_type_combo.currentTextChanged.connect(self._toggle_price_input)
        self._toggle_price_input(self.order_type_combo.currentText())

        group_layout.addLayout(form_layout)
        
        buttons_layout = QHBoxLayout()
        self.buy_button = QPushButton("Comprar")
        self.buy_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.buy_button.clicked.connect(lambda: self._prepare_order('buy'))
        self.sell_button = QPushButton("Vender")
        self.sell_button.setStyleSheet("background-color: #F44336; color: white;")
        self.sell_button.clicked.connect(lambda: self._prepare_order('sell'))
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.buy_button)
        buttons_layout.addWidget(self.sell_button)
        
        group_layout.addLayout(buttons_layout)
        
        self._layout.addWidget(controls_group)

    def _toggle_price_input(self, order_type: str):
        """Muestra u oculta el campo de precio si la orden no es de mercado."""
        is_visible = order_type == "Limit"
        self.price_label.setVisible(is_visible)
        self.price_input.setVisible(is_visible)

    def _setup_price_chart(self):
        """Configura el gráfico para la visualización de precios en tiempo real."""
        chart_group = QGroupBox("Precio del Activo")
        chart_layout = QVBoxLayout(chart_group)

        self.chart = QChart()
        self.chart.setTitle("Evolución del Precio (Tiempo Real)")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        self.price_series = QLineSeries()
        self.price_series.setName("Precio")
        self.chart.addSeries(self.price_series)

        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()
        self.chart.setAxisX(self.axis_x, self.price_series)
        self.chart.setAxisY(self.axis_y, self.price_series)
        self.axis_x.setLabelFormat("%i")
        self.axis_y.setLabelFormat("%.2f")

        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        chart_layout.addWidget(chart_view)
        self._layout.addWidget(chart_group)

        logger.info("Price chart initialized for TradingTerminalView.")

    def start_price_feed(self, symbol: str):
        """Inicia el worker para obtener datos de precios para el símbolo dado."""
        if self.price_worker:
            self.price_worker.stop()
            self.price_worker.deleteLater()
            self.price_worker = None

        self.price_data.clear()
        self.price_series.clear()
        self.chart.setTitle(f"Evolución de {symbol} (Tiempo Real)")

        if not self.main_event_loop:
            QMessageBox.critical(self, "Error de Inicialización", "El bucle de eventos principal no está disponible. El feed de precios no se iniciará.")
            logger.error("TradingTerminalView: No se puede iniciar el feed de precios porque el bucle de eventos principal no está disponible.")
            return

        self.price_worker = TradingTerminalWorker(self.api_client, symbol, self.main_event_loop)
        self.price_worker.price_updated.connect(self._update_price_chart)
        self.price_worker.finished.connect(self.price_worker.deleteLater)
        
        thread = QThread()
        thread.setObjectName(f"PriceFeedWorkerThread_{symbol}")
        self.price_worker.moveToThread(thread)
        thread.started.connect(self.price_worker.run)
        thread.finished.connect(thread.deleteLater)
        
        self.main_window.add_thread(thread)
        thread.start()
        logger.info(f"Price feed worker started for {symbol}.")

    @Slot(dict)
    def _update_price_chart(self, data: dict):
        """Actualiza la serie del gráfico con nuevos datos de precios."""
        timestamp = data['timestamp']
        price = data['price']
        
        self.price_data.append((timestamp, price))
        
        new_points = [QPointF(i, p[1]) for i, p in enumerate(self.price_data)]
        self.price_series.replace(new_points)

        if self.price_data:
            prices = [p[1] for p in self.price_data]
            min_y = min(prices)
            max_y = max(prices)
            
            x_range_max = self.price_data.maxlen if self.price_data.maxlen is not None else 60
            self.axis_x.setRange(0, x_range_max)
            self.axis_y.setRange(min_y * 0.99, max_y * 1.01)

    def _prepare_order(self, side: str):
        """Prepara y envía una orden de trading a través de la API."""
        symbol = self.symbol_combo.currentText()
        order_type = self.order_type_combo.currentText().lower()
        amount_str = self.amount_input.text()
        price_str = self.price_input.text()

        if not amount_str:
            QMessageBox.warning(self, "Entrada Inválida", "La cantidad no puede estar vacía.")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            QMessageBox.warning(self, "Entrada Inválida", "La cantidad debe ser un número.")
            return

        price = None
        if order_type == 'limit':
            if not price_str:
                QMessageBox.warning(self, "Entrada Inválida", "El precio no puede estar vacío para órdenes límite.")
                return
            try:
                price = float(price_str)
            except ValueError:
                QMessageBox.warning(self, "Entrada Inválida", "El precio debe ser un número.")
                return
        
        logger.info(f"Preparando orden: {side.upper()} {amount} {symbol} @ {price if price else 'Market'}")

        def coroutine_factory(api_client: UltiBotAPIClient):
            return api_client.create_order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                amount=amount,
                price=price
            )

        order_worker = ApiWorker(api_client=self.api_client, coroutine_factory=coroutine_factory)
        order_thread = QThread()
        order_thread.setObjectName(f"OrderWorkerThread_{symbol}_{side}")
        order_worker.moveToThread(order_thread)

        order_worker.result_ready.connect(self._on_order_success)
        order_worker.error_occurred.connect(self._on_order_error)
        
        order_thread.started.connect(order_worker.run)
        
        order_worker.result_ready.connect(order_worker.deleteLater)
        order_worker.error_occurred.connect(order_worker.deleteLater)
        order_worker.finished.connect(order_thread.quit)
        order_thread.finished.connect(order_thread.deleteLater)
        
        self.main_window.add_thread(order_thread)
        order_thread.start()

    @Slot(object)
    def _on_order_success(self, result: dict):
        """Maneja la respuesta exitosa de la creación de una orden."""
        logger.info(f"Orden creada exitosamente: {result}")
        QMessageBox.information(self, "Orden Enviada", f"La orden ha sido enviada con éxito.\nID de Orden: {result.get('id')}")
        self.amount_input.clear()
        self.price_input.clear()

    @Slot(str)
    def _on_order_error(self, error_message: str):
        """Maneja los errores durante la creación de una orden."""
        logger.error(f"Error al crear la orden: {error_message}")
        QMessageBox.critical(self, "Error de Orden", f"No se pudo enviar la orden:\n{error_message}")

    def cleanup(self):
        """Limpia los recursos de la vista. Los hilos son gestionados por MainWindow."""
        logger.info("TradingTerminalView: Cleanup initiated. Threads are managed by MainWindow.")
        if self.price_worker:
            self.price_worker = None
        logger.info("TradingTerminalView: Cleanup finished.")
