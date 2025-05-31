import asyncio
import uuid # For UUID type hinting and example
from typing import Optional, List, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
)
from PySide6.QtCore import Qt

import pyqtgraph as pg
from pyqtgraph import CandlestickItem, DateAxisItem # mkPen, TextItem, InfiniteLine, AxisItem are also common

import numpy as np
from datetime import datetime

from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService
from src.ultibot_ui.models import MarketData, Kline # Assuming models are correctly defined

# Default values
DEFAULT_PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"] # Adjusted to common format
DEFAULT_INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]


class ChartWidget(QWidget):
    def __init__(self, user_id: uuid.UUID, market_data_service: UIMarketDataService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.current_market_data: Optional[MarketData] = None # Renamed for clarity

        self._init_ui()
        # Don't auto-load on init, let user click "Load Chart" or select pair/interval
        # asyncio.create_task(self.load_initial_data())
        self.status_label.setText("Select pair and interval, then click 'Load Chart'.")


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Controls Layout
        controls_layout = QHBoxLayout()

        self.pair_combo = QComboBox()
        self.pair_combo.addItems(DEFAULT_PAIRS)
        controls_layout.addWidget(QLabel("Pair:"))
        controls_layout.addWidget(self.pair_combo)

        self.interval_combo = QComboBox()
        self.interval_combo.addItems(DEFAULT_INTERVALS)
        controls_layout.addWidget(QLabel("Interval:"))
        controls_layout.addWidget(self.interval_combo)

        self.refresh_button = QPushButton("Load Chart")
        controls_layout.addWidget(self.refresh_button)

        main_layout.addLayout(controls_layout)

        # Chart Area
        # Using DateAxisItem for the bottom axis
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': DateAxisItem(orientation='bottom')})
        self.plot_widget.setBackground('w') # White background
        # self.plot_widget.setBackground('#1E1E1E') # Dark theme example
        self.candlestick_item = None
        main_layout.addWidget(self.plot_widget)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Connections
        self.refresh_button.clicked.connect(lambda: asyncio.create_task(self.load_chart_data()))
        # Optionally, auto-load on change, or require button press. For now, button press.
        # self.pair_combo.currentTextChanged.connect(lambda: asyncio.create_task(self.load_chart_data()))
        # self.interval_combo.currentTextChanged.connect(lambda: asyncio.create_task(self.load_chart_data()))

        # Basic plot styling
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.getAxis('left').setLabel('Price', units='USD') # Example unit

    async def load_initial_data(self):
        # This can be called if you want to load a default chart on startup
        # For instance, load the first pair and interval from the combos.
        if self.pair_combo.count() > 0 and self.interval_combo.count() > 0:
            await self.load_chart_data()

    async def load_chart_data(self):
        symbol = self.pair_combo.currentText()
        interval = self.interval_combo.currentText()

        if not symbol or not interval:
            self.status_label.setText("Please select a symbol and interval.")
            return

        self.refresh_button.setEnabled(False)
        self.status_label.setText(f"Loading {symbol} ({interval}) chart...")
        self.plot_widget.clear() # Clear previous plot items

        try:
            market_data: Optional[MarketData] = await self.market_data_service.fetch_historical_market_data(symbol, interval)

            if market_data and market_data.klines:
                self.current_market_data = market_data
                self.update_chart()
                self.status_label.setText(f"Displaying {symbol} ({interval})")
            else:
                self.current_market_data = None
                self.update_chart() # This will clear the chart if current_market_data is None
                self.status_label.setText(f"No data or error loading chart for {symbol} ({interval}).")
        except Exception as e:
            self.current_market_data = None
            self.update_chart()
            self.status_label.setText(f"Exception loading chart: {e}")
        finally:
            self.refresh_button.setEnabled(True)

    def update_chart(self):
        self.plot_widget.clear() # Clear previous plot items, including title

        if not self.current_market_data or not self.current_market_data.klines:
            self.plot_widget.setTitle("No data to display")
            # self.plot_widget.getAxis('bottom').setTicks(None) # Clear old ticks if any
            return

        # Set title after clearing
        symbol = self.current_market_data.asset_id
        interval = self.current_market_data.interval
        self.plot_widget.setTitle(f"{symbol} - {interval}")

        # Data for pyqtgraph.CandlestickItem: list of (time, open, high, low, close)
        # Our Kline model: [timestamp_ms, open, high, low, close, volume]

        # pyqtgraph's CandlestickItem is a bit particular. It doesn't directly use timestamps for x-values
        # but rather indices, and then you format the axis.
        # It expects data as a list of dicts or a NumPy array with fields: 'x', 'open', 'high', 'low', 'close'.
        # Or, it can take a list of tuples (index, open, high, low, close).

        ohlc_data_for_item = [] # list of (index, open, high, low, close)
        timestamps_for_axis = [] # list of actual timestamps (in seconds) for x-axis labeling

        for i, kline_obj in enumerate(self.current_market_data.klines):
            # kline_obj is an instance of our Pydantic Kline model
            # Access fields by name: kline_obj.timestamp, kline_obj.open, etc.
            ohlc_data_for_item.append((
                i,                    # Index for x-value
                float(kline_obj.open),
                float(kline_obj.high),
                float(kline_obj.low),
                float(kline_obj.close)
            ))
            timestamps_for_axis.append(kline_obj.timestamp / 1000) # Convert ms to seconds

        if not ohlc_data_for_item:
            self.plot_widget.setTitle(f"{symbol} - {interval} (No Kline Data)")
            return

        # Create CandlestickItem
        # Need to convert to NumPy array with specific dtype for CandlestickItem
        # dtype fields are 'x', 'open', 'high', 'low', 'close'
        # However, their example uses just a list of tuples (index, o, h, l, c)
        # Let's try simpler first, then np array if needed.
        # The CandlestickItem constructor seems to prefer a direct list of dicts or specific numpy array.
        # Let's structure it as list of dicts:
        processed_candles = []
        for i, k_open, k_high, k_low, k_close in ohlc_data_for_item:
            processed_candles.append({'x': i, 'open': k_open, 'high': k_high, 'low': k_low, 'close': k_close})

        self.candlestick_item = CandlestickItem(processed_candles) # Pass list of dicts
        self.plot_widget.addItem(self.candlestick_item)

        # Set X-axis to display dates using timestamps_for_axis
        bottom_axis = self.plot_widget.getAxis('bottom')

        num_klines = len(timestamps_for_axis)
        if num_klines > 0:
            # Generate ticks: list of (index, label_string)
            # Show fewer ticks if there's a lot of data to avoid clutter
            tick_spacing = max(1, num_klines // 10) # Show about 10 major ticks

            ticks_data = []
            for i in range(0, num_klines, tick_spacing):
                dt_obj = datetime.fromtimestamp(timestamps_for_axis[i])
                # Adjust strftime format based on interval (e.g., show date for daily, time for intraday)
                if interval.endswith('d') or interval.endswith('w') or interval.endswith('M'):
                     tick_label = dt_obj.strftime('%Y-%m-%d')
                else: # intraday
                     tick_label = dt_obj.strftime('%H:%M\n%d-%b') # Time over Date
                ticks_data.append((i, tick_label)) # x-value is index, label is formatted time

            bottom_axis.setTicks([ticks_data])
        else:
            bottom_axis.setTicks(None) # Clear ticks if no data

        # Auto-range can sometimes be too tight, give some padding or set manually
        self.plot_widget.autoRange()

    def cleanup(self):
        # Currently, ChartWidget doesn't manage any persistent resources like timers
        # that need explicit stopping. PlotWidget items are managed by Qt's parent-child lifecycle.
        # If timers or background tasks were added, they would be stopped here.
        print("ChartWidget cleaned up (no active resources to stop).")


# --- Example Usage ---
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    import qasync # Required for asyncio integration

    # --- Mocking Services and Models ---
    from src.ultibot_ui.services.api_client import ApiClient # For UIMarketDataService
    from src.ultibot_ui.models import Kline # Ensure Kline model is available

    class MockChartApiClient(ApiClient):
        async def get_market_historical_data(self, asset_id: str, interval: str) -> Optional[MarketData]:
            print(f"MockChartApiClient: Fetching historical data for {asset_id}, interval {interval}")
            await asyncio.sleep(0.5) # Simulate network delay

            klines_list = []
            current_time = datetime.now().timestamp() * 1000 # ms
            price = 100.0
            volume = 1000

            for i in range(50): # Generate 50 klines
                open_p = price + np.random.uniform(-1, 1)
                high_p = open_p + np.random.uniform(0, 2)
                low_p = open_p - np.random.uniform(0, 2)
                close_p = low_p + np.random.uniform(0, (high_p - low_p) * 0.8) # ensure close is between low and high portion

                # Ensure high is highest, low is lowest
                actual_high = max(open_p, high_p, low_p, close_p)
                actual_low = min(open_p, high_p, low_p, close_p)

                # Kline model: timestamp, open, high, low, close, volume
                # For pyqtgraph, timestamp is usually in seconds for DateAxisItem
                # Our model stores timestamp as int (assumed ms)
                kline_ts = int(current_time - (50 - i) * (60 * 1000 * (DEFAULT_INTERVALS.index(interval) + 1))) # Simulate time intervals

                # Use the Pydantic Kline model for constructing klines
                klines_list.append(
                    Kline(timestamp=kline_ts, open=open_p, high=actual_high, low=actual_low, close=close_p, volume=volume + np.random.uniform(-100,100))
                )
                price = close_p # Next kline starts from previous close (simplified)

            if asset_id == "BTC-USD": # Only return data for a specific asset for testing
                 return MarketData(asset_id=asset_id, interval=interval, klines=klines_list)
            return MarketData(asset_id=asset_id, interval=interval, klines=[]) # Return empty for others

    async def main_async_chart():
        app = QApplication.instance() or QApplication(sys.argv)

        mock_api_client = MockChartApiClient()
        market_data_service = UIMarketDataService(api_client=mock_api_client)

        test_user_id = uuid.uuid4() # Not directly used by ChartWidget logic itself, but good practice

        chart_widget = ChartWidget(user_id=test_user_id, market_data_service=market_data_service)
        chart_widget.setWindowTitle("Chart Widget Test")
        chart_widget.resize(800, 600)
        chart_widget.show()

        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Load initial data for the first pair in the combo
        # await chart_widget.load_initial_data() # Or trigger manually via UI

        try:
            await loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            chart_widget.cleanup() # Test cleanup
            if hasattr(mock_api_client, 'close'):
                 await mock_api_client.close()

    if __name__ == "__main__":
        try:
            qasync.run(main_async_chart())
        except RuntimeError as e:
            if "another loop is running" not in str(e).lower(): # Be more specific
                raise
        except KeyboardInterrupt:
            print("Chart test application terminated.")
        print("Exiting chart example.")
