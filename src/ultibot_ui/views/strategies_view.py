import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class StrategiesView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trading Strategies")
        
        self._layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Configured Trading Strategies")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self.title_label)
        
        self.strategies_list_widget = QListWidget()
        self._layout.addWidget(self.strategies_list_widget)
        
        self.setLayout(self._layout)
        
    def update_strategies(self, strategies: List[Dict[str, Any]]):
        """
        Populates the list widget with strategy information.
        """
        self.strategies_list_widget.clear()
        if not strategies:
            self.strategies_list_widget.addItem("No strategies configured.")
            return
            
        for strategy in strategies:
            # Customize how the strategy is displayed in the list
            item_text = f"{strategy.get('name', 'Unnamed Strategy')} ({strategy.get('id')})"
            list_item = QListWidgetItem(item_text)
            self.strategies_list_widget.addItem(list_item)
        
        logger.info(f"Strategies view updated with {len(strategies)} strategies.")
