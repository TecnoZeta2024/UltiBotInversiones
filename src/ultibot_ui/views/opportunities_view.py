import asyncio # Añadido para la anotación de tipo AbstractEventLoop
import logging
from uuid import UUID
from typing import List, Dict, Any, Coroutine, Callable # Coroutine y Callable importados desde typing

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
    def __init__(self, user_id: UUID, backend_base_url: str, qasync_loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        logger.info("OpportunitiesView: __init__ called.") # Log de inicialización
        self.user_id = user_id
        self.backend_base_url = backend_base_url
        self.qasync_loop = qasync_loop # Almacenar el bucle qasync
        self.active_threads = []
        logger.debug(f"OpportunitiesView initialized with qasync_loop: {self.qasync_loop}")

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
        logger.info("OpportunitiesView: _load_initial_data called.") # Log de llamada a la función
        # Reducir el retraso para que la carga de oportunidades sea casi inmediata.
        logger.info("OpportunitiesView: Setting up QTimer.singleShot for _fetch_opportunities in 0.1s.")
        QTimer.singleShot(100, self._fetch_opportunities) # Retraso de 100 ms
        logger.info("OpportunitiesView: QTimer.singleShot for _fetch_opportunities has been set.")

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
        logger.info("[TRACE] OpportunitiesView: _fetch_opportunities called. Fetching Gemini IA opportunities.")
        print("[TRACE] OpportunitiesView: _fetch_opportunities called. Fetching Gemini IA opportunities.")
        self.status_label.setText("Loading opportunities...")
        self.refresh_button.setEnabled(False)
        self.opportunities_table.setRowCount(0)  # Clear table while loading
        logger.debug("[TRACE] OpportunitiesView: Attempting to get get_gemini_opportunities coroutine.")
        print("[TRACE] OpportunitiesView: Attempting to get get_gemini_opportunities coroutine.")
        self._start_api_worker(lambda api_client: api_client.get_gemini_opportunities(),)

    def _start_api_worker(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine]):
        # Import local para evitar ciclo de importación
        from src.ultibot_ui.main import ApiWorker

        logger.debug(f"OpportunitiesView._start_api_worker: Creating ApiWorker for coroutine_factory.")
        if not self.qasync_loop:
            logger.error("OpportunitiesView: qasync_loop no está disponible para _start_api_worker.")
            self._handle_opportunities_error("Error interno: Bucle de eventos no configurado para worker.")
            return
        
        # Pasar la fábrica de corutinas, la URL base del backend y el qasync_loop al constructor de ApiWorker
        worker = ApiWorker(coroutine_factory, self.backend_base_url)
        logger.debug(f"OpportunitiesView._start_api_worker: ApiWorker instance created: {worker} with loop {self.qasync_loop}")
        thread = QThread()
        logger.debug(f"OpportunitiesView._start_api_worker: QThread instance created: {thread}")
        self.active_threads.append(thread)
        worker.moveToThread(thread)
        logger.debug(f"OpportunitiesView._start_api_worker: Worker {worker} moved to thread {thread}. Connecting signals...")

        worker.result_ready.connect(self._handle_opportunities_result)
        worker.error_occurred.connect(self._handle_opportunities_error)

        thread.started.connect(worker.run)

        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        
        # El worker se autoelimina DESPUÉS de emitir la señal.
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)

        # El thread se elimina a sí mismo cuando termina.
        # No conectar thread.finished directamente a worker.deleteLater.
        
        def on_thread_finished():
            logger.debug(f"OpportunitiesView: Thread {thread} finished. Removing from active_threads.")
            if thread in self.active_threads:
                self.active_threads.remove(thread)
            # El thread se eliminará a sí mismo.
            thread.deleteLater()

        thread.finished.connect(on_thread_finished)
        
        logger.debug(f"OpportunitiesView._start_api_worker: Signals connected. Starting thread for worker: {worker} on thread: {thread}")
        thread.start()
        logger.debug(f"OpportunitiesView._start_api_worker: thread.start() called for worker: {worker}. IsRunning: {thread.isRunning()}, IsFinished: {thread.isFinished()}")
        if not thread.isRunning() and not thread.isFinished():
            logger.warning(f"OpportunitiesView._start_api_worker: Thread {thread} for worker {worker} did not start immediately. Check event loop or thread contention.")


    def _handle_opportunities_result(self, opportunities_data: List[Dict[str, Any]]):
        logger.info(f"[TRACE] OpportunitiesView: Received {len(opportunities_data)} opportunities. Data: {opportunities_data}")
        # print(f"[TRACE] OpportunitiesView: Received {len(opportunities_data)} opportunities. Data: {opportunities_data}") # Redundant with logger
        logger.debug(f"[DEBUG_TABLE] Total opportunities received: {len(opportunities_data)}")
        logger.debug(f"[DEBUG_TABLE] Raw opportunities_data: {opportunities_data}")

        self.status_label.setText(f"Loaded {len(opportunities_data)} opportunities.")
        self.refresh_button.setEnabled(True)
        self.opportunities_table.setRowCount(0)

        if not opportunities_data:
            logger.debug("[DEBUG_TABLE] No opportunities data. Setting placeholder message.")
            self.opportunities_table.setRowCount(1)
            placeholder_item = QTableWidgetItem("No opportunities to display.")
            placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.opportunities_table.setItem(0, 0, placeholder_item)
            logger.debug("[DEBUG_TABLE] Set placeholder item at row 0, col 0.")
            self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())
            self.status_label.setText("No high-confidence opportunities found at the moment.")
            self.opportunities_table.resizeColumnsToContents()
            self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")
            return

        self.opportunities_table.setRowCount(len(opportunities_data))
        logger.debug(f"[DEBUG_TABLE] Set opportunities_table row count to: {len(opportunities_data)}")

        for row, opp_data in enumerate(opportunities_data):
            logger.debug(f"[DEBUG_TABLE] Processing row index: {row}")

            symbol = opp_data.get("symbol", "N/A").replace("/", "")
            logger.debug(f"[DEBUG_TABLE] Row {row}: Extracted symbol: {symbol}")

            side = opp_data.get("side", "N/A")
            logger.debug(f"[DEBUG_TABLE] Row {row}: Extracted side: {side}")

            entry_price = opp_data.get("entry_price")
            logger.debug(f"[DEBUG_TABLE] Row {row}: Extracted entry_price: {entry_price}")

            confidence_score = opp_data.get("confidence_score")
            logger.debug(f"[DEBUG_TABLE] Row {row}: Extracted confidence_score: {confidence_score}")

            strategy_id = opp_data.get("strategy_id", "N/A")
            logger.debug(f"[DEBUG_TABLE] Row {row}: Extracted strategy_id: {strategy_id}")

            exchange = opp_data.get("exchange", "N/A")
            logger.debug(f"[DEBUG_TABLE] Row {row}: Extracted exchange: {exchange}")

            timestamp = opp_data.get("timestamp_utc", opp_data.get("createdAt", "N/A"))
            logger.debug(f"[DEBUG_TABLE] Row {row}: Extracted timestamp: {timestamp}")

            # Columna 0: símbolo
            symbol_item = QTableWidgetItem(str(symbol))
            self.opportunities_table.setItem(row, 0, symbol_item)
            logger.debug(f"[DEBUG_TABLE] Row {row}, Col 0: SetItem with symbol: {symbol}")

            # Columna 1: side
            side_item = QTableWidgetItem(str(side))
            if side == "BUY":
                side_item.setForeground(QColor("lightgreen"))
            elif side == "SELL":
                side_item.setForeground(QColor("lightcoral"))
            self.opportunities_table.setItem(row, 1, side_item)
            logger.debug(f"[DEBUG_TABLE] Row {row}, Col 1: SetItem with side: {side}")

            # Columna 2: entry_price
            entry_price_str = f"{entry_price:,.2f}" if isinstance(entry_price, (int, float)) else str(entry_price)
            entry_price_item = QTableWidgetItem(entry_price_str)
            self.opportunities_table.setItem(row, 2, entry_price_item)
            logger.debug(f"[DEBUG_TABLE] Row {row}, Col 2: SetItem with entry_price: {entry_price_str}")

            # Columna 3: confidence_score
            confidence_score_str = f"{confidence_score:.2f}" if isinstance(confidence_score, (int, float)) else str(confidence_score)
            score_item = QTableWidgetItem(confidence_score_str)
            if isinstance(confidence_score, (int, float)):
                if confidence_score >= 0.9:
                    score_item.setForeground(QColor("lightgreen"))
                elif confidence_score >= 0.7:
                    score_item.setForeground(QColor("yellow"))
                else:
                    score_item.setForeground(QColor("orange"))
            self.opportunities_table.setItem(row, 3, score_item)
            logger.debug(f"[DEBUG_TABLE] Row {row}, Col 3: SetItem with confidence_score: {confidence_score_str}")

            # Columna 4: strategy_id
            strategy_id_item = QTableWidgetItem(str(strategy_id))
            self.opportunities_table.setItem(row, 4, strategy_id_item)
            logger.debug(f"[DEBUG_TABLE] Row {row}, Col 4: SetItem with strategy_id: {strategy_id}")

            # Columna 5: exchange
            exchange_item = QTableWidgetItem(str(exchange))
            self.opportunities_table.setItem(row, 5, exchange_item)
            logger.debug(f"[DEBUG_TABLE] Row {row}, Col 5: SetItem with exchange: {exchange}")

            # Columna 6: timestamp
            timestamp_item = QTableWidgetItem(str(timestamp))
            self.opportunities_table.setItem(row, 6, timestamp_item)
            logger.debug(f"[DEBUG_TABLE] Row {row}, Col 6: SetItem with timestamp: {timestamp}")

        logger.debug("[DEBUG_TABLE] Table population loop complete.")
        self.opportunities_table.resizeColumnsToContents()
        self.opportunities_table.resizeRowsToContents()
        self.opportunities_table.update()
        self.opportunities_table.repaint() # Added repaint call

        self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")

        # [DEBUG_UI] Logging
        logger.debug(f"[DEBUG_UI] Table visible: {self.opportunities_table.isVisible()}")
        logger.debug(f"[DEBUG_UI] OpportunitiesView visible: {self.isVisible()}")
        logger.debug(f"[DEBUG_UI] Table size: {self.opportunities_table.size().width()}x{self.opportunities_table.size().height()}")
        logger.debug(f"[DEBUG_UI] Table rowCount: {self.opportunities_table.rowCount()}, columnCount: {self.opportunities_table.columnCount()}")
        for i in range(self.opportunities_table.columnCount()):
            logger.debug(f"[DEBUG_UI] Column {i} width: {self.opportunities_table.columnWidth(i)}")
        # Only log row heights if there are rows, to avoid issues if table is empty or has placeholder
        if self.opportunities_table.rowCount() > 0 and opportunities_data: # Check opportunities_data to avoid logging placeholder row height
            for i in range(self.opportunities_table.rowCount()):
                logger.debug(f"[DEBUG_UI] Row {i} height: {self.opportunities_table.rowHeight(i)}")
        elif not opportunities_data:
            logger.debug("[DEBUG_UI] No actual data rows to log heights for (placeholder might be present).")


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

        # Schedule fetching notification history
        if self.qasync_loop and self.api_client and self.user_id:
            try:
                self.qasync_loop.create_task(self.api_client.get_notification_history(self.user_id))
                logger.info("OpportunitiesView: Scheduled get_notification_history task in error handler.")
            except Exception as e:
                logger.error(f"OpportunitiesView: Failed to schedule get_notification_history: {e}", exc_info=True)
        else:
            logger.warning("OpportunitiesView: qasync_loop, api_client, or user_id not available. Cannot schedule get_notification_history.")


    def cleanup(self):
        logger.info("OpportunitiesView: Cleaning up...")
        # Detener el timer de auto-refresco
        if self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.stop()
            logger.info("OpportunitiesView: Auto-refresh timer stopped.")

        for thread in list(self.active_threads):
            if thread.isRunning():
                logger.info(f"OpportunitiesView: Deteniendo thread {thread.objectName()}...")
                thread.quit()
                if not thread.wait(2000): # Esperar hasta 2 segundos
                    logger.warning(f"OpportunitiesView: Thread {thread.objectName()} no terminó a tiempo. Forzando terminación.")
                    thread.terminate()
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
        def __init__(self, base_url: str = ""): self.base_url = base_url
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

    # Para la prueba independiente, necesitamos un mock del bucle de eventos si no se ejecuta qasync completo
    mock_loop = asyncio.new_event_loop()

    view_success = OpportunitiesView(
        user_id=UUID("00000000-0000-0000-0000-000000000000"), 
        backend_base_url="http://localhost:8000", # type: ignore
        qasync_loop=mock_loop # Pasar el mock_loop
    ) 
    view_success.setWindowTitle("Opportunities View - Success Test")
    view_success.show()

    # Test error case
    mock_client_error = MockUltiBotAPIClient()
    # For error, the MockApiWorker will raise based on the function name, so we assign the error mock
    mock_client_error.get_real_trading_candidates = _mock_get_real_trading_candidates_error # type: ignore
