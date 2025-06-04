import logging
from uuid import UUID
from typing import List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QAbstractItemView, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, QTimer, QDateTime  # Added QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QObject, pyqtSignal  # Import for mocks/signals

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class OpportunitiesView(QWidget):
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.active_threads = []

        self._setup_ui()
        self._load_initial_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16) # Consistent margins
        main_layout.setSpacing(12) # Consistent spacing for elements within this view
        self.setLayout(main_layout)

        # Title Frame
        title_frame = QFrame() # This frame can be styled by QSS if QFrame has global styles
        title_frame.setObjectName("viewHeaderFrame") # Specific name if needed
        title_frame_layout = QHBoxLayout(title_frame)
        title_frame_layout.setContentsMargins(0,0,0,0)

        title_label = QLabel("High-Confidence Trading Opportunities")
        title_label.setObjectName("viewTitleLabel")
        title_frame_layout.addWidget(title_label)
        title_frame_layout.addStretch()
        main_layout.addWidget(title_frame)
        # self._apply_shadow_effect(title_frame, y_offset=1, blur_radius=5, color_hex="#00FF8C") # Subtle glow for title frame


        # Controls (Refresh Button and Status Label)
        controls_frame = QFrame() # Wrap controls in a frame for potential card-like styling
        controls_frame.setObjectName("controlsFrame")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(10)
        controls_layout.setContentsMargins(0, 6, 0, 6) # Add some vertical padding if frame has no border/bg

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("statusLabel")
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()
        self.refresh_button = QPushButton("Refresh Opportunities")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.clicked.connect(self._fetch_opportunities)
        controls_layout.addWidget(self.refresh_button)

        self.last_updated_label = QLabel("Last updated: --")
        controls_layout.addWidget(self.last_updated_label)

        main_layout.addWidget(controls_frame)
        # self._apply_shadow_effect(controls_frame) # Optional: if controls should be a card


        # Table for Opportunities - Main content area
        table_container_frame = QFrame() # Use a frame to apply shadow to the table area
        table_container_frame.setObjectName("tableContainerFrame")
        table_layout = QVBoxLayout(table_container_frame)
        table_layout.setContentsMargins(0,0,0,0) # Frame handles padding via QSS on QFrame

        self.opportunities_table = QTableWidget()
        self.opportunities_table.setObjectName("opportunitiesTable") # For specific QSS
        self.opportunities_table.setColumnCount(7)
        self.opportunities_table.setHorizontalHeaderLabels([
            "Symbol", "Side", "Entry Price", "Score", "Strategy", "Exchange", "Timestamp"
        ])
        # Usar ResizeMode para compatibilidad con PyQt5 >= 5.11
        header = self.opportunities_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vheader = self.opportunities_table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        self.opportunities_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.opportunities_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.opportunities_table.setAlternatingRowColors(True)

        table_layout.addWidget(self.opportunities_table)
        main_layout.addWidget(table_container_frame, 1)
        self._apply_shadow_effect(table_container_frame) # Apply shadow to the table's container

        # Timer for auto-refresh (every 30s)
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setInterval(30_000)  # 30 seconds
        self._auto_refresh_timer.timeout.connect(self._fetch_opportunities)
        self._auto_refresh_timer.start()

    def _load_initial_data(self):
        # Añadir un retraso de 5 segundos para dar tiempo al backend a estabilizarse completamente
        QTimer.singleShot(5000, self._fetch_opportunities)

    def _apply_shadow_effect(self, widget: QWidget, color_hex: str = "#000000", blur_radius: int = 10, x_offset: int = 0, y_offset: int = 1):
        """Applies QGraphicsDropShadowEffect to a widget.
           Defaulting to a subtle dark shadow suitable for light or dark themes.
           For specific "glow" on dark theme, color_hex would be an accent.
        """
        # Example: In dark mode, a glow might be preferred.
        # current_theme = "dark" # This would ideally come from a theme manager
        # if current_theme == "dark" and color_hex == "#000000":
        #     color_hex = "#00FF8C" # Neon green glow
        #     blur_radius = 15
        #     y_offset = 0

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(color_hex))
        shadow.setOffset(x_offset, y_offset)
        widget.setGraphicsEffect(shadow)

    def _fetch_opportunities(self):
        logger.info("OpportunitiesView: Fetching Gemini IA opportunities.")
        self.status_label.setText("Loading opportunities...")
        self.refresh_button.setEnabled(False)
        self.opportunities_table.setRowCount(0) # Clear table while loading

        logger.debug("OpportunitiesView: Attempting to get get_gemini_opportunities coroutine.")
        coroutine = self.api_client.get_gemini_opportunities()
        logger.debug(f"OpportunitiesView: Coroutine object created: {coroutine}")
        self._start_api_worker(coroutine)

    def _start_api_worker(self, *args, **kwargs):
        # Import local para evitar ciclo de importación
        from src.ultibot_ui.main import ApiWorker

        worker = ApiWorker(*args, **kwargs)
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_opportunities_result)
        worker.error_occurred.connect(self._handle_opportunities_error)

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        thread.start()

    def _handle_opportunities_result(self, opportunities_data: List[Dict[str, Any]]):
        logger.info(f"OpportunitiesView: Received {len(opportunities_data)} opportunities.")
        self.status_label.setText(f"Loaded {len(opportunities_data)} opportunities.")
        self.refresh_button.setEnabled(True)

        self.opportunities_table.setRowCount(len(opportunities_data))
        for row, opp_data in enumerate(opportunities_data):
            # Example: Adapt these based on the actual structure of opp_data from API
            self.opportunities_table.setItem(row, 0, QTableWidgetItem(str(opp_data.get("symbol", "N/A"))))
            self.opportunities_table.setItem(row, 1, QTableWidgetItem(str(opp_data.get("side", "N/A"))))
            self.opportunities_table.setItem(row, 2, QTableWidgetItem(str(opp_data.get("entry_price", "N/A")))) # entryPrice or similar
            self.opportunities_table.setItem(row, 3, QTableWidgetItem(str(opp_data.get("confidence_score", "N/A")))) # confidence_score or score
            self.opportunities_table.setItem(row, 4, QTableWidgetItem(str(opp_data.get("strategy_id", "N/A")))) # strategy_id or strategy_name
            self.opportunities_table.setItem(row, 5, QTableWidgetItem(str(opp_data.get("exchange", "N/A"))))
            timestamp = opp_data.get("timestamp_utc", opp_data.get("createdAt", "N/A")) # Check for common timestamp fields
            self.opportunities_table.setItem(row, 6, QTableWidgetItem(str(timestamp)))

        if not opportunities_data:
            self.status_label.setText("No high-confidence opportunities found at the moment.")
            # Optionally, display a message in the table itself if it's empty
            if self.opportunities_table.rowCount() == 0:
                self.opportunities_table.setRowCount(1)
                placeholder_item = QTableWidgetItem("No opportunities to display.")
                placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.opportunities_table.setItem(0, 0, placeholder_item)
                self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())

        self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")

    def _handle_opportunities_error(self, error_message: str):
        logger.error(f"OpportunitiesView: Error fetching opportunities: {error_message}")
        self.status_label.setText("Failed to load opportunities.")
        self.refresh_button.setEnabled(True)
        QMessageBox.warning(self, "Opportunities Error",
                            f"Could not load trading opportunities.\n"
                            f"Details: {error_message}\n\n"
                            "Please try refreshing or check your connection.")
        # Clear table or show error message in table
        self.opportunities_table.setRowCount(1)
        error_item = QTableWidgetItem(f"Error loading data: {error_message}")
        error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opportunities_table.setItem(0, 0, error_item)
        self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())

    def cleanup(self):
        logger.info("OpportunitiesView: Cleaning up...")
        for thread in list(self.active_threads):
            if thread.isRunning():
                thread.quit()
                thread.wait()
        self.active_threads.clear()
        logger.info("OpportunitiesView: Cleanup finished.")

