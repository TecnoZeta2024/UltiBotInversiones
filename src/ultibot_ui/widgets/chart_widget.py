from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QPainter, QColor, QPen
import mplfinance as mpf
import pandas as pd
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio

from src.ultibot_ui.workers import ApiWorker
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
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
    
    def __init__(self, backend_base_url: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.backend_base_url = backend_base_url
        self.current_symbol: Optional[str] = None
        self.current_interval: Optional[str] = "1h"
        self.candlestick_data: List[Dict[str, Any]] = []
        self.active_api_workers = []

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

    def set_candlestick_data(self, data: List[Dict[str, Any]]):
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
            
            import qasync

            qasync_loop = asyncio.get_event_loop()

            current_symbol = self.current_symbol
            current_interval = self.current_interval

            if current_symbol is None or current_interval is None:
                logger.error("ChartWidget: Símbolo o intervalo no definidos al intentar cargar datos del gráfico.")
                self.chart_area.setText("Error: Símbolo o intervalo no definidos.")
                return

            worker = ApiWorker(
                base_url=self.backend_base_url,
                coroutine_factory=lambda api_client: api_client.get_candlestick_data(
                    symbol=current_symbol,
                    interval=current_interval,
                    limit=200
                )
            )
            thread = QThread()
            self.active_api_workers.append((worker, thread))

            worker.moveToThread(thread)

            worker.result_ready.connect(self.candlestick_data_fetched.emit)
            worker.error_occurred.connect(lambda e: self.api_error_occurred.emit(str(e)))
            
            worker.result_ready.connect(thread.quit)
            worker.error_occurred.connect(thread.quit)
            thread.finished.connect(worker.deleteLater)
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(lambda: self.active_api_workers.remove((worker, thread)) if (worker, thread) in self.active_api_workers else None)

            thread.started.connect(worker.run)
            thread.start()
        else:
            self.chart_area.setText("Seleccione un par y una temporalidad para ver el gráfico.")

    def update_chart_display(self):
        if not self.candlestick_data:
            self.chart_area.setText("No hay datos disponibles para mostrar el gráfico.")
            return

        df = pd.DataFrame(self.candlestick_data)
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

        try:
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
            print(f"Error al renderizar el gráfico: {e}")

    def cleanup(self):
        logger.info("ChartWidget: Iniciando limpieza de ApiWorkers activos.")
        for worker, thread in list(self.active_api_workers):
            if thread.isRunning():
                logger.info(f"ChartWidget: Deteniendo ApiWorker en thread {thread.objectName()}...")
                thread.quit()
                if not thread.wait(2000):
                    logger.warning(f"ChartWidget: Thread {thread.objectName()} no terminó a tiempo. Forzando terminación.")
                    thread.terminate()
                    thread.wait()
            if (worker, thread) in self.active_api_workers:
                self.active_api_workers.remove((worker, thread))
                worker.deleteLater()
                thread.deleteLater()
        logger.info("ChartWidget: Limpieza de ApiWorkers completada.")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow
    import sys
    import logging
    from src.ultibot_ui.workers import ApiWorker
    import qasync

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Chart Widget Test")
    main_window.setGeometry(100, 100, 800, 600)

    class MockAPIClient:
        async def get_candlestick_data(self, symbol: str, interval: str, limit: int, start_time: Optional[Any]=None, end_time: Optional[Any]=None) -> List[Dict[str, Any]]:
            logger.info(f"MockAPIClient: Obteniendo datos de velas para {symbol}-{interval}")
            sample_data = [
                {"open_time": 1678886400000, "open": "20000.0", "high": "20100.0", "low": "19900.0", "close": "20050.0", "volume": "1000.0"},
                {"open_time": 1678890000000, "open": "20050.0", "high": "20200.0", "low": "20000.0", "close": "20150.0", "volume": "1200.0"},
                {"open_time": 1678893600000, "open": "20150.0", "high": "20300.0", "low": "20100.0", "close": "20250.0", "volume": "1100.0"},
                {"open_time": 1678897200000, "open": "20250.0", "high": "20400.0", "low": "20200.0", "close": "20350.0", "volume": "1300.0"},
                {"open_time": 1678900800000, "open": "20350.0", "high": "20500.0", "low": "20300.0", "close": "20450.0", "volume": "1400.0"},
            ]
            for row in sample_data:
                row["open"] = float(row["open"])
                row["high"] = float(row["high"])
                row["low"] = float(row["low"])
                row["close"] = float(row["close"])
                row["volume"] = float(row["volume"])
            return sample_data

    mock_backend_base_url = "http://localhost:8000"
    chart_widget = ChartWidget(backend_base_url=mock_backend_base_url)
    main_window.setCentralWidget(chart_widget)
    main_window.show()

    event_loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    with event_loop:
        sys.exit(app.exec_())
