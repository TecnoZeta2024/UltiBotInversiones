from PySide6 import QtWidgets, QtCore, QtGui # Importar módulos completos
import mplfinance as mpf
import pandas as pd
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
from unittest.mock import MagicMock # Importar MagicMock

from ultibot_ui.models import BaseMainWindow
from ultibot_ui.workers import ApiWorker
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from shared.data_types import Kline
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging
import httpx # Importar httpx para el mock

logger = logging.getLogger(__name__)

class ChartWidget(QtWidgets.QWidget):
    """
    Widget para la visualización de gráficos financieros utilizando mplfinance.
    """
    symbol_selected = QtCore.Signal(str)
    interval_selected = QtCore.Signal(str)
    candlestick_data_fetched = QtCore.Signal(list)
    api_error_occurred = QtCore.Signal(str)
    
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, main_event_loop: asyncio.AbstractEventLoop, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.api_client = api_client # Usar la instancia de api_client
        self.main_window = main_window
        self.main_event_loop = main_event_loop # Guardar la referencia al bucle de eventos
        self.current_symbol: Optional[str] = None
        self.current_interval: Optional[str] = "1h"
        self.candlestick_data: List[Kline] = []

        self.init_ui()
        self.candlestick_data_fetched.connect(self.set_candlestick_data)
        self.api_error_occurred.connect(self._handle_api_error)

    def init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        self.controls_layout = QtWidgets.QHBoxLayout()
        
        self.symbol_label = QtWidgets.QLabel("Par:")
        self.symbol_combo = QtWidgets.QComboBox()
        self.symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "BNBUSDT"]) 
        self.symbol_combo.currentIndexChanged.connect(self._on_symbol_changed)
        
        self.interval_label = QtWidgets.QLabel("Temporalidad:")
        self.interval_combo = QtWidgets.QComboBox()
        self.interval_combo.addItems(["1m", "5m", "15m", "1H", "4H", "1D"])
        if self.current_interval is not None: # Corrección para el error de tipo
            self.interval_combo.setCurrentText(self.current_interval)
        self.interval_combo.currentIndexChanged.connect(self._on_interval_changed)

        self.controls_layout.addWidget(self.symbol_label)
        self.controls_layout.addWidget(self.symbol_combo)
        self.controls_layout.addWidget(self.interval_label)
        self.controls_layout.addWidget(self.interval_combo)
        self.controls_layout.addStretch(1)

        self.main_layout.addLayout(self.controls_layout)

        self.chart_area = QtWidgets.QLabel("Cargando gráfico...")
        self.chart_area.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
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
        if isinstance(self.chart_area, QtWidgets.QLabel):
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

            # Obtener el bucle de eventos principal de la aplicación
            app_instance = QtWidgets.QApplication.instance()
            if not app_instance:
                logger.error("ChartWidget: No se encontró la instancia de QApplication para ApiWorker.")
                self.api_error_occurred.emit("Error interno: No se pudo obtener la instancia de la aplicación.")
                return
            
            main_event_loop = app_instance.property("main_event_loop")
            if not main_event_loop:
                logger.error("ChartWidget: No se encontró el bucle de eventos principal de qasync para ApiWorker.")
                self.api_error_occurred.emit("Error interno: Bucle de eventos principal no disponible.")
                return

        # Usar el cliente API real para obtener datos
        async def get_ohlcv_data_coro(api_client: UltiBotAPIClient):
            logger.info(f"Obteniendo datos reales para {current_symbol} - {current_interval}")
            return await api_client.get_ohlcv_data(
                symbol=current_symbol,
                timeframe=current_interval,
                limit=200
            )

        worker = ApiWorker(
            api_client=self.api_client,
            main_event_loop=self.main_event_loop, # Pasar el bucle de eventos
            coroutine_factory=get_ohlcv_data_coro
        )
        thread = QtCore.QThread()
        thread.setObjectName(f"ChartWorkerThread_{current_symbol}_{current_interval}")
        self.main_window.add_thread(thread)

        worker.moveToThread(thread)

        worker.result_ready.connect(self.candlestick_data_fetched.emit)
        worker.error_occurred.connect(lambda e: self.api_error_occurred.emit(str(e)))
        
        # Conectar la señal finished del worker para que el hilo se cierre
        worker.finished.connect(thread.quit)
        
        # Conectar la señal finished del hilo para limpiar el worker y el hilo
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        thread.started.connect(worker.run)
        thread.start()

    def update_chart_display(self):
        if not self.candlestick_data:
            self.chart_area.setText("No hay datos disponibles para mostrar el gráfico.")
            return

        try:
            # Convertir lista de objetos Kline a lista de diccionarios
            data_for_df = [kline.model_dump() for kline in self.candlestick_data]
            df = pd.DataFrame(data_for_df)

            # Convertir lista de objetos Kline a DataFrame de pandas
            # Asegurarse de que los nombres de las columnas coincidan con lo que espera mplfinance
            df = pd.DataFrame([kline.model_dump() for kline in self.candlestick_data])
            
            # Renombrar columnas para mplfinance
            df.rename(columns={
                'open_time': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)

            # Convertir 'Date' a formato de fecha y establecer como índice
            df['Date'] = pd.to_datetime(df['Date'], unit='ms')
            df.set_index('Date', inplace=True)

            # Crear estilos para el gráfico
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

            # Crear el gráfico
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
            
            # Crear un canvas de Qt para el gráfico de Matplotlib
            canvas = FigureCanvas(fig)
            
            # Limpiar el layout existente antes de añadir el nuevo gráfico
            for i in reversed(range(self.main_layout.count())):
                item = self.main_layout.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    if widget and widget != self.chart_area and widget not in self.controls_layout.findChildren(QtWidgets.QWidget):
                        self.main_layout.removeWidget(widget)
                        widget.setParent(None)
                        widget.deleteLater()
            
            # Eliminar el QLabel de "Cargando gráfico..." si existe
            if isinstance(self.chart_area, QtWidgets.QLabel) and self.main_layout.indexOf(self.chart_area) != -1:
                self.main_layout.removeWidget(self.chart_area)
                self.chart_area.setParent(None)
                self.chart_area.deleteLater()
            
            # Añadir el nuevo canvas al layout
            self.main_layout.addWidget(canvas)
            self.chart_area = canvas # Actualizar la referencia al área del gráfico

            canvas.setSizePolicy(self.chart_area.sizePolicy())
            canvas.updateGeometry()

        except Exception as e:
            if isinstance(self.chart_area, QtWidgets.QLabel):
                self.chart_area.show()
                self.chart_area.setText(f"Error al renderizar el gráfico: {e}")
            else: # Si chart_area ya es un canvas, reemplazarlo con un QLabel de error
                error_label = QtWidgets.QLabel(f"Error al renderizar el gráfico: {e}")
                error_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                error_label.setStyleSheet("color: red; font-size: 14px;")
                
                for i in reversed(range(self.main_layout.count())):
                    item = self.main_layout.itemAt(i)
                    if item and item.widget() == self.chart_area:
                        self.main_layout.removeWidget(self.chart_area)
                        self.chart_area.setParent(None)
                        self.chart_area.deleteLater()
                        break
                self.main_layout.addWidget(error_label)
                self.chart_area = error_label # Actualizar la referencia
            logger.critical(f"Error al renderizar el gráfico: {e}", exc_info=True)


    def start_updates(self):
        """Inicia la carga inicial de datos del gráfico."""
        self.load_chart_data()
        # No hay un temporizador de actualización continua para el gráfico,
        # ya que se actualiza al cambiar símbolo/intervalo o al ser solicitado.

    def stop_updates(self):
        """Detiene cualquier proceso de actualización (no aplica directamente aquí)."""
        pass # No hay un temporizador activo para detener en este widget

    def cleanup(self):
        logger.info("ChartWidget: Limpieza completada.")

if __name__ == '__main__':
    import sys
    import logging
    from ultibot_ui.workers import ApiWorker
    import qasync

    logging.basicConfig(level=logging.INFO)

    app = QtWidgets.QApplication(sys.argv)
    
    class MockMainWindow(BaseMainWindow):
        def add_thread(self, thread: QtCore.QThread):
            logger.info(f"MockMainWindow: Thread '{thread.objectName()}' added for tracking.")

    mock_main_window = MockMainWindow()
    main_window_widget = QtWidgets.QMainWindow()
    main_window_widget.setWindowTitle("Chart Widget Test")
    main_window_widget.setGeometry(100, 100, 800, 600)

    class MockAPIClient(UltiBotAPIClient):
        def __init__(self, base_url: str):
            super().__init__(base_url)
            self._client = MagicMock(spec=httpx.AsyncClient)

        async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 200) -> List[Kline]:
            logger.info(f"MockAPIClient: Obteniendo datos de velas para {symbol}-{timeframe}")
            sample_data = [
                {"open_time": 1678886400000, "open": 20000.0, "high": 20100.0, "low": 19900.0, "close": 20050.0, "volume": 1000.0, "close_time": 1678886459999, "quote_asset_volume": "20050000", "number_of_trades": 100, "taker_buy_base_asset_volume": "500", "taker_buy_quote_asset_volume": "10025000"},
                {"open_time": 1678890000000, "open": 20050.0, "high": 20200.0, "low": 20000.0, "close": 20150.0, "volume": 1200.0, "close_time": 1678890059999, "quote_asset_volume": "24180000", "number_of_trades": 120, "taker_buy_base_asset_volume": "600", "taker_buy_quote_asset_volume": "12090000"},
                {"open_time": 1678893600000, "open": 20150.0, "high": 20300.0, "low": 20100.0, "close": 20250.0, "volume": 1100.0, "close_time": 1678893659999, "quote_asset_volume": "22275000", "number_of_trades": 110, "taker_buy_base_asset_volume": "550", "taker_buy_quote_asset_volume": "11137500"},
                {"open_time": 1678897200000, "open": 20250.0, "high": 20400.0, "low": 20200.0, "close": 20350.0, "volume": 1300.0, "close_time": 1678897259999, "quote_asset_volume": "26455000", "number_of_trades": 130, "taker_buy_base_asset_volume": "650", "taker_buy_quote_asset_volume": "13227500"},
                {"open_time": 1678900800000, "open": 20350.0, "high": 20500.0, "low": 20300.0, "close": 20450.0, "volume": 1400.0, "close_time": 1678900859999, "quote_asset_volume": "28630000", "number_of_trades": 140, "taker_buy_base_asset_volume": "700", "taker_buy_quote_asset_volume": "14315000"},
            ]
            return [Kline(**d) for d in sample_data]

    mock_api_client_instance = MockAPIClient(base_url="http://mock-api")
    
    event_loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    app.setProperty("main_event_loop", event_loop) # Establecer el bucle de eventos para el mock

    chart_widget = ChartWidget(api_client=mock_api_client_instance, main_window=mock_main_window, main_event_loop=event_loop)
    main_window_widget.setCentralWidget(chart_widget)
    main_window_widget.show()

    with event_loop:
        sys.exit(app.exec_())
