import logging
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget, QSpacerItem
from PySide6.QtCore import Qt, Signal as pyqtSignal, QRunnable, QThreadPool, QObject
from ultibot_backend.core.domain_models.opportunity_models import Opportunity, OpportunityStatus, AIAnalysis
from PySide6.QtGui import QFont, QColor, QPalette
from typing import Any, Optional, Callable, Coroutine # Importar Callable, Coroutine, Optional
import asyncio

from shared.data_types import Opportunity, OpportunityStatus
from ultibot_ui.services.api_client import UltiBotAPIClient

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """
    Define las señales disponibles de un QRunnable worker.
    """
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)

class Worker(QRunnable):
    """
    Worker para ejecutar una función asíncrona en el bucle de eventos principal.
    """
    def __init__(self, fn: Callable[..., Coroutine[Any, Any, Any]], main_event_loop: asyncio.AbstractEventLoop, *args: Any, **kwargs: Any):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.main_event_loop = main_event_loop

    def run(self):
        """
        Programa la corrutina en el bucle de eventos principal y espera su resultado.
        """
        future = asyncio.run_coroutine_threadsafe(self.fn(*self.args, **self.kwargs), self.main_event_loop)
        try:
            result = future.result() # Espera a que la corrutina termine
            self.signals.result.emit(result)
        except Exception as e:
            logger.error(f"Error en worker asíncrono: {e}", exc_info=True)
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()

