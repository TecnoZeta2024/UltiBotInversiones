# src/ultibot_ui/dialogs/confirmation_dialog.py
"""
A generic confirmation dialog for critical actions.
"""
from PySide6.QtWidgets import ( # MODIFIED
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QDialogButtonBox,
    QWidget,
)
from PySide6.QtCore import Qt # MODIFIED

class ConfirmationDialog(QDialog):
    """
    A modal dialog to ask the user for confirmation before a critical action.
    """
    def __init__(
        self,
        title: str,
        message: str,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Message Label
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.setMinimumWidth(300)

    @staticmethod
    def ask(title: str, message: str, parent: QWidget = None) -> bool:
        """
        Static method to show the dialog and get the user's choice.

        Args:
            title: The title for the dialog window.
            message: The confirmation message to display to the user.
            parent: The parent widget.

        Returns:
            True if the user clicks 'Ok', False otherwise.
        """
        dialog = ConfirmationDialog(title, message, parent)
        return dialog.exec_() == QDialog.Accepted
