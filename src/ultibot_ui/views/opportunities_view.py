import asyncio
import logging
from uuid import UUID
from typing import List, Dict, Any, Coroutine, Callable, Optional

from PySide6 import QtWidgets
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QAbstractItemView, QFrame, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QColor
from src.core.domain_models.opportunity_models import Opportunity, AIAnalysis, OpportunityStatus
from src.core.domain_models.user_configuration_models import AIStrategyConfiguration
from src.core.domain_models.trading_strategy_models import TradingStrategyConfig
from src.ultibot_ui.models import BaseMainWindow
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.dialogs.ai_analysis_dialog import AIAnalysisDialog # Nueva importación para el diálogo de análisis de IA

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class OpportunitiesView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, main_event_loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        logger.info("OpportunitiesView: __init__ called.")
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client # Usar la instancia de api_client
        self.main_window = main_window
        self.main_event_loop = main_event_loop # Inyectar el bucle de eventos
        logger.debug("OpportunitiesView initialized.")

        self._setup_ui()
        # No llamar a _load_initial_data aquí, se llamará después de set_user_id

    def set_user_id(self, user_id: UUID):
        """Establece el user_id y actualiza los widgets dependientes."""
        self.user_id = user_id
        logger.info(f"OpportunitiesView: User ID set to {user_id}.")
        # La carga inicial de datos ahora se maneja en initialize_view_data,
        # que es llamado por MainWindow.

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        self.setLayout(main_layout)

        title_frame = QFrame()
        title_frame.setObjectName("viewHeaderFrame")
        title_frame_layout = QHBoxLayout(title_frame)
        title_frame_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("High-Confidence Trading Opportunities")
        title_label.setObjectName("viewTitleLabel")
        title_frame_layout.addWidget(title_label)
        title_frame_layout.addStretch()
        main_layout.addWidget(title_frame)

        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(10)
        controls_layout.setContentsMargins(0, 6, 0, 6)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("statusLabel")
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()
        self.refresh_button = QPushButton("Refresh Opportunities")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.clicked.connect(lambda: self.main_event_loop.create_task(self._fetch_opportunities_async()))
        controls_layout.addWidget(self.refresh_button)

        self.last_updated_label = QLabel("Last updated: --")
        controls_layout.addWidget(self.last_updated_label)
        main_layout.addWidget(controls_frame)

        table_container_frame = QFrame()
        table_container_frame.setObjectName("tableContainerFrame")
        table_layout = QVBoxLayout(table_container_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.opportunities_table = QTableWidget()
        self.opportunities_table.setObjectName("opportunitiesTable")
        self.opportunities_table.setColumnCount(9) # Aumentar a 9 columnas
        self.opportunities_table.setHorizontalHeaderLabels([
            "Symbol", "Side", "Entry Price", "Score", "Strategy", "Exchange", "Timestamp", "Status Análisis IA", "Acción"
        ])
        header = self.opportunities_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vheader = self.opportunities_table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        self.opportunities_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.opportunities_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.opportunities_table.setAlternatingRowColors(True)

        table_layout.addWidget(self.opportunities_table)
        main_layout.addWidget(table_container_frame, 1)
        self._apply_shadow_effect(table_container_frame)

        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setInterval(30_000)
        self._auto_refresh_timer.timeout.connect(lambda: self.main_event_loop.create_task(self._fetch_opportunities_async()))
        self._auto_refresh_timer.start()

    async def initialize_view_data(self):
        """Inicia la carga de datos asíncrona para la vista de oportunidades."""
        logger.info("OpportunitiesView: initialize_view_data called.")
        await self._fetch_opportunities_async()

    def _apply_shadow_effect(self, widget: QWidget, color_hex: str = "#000000", blur_radius: int = 10, x_offset: int = 0, y_offset: int = 1):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(color_hex))
        shadow.setOffset(x_offset, y_offset)
        widget.setGraphicsEffect(shadow)

    # Este método ya no es necesario ya que las llamadas se hacen directamente a _fetch_opportunities_async
    # desde los conectores de los botones y el timer.
    # def _fetch_opportunities(self):
    #     logger.info("Fetching Gemini IA opportunities.")
    #     self.status_label.setText("Loading opportunities...")
    #     self.refresh_button.setEnabled(False)
    #     self.opportunities_table.setRowCount(0)
    #     self.main_event_loop.create_task(self._fetch_opportunities_async())

    async def _fetch_opportunities_async(self):
        try:
            opportunities_data = await self.api_client.get_ai_opportunities()
            opportunities = [Opportunity.model_validate(o) for o in opportunities_data]
            self._handle_opportunities_result(opportunities)
        except Exception as e:
            self._handle_opportunities_error(str(e))

    def _handle_opportunities_result(self, opportunities: List[Opportunity]):
        logger.info(f"Received {len(opportunities)} opportunities.")
        self.status_label.setText(f"Loaded {len(opportunities)} opportunities.")
        self.refresh_button.setEnabled(True)
        self.opportunities_table.setRowCount(0)

        if not opportunities:
            self.opportunities_table.setRowCount(1)
            placeholder_item = QTableWidgetItem("No opportunities to display.")
            placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.opportunities_table.setItem(0, 0, placeholder_item)
            self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())
            self.status_label.setText("No high-confidence opportunities found.")
            self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")
            return

        self.opportunities_table.setRowCount(len(opportunities))
        for row, opp in enumerate(opportunities):
            symbol = opp.symbol.replace("/", "") if opp.symbol else "N/A"
            side = opp.initial_signal.direction_sought.value if opp.initial_signal and opp.initial_signal.direction_sought else "N/A"
            entry_price = opp.initial_signal.entry_price_target if opp.initial_signal else "N/A"
            confidence_score = opp.get_effective_confidence()
            strategy_id = "AI" # Placeholder, as strategy is not directly linked here
            exchange = opp.exchange or "N/A"
            timestamp = opp.detected_at.strftime('%Y-%m-%d %H:%M:%S') if opp.detected_at else "N/A"
            
            ai_analysis_status = "Pendiente"
            ai_suggested_action = "N/A"
            
            if opp.ai_analysis:
                ai_analysis_status = "Completado"
                ai_suggested_action = opp.ai_analysis.suggested_action.value if opp.ai_analysis.suggested_action else "N/A"
                if opp.ai_analysis.ai_warnings:
                    ai_analysis_status += " (Advertencias)"
                if opp.ai_analysis.data_verification and any(status != "OK" for status in opp.ai_analysis.data_verification.dict().values()):
                    ai_analysis_status += " (Datos Inconsistentes)"
            elif opp.status == OpportunityStatus.UNDER_AI_ANALYSIS:
                ai_analysis_status = "En Curso"
            elif opp.status == OpportunityStatus.ERROR_IN_PROCESSING:
                ai_analysis_status = "Fallido"
            elif opp.status == OpportunityStatus.PENDING_AI_ANALYSIS:
                ai_analysis_status = "Pendiente"
            else:
                ai_analysis_status = "N/A" # Default for other statuses

            self.opportunities_table.setItem(row, 0, QTableWidgetItem(symbol))
            
            side_item = QTableWidgetItem(side)
            if side == "buy":
                side_item.setForeground(QColor("lightgreen"))
            elif side == "sell":
                side_item.setForeground(QColor("lightcoral"))
            self.opportunities_table.setItem(row, 1, side_item)

            entry_price_str = f"{entry_price:,.2f}" if isinstance(entry_price, (int, float)) else "N/A"
            self.opportunities_table.setItem(row, 2, QTableWidgetItem(entry_price_str))

            score_str = f"{confidence_score:.2f}" if isinstance(confidence_score, float) else "N/A"
            score_item = QTableWidgetItem(score_str)
            if isinstance(confidence_score, float):
                if confidence_score >= 0.9: score_item.setForeground(QColor("lightgreen"))
                elif confidence_score >= 0.7: score_item.setForeground(QColor("yellow"))
                elif confidence_score >= 0.5: score_item.setForeground(QColor("orange")) # >= 50% confidence
                else: score_item.setForeground(QColor("red")) # < 50% confidence
            self.opportunities_table.setItem(row, 3, score_item)

            self.opportunities_table.setItem(row, 4, QTableWidgetItem(strategy_id))
            self.opportunities_table.setItem(row, 5, QTableWidgetItem(exchange))
            self.opportunities_table.setItem(row, 6, QTableWidgetItem(timestamp))
            self.opportunities_table.setItem(row, 7, QTableWidgetItem(ai_analysis_status))

            action_button = QPushButton("Analizar con IA")
            action_button.setObjectName("analyzeAIButton")
            
            if opp.ai_analysis:
                action_button.setText("Ver Análisis IA")
                action_button.clicked.connect(lambda _, o=opp: self._show_ai_analysis_dialog(o))
                action_button.setEnabled(True)
            elif opp.status == OpportunityStatus.UNDER_AI_ANALYSIS:
                action_button.setText("Análisis en Curso")
                action_button.setEnabled(False)
            elif opp.status == OpportunityStatus.ERROR_IN_PROCESSING:
                action_button.setText("Análisis Fallido")
                action_button.setEnabled(False)
            elif opp.status == OpportunityStatus.PENDING_AI_ANALYSIS:
                action_button.setText("Analizar con IA")
                action_button.clicked.connect(lambda _, o=opp: self._analyze_opportunity_with_ai(o))
                action_button.setEnabled(True)
            else: # Default case for other statuses
                action_button.setText("Acción No Disponible")
                action_button.setEnabled(False)


            self.opportunities_table.setCellWidget(row, 8, action_button)

        self.opportunities_table.resizeColumnsToContents()
        self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")

    def _analyze_opportunity_with_ai(self, opportunity: Opportunity):
        logger.info(f"Initiating AI analysis for opportunity: {opportunity.id}")
        if not self.user_id or not opportunity.id:
            QMessageBox.warning(self, "Error", "Falta información del usuario o de la oportunidad para iniciar el análisis.")
            return

        sender_button = self.sender()
        if isinstance(sender_button, QPushButton):
            sender_button.setEnabled(False)
            sender_button.setText("Analizando...")

        self.main_event_loop.create_task(self._analyze_opportunity_async(opportunity))

    async def _analyze_opportunity_async(self, opportunity: Opportunity):
        if not self.user_id or not opportunity.id:
            self._handle_ai_analysis_error("User ID or Opportunity ID is missing.")
            return
        try:
            result = await self.api_client.analyze_opportunity_with_ai(
                opportunity_id=str(opportunity.id)
            )
            analysis_model = AIAnalysis.model_validate(result)
            temp_opportunity = opportunity.model_copy(deep=True)
            temp_opportunity.ai_analysis = analysis_model
            self._show_ai_analysis_dialog(temp_opportunity)
            await self._fetch_opportunities_async()
        except Exception as e:
            self._handle_ai_analysis_error(f"Error al procesar el resultado del análisis: {e}")

    def _show_ai_analysis_dialog(self, opportunity: Opportunity):
        if not opportunity.ai_analysis:
            QMessageBox.warning(self, "Error", "No hay datos de análisis de IA para esta oportunidad.")
            return
            
        logger.info(f"Showing AI analysis dialog for opportunity ID: {opportunity.id}")
        dialog = AIAnalysisDialog(opportunity, self)
        dialog.execute_trade_requested.connect(self._handle_execute_trade_request)
        dialog.reanalyze_requested.connect(self._handle_reanalyze_request)
        dialog.exec()

    def _handle_execute_trade_request(self, opportunity: Opportunity):
        logger.info(f"Received request to execute trade for opportunity ID: {opportunity.id}")
        if not self.user_id:
            QMessageBox.warning(self, "Error", "User ID not set. Cannot execute trade.")
            return

        from ultibot_ui.services.trading_mode_state import get_trading_mode_manager
        trading_mode_manager = get_trading_mode_manager()
        trading_mode = trading_mode_manager.current_mode.value
        self.main_event_loop.create_task(self._execute_trade_async(opportunity, trading_mode))

    async def _execute_trade_async(self, opportunity: Opportunity, trading_mode: str):
        # TODO: [LEADCODER-REFACTOR] La funcionalidad de confirmación de trades está deshabilitada temporalmente.
        if not opportunity.id:
            self._handle_execute_trade_error("Opportunity ID is missing.")
            return
        
        # El `trading_mode` se infiere del endpoint del backend, que es para trades 'real'.
        # La lógica de la UI puede querer diferenciar, pero la llamada a la API es específica.
        logger.info(f"Executing {trading_mode} trade for opportunity {opportunity.id} via confirmation endpoint.")

        try:
            # Usar el nuevo método unificado del API client
            result = await self.api_client.confirm_real_trade_opportunity(
                opportunity_id=str(opportunity.id)
            )
            self._handle_execute_trade_result(result)
        except APIError as e:
            self._handle_execute_trade_error(f"API Error ({e.status_code}): {e.message}")
        except Exception as e:
            self._handle_execute_trade_error(str(e))

    def _handle_reanalyze_request(self, opportunity: Opportunity):
        logger.info(f"Received request to re-analyze opportunity ID: {opportunity.id}")
        # Reutilizar la lógica de análisis existente
        self._analyze_opportunity_with_ai(opportunity)

    def _handle_execute_trade_result(self, result: dict):
        logger.info(f"Trade execution successful: {result}")
        trade_id = result.get("id", "N/A")
        QMessageBox.information(self, "Trade Executed", f"Trade executed successfully.\nTrade ID: {trade_id}")
        self.main_event_loop.create_task(self._fetch_opportunities_async())

    def _handle_execute_trade_error(self, error_message: str):
        logger.error(f"Error during trade execution: {error_message}")
        QMessageBox.critical(self, "Trade Execution Error", f"Could not execute trade.\nDetails: {error_message}")
        self.main_event_loop.create_task(self._fetch_opportunities_async())

    def _handle_ai_analysis_result(self, result: dict):
        """Este método ahora es un manejador de éxito genérico que abre el diálogo."""
        try:
            analysis_model = AIAnalysis.model_validate(result)
            # Aquí necesitaríamos la oportunidad original para mostrar el diálogo.
            # Esta ruta es ahora manejada directamente en la función de éxito de _analyze_opportunity_with_ai
            logger.info(f"AI analysis completed for opportunity: {analysis_model.analysis_id}")
            QMessageBox.information(self, "Análisis de IA Completado", "El análisis de IA se ha completado con éxito. La tabla se refrescará.")
            self.main_event_loop.create_task(self._fetch_opportunities_async())
        except Exception as e:
            self._handle_ai_analysis_error(f"Error al procesar el resultado del análisis: {e}")

    def _handle_ai_analysis_error(self, error_message: str):
        logger.error(f"Error during AI analysis: {error_message}")
        QMessageBox.warning(self, "AI Analysis Error", f"Could not complete AI analysis.\nDetails: {error_message}")
        self.main_event_loop.create_task(self._fetch_opportunities_async()) # Refresh the table to re-enable buttons

    def _handle_opportunities_error(self, error_message: str):
        logger.error(f"Error fetching opportunities: {error_message}")
        self.status_label.setText("Failed to load opportunities.")
        self.refresh_button.setEnabled(True)
        QMessageBox.warning(self, "Opportunities Error", f"Could not load trading opportunities.\nDetails: {error_message}")
        
        self.opportunities_table.setRowCount(1)
        error_item = QTableWidgetItem(f"Error loading data: {error_message}")
        error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opportunities_table.setItem(0, 0, error_item)
        self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())

    def cleanup(self):
        logger.info("Cleaning up OpportunitiesView...")
        if self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.stop()
        logger.info("OpportunitiesView cleanup finished.")

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    print("To test this view, please run it as part of the main application.")