class RealTradeConfirmationDialog(QDialog):
    """
    Diálogo de confirmación para operaciones de trading real.
    Muestra los detalles de la oportunidad y solicita la confirmación del usuario.
    """
    trade_confirmed = pyqtSignal(str) # Emite el opportunity_id al confirmar
    trade_cancelled = pyqtSignal(str) # Emite el opportunity_id al cancelar

    def __init__(self, opportunity: Opportunity, api_client: UltiBotAPIClient, main_event_loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.opportunity = opportunity
        self.api_client = api_client
        self.main_event_loop = main_event_loop # Guardar la referencia al bucle de eventos
        self.user_id = opportunity.user_id # Asumimos que el user_id está en la oportunidad
        self.setWindowTitle("Confirmación de Operación REAL")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint) # Eliminar botón de ayuda

        self._setup_ui()
        self._populate_data()
        self._apply_styles()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        title_label = QLabel("¡ATENCIÓN! Confirmar Operación de Trading REAL")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Detalles de la operación
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)

        self._add_detail_row(details_layout, "Par de Trading:", self.opportunity.symbol)
        suggested_action = "N/A"
        if self.opportunity.ai_analysis and self.opportunity.ai_analysis.suggested_action:
            suggested_action = self.opportunity.ai_analysis.suggested_action.value
        self._add_detail_row(details_layout, "Dirección:", suggested_action)
        
        confidence_str = "N/A"
        if self.opportunity.ai_analysis and self.opportunity.ai_analysis.calculated_confidence is not None:
            confidence_score = self.opportunity.ai_analysis.calculated_confidence
            confidence_str = f"{confidence_score:.2%}"
            if confidence_score < 0.5:
                self._add_detail_row(details_layout, "Confianza IA:", QLabel(f"<b style=\"color: red;\">{confidence_str} (Baja)</b>"))
            else:
                self._add_detail_row(details_layout, "Confianza IA:", QLabel(f"<b style=\"color: lightgreen;\">{confidence_str} (Alta)</b>"))
        else:
            self._add_detail_row(details_layout, "Confianza IA:", confidence_str)

        entry_price_str = "N/A"
        if self.opportunity.initial_signal and self.opportunity.initial_signal.entry_price_target is not None:
            entry_price_str = f"{self.opportunity.initial_signal.entry_price_target:.4f}"
        self._add_detail_row(details_layout, "Precio Estimado de Entrada:", entry_price_str)
        
        # Placeholder para cantidad calculada (se llenará en _populate_data si es posible)
        self.calculated_quantity_label = QLabel("Calculando...")
        self._add_detail_row(details_layout, "Cantidad a Operar:", self.calculated_quantity_label)

        # Resumen de IA
        if self.opportunity.ai_analysis and self.opportunity.ai_analysis.reasoning_ai:
            reasoning_label = QLabel("<b>Resumen de Análisis de IA:</b>")
            reasoning_text = QLabel(self.opportunity.ai_analysis.reasoning_ai)
            reasoning_text.setWordWrap(True)
            details_layout.addWidget(reasoning_label)
            details_layout.addWidget(reasoning_text)

        main_layout.addLayout(details_layout)

        main_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Mensaje de advertencia
        warning_label = QLabel("Esta operación utilizará FONDOS REALES. Asegúrese de comprender los riesgos.")
        warning_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        warning_label.setStyleSheet("color: #FF6347;") # Tomato color for warning
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(warning_label)

        main_layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch(1)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(self.cancel_button)

        self.confirm_button = QPushButton("Confirmar y Ejecutar Operación REAL")
        self.confirm_button.clicked.connect(self._start_confirm_trade_worker) # Conectar a la función que inicia el worker
        self.confirm_button.setStyleSheet("background-color: #28a745; color: white;") # Green for confirm
        buttons_layout.addWidget(self.confirm_button)

        buttons_layout.addStretch(1)
        main_layout.addLayout(buttons_layout)

        self.loading_indicator = QLabel("Procesando...")
        self.loading_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_indicator.setStyleSheet("color: #17a2b8; font-weight: bold;") # Info color
        self.loading_indicator.hide()
        main_layout.addWidget(self.loading_indicator)

    def _add_detail_row(self, layout: QVBoxLayout, label_text: str, value_widget_or_text: Any):
        row_layout = QHBoxLayout()
        label = QLabel(f"<b>{label_text}</b>")
        row_layout.addWidget(label)
        row_layout.addStretch(1)
        if isinstance(value_widget_or_text, QWidget):
            row_layout.addWidget(value_widget_or_text)
        else:
            value_label = QLabel(str(value_widget_or_text))
            row_layout.addWidget(value_label)
        layout.addLayout(row_layout)

    def _populate_data(self):
        # La cantidad no está en el modelo Opportunity, se calcula en el backend.
        self.calculated_quantity_label.setText("N/A (Calculado en Backend)")
        logger.warning(f"Cantidad a operar no disponible en la oportunidad {self.opportunity.id} para mostrar en el diálogo. Se determinará en el backend.")

    def _apply_styles(self):
        # Aplicar estilos generales del tema oscuro si QDarkStyleSheet está activo
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b")) # Fondo oscuro
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff")) # Texto blanco
        self.setPalette(palette)

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QLabel#title_label {
                font-size: 16px;
                font-weight: bold;
                color: #17a2b8; /* Info color */
            }
            QPushButton {
                background-color: #007bff; /* Primary blue */
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton#cancel_button {
                background-color: #6c757d; /* Secondary grey */
            }
            QPushButton#cancel_button:hover {
                background-color: #545b62;
            }
            QPushButton#confirm_button {
                background-color: #28a745; /* Success green */
            }
            QPushButton#confirm_button:hover {
                background-color: #218838;
            }
        """)

    def _start_confirm_trade_worker(self):
        self.confirm_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.loading_indicator.show()
        logger.info(f"Usuario confirmó operación real para oportunidad {self.opportunity.id}. Iniciando worker.")

        worker = Worker(self._on_confirm_async, self.main_event_loop)
        worker.signals.result.connect(self._handle_confirm_result)
        worker.signals.error.connect(self._handle_confirm_error)
        worker.signals.finished.connect(self._handle_confirm_finished)
        QThreadPool.globalInstance().start(worker)

    async def _on_confirm_async(self):
        """
        Función asíncrona que realiza la llamada a la API.
        Esta será ejecutada por el Worker.
        """
        if not self.opportunity.id:
            raise ValueError("ID de oportunidad no puede ser nulo para confirmar el trade.")
            
        response = await self.api_client.confirm_real_trade_opportunity(
            opportunity_id=self.opportunity.id
        )
        return response

    def _handle_confirm_result(self, result):
        logger.info(f"Respuesta del backend al confirmar trade: {result}")
        self.trade_confirmed.emit(str(self.opportunity.id))
        self.accept() # Cierra el diálogo con QDialog.Accepted

    def _handle_confirm_error(self, error_message: str):
        logger.error(f"Error al confirmar operación real para oportunidad {self.opportunity.id}: {error_message}")
        self.loading_indicator.setText(f"Error: {error_message}")
        self.loading_indicator.setStyleSheet("color: #dc3545; font-weight: bold;") # Danger color
        self.confirm_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        # Opcional: Mostrar un QMessageBox más amigable

    def _handle_confirm_finished(self):
        self.loading_indicator.hide()
        # Los botones se re-habilitan en _handle_confirm_error si hay un error.
        # Si no hay error, el diálogo se cierra con self.accept().

    def _on_cancel(self):
        logger.info(f"Usuario canceló operación real para oportunidad {self.opportunity.id}.")
        self.trade_cancelled.emit(str(self.opportunity.id))
        self.reject() # Cierra el diálogo con QDialog.Rejected

    # Método para simular la obtención de la cantidad calculada (si fuera necesario)
    async def _fetch_calculated_quantity(self):
        # Esto es un placeholder. En un escenario real, se llamaría a un endpoint
        # que devuelva la cantidad calculada sin ejecutar la orden.
        # Por ahora, solo simula un retraso y actualiza el label.
        await asyncio.sleep(0.5) # Simular llamada a API
        simulated_quantity = 0.00123456 # Ejemplo
        if self.opportunity.symbol is not None:
            self.calculated_quantity_label.setText(f"{simulated_quantity:.8f} {self.opportunity.symbol.split('/')[0]}")
        else:
            self.calculated_quantity_label.setText(f"{simulated_quantity:.8f} N/A")
