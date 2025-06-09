from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QPainter, QColor, QPen
import mplfinance as mpf
import pandas as pd
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio

from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.workers import ApiWorker
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.shared.data_types import Kline
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging

logger = logging.getLogger(__name__)

class ChartWidget(QWidget):
    """
    Widget para la visualización de gráficos financieros utilizando mplfinance.
    """
    symbol_selected = pyqtSignal(str)
    interval_selected = pyqtSignal(str)
    candlestick_data_fetched = pyqtSignal(list)
    api_error_occurred = pyqtSignal(str)
    
    def __init__(self, main_window: BaseMainWindow, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_window = main_window
        self.current_symbol: Optional[str] = None
        self.current_interval: Optional[str] = "1h"
        self.candlestick_data: List[Kline] = []

        self.init_ui()
        self.candlestick_data_fetched.connect(self.set_candlestick_data)
        self.api_error_occurred.connect(self._handle_api_error)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        self.controls_layout = QHBoxLayout()
        
        self.symbol_label = QLabel("Par:")
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "BNBUSDT"]) 
        self.symbol_combo.currentIndexChanged.connect(self._on_symbol_changed)
        
        self.interval_label = QLabel("Temporalidad:")
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1m", "5m", "15m", "1H", "4H", "1D"])
        self.interval_combo.setCurrentText(self.current_interval)
        self.interval_combo.currentIndexChanged.connect(self._on_interval_changed)

        self.controls_layout.addWidget(self.symbol_label)
        self.controls_layout.addWidget(self.symbol_combo)
        self.controls_layout.addWidget(self.interval_label)
        self.controls_layout.addWidget(self.interval_combo)
        self.controls_layout.addStretch(1)

        self.main_layout.addLayout(self.controls_layout)

        self.chart_area = QLabel("Cargando gráfico...")
        self.chart_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.chart_area)

        self.setLayout(self.main_layout)
        self.setStyleSheet("background-color: #1e1e1e; color: #cccccc;")

        self.current_symbol = self.symbol_combo.currentText()
        self.load_chart_data()

    def _on_symbol_changed(self, index: int):
        self.current_symbol = self.symbol_combo.currentText()
        self.symbol_selected.emit(self.current_symbol)
        self.load_chart_data()

    def _on_interval_changed(self, index: int):
        self.current_interval = self.interval_combo.currentText()
        self.interval_selected.emit(self.current_interval)
        self.load_chart_data()

    def set_candlestick_data(self, data: List[Kline]):
        self.candlestick_data = data
        self.update_chart_display()

    def _handle_api_error(self, message: str):
        logger.error(f"Error de API en ChartWidget: {message}")
        self.set_candlestick_data([])
        if isinstance(self.chart_area, QLabel):
            self.chart_area.setText(f"Error API: {message}")

    def load_chart_data(self):
        if self.current_symbol and self.current_interval:
            self.chart_area.setText(f"Cargando datos para {self.current_symbol} ({self.current_interval})...")
            logger.info(f"Solicitando datos para {self.current_symbol} - {self.current_interval} usando ApiWorker")
            
            current_symbol = self.current_symbol
            current_interval = self.current_interval

            if current_symbol is None or current_interval is None:
                logger.error("ChartWidget: Símbolo o intervalo no definidos al intentar cargar datos del gráfico.")
                self.chart_area.setText("Error: Símbolo o intervalo no definidos.")
                return

            worker = ApiWorker(
                coroutine_factory=lambda api_client: api_client.get_candlestick_data(
                    symbol=current_symbol,
                    interval=current_interval,
                    limit=200
                )
            )
            thread = QThread()
            self.main_window.add_thread(thread)

            worker.moveToThread(thread)

            worker.result_ready.connect(self.candlestick_data_fetched.emit)
            worker.error_occurred.connect(lambda e: self.api_error_occurred.emit(str(e)))
            
            worker.result_ready.connect(thread.quit)
            worker.error_occurred.connect(thread.quit)
            thread.finished.connect(worker.deleteLater)

            thread.started.connect(worker.run)
            thread.start()
        else:
            self.chart_area.setText("Seleccione un par y una temporalidad para ver el gráfico.")

    def update_chart_display(self):
        if not self.candlestick_data:
            self.chart_area.setText("No hay datos disponibles para mostrar el gráfico.")
            return

        try:
            # Convertir lista de objetos Kline a lista de diccionarios
            data_for_df = [kline.model_dump() for kline in self.candlestick_data]
            df = pd.DataFrame(data_for_df)

            if 'open_time' not in df.columns:
                logger.error("La columna 'open_time' no se encuentra en los datos del gráfico después de la conversión.")
                self.chart_area.setText("Error: Faltan datos clave para el gráfico (open_time).")
                return

            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df = df.set_index('open_time')
            df.index.name = 'Date'

            df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)

            mc = mpf.make_marketcolors(up='#00ff00', down='#ff0000',
                                       edge='inherit', wick='inherit',
                                       volume='#1f77b4',
                                       ohlc='i')
            s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc,
                                   figcolor='#1e1e1e',
                                   facecolor='#1e1e1e',
                                   gridcolor='#333333',
                                   rc={'axes.edgecolor': '#333333',
                                       'axes.labelcolor': '#cccccc',
                                       'xtick.color': '#cccccc',
                                       'ytick.color': '#cccccc'})

            fig, axlist = mpf.plot(df,
                                   type='candle',
                                   volume=True,
                                   style=s,
                                   returnfig=True,
                                   figscale=1.5,
                                   addplot=[mpf.make_addplot(df['Volume'], panel=1, type='bar', ylabel='Volume')],
                                   title=f"{self.current_symbol} - {self.current_interval}",
                                   ylabel='Price',
                                   ylabel_lower='Volume',
                                   xrotation=0
                                  )
            
            canvas = FigureCanvas(fig)
            
            for i in reversed(range(self.main_layout.count())):
                item = self.main_layout.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    if widget and widget != self.chart_area and widget not in self.controls_layout.findChildren(QWidget):
                        self.main_layout.removeWidget(widget)
                        widget.setParent(None)
                        widget.deleteLater()
            
            if isinstance(self.chart_area, QLabel) and self.main_layout.indexOf(self.chart_area) != -1:
                self.main_layout.removeWidget(self.chart_area)
                self.chart_area.setParent(None)
                self.chart_area.deleteLater()
            
            self.main_layout.addWidget(canvas)
            self.chart_area = canvas

            canvas.setSizePolicy(self.chart_area.sizePolicy())
            canvas.updateGeometry()

        except Exception as e:
            self.chart_area.show()
            self.chart_area.setText(f"Error al renderizar el gráfico: {e}")
            logger.critical(f"Error al renderizar el gráfico: {e}", exc_info=True)


    def cleanup(self):
        logger.info("ChartWidget: Limpieza completada.")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow
    import sys
    import logging
    from src.ultibot_ui.workers import ApiWorker
    import qasync

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    
    class MockMainWindow(BaseMainWindow):
        def add_thread(self, thread: QThread):
            logger.info(f"MockMainWindow: Thread '{thread.objectName()}' added for tracking.")

    mock_main_window = MockMainWindow()
    main_window_widget = QMainWindow()
    main_window_widget.setWindowTitle("Chart Widget Test")
    main_window_widget.setGeometry(100, 100, 800, 600)

    class MockAPIClient(UltiBotAPIClient):
        def __init__(self, base_url: str, token: Optional[str] = None):
            super().__init__(base_url, token)

        async def get_candlestick_data(self, symbol: str, interval: str, limit: int = 200) -> List[Kline]:
            logger.info(f"MockAPIClient: Obteniendo datos de velas para {symbol}-{interval}")
            sample_data = [
                {"open_time": 1678886400000, "open": 20000.0, "high": 20100.0, "low": 19900.0, "close": 20050.0, "volume": 1000.0, "close_time": 1678886459999, "quote_asset_volume": "20050000", "number_of_trades": 100, "taker_buy_base_asset_volume": "500", "taker_buy_quote_asset_volume": "10025000"},
                {"open_time": 1678890000000, "open": 20050.0, "high": 20200.0, "low": 20000.0, "close": 20150.0, "volume": 1200.0, "close_time": 1678890059999, "quote_asset_volume": "24180000", "number_of_trades": 120, "taker_buy_base_asset_volume": "600", "taker_buy_quote_asset_volume": "12090000"},
                {"open_time": 1678893600000, "open": 20150.0, "high": 20300.0, "low": 20100.0, "close": 20250.0, "volume": 1100.0, "close_time": 1678893659999, "quote_asset_volume": "22275000", "number_of_trades": 110, "taker_buy_base_asset_volume": "550", "taker_buy_quote_asset_volume": "11137500"},
                {"open_time": 1678897200000, "open": 20250.0, "high": 20400.0, "low": 20200.0, "close": 20350.0, "volume": 1300.0, "close_time": 1678897259999, "quote_asset_volume": "26455000", "number_of_trades": 130, "taker_buy_base_asset_volume": "650", "taker_buy_quote_asset_volume": "13227500"},
                {"open_time": 1678900800000, "open": 20350.0, "high": 20500.0, "low": 20300.0, "close": 20450.0, "volume": 1400.0, "close_time": 1678900859999, "quote_asset_volume": "28630000", "number_of_trades": 140, "taker_buy_base_asset_volume": "700", "taker_buy_quote_asset_volume": "14315000"},
            ]
            return [Kline(**d) for d in sample_data]

    # mock_api_client = MockAPIClient(base_url="http://mock-api") # Eliminado
    chart_widget = ChartWidget(main_window=mock_main_window)
    main_window_widget.setCentralWidget(chart_widget)
    main_window_widget.show()

    event_loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    with event_loop:
        sys.exit(app.exec_())
