import logging
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QLabel, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialogButtonBox, QProgressBar, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette, QColor, QFont

from src.core.domain_models.opportunity_models import AIAnalysis, Opportunity

logger = logging.getLogger(__name__)

class AIAnalysisDialog(QDialog):
    """
    A dialog to display the detailed results of an AI analysis.
    """
    execute_trade_requested = Signal(Opportunity)
    reanalyze_requested = Signal(Opportunity)

    def __init__(self, opportunity: Opportunity, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.opportunity = opportunity
        self.analysis_result = opportunity.ai_analysis
        self.setWindowTitle(f"Análisis IA para {opportunity.symbol}")
        self.setMinimumSize(800, 600)

        self._init_ui()
        self._populate_data()

    def _init_ui(self):
        """Initialize the user interface of the dialog."""
        main_layout = QVBoxLayout(self)
        
        # Grid for summary section
        summary_layout = QGridLayout()
        
        # Confidence
        summary_layout.addWidget(QLabel("<b>Confianza:</b>"), 0, 0)
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setRange(0, 100)
        summary_layout.addWidget(self.confidence_bar, 0, 1)

        # Suggested Action
        summary_layout.addWidget(QLabel("<b>Acción Sugerida:</b>"), 1, 0)
        self.action_label = QLabel()
        self.action_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        summary_layout.addWidget(self.action_label, 1, 1)

        # Model Used
        summary_layout.addWidget(QLabel("<b>Modelo Utilizado:</b>"), 2, 0)
        self.model_label = QLabel()
        summary_layout.addWidget(self.model_label, 2, 1)

        # Processing Time
        summary_layout.addWidget(QLabel("<b>Tiempo de Procesamiento:</b>"), 3, 0)
        self.time_label = QLabel()
        summary_layout.addWidget(self.time_label, 3, 1)

        main_layout.addLayout(summary_layout)

        # Reasoning
        main_layout.addWidget(self._create_section_label("Razonamiento de la IA"))
        self.reasoning_text = QTextEdit()
        self.reasoning_text.setReadOnly(True)
        main_layout.addWidget(self.reasoning_text)

        # Trade Parameters
        main_layout.addWidget(self._create_section_label("Parámetros de Trading Recomendados"))
        self.params_table = self._create_simple_table(["Parámetro", "Valor"])
        main_layout.addWidget(self.params_table)

        # Data Verification
        main_layout.addWidget(self._create_section_label("Verificación de Datos"))
        self.verification_table = self._create_simple_table(["Verificación", "Estado"])
        main_layout.addWidget(self.verification_table)
        
        # Warnings
        main_layout.addWidget(self._create_section_label("Advertencias"))
        self.warnings_text = QTextEdit()
        self.warnings_text.setReadOnly(True)
        self.warnings_text.setVisible(False) # Hide if no warnings
        main_layout.addWidget(self.warnings_text)

        # Dialog buttons
        self.button_box = QDialogButtonBox()
        self.reanalyze_button = self.button_box.addButton("Re-analizar", QDialogButtonBox.ButtonRole.ActionRole)
        self.execute_button = self.button_box.addButton("Ejecutar Trade", QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close)

        self.button_box.clicked.connect(self._handle_button_click)
        
        main_layout.addWidget(self.button_box)

    def _create_section_label(self, text: str) -> QLabel:
        """Creates a styled label for a section header."""
        label = QLabel(text)
        font = label.font()
        font.setBold(True)
        font.setPointSize(11)
        label.setFont(font)
        return label

    def _create_simple_table(self, headers: List[str]) -> QTableWidget:
        """Creates a simple two-column table."""
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return table

    def _populate_data(self):
        """Populate the UI widgets with data from the analysis_result."""
        if not self.analysis_result:
            logger.warning("AIAnalysisDialog: _populate_data called with no analysis_result.")
            # Optionally, disable buttons or show a message
            self.execute_button.setEnabled(False)
            self.reanalyze_button.setText("Analizar") # Change text to reflect action
            return

        # Summary
        confidence = int(self.analysis_result.calculated_confidence * 100)
        self.confidence_bar.setValue(confidence)
        self._set_confidence_color(confidence)

        action = self.analysis_result.suggested_action.value.replace("_", " ").title()
        self.action_label.setText(action)
        self._set_action_color(action)

        self.model_label.setText(self.analysis_result.model_used or "No especificado")
        self.time_label.setText(f"{self.analysis_result.processing_time_ms} ms")

        # Reasoning
        self.reasoning_text.setText(self.analysis_result.reasoning_ai)

        # Trade Parameters
        if self.analysis_result.recommended_trade_params:
            params = self.analysis_result.recommended_trade_params.model_dump()
            self.params_table.setRowCount(len(params))
            for i, (key, value) in enumerate(params.items()):
                self.params_table.setItem(i, 0, QTableWidgetItem(key.replace("_", " ").title()))
                self.params_table.setItem(i, 1, QTableWidgetItem(str(value)))

        # Data Verification
        if self.analysis_result.data_verification:
            verifications = self.analysis_result.data_verification.model_dump()
            self.verification_table.setRowCount(len(verifications))
            for i, (key, value) in enumerate(verifications.items()):
                self.verification_table.setItem(i, 0, QTableWidgetItem(key.replace("_", " ").title()))
                status_item = QTableWidgetItem(str(value))
                color = QColor("green") if value and "ok" in str(value).lower() or "verified" in str(value).lower() else QColor("red")
                status_item.setForeground(color)
                self.verification_table.setItem(i, 1, status_item)

        # Warnings
        if self.analysis_result.ai_warnings:
            self.warnings_text.setVisible(True)
            self.warnings_text.setText("\n".join(self.analysis_result.ai_warnings))
            palette = self.warnings_text.palette()
            palette.setColor(QPalette.ColorRole.Base, QColor("#fff3cd"))
            self.warnings_text.setPalette(palette)

    def _set_confidence_color(self, value: int):
        """Sets the color of the confidence bar based on the value."""
        if value < 40:
            color = "#dc3545"  # Red
        elif value < 70:
            color = "#ffc107"  # Yellow
        else:
            color = "#28a745"  # Green
        self.confidence_bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

    def _set_action_color(self, action: str):
        """Sets the color of the action label based on the action."""
        if "Buy" in action:
            color = QColor("green")
        elif "Sell" in action:
            color = QColor("red")
        else:
            color = QColor("orange")
        
        palette = self.action_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, color)
        self.action_label.setPalette(palette)

    def _handle_button_click(self, button):
        """Handle clicks on the dialog's buttons."""
        if not self.opportunity:
            return

        role = self.button_box.buttonRole(button)
        if button == self.reanalyze_button:
            self.reanalyze_requested.emit(self.opportunity)
            self.accept()
        elif button == self.execute_button:
            self.execute_trade_requested.emit(self.opportunity)
            self.accept()
        elif self.button_box.standardButton(button) == QDialogButtonBox.StandardButton.Close:
            self.reject()
