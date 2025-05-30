from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal

class SidebarNavigationWidget(QWidget):
    navigation_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 20, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        # Título o Logo
        logo_label = QLabel("UltiBot")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(logo_label)

        # Botones de navegación
        self._add_nav_button(layout, "Dashboard", "dashboard")
        self._add_nav_button(layout, "Oportunidades", "opportunities")
        self._add_nav_button(layout, "Estrategias", "strategies")
        self._add_nav_button(layout, "Historial", "history")
        self._add_nav_button(layout, "Configuración", "settings")

        layout.addStretch(1) # Empuja los botones hacia arriba

    def _add_nav_button(self, layout, text, name):
        button = QPushButton(text)
        button.setObjectName(f"navButton_{name}")
        button.setCheckable(True) # Para indicar el estado seleccionado
        button.clicked.connect(lambda: self._on_nav_button_clicked(name))
        button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
                background-color: transparent;
                color: #E0E0E0;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #2D2D2D;
            }
            QPushButton:checked {
                background-color: #0D6EFD;
                color: white;
                font-weight: bold;
            }
        """)
        layout.addWidget(button)

    def _on_nav_button_clicked(self, name):
        # Desmarcar todos los botones excepto el actual
        for button in self.findChildren(QPushButton):
            if button.objectName().startswith("navButton_") and button.objectName() != f"navButton_{name}":
                button.setChecked(False)
        self.navigation_requested.emit(name)
