import logging
import os
from typing import Callable, Optional
from PySide6.QtWidgets import ( # MODIFIED
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QDialogButtonBox, QWidget, QHBoxLayout
)
from PySide6.QtCore import pyqtSignal, Qt, QObject, QThread # MODIFIED

# Importar ApiWorker para type hinting y uso.
from src.ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class LoginDialog(QDialog):
    """
    Diálogo para la autenticación de usuarios.
    """
    # Señal emitida cuando el login es exitoso, enviando el token de acceso
    login_successful = pyqtSignal(str)

    # Type hints para los botones para ayudar a Pylance
    login_button: QPushButton
    cancel_button: QPushButton
    admin_login_button: QPushButton

    def __init__(self, api_worker_factory: Callable[..., ApiWorker], parent: Optional[QWidget] = None):
        """
        Inicializa el diálogo de login.

        Args:
            api_worker_factory: Una función o factoría que puede crear instancias de ApiWorker.
            parent: Widget padre.
        """
        super().__init__(parent)
        self.setWindowTitle("Login - UltiBotInversiones")
        self.setModal(True)

        self.api_worker_factory = api_worker_factory
        self.thread: Optional[QThread] = None
        self.worker: Optional[ApiWorker] = None

        # --- Layout y Widgets ---
        layout = QVBoxLayout(self)

        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("tuemail@example.com")
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        self.password_label = QLabel("Contraseña:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Botones
        button_layout = QHBoxLayout()
        self.admin_login_button = QPushButton("Admin Login")
        self.admin_login_button.setStyleSheet("background-color: #4CAF50; color: white;") # Estilo verde
        button_layout.addWidget(self.admin_login_button)
        button_layout.addStretch()

        self.button_box = QDialogButtonBox()
        self.login_button = self.button_box.addButton("Login", QDialogButtonBox.AcceptRole)
        self.cancel_button = self.button_box.addButton(QDialogButtonBox.Cancel)
        button_layout.addWidget(self.button_box)
        
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # --- Conexiones ---
        self.login_button.clicked.connect(self.attempt_login)
        self.admin_login_button.clicked.connect(self.admin_login)
        self.cancel_button.clicked.connect(self.reject)

        # Conectar Enter en campos de texto al botón de login
        self.email_input.returnPressed.connect(self.login_button.click)
        self.password_input.returnPressed.connect(self.login_button.click)
        
        self.setMinimumWidth(300) # Ajustar el ancho mínimo

    def admin_login(self):
        """
        Rellena los campos con las credenciales de administrador del .env y intenta el login.
        """
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not admin_email or not admin_password:
            QMessageBox.warning(self, "Error de Configuración", "Las credenciales de administrador no están configuradas en el archivo .env.")
            return
        
        self.email_input.setText(admin_email)
        self.password_input.setText(admin_password)
        self.attempt_login()

    def attempt_login(self):
        """
        Intenta autenticar al usuario usando el ApiWorker en un hilo separado.
        """
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Campos incompletos", "Por favor, ingrese su email y contraseña.")
            return

        logger.info(f"Iniciando intento de login para el usuario: {email}")
        self.login_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

        # Crear la corutina de login
        login_coro_factory = lambda client: client.login(email, password)

        # Crear el worker y el hilo, manteniendo las referencias
        self.worker = self.api_worker_factory(coroutine_factory=login_coro_factory)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # Conectar señales
        self.worker.result_ready.connect(self.on_login_result)
        self.worker.error_occurred.connect(self.on_login_error)
        
        # Limpieza cuando el hilo termina
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.cleanup_thread_and_worker)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def on_login_result(self, token: str):
        """Manejador para la señal result_ready del ApiWorker."""
        logger.info("LoginDialog: Señal de login exitoso recibida del worker.")
        if self.thread:
            self.thread.quit()
        self.login_successful.emit(token)
        self.accept()

    def on_login_error(self, error_message: str):
        """Manejador para la señal error_occurred del ApiWorker."""
        logger.warning(f"LoginDialog: Señal de login fallido recibida: {error_message}")
        if self.thread:
            self.thread.quit()
        QMessageBox.warning(self, "Login Fallido", f"No se pudo iniciar sesión:\n{error_message}")
        self.login_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.email_input.setFocus()

    def cleanup_thread_and_worker(self):
        """Limpia las referencias al hilo y al worker."""
        logger.debug("Cleaning up thread and worker references.")
        self.worker = None
        self.thread = None

    def reject(self):
        """Sobrescribe reject para asegurar que el hilo se detenga si está en ejecución."""
        logger.info("Diálogo de login cancelado por el usuario.")
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(1000)
        super().reject()

    def closeEvent(self, event):
        """Maneja el evento de cierre del diálogo (ej. click en la 'X')."""
        self.reject()
        event.accept()

# El bloque de prueba __main__ ha sido eliminado para centrarse en la integración real.
