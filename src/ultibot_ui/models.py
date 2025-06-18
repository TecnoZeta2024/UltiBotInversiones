from PySide6.QtCore import QThread

class BaseMainWindow:
    """
    Clase base para type hinting de MainWindow y evitar importaciones circulares.
    """
    def add_thread(self, thread: QThread):
        raise NotImplementedError
