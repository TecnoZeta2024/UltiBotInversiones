import asyncio
from typing import List, Dict, Optional, Any
from uuid import UUID

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QHeaderView, QDialog, QListWidget,
    QDialogButtonBox, QLabel, QLineEdit, QMessageBox
)

from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService
from src.ultibot_ui.services.ui_config_service import UIConfigService
# Pydantic models typically not directly used in widget, data flows through services
# from src.ultibot_ui.models import MarketData # Example if needed

# TODO: Fetch this from a configuration or a dedicated API endpoint via UIConfigService
ALL_AVAILABLE_PAIRS_EXAMPLE = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "DOGE-USD",
    "DOT-USD", "LINK-USD", "LTC-USD", "XRP-USD", "BNB-USD",
    "AAPL-USD", "GOOGL-USD", "MSFT-USD", "AMZN-USD", "TSLA-USD" # Example "stock" pairs
]


class PairConfigurationDialog(QDialog):
    def __init__(self, current_pairs: List[str], all_available_pairs: List[str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Configure Favorite Pairs")
        self.setMinimumSize(400, 300)

        self.all_available_pairs = sorted(list(set(all_available_pairs))) # Ensure unique and sorted
        self.selected_pairs = list(current_pairs) # Work with a copy

        layout = QVBoxLayout(self)

        search_label = QLabel("Search Pairs:")
        layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter...")
        self.search_input.textChanged.connect(self.filter_pairs)
        layout.addWidget(self.search_input)

        self.pair_list_widget = QListWidget()
        self.pair_list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self._populate_pair_list()
        self._select_current_pairs()
        layout.addWidget(self.pair_list_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_pair_list(self, filter_text: str = ""):
        self.pair_list_widget.clear()
        for pair in self.all_available_pairs:
            if filter_text.lower() in pair.lower():
                item = QListWidget.item.QListWidgetItem(pair) # type: ignore
                self.pair_list_widget.addItem(item)

    def _select_current_pairs(self):
        for i in range(self.pair_list_widget.count()):
            item = self.pair_list_widget.item(i)
            if item.text() in self.selected_pairs:
                item.setSelected(True)

    def filter_pairs(self, text: str):
        self._populate_pair_list(text)
        # Re-apply selection after filtering might be complex if items are hidden/shown
        # For simplicity, current selections might be lost if they don't match filter
        # A more robust way would be to hide/show items instead of clearing and repopulating
        # or maintain a master list of selected items.
        # For now, we re-select based on the initial self.selected_pairs
        # This means if you select, then filter out, then clear filter, selection is remembered.
        # If you select, then filter and it hides, then change selection, it's based on visible items.
        current_selection_texts = [item.text() for item in self.pair_list_widget.selectedItems()]

        # Update self.selected_pairs based on current visible selection
        # This is tricky because filtering changes what's visible.
        # A simpler approach might be to just filter the display list and make final selection on "OK"
        # For now, let's just filter the display. The final selection is gathered on accept().
        pass


    def get_selected_pairs(self) -> List[str]:
        return sorted([item.text() for item in self.pair_list_widget.selectedItems()])


class MarketDataWidget(QWidget):
    data_updated = Signal(dict)  # Emits the updated market_data dictionary

    def __init__(self, user_id: UUID, market_data_service: UIMarketDataService, config_service: UIConfigService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        # Ensure user_id is set in config_service if it's used for loading/saving configs
        self.config_service.set_user_id(user_id)


        self.favorite_pairs: List[str] = []
        # Market data structure: {'PAIR_SYMBOL': {'lastPrice': '...', 'priceChangePercent': '...', 'quoteVolume': '...', 'error': '...'}}
        self.market_data: Dict[str, Dict[str, Any]] = {}

        self._init_ui()

        self.rest_update_timer = QTimer(self)
        self.rest_update_timer.timeout.connect(self._on_rest_update_timeout)

        # Initial load
        asyncio.create_task(self.load_and_refresh_data())


    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Table for market data
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4) # Pair, Price, Change, Volume
        self.table_widget.setHorizontalHeaderLabels(["Pair", "Last Price", "Change (24h)", "Volume (24h)"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
        layout.addWidget(self.table_widget)

        self.status_label = QLabel("Loading initial data...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.clicked.connect(self._on_refresh_button_clicked)
        button_layout.addWidget(self.refresh_button)

        self.configure_button = QPushButton("Configure Pairs")
        self.configure_button.clicked.connect(self.open_pair_configuration_dialog)
        button_layout.addWidget(self.configure_button)

        layout.addLayout(button_layout)
        self.data_updated.connect(self.update_table)


    async def load_and_refresh_data(self):
        """Loads configuration and then fetches initial market data."""
        self.status_label.setText("Loading configuration...")
        self.table_widget.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.configure_button.setEnabled(False)
        try:
            # Load user configuration (which includes favorite pairs)
            # The user_id is already set in config_service constructor or via set_user_id
            user_config = await self.config_service.load_user_configuration()
            if user_config and "favoritePairs" in user_config:
                loaded_pairs = user_config["favoritePairs"]
            else:
                # Fallback or handle error if config loading fails
                loaded_pairs = await self.config_service.get_favorite_pairs() # Try direct getter which has defaults
                if not user_config: # If load_user_configuration returned None
                    self.status_label.setText("Could not load user configuration. Using default pairs.")
                    # Optionally save these defaults back if appropriate
                    # await self.config_service.save_user_configuration({"favoritePairs": loaded_pairs})

            self.set_favorite_pairs(loaded_pairs) # This will also trigger an initial table update (empty)

            if not self.favorite_pairs:
                self.status_label.setText("No favorite pairs configured. Click 'Configure Pairs'.")
            else:
                self.status_label.setText(f"Loaded {len(self.favorite_pairs)} pairs. Fetching data...")
                await self._fetch_rest_data() # Fetch initial data

            # Start the timer for periodic REST updates if there are pairs
            if self.favorite_pairs:
                if not self.rest_update_timer.isActive():
                    self.rest_update_timer.start(30 * 1000) # 30 seconds
            else:
                if self.rest_update_timer.isActive():
                    self.rest_update_timer.stop()

        except Exception as e:
            self.status_label.setText(f"Error during initial load: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load initial data: {e}")
        finally:
            self.table_widget.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.configure_button.setEnabled(True)


    def _on_rest_update_timeout(self):
        if self.favorite_pairs:
            asyncio.create_task(self._fetch_rest_data())
        else:
            self.status_label.setText("No pairs to fetch. Configure pairs.")
            if self.rest_update_timer.isActive():
                self.rest_update_timer.stop()


    def _on_refresh_button_clicked(self):
        if self.favorite_pairs:
            asyncio.create_task(self._fetch_rest_data())
        else:
            QMessageBox.information(self, "No Pairs", "Please configure favorite pairs first.")


    async def _fetch_rest_data(self):
        """Fetches current ticker data for favorite pairs using UIMarketDataService."""
        if not self.favorite_pairs:
            self.status_label.setText("No favorite pairs to fetch.")
            self.market_data = {}
            self.data_updated.emit(self.market_data)
            return

        self.status_label.setText(f"Fetching data for {len(self.favorite_pairs)} pairs...")
        self.table_widget.setEnabled(False) # Disable table during update
        self.refresh_button.setEnabled(False)

        try:
            # Using the new batch ticker fetch method
            tickers_data = await self.market_data_service.fetch_tickers_data(self.favorite_pairs)

            if tickers_data is None:
                # API call failed or returned None (e.g., network error, server error)
                self.status_label.setText("Error fetching market data. Check connection or try again.")
                # Preserve old data but mark as error, or clear and show error per row
                for pair in self.favorite_pairs:
                    self.market_data[pair] = {
                        "lastPrice": "Error",
                        "priceChangePercent": "Error",
                        "quoteVolume": "Error",
                        "error": "Failed to fetch"
                    }
            else:
                # API call succeeded, update market_data
                # Ensure all favorite pairs have an entry, even if API didn't return them (maybe they are delisted)
                new_market_data = {}
                for pair in self.favorite_pairs:
                    if pair in tickers_data:
                        new_market_data[pair] = tickers_data[pair]
                    else:
                        new_market_data[pair] = {
                            "lastPrice": "N/A",
                            "priceChangePercent": "N/A",
                            "quoteVolume": "N/A",
                            "error": "Not found"
                        }
                self.market_data = new_market_data
                self.status_label.setText(f"Market data updated. Last: {QDateTime.currentDateTime().toString()}") # type: ignore

            self.data_updated.emit(self.market_data)

        except Exception as e:
            self.status_label.setText(f"An error occurred: {e}")
            # You might want to update the table to show errors for all rows
            for pair in self.favorite_pairs:
                 self.market_data[pair] = {"lastPrice": "Error", "priceChangePercent": "N/A", "quoteVolume": "N/A", "error": str(e)}
            self.data_updated.emit(self.market_data)
        finally:
            self.table_widget.setEnabled(True)
            self.refresh_button.setEnabled(True)

    def update_table(self, new_data: Dict[str, Dict[str, Any]]):
        self.table_widget.setRowCount(0) # Clear existing rows

        if not new_data and self.favorite_pairs: # Data is empty but we have pairs, likely an error state
             for i, pair_symbol in enumerate(self.favorite_pairs):
                self.table_widget.insertRow(i)
                self.table_widget.setItem(i, 0, QTableWidgetItem(pair_symbol))
                error_item = QTableWidgetItem("Error fetching")
                error_item.setForeground(Qt.GlobalColor.red) # type: ignore
                self.table_widget.setItem(i, 1, error_item)
                self.table_widget.setItem(i, 2, QTableWidgetItem("-"))
                self.table_widget.setItem(i, 3, QTableWidgetItem("-"))
             return

        for i, pair_symbol in enumerate(self.favorite_pairs): # Iterate over configured pairs to maintain order
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(pair_symbol))

            pair_data = new_data.get(pair_symbol)
            if pair_data:
                if pair_data.get("error"):
                    price_item = QTableWidgetItem(str(pair_data.get("lastPrice", "Error"))) # Show error if available
                    price_item.setForeground(Qt.GlobalColor.red) # type: ignore
                    change_item = QTableWidgetItem(str(pair_data.get("priceChangePercent", "-")))
                    volume_item = QTableWidgetItem(str(pair_data.get("quoteVolume", "-")))
                    if pair_data.get("error") == "Not found":
                         price_item.setForeground(Qt.GlobalColor.gray) # type: ignore
                else:
                    price_item = QTableWidgetItem(str(pair_data.get("lastPrice", "N/A")))
                    change_val_str = str(pair_data.get("priceChangePercent", "0"))
                    try:
                        change_val = float(change_val_str)
                        change_item = QTableWidgetItem(f"{change_val:.2f}%")
                        if change_val > 0:
                            change_item.setForeground(Qt.GlobalColor.green) # type: ignore
                        elif change_val < 0:
                            change_item.setForeground(Qt.GlobalColor.red) # type: ignore
                        else:
                            change_item.setForeground(Qt.GlobalColor.gray) # type: ignore
                    except ValueError:
                        change_item = QTableWidgetItem(change_val_str) # Show as is if not float
                        change_item.setForeground(Qt.GlobalColor.gray) # type: ignore

                    volume_item = QTableWidgetItem(str(pair_data.get("quoteVolume", "N/A")))

                self.table_widget.setItem(i, 1, price_item)
                self.table_widget.setItem(i, 2, change_item)
                self.table_widget.setItem(i, 3, volume_item)
            else:
                # Pair was in favorite_pairs but not in new_data (should be handled by _fetch_rest_data)
                self.table_widget.setItem(i, 1, QTableWidgetItem("Waiting..."))
                self.table_widget.setItem(i, 2, QTableWidgetItem("-"))
                self.table_widget.setItem(i, 3, QTableWidgetItem("-"))


    def set_favorite_pairs(self, pairs: List[str]):
        """Updates the list of favorite pairs and refreshes the table structure."""
        self.favorite_pairs = sorted(list(set(pairs))) # Ensure unique and sorted

        # Update table structure (rows) based on new pairs
        # This will clear data, but _fetch_rest_data will be called soon after.
        self.market_data = {pair: {} for pair in self.favorite_pairs} # Reset data with new keys
        self.update_table(self.market_data) # Display empty rows for new pairs

        if not self.favorite_pairs:
            self.status_label.setText("No favorite pairs configured.")
            if self.rest_update_timer.isActive():
                self.rest_update_timer.stop()
        else:
            self.status_label.setText(f"{len(self.favorite_pairs)} pairs configured. Fetching data...")
            if not self.rest_update_timer.isActive():
                 self.rest_update_timer.start(30 * 1000) # Restart timer if it was stopped


    def open_pair_configuration_dialog(self):
        # TODO: Fetch ALL_AVAILABLE_PAIRS_EXAMPLE from config service or market data service eventually
        # For now, using the example list.
        # all_pairs = await self.market_data_service.get_all_available_symbols() or ALL_AVAILABLE_PAIRS_EXAMPLE
        all_pairs = ALL_AVAILABLE_PAIRS_EXAMPLE
        
        dialog = PairConfigurationDialog(self.favorite_pairs, all_pairs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_pairs = dialog.get_selected_pairs()
            self.set_favorite_pairs(new_pairs) # Updates UI and self.favorite_pairs

            # Save the new configuration
            # The user_id is already set in config_service
            asyncio.create_task(
                self.config_service.save_user_configuration({"favoritePairs": new_pairs})
            )

            # Refresh data for the new set of pairs
            if new_pairs:
                asyncio.create_task(self._fetch_rest_data())
            else: # No pairs selected, clear table and stop updates
                self.market_data = {}
                self.data_updated.emit(self.market_data)
                if self.rest_update_timer.isActive():
                    self.rest_update_timer.stop()
                self.status_label.setText("No favorite pairs configured.")


    def cleanup(self):
        """Clean up resources, like stopping timers."""
        if self.rest_update_timer.isActive():
            self.rest_update_timer.stop()
        # Any other cleanup (WebSockets were removed, but if added back, close here)
        print("MarketDataWidget cleaned up.")

# Need QDateTime for status label update, if not already imported by PySide6
from PySide6.QtCore import QDateTime
