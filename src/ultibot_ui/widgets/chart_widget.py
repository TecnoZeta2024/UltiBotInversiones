from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QLayoutItem
from PyQt5.QtCore import Qt, pyqtSignal, QTimer # Importar QTimer para actualizaciones dinámicas
from PyQt5.QtGui import QPainter, QColor, QPen
import mplfinance as mpf
import pandas as pd
import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID

# from src.ultibot_backend.services.market_data_service import MarketDataService # Reemplazado por api_client
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError # Importar APIClient
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging # Añadir logging

logger = logging.getLogger(__name__) # Configurar logger

class ChartWidget(QWidget):
    """
    Widget para la visualización de gráficos financieros utilizando mplfinance.
    """
    # Señales para comunicar eventos al servicio de UI o al backend
    symbol_selected = pyqtSignal(str)
    interval_selected = pyqtSignal(str)
    
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, parent: Optional[QWidget] = None): # Cambiado market_data_service a api_client
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client # Guardar la referencia al api_client
        self.current_symbol: Optional[str] = None
        self.current_interval: Optional[str] = "1h" # Intervalo por defecto
        self.candlestick_data: List[Dict[str, Any]] = []

        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        # Controles de selección (temporal, se integrarán con la lista de seguimiento)
        self.controls_layout = QHBoxLayout()
        
        self.symbol_label = QLabel("Par:")
        self.symbol_combo = QComboBox()
        # Estos símbolos serán cargados dinámicamente desde la lista de seguimiento
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
        self.controls_layout.addStretch(1) # Empuja los controles a la izquierda

        self.main_layout.addLayout(self.controls_layout)

        # Área para el gráfico (inicialmente un QLabel de placeholder)
        self.chart_area = QLabel("Cargando gráfico...")
        self.chart_area.setAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
        self.main_layout.addWidget(self.chart_area)

        self.setLayout(self.main_layout)
        self.setStyleSheet("background-color: #1e1e1e; color: #cccccc;") # Estilo básico oscuro

        # Cargar el primer gráfico al iniciar
        self.current_symbol = self.symbol_combo.currentText()
        # La carga de datos ahora se difiere dentro de load_chart_data
        self.load_chart_data()

    def _schedule_task(self, coro):
        """Helper method to schedule an asyncio task without returning the task object to QTimer."""
        asyncio.create_task(coro)

    def _on_symbol_changed(self, index: int):
        self.current_symbol = self.symbol_combo.currentText()
        self.symbol_selected.emit(self.current_symbol)
        self.load_chart_data()

    def _on_interval_changed(self, index: int):
        self.current_interval = self.interval_combo.currentText()
        self.interval_selected.emit(self.current_interval)
        self.load_chart_data()

    def set_candlestick_data(self, data: List[Dict[str, Any]]):
        """
        Establece los datos de velas y actualiza el gráfico.
        """
        self.candlestick_data = data
        self.update_chart_display()

    def load_chart_data(self):
        """
        Solicita la carga de datos del gráfico.
        En una aplicación real, esto emitiría una señal o llamaría a un servicio
        para obtener los datos del backend de forma asíncrona.
        """
        if self.current_symbol and self.current_interval:
            self.chart_area.setText(f"Cargando datos para {self.current_symbol} ({self.current_interval})...")
            print(f"Solicitando datos para {self.current_symbol} - {self.current_interval}")
            # Llamada real al backend diferida
            QTimer.singleShot(0, lambda: self._schedule_task(self._fetch_real_data()))
        else:
            self.chart_area.setText("Seleccione un par y una temporalidad para ver el gráfico.")

    async def _fetch_real_data(self):
        """Obtiene datos reales de velas del backend."""
        try:
            if self.current_symbol is None or self.current_interval is None:
                self.chart_area.setText("Error: Símbolo o temporalidad no seleccionados.")
                return
            # Ahora pasamos user_id explícitamente
            candlestick_data = await self.api_client.get_candlestick_data(
                user_id=self.user_id,
                symbol=self.current_symbol,
                interval=self.current_interval,
                limit=200
            )
            self.set_candlestick_data(candlestick_data)
        except APIError as e:
            logger.error(f"APIError al obtener datos de velas para {self.current_symbol}-{self.current_interval}: {e.message}", exc_info=True)
            self.set_candlestick_data([])
            if isinstance(self.chart_area, QLabel):
                self.chart_area.setText(f"Error API: {e.message}")
        except Exception as e:
            logger.error(f"Error inesperado al obtener datos de velas para {self.current_symbol}-{self.current_interval}: {e}", exc_info=True)
            self.set_candlestick_data([]) 
            if isinstance(self.chart_area, QLabel):
                self.chart_area.setText(f"Error inesperado al cargar datos: {str(e)}")


    def update_chart_display(self):
        """
        Renderiza el gráfico de velas japonesas y volumen utilizando mplfinance.
        """
        if not self.candlestick_data:
            self.chart_area.setText("No hay datos disponibles para mostrar el gráfico.")
            return

        # Convertir los datos a un DataFrame de Pandas
        df = pd.DataFrame(self.candlestick_data)
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df = df.set_index('open_time')
        df.index.name = 'Date' # mplfinance espera 'Date' como nombre del índice

        # Renombrar columnas para mplfinance
        df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }, inplace=True)

        # Crear el gráfico
        try:
            # Configurar el estilo oscuro
            mc = mpf.make_marketcolors(up='#00ff00', down='#ff0000',
                                       edge='inherit', wick='inherit',
                                       volume='#1f77b4', # Color del volumen
                                       ohlc='i')
            s = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc,
                                   figcolor='#1e1e1e', # Fondo de la figura
                                   facecolor='#1e1e1e', # Fondo del área de trazado
                                   gridcolor='#333333', # Color de la cuadrícula
                                   textcolor='#cccccc', # Color del texto
                                   rc={'axes.edgecolor': '#333333'}) # Color del borde de los ejes

            # Crear la figura y los ejes para mplfinance
            fig, axlist = mpf.plot(df,
                                   type='candle',
                                   volume=True,
                                   style=s,
                                   returnfig=True,
                                   figscale=1.5, # Escala de la figura para mejor visualización
                                   addplot=[mpf.make_addplot(df['Volume'], panel=1, type='bar', color='inherit', ylabel='Volume')],
                                   title=f"{self.current_symbol} - {self.current_interval}",
                                   ylabel='Price',
                                   ylabel_lower='Volume',
                                   xrotation=0 # Evitar rotación automática de etiquetas del eje X
                                  )
            
            # Crear el canvas de la figura
            canvas = FigureCanvas(fig)
            
            # Limpiar el layout anterior si existe
            # Iterar sobre los elementos del layout y eliminar los widgets de gráfico anteriores
            # Se itera en reversa para evitar problemas con los índices al eliminar elementos
            for i in reversed(range(self.main_layout.count())):
                item = self.main_layout.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    # Asegurarse de que el widget no sea None y no sea el área de control
                    # El placeholder original (QLabel) ya no es self.chart_area después de la primera renderización
                    # Ahora self.chart_area es el canvas, por lo que no queremos eliminarlo
                    if widget and widget != self.chart_area and widget not in self.controls_layout.findChildren(QWidget):
                        self.main_layout.removeWidget(widget)
                        widget.setParent(None)
                        widget.deleteLater()
            
            # Si el chart_area actual es un QLabel (el placeholder inicial), lo eliminamos
            if isinstance(self.chart_area, QLabel) and self.main_layout.indexOf(self.chart_area) != -1:
                self.main_layout.removeWidget(self.chart_area)
                self.chart_area.setParent(None)
                self.chart_area.deleteLater()
            
            # Añadir el nuevo canvas al layout
            self.main_layout.addWidget(canvas)
            self.chart_area = canvas # Actualizar la referencia al "área del gráfico" para que sea el nuevo canvas

            # Ajustar el tamaño del canvas para que se ajuste al layout
            canvas.setSizePolicy(self.chart_area.sizePolicy())
            canvas.updateGeometry()

        except Exception as e:
            self.chart_area.show() # Mostrar el placeholder de nuevo
            self.chart_area.setText(f"Error al renderizar el gráfico: {e}")
            print(f"Error al renderizar el gráfico: {e}")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow
    import sys
    import logging

    # Configurar logging para ver mensajes
    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("Chart Widget Test")
    main_window.setGeometry(100, 100, 800, 600)

    # ID de usuario de prueba
    test_user_id = UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef")

    # Ejemplo de inicialización de servicios mockeados para pruebas
    class MockAPIClient: # Cambiado de MockMarketDataService a MockAPIClient
        async def get_candlestick_data(self, user_id: UUID, symbol: str, interval: str, limit: int, start_time: Optional[Any]=None, end_time: Optional[Any]=None) -> List[Dict[str, Any]]: # Ajustar signatura
            logger.info(f"MockAPIClient: Obteniendo datos de velas para {symbol}-{interval}")
            # Datos de ejemplo para el mock
            sample_data = [
                {"open_time": 1678886400000, "open": "20000.0", "high": "20100.0", "low": "19900.0", "close": "20050.0", "volume": "1000.0"},
                {"open_time": 1678890000000, "open": "20050.0", "high": "20200.0", "low": "20000.0", "close": "20150.0", "volume": "1200.0"},
                {"open_time": 1678893600000, "open": "20150.0", "high": "20300.0", "low": "20100.0", "close": "20250.0", "volume": "1100.0"},
                {"open_time": 1678897200000, "open": "20250.0", "high": "20400.0", "low": "20200.0", "close": "20350.0", "volume": "1300.0"},
                {"open_time": 1678900800000, "open": "20350.0", "high": "20500.0", "low": "20300.0", "close": "20450.0", "volume": "1400.0"},
            ]
            # Asegurarse de que los datos numéricos sean float o int, no strings, para mplfinance
            for row in sample_data:
                row["open"] = float(row["open"])
                row["high"] = float(row["high"])
                row["low"] = float(row["low"])
                row["close"] = float(row["close"])
                row["volume"] = float(row["volume"])
            return sample_data

    mock_api_client = MockAPIClient() # Usar MockAPIClient
    chart_widget = ChartWidget(user_id=test_user_id, api_client=mock_api_client) # type: ignore
    main_window.setCentralWidget(chart_widget)
    main_window.show()

    sys.exit(app.exec_())