if __name__ == '__main__':
    # This is a minimal example for testing the OpportunitiesView independently.
    # In a real application, QApplication is managed by main.py.
    from PyQt5.QtWidgets import QApplication
    import sys

    # Mock ApiWorker and UltiBotAPIClient for standalone testing
    class MockApiWorker(QObject): # Use QObject for signals if not importing full ApiWorker
        result_ready = pyqtSignal(object)
        error_occurred = pyqtSignal(str)
        def __init__(self, coro): self.coro = coro
        def run(self):
            try:
                # Simplified run for testing; real ApiWorker handles asyncio loop
                # For this test, we'll assume the coro is a function that returns data or raises
                if hasattr(self.coro, "__name__") and self.coro.__name__ == "_mock_get_real_trading_candidates_success":
                    self.result_ready.emit(self.coro())
                elif hasattr(self.coro, "__name__") and self.coro.__name__ == "_mock_get_real_trading_candidates_error":
                    raise APIError("Simulated API error", 500)
                else:
                     self.result_ready.emit([]) # Default empty
            except APIError as e:
                self.error_occurred.emit(str(e))
            except Exception as e:
                self.error_occurred.emit(f"Unexpected test error: {str(e)}")

    # ApiWorker original se guarda y MockApiWorker se asigna a ApiWorker DENTRO del if __name__ == '__main__'
    # para que no afecte el scope global del módulo cuando es importado.

    class MockUltiBotAPIClient:
        def __init__(self, base_url=""): pass
        async def get_real_trading_candidates(self): # Make it async for consistency with real one
            # This method will be replaced with the mock functions for testing
            return []

    def _mock_get_real_trading_candidates_success():
        return [
            {"id": "opp1", "symbol": "BTCUSDT", "side": "BUY", "entry_price": 60000.0, "confidence_score": 0.95, "strategy_id": "ScalpBasic", "exchange": "Binance", "timestamp_utc": "2023-10-27T10:00:00Z"},
            {"id": "opp2", "symbol": "ETHUSDT", "side": "SELL", "entry_price": 2000.0, "confidence_score": 0.88, "strategy_id": "SwingTrend", "exchange": "Binance", "timestamp_utc": "2023-10-27T10:05:00Z"},
        ]

    def _mock_get_real_trading_candidates_error():
        # This function itself doesn't need to do anything as the error is raised in MockApiWorker
        pass


    app = QApplication(sys.argv)

    from src.ultibot_ui.main import ApiWorker # Importar ApiWorker para el bloque de prueba
    OriginalApiWorker = ApiWorker # Guardar el original ANTES de sobreescribir
    ApiWorker = MockApiWorker # Sobreescribir con el mock para este bloque de prueba

    # Test success case
    mock_client_success = MockUltiBotAPIClient()
    mock_client_success.get_real_trading_candidates = _mock_get_real_trading_candidates_success # type: ignore

    view_success = OpportunitiesView(user_id=UUID("00000000-0000-0000-0000-000000000000"), api_client=mock_client_success) # type: ignore
    view_success.setWindowTitle("Opportunities View - Success Test")
    view_success.show()

    # Test error case
    mock_client_error = MockUltiBotAPIClient()
    # For error, the MockApiWorker will raise based on the function name, so we assign the error mock
    mock_client_error.get_real_trading_candidates = _mock_get_real_trading_candidates_error # type: ignore
