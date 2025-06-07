from PyQt5.QtCore import QObject, QThread

class BaseMainWindow(QObject):
    """
    Clase base para type hinting de MainWindow y evitar importaciones circulares.
    """
    def add_thread(self, thread: QThread):
        raise NotImplementedError
