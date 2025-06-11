from PyQt5.QtCore import QObject
import asyncio
from typing import Callable, Coroutine

class BaseMainWindow(QObject):
    """
    Clase base para type hinting de MainWindow y evitar importaciones circulares.
    Define la interfaz esperada que otros componentes pueden usar.
    """
    def submit_task(self, coro: Coroutine, on_success: Callable, on_error: Callable):
        """
        Envía una corutina para ser ejecutada en el pool de hilos.

        Args:
            coro: La corutina a ejecutar.
            on_success: Callback a ejecutar en caso de éxito. Recibe el futuro completado.
            on_error: Callback a ejecutar en caso de error. Recibe el futuro completado.
        """
        raise NotImplementedError

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """
        Retorna el bucle de eventos de asyncio en uso.
        """
        raise NotImplementedError
