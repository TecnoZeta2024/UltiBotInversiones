from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class StrategyManagementView(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        title_label = QLabel("Strategy Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # Placeholder for strategy list
        placeholder_label = QLabel("Strategy list will be displayed here.")
        layout.addWidget(placeholder_label)

    def load_strategies(self):
        # TODO: Implement logic to fetch and display strategies using the api_client
        pass
