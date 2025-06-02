"""
Trading mode selector widget for the UI header/navigation.
Provides a visual control to switch between paper and real trading modes.
"""
import logging
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox, 
    QFrame, QButtonGroup, QRadioButton, QToolTip
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

from src.ultibot_ui.services.trading_mode_state import (
    get_trading_mode_manager, TradingModeStateManager, TradingModeEnum, TradingMode
)

logger = logging.getLogger(__name__)

class TradingModeSelector(QWidget):
    """
    Widget for selecting between paper and real trading modes.
    
    Provides both toggle button and dropdown styles with visual indicators.
    """
    
    # Signal emitted when user changes trading mode
    mode_changed = pyqtSignal(str)
    
    def __init__(self, style: str = "toggle", parent: Optional[QWidget] = None):
        """
        Initialize the trading mode selector.
        
        Args:
            style: Widget style - 'toggle', 'dropdown', or 'radio'
            parent: Parent widget
        """
        super().__init__(parent)
        self.style = style
        self.state_manager: TradingModeStateManager = get_trading_mode_manager()
        
        # UI components
        self.mode_label: Optional[QLabel] = None
        self.toggle_button: Optional[QPushButton] = None
        self.mode_combo: Optional[QComboBox] = None
        self.radio_group: Optional[QButtonGroup] = None
        self.paper_radio: Optional[QRadioButton] = None
        self.real_radio: Optional[QRadioButton] = None
        self.status_indicator: Optional[QLabel] = None
        
        self.init_ui()
        self.connect_signals()
        self.update_display()
        
        logger.info(f"TradingModeSelector initialized with style: {style}")
    
    def init_ui(self):
        """Initialize the user interface based on the selected style."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Main container frame
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #2C2C2C;
                padding: 5px;
            }
        """)
        
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(8, 4, 8, 4)
        container_layout.setSpacing(8)
        
        # Mode label
        self.mode_label = QLabel("Trading Mode:")
        self.mode_label.setStyleSheet("color: #EEE; font-weight: bold;")
        container_layout.addWidget(self.mode_label)
        
        # Status indicator (colored dot)
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 12))
        container_layout.addWidget(self.status_indicator)
        
        # Style-specific widgets
        if self.style == "toggle":
            self._init_toggle_style(container_layout)
        elif self.style == "dropdown":
            self._init_dropdown_style(container_layout)
        elif self.style == "radio":
            self._init_radio_style(container_layout)
        else:
            logger.warning(f"Unknown style: {self.style}, defaulting to toggle")
            self._init_toggle_style(container_layout)
        
        layout.addWidget(container)
        layout.addStretch()  # Push everything to the left
    
    def _init_toggle_style(self, layout: QHBoxLayout):
        """Initialize toggle button style."""
        self.toggle_button = QPushButton()
        self.toggle_button.setMinimumWidth(120)
        self.toggle_button.setMinimumHeight(30)
        self.toggle_button.clicked.connect(self._toggle_mode)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #555;
                border-radius: 15px;
                padding: 5px 15px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                border: 2px solid #777;
            }
            QPushButton:pressed {
                border: 2px solid #999;
            }
        """)
        layout.addWidget(self.toggle_button)
    
    def _init_dropdown_style(self, layout: QHBoxLayout):
        """Initialize dropdown style."""
        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumWidth(130)
        self.mode_combo.setMinimumHeight(30)
        
        # Add items for each trading mode
        for mode_enum in TradingModeEnum:
            self.mode_combo.addItem(f"{mode_enum.icon} {mode_enum.display_name}", mode_enum.value)
        
        self.mode_combo.currentTextChanged.connect(self._combo_changed)
        self.mode_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #3C3C3C;
                color: white;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 2px solid #777;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #3C3C3C;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #3C3C3C;
                color: white;
                selection-background-color: #555;
            }
        """)
        layout.addWidget(self.mode_combo)
    
    def _init_radio_style(self, layout: QHBoxLayout):
        """Initialize radio button style."""
        self.radio_group = QButtonGroup()
        
        # Paper trading radio button
        self.paper_radio = QRadioButton(f"{TradingModeEnum.PAPER.icon} {TradingModeEnum.PAPER.display_name}")
        self.paper_radio.setStyleSheet("""
            QRadioButton {
                color: white;
                font-weight: bold;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #555;
                border-radius: 9px;
                background-color: #2C2C2C;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #4CAF50;
                border-radius: 9px;
                background-color: #4CAF50;
            }
        """)
        
        # Real trading radio button
        self.real_radio = QRadioButton(f"{TradingModeEnum.REAL.icon} {TradingModeEnum.REAL.display_name}")
        self.real_radio.setStyleSheet("""
            QRadioButton {
                color: white;
                font-weight: bold;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #555;
                border-radius: 9px;
                background-color: #2C2C2C;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #FF9800;
                border-radius: 9px;
                background-color: #FF9800;
            }
        """)
        
        self.radio_group.addButton(self.paper_radio, 0)
        self.radio_group.addButton(self.real_radio, 1)
        self.radio_group.buttonClicked.connect(self._radio_changed)
        
        layout.addWidget(self.paper_radio)
        layout.addWidget(self.real_radio)
    
    def connect_signals(self):
        """Connect to state manager signals."""
        self.state_manager.trading_mode_changed.connect(self.on_mode_changed_external)
    
    def _toggle_mode(self):
        """Handle toggle button click."""
        new_mode = self.state_manager.toggle_mode()
        logger.info(f"Toggle button clicked, new mode: {new_mode}")
    
    def _combo_changed(self):
        """Handle combo box selection change."""
        if self.mode_combo:
            selected_data = self.mode_combo.currentData()
            if selected_data and selected_data != self.state_manager.current_mode:
                self.state_manager.set_trading_mode(selected_data)
                logger.info(f"Combo selection changed to: {selected_data}")
    
    def _radio_changed(self, button):
        """Handle radio button selection change."""
        if button == self.paper_radio:
            if self.state_manager.current_mode != "paper":
                self.state_manager.set_trading_mode("paper")
                logger.info("Radio button changed to paper mode")
        elif button == self.real_radio:
            if self.state_manager.current_mode != "real":
                self.state_manager.set_trading_mode("real")
                logger.info("Radio button changed to real mode")
    
    def on_mode_changed_external(self, new_mode: str):
        """Handle external mode changes (from state manager)."""
        self.update_display()
        self.mode_changed.emit(new_mode)
        logger.debug(f"External mode change detected: {new_mode}")
    
    def update_display(self):
        """Update the visual display based on current mode."""
        current_mode = self.state_manager.current_mode
        mode_info = self.state_manager.get_mode_display_info()
        
        # Update status indicator color
        if self.status_indicator:
            self.status_indicator.setStyleSheet(f"color: {mode_info['color']};")
            self.status_indicator.setToolTip(f"Current mode: {mode_info['display_name']}")
        
        # Update style-specific displays
        if self.style == "toggle" and self.toggle_button:
            self.toggle_button.setText(f"{mode_info['icon']} {mode_info['display_name']}")
            self.toggle_button.setStyleSheet(f"""
                QPushButton {{
                    border: 2px solid {mode_info['color']};
                    border-radius: 15px;
                    padding: 5px 15px;
                    font-weight: bold;
                    color: white;
                    background-color: {mode_info['color']}33;
                }}
                QPushButton:hover {{
                    background-color: {mode_info['color']}55;
                    border: 2px solid {mode_info['color']};
                }}
                QPushButton:pressed {{
                    background-color: {mode_info['color']}77;
                    border: 2px solid {mode_info['color']};
                }}
            """)
        
        elif self.style == "dropdown" and self.mode_combo:
            # Find and select the correct index
            for i in range(self.mode_combo.count()):
                if self.mode_combo.itemData(i) == current_mode:
                    self.mode_combo.setCurrentIndex(i)
                    break
        
        elif self.style == "radio":
            if current_mode == "paper" and self.paper_radio:
                self.paper_radio.setChecked(True)
            elif current_mode == "real" and self.real_radio:
                self.real_radio.setChecked(True)
    
    def set_enabled_modes(self, modes: list):
        """
        Enable/disable specific trading modes.
        
        Args:
            modes: List of enabled modes ('paper' and/or 'real')
        """
        if self.style == "dropdown" and self.mode_combo:
            # Update combo box items
            self.mode_combo.clear()
            for mode_enum in TradingModeEnum:
                if mode_enum.value in modes:
                    self.mode_combo.addItem(f"{mode_enum.icon} {mode_enum.display_name}", mode_enum.value)
        
        elif self.style == "radio":
            if self.paper_radio:
                self.paper_radio.setEnabled("paper" in modes)
            if self.real_radio:
                self.real_radio.setEnabled("real" in modes)
        
        elif self.style == "toggle" and self.toggle_button:
            # For toggle, if only one mode is enabled, disable the toggle
            self.toggle_button.setEnabled(len(modes) > 1)
        
        logger.info(f"Enabled modes updated: {modes}")
    
    def get_current_mode(self) -> TradingMode:
        """Get the current trading mode."""
        return self.state_manager.current_mode


class TradingModeStatusBar(QWidget):
    """
    Simple status bar widget showing current trading mode.
    Useful for placing in status bars or footers.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.state_manager = get_trading_mode_manager()
        self.init_ui()
        self.connect_signals()
        self.update_display()
    
    def init_ui(self):
        """Initialize the status bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #CCC;
                font-size: 11px;
                padding: 2px 8px;
                border-radius: 3px;
                background-color: #333;
            }
        """)
        
        layout.addWidget(self.status_label)
        layout.addStretch()
    
    def connect_signals(self):
        """Connect to state manager signals."""
        self.state_manager.trading_mode_changed.connect(self.update_display)
    
    def update_display(self):
        """Update the status display."""
        mode_info = self.state_manager.get_mode_display_info()
        self.status_label.setText(f"{mode_info['icon']} Mode: {mode_info['display_name']}")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 3px;
                background-color: {mode_info['color']};
            }}
        """)
