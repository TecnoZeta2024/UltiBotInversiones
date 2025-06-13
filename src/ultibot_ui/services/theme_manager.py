"""
Módulo que gestiona la aplicación de temas QSS a la interfaz de usuario.
Permite cambiar dinámicamente entre diferentes temas (oscuro, claro, etc.).
"""

from PyQt6.QtCore import QObject, pyqtSignal, QFile, QTextStream
from PyQt6.QtWidgets import QApplication
from typing import Dict, Optional

class ThemeManager(QObject):
    """
    Gestiona la carga y aplicación de temas QSS a la aplicación PyQt.
    """
    theme_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None):
        """
        Inicializa el ThemeManager.

        Args:
            parent (Optional[QObject]): El objeto padre de PyQt.
        """
        super().__init__(parent)
        self._current_theme: str = "dark"
        # Mapeo de nombres de tema a rutas de archivo QSS (usando el sistema de recursos de Qt)
        self._themes: Dict[str, str] = {
            "dark": ":/themes/dark_theme.qss",
            "light": ":/themes/light_theme.qss"
        }

    @property
    def current_theme(self) -> str:
        """
        Obtiene el nombre del tema actualmente aplicado.
        """
        return self._current_theme

    def apply_theme(self, theme_name: str) -> bool:
        """
        Aplica un tema QSS a la aplicación.

        Args:
            theme_name (str): El nombre del tema a aplicar ("dark" o "light").

        Returns:
            bool: True si el tema se aplicó exitosamente, False en caso contrario.
        """
        if theme_name not in self._themes:
            print(f"Error: Tema '{theme_name}' no encontrado.")
            return False

        qss_path = self._themes[theme_name]
        qss_content = self._load_qss_file(qss_path)

        if qss_content:
            QApplication.instance().setStyleSheet(qss_content)
            self._current_theme = theme_name
            self.theme_changed.emit(theme_name)
            print(f"Tema '{theme_name}' aplicado exitosamente.")
            return True
        else:
            print(f"Error: No se pudo cargar el archivo QSS para el tema '{theme_name}' en {qss_path}.")
            return False

    def _load_qss_file(self, path: str) -> Optional[str]:
        """
        Carga el contenido de un archivo QSS desde el sistema de recursos de Qt.

        Args:
            path (str): La ruta del archivo QSS en el sistema de recursos (ej. ":/themes/dark_theme.qss").

        Returns:
            Optional[str]: El contenido del archivo QSS como string, o None si falla.
        """
        file = QFile(path)
        if not file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            print(f"Error: No se pudo abrir el archivo QSS: {path} - {file.errorString()}")
            return None
        
        stream = QTextStream(file)
        content = stream.readAll()
        file.close()
        return content
