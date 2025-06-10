from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen
import mplfinance as mpf
import pandas as pd
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
import httpx
import qasync

from src.ultibot_ui.models import BaseMainWindow
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
    candlestick_data_fetched = pyqtSignal(object)
    api_error_occurred = pyqtSignal(str)
    
    def __init__(self, main_window: BaseMainWindow, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.main_window = main_window
        self.api_client = api_client
        self.loop = loop
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
        self.interval_combo.addItems(["1m", "5m", "15m", "1h", "4h", "1d"])
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
        self.chart_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Asegurar que el QLabel inicial se expanda

        self.setLayout(self.main_layout)
        # Se elimina el estilo local para que el estilo global de style.qss se aplique
        # self.setStyleSheet("background-color: #1e1e1e; color: #cccccc;")

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

    def _on_data_loaded_success(self, data: object):
        """Callback para cuando los datos del gráfico se cargan con éxito."""
        self.candlestick_data_fetched.emit(data)

    def _on_data_loaded_error(self, error_message: str):
        """Callback para cuando ocurre un error al cargar los datos del gráfico."""
        self.api_error_occurred.emit(error_message)

    @qasync.asyncSlot(object)
    async def set_candlestick_data(self, data: object):
        if not isinstance(data, list):
            await self._handle_api_error(f"Invalid data format: Expected list, got {type(data).__name__}")
            return
        
        try:
            self.candlestick_data = [Kline(**item) for item in data]
        except (TypeError, ValueError) as e:
            await self._handle_api_error(f"Data parsing error: {e}")
            return
            
        await self.update_chart_display()

    @qasync.asyncSlot(str)
    async def _handle_api_error(self, message: str):
        logger.error(f"Error de API en ChartWidget: {message}")
        self.candlestick_data = []
        if isinstance(self.chart_area, QLabel):
            self.chart_area.setText(f"Error API: {message}")
        else:
            logger.warning("Chart area is not a QLabel, cannot display error text directly.")

    def load_chart_data(self):
        if self.current_symbol and self.current_interval:
            if isinstance(self.chart_area, QLabel):
                self.chart_area.setText(f"Cargando datos para {self.current_symbol} ({self.current_interval})...")
            
            logger.info(f"Solicitando datos para {self.current_symbol} - {self.current_interval} usando TaskManager")
            
            coroutine_factory = lambda client: client.get_ohlcv_data(
                symbol=self.current_symbol,
                timeframe=self.current_interval,
                limit=100
            )
            
            self.main_window.submit_task(
                coroutine_factory, 
                self._on_data_loaded_success, 
                self._on_data_loaded_error
            )
        else:
            if isinstance(self.chart_area, QLabel):
                self.chart_area.setText("Seleccione un par y una temporalidad para ver el gráfico.")

    async def update_chart_display(self):
        if not self.candlestick_data:
            if isinstance(self.chart_area, QLabel):
                self.chart_area.setText("No hay datos disponibles para mostrar el gráfico.")
            return

        try:
            df = pd.DataFrame([k.model_dump() for k in self.candlestick_data])

            if df.empty or 'open_time' not in df.columns:
                logger.error("La columna 'open_time' no se encuentra en los datos del gráfico o el dataframe está vacío.")
                if isinstance(self.chart_area, QLabel):
                    self.chart_area.setText("Error: Faltan datos clave para el gráfico (open_time).")
                return

            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df = df.set_index('open_time')
            df.index.name = 'Date'
            
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.dropna(subset=numeric_cols, inplace=True)

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
            s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc,
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
                                   figscale=1.2,
                                   title=f"\n{self.current_symbol} - {self.current_interval}",
                                   ylabel='Price (USD)',
                                   xrotation=0,
                                   datetime_format='%H:%M'
                                  )
            fig.set_facecolor('#1e1e1e')
            axlist[0].set_ylabel('Price (USD)', color='#cccccc')
            axlist[2].set_ylabel('Volume', color='#cccccc')
            
            canvas = FigureCanvas(fig)
            canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # Asegurar que el canvas se expanda
            
            old_widget = self.main_layout.itemAt(1).widget()
            if old_widget:
                self.main_layout.removeWidget(old_widget)
                old_widget.setParent(None)
                old_widget.deleteLater()
            
            self.main_layout.addWidget(canvas)
            self.chart_area = canvas

        except Exception as e:
            logger.critical(f"Error al renderizar el gráfico: {e}", exc_info=True)
            if not isinstance(self.chart_area, QLabel):
                old_widget = self.main_layout.itemAt(1).widget()
                if old_widget:
                    self.main_layout.removeWidget(old_widget)
                    old_widget.setParent(None)
                    old_widget.deleteLater()
                self.chart_area = QLabel()
                self.chart_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_layout.addWidget(self.chart_area)
            self.chart_area.setText(f"Error al renderizar el gráfico: {e}")

    def cleanup(self):
        logger.info("ChartWidget: Limpieza completada.")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow
    import sys
    import logging
    import qasync

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    
    class MockMainWindow(QMainWindow, BaseMainWindow):
        def __init__(self):
            super().__init__()
            self._threads = []

        def submit_task(self, coro, on_success, on_error):
            # Mock implementation for testing
            logger.info("MockMainWindow: Tarea enviada.")
            async def task_wrapper():
                try:
                    result = await coro
                    future = asyncio.Future()
                    future.set_result(result)
                    on_success(future)
                except Exception as e:
                    future = asyncio.Future()
                    future.set_exception(e)
                    on_error(future)
            asyncio.create_task(task_wrapper())

    class MockAPIClient(UltiBotAPIClient):
        async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
            logger.info(f"MockAPIClient: Obteniendo datos de velas para {symbol}-{timeframe}")
            import random
            import time
            
            price = 20000 + random.uniform(-500, 500)
            now = int(time.time() * 1000)
            data = []
            for i in range(limit):
                open_price = price
                high = open_price * (1 + random.uniform(0, 0.01))
                low = open_price * (1 - random.uniform(0, 0.01))
                close_price = low + (high - low) * random.uniform(0, 1)
                volume = random.uniform(100, 2000)
                open_time = now - (limit - i) * 60000
                
                data.append({
                    "open_time": open_time,
                    "open": f"{open_price:.2f}",
                    "high": f"{high:.2f}",
                    "low": f"{low:.2f}",
                    "close": f"{close_price:.2f}",
                    "volume": f"{volume:.2f}",
                    "close_time": open_time + 59999,
                    "quote_asset_volume": f"{volume * price:.2f}",
                    "number_of_trades": random.randint(50, 200),
                    "taker_buy_base_asset_volume": f"{volume * 0.5:.2f}",
                    "taker_buy_quote_asset_volume": f"{volume * 0.5 * price:.2f}",
                })
                price = close_price
            return data

    async def main():
        loop = asyncio.get_running_loop()
        
        mock_main_window = MockMainWindow()
        mock_main_window.setWindowTitle("Chart Widget Test")
        mock_main_window.setGeometry(100, 100, 900, 700)

        mock_http_client = httpx.AsyncClient()
        mock_api_client = MockAPIClient(client=mock_http_client)
        
        chart_widget = ChartWidget(
            main_window=mock_main_window,
            api_client=mock_api_client,
            loop=loop
        )
        mock_main_window.setCentralWidget(chart_widget)
        mock_main_window.show()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    qasync.run(main())
