import pytest
import asyncio
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QObject, Signal
from decimal import Decimal # Importar Decimal

from src.ultibot_ui.windows.main_window import MainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.views.strategies_view import StrategiesView
from PySide6.QtWidgets import QPushButton, QWidget

# Mock data similar to what the backend would return
MOCK_STRATEGIES_DATA = [
    {
        "id": "strat_1",
        "name": "Momentum Breakout",
        "description": "A strategy that buys on strong upward movements.",
        "is_active_paper_mode": True,
        "is_active_real_mode": False,
        "created_at": "2025-01-15T10:00:00Z",
        "total_pnl": Decimal("123.45"), # Cambiado a Decimal
        "number_of_trades": 10
    },
    {
        "id": "strat_2",
        "name": "Mean Reversion",
        "description": "A strategy that sells high and buys low.",
        "is_active_paper_mode": False,
        "is_active_real_mode": True,
        "created_at": "2025-01-16T11:30:00Z",
        "total_pnl": Decimal("-50.20"), # Cambiado a Decimal
        "number_of_trades": 5
    }
]


class SignalEmitter(QObject):
    """A simple QObject to emit signals for testing."""
    data_ready = Signal(list)


@pytest.fixture
def app(qtbot):
    """
    Fixture to create the main application window and register it with qtbot.
    """
    # This dummy __init__ calls the QWidget base constructor and adds a dummy cleanup,
    # preventing errors during teardown.
    def dummy_init(self, *args, **kwargs):
        QWidget.__init__(self)
        self.cleanup = lambda: None
        # Prevent load_initial_configuration from being called in the mocked __init__
        self.load_initial_configuration = lambda: None

    # We patch the __init__ of other views and problematic methods to prevent side effects.
    with patch('src.ultibot_ui.windows.main_window.DashboardView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.MarketDataWidget.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.OpportunitiesView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.PortfolioView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.HistoryView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.SettingsView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.TradingTerminalView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.UIStrategyService'):

        mock_api_client = MagicMock(spec=UltiBotAPIClient)
        
        # Provide a mock event loop, as MainWindow requires it.
        mock_event_loop = MagicMock(spec=asyncio.AbstractEventLoop)

        window = MainWindow(api_client=mock_api_client, main_event_loop=mock_event_loop)
        qtbot.addWidget(window)
        window.show()

        # Create a generic signal emitter to test the view's reaction to data.
        emitter = SignalEmitter()
        strategies_view = window.strategies_view
        emitter.data_ready.connect(strategies_view.update_strategies)
        
        yield window, emitter
        
        window.close()

def test_strategies_view_loads_data_correctly(qtbot, app):
    """
    Test Case 1: Verify that the Strategies View correctly displays data upon signal.
    
    Steps:
    1. Launch the main window.
    2. Navigate to the "Strategies" view.
    3. Manually emit a signal with mock data.
    4. Check if the table in StrategiesView is populated with the correct number of rows.
    5. Verify the content of the first row to ensure data is mapped correctly.
    """
    main_window, emitter = app
    
    # 1. & 2. Navigate to the Strategies view by clicking the corresponding button
    sidebar = main_window.sidebar
    strategies_button = sidebar.findChild(QPushButton, "navButton_strategies")
    assert strategies_button is not None, "Could not find the strategies navigation button"
    qtbot.mouseClick(strategies_button, Qt.MouseButton.LeftButton)

    # 3. Manually emit the signal with the mock data.
    with qtbot.waitSignal(emitter.data_ready, raising=True, timeout=2000):
        emitter.data_ready.emit(MOCK_STRATEGIES_DATA)

    # 4. Check if the table is populated correctly
    strategies_view = main_window.strategies_view
    assert strategies_view.strategies_table_widget.rowCount() == len(MOCK_STRATEGIES_DATA)

    # 5. Verify the content of the first row
    assert strategies_view.strategies_table_widget.item(0, 0).text() == MOCK_STRATEGIES_DATA[0]["name"]
    assert strategies_view.strategies_table_widget.item(0, 1).text() == "Papel: Activa, Real: Inactiva"
    assert strategies_view.strategies_table_widget.item(0, 2).text() == "123.45"
