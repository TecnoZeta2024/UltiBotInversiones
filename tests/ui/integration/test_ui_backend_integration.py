import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from PySide6.QtCore import Qt, QObject, Signal

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
        "active": True,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": "strat_2",
        "name": "Mean Reversion",
        "description": "A strategy that sells high and buys low.",
        "active": False,
        "created_at": "2025-01-16T11:30:00Z"
    }
]


class MockStrategiesWorker(QObject):
    """
    A mock worker that inherits from QObject to provide real Qt signals,
    which is necessary for qtbot.waitSignal to work correctly.
    """
    strategies_ready = Signal(list)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__()
        # We can mock methods if we need to assert they were called
        self.run = MagicMock()
        self.start = MagicMock()


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

    # We patch the __init__ of other views to prevent side effects.
    with patch('src.ultibot_ui.windows.main_window.DashboardView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.OpportunitiesView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.PortfolioView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.HistoryView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.SettingsView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.TradingTerminalView.__init__', side_effect=dummy_init, autospec=True), \
         patch('src.ultibot_ui.windows.main_window.UIStrategyService'), \
         patch('src.ultibot_ui.windows.main_window.ApiWorker') as MockApiWorker, \
         patch('src.ultibot_ui.views.strategies_view.StrategiesWorker') as MockStrategiesWorkerClass:

        # Instantiate our custom mock worker
        mock_strategies_worker_instance = MockStrategiesWorker()
        # Configure the patch to return our custom mock instance
        MockStrategiesWorkerClass.return_value = mock_strategies_worker_instance
        
        # Configure the mock for the ApiWorker created in MainWindow
        mock_api_worker_instance = MockApiWorker.return_value
        mock_api_worker_instance.error_occurred.connect(lambda x: print(f"MockApiWorker error: {x}"))

        mock_api_client = MagicMock(spec=UltiBotAPIClient)
        mock_user_id = uuid4()

        window = MainWindow(user_id=mock_user_id, api_client=mock_api_client)
        qtbot.addWidget(window)
        window.show()

        # Manually trigger the signal emission that the real worker would do.
        # This simulates the worker finishing its job and sending the data to the view.
        # We connect the signal from our mock worker to the actual slot in the view.
        strategies_view = window.strategies_view
        mock_strategies_worker_instance.strategies_ready.connect(strategies_view.update_strategies)
        
        # We yield the window and the mock instance to check calls on it later.
        yield window, mock_strategies_worker_instance
        
        window.close()

def test_strategies_view_loads_data_correctly(qtbot, app):
    """
    Test Case 1: Verify that the Strategies View correctly fetches and displays data.
    
    Steps:
    1. Launch the main window.
    2. Navigate to the "Strategies" view.
    3. Manually emit the signal from the mock worker to simulate data arrival.
    4. Check if the table in StrategiesView is populated with the correct number of rows.
    5. Verify the content of the first row to ensure data is mapped correctly.
    """
    main_window, mock_strategies_worker_instance = app
    
    # 1. & 2. Navigate to the Strategies view by clicking the corresponding button
    sidebar = main_window.sidebar
    strategies_button = sidebar.findChild(QPushButton, "navButton_strategies")
    assert strategies_button is not None, "Could not find the strategies navigation button"
    qtbot.mouseClick(strategies_button, Qt.MouseButton.LeftButton)

    # 3. Manually emit the signal from the mock worker with the mock data.
    # qtbot.waitSignal will now work because our mock has a real Signal.
    with qtbot.waitSignal(mock_strategies_worker_instance.strategies_ready, raising=True, timeout=2000):
        mock_strategies_worker_instance.strategies_ready.emit(MOCK_STRATEGIES_DATA)

    # 4. Check if the table is populated correctly
    strategies_view = main_window.strategies_view
    assert strategies_view.strategies_table_widget.rowCount() == len(MOCK_STRATEGIES_DATA)

    # 5. Verify the content of the first row
    assert strategies_view.strategies_table_widget.item(0, 0).text() == MOCK_STRATEGIES_DATA[0]["name"]
    assert strategies_view.strategies_table_widget.item(0, 1).text() == "N/A"
    assert strategies_view.strategies_table_widget.item(0, 2).text() == "N/A"

    # The worker is created, but we control when its signal is emitted, so we don't check run()
