"""
Módulo que define la clase base para todos los ViewModels de la interfaz de usuario.
Implementa la lógica común para la gestión de propiedades y la comunicación con la vista.
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import Any, Dict, Optional, Callable, Awaitable
import asyncio

class BaseViewModel(QObject):
    """
    Clase base abstracta para todos los ViewModels.
    Proporciona funcionalidad para la gestión de propiedades reactivas y la ejecución de comandos.
    """
    property_changed = pyqtSignal(str, object)
    error_occurred = pyqtSignal(str)
    command_executed = pyqtSignal(str, bool, object)

    def __init__(self, parent: Optional[QObject] = None):
        """
        Inicializa el BaseViewModel.

        Args:
            parent (Optional[QObject]): El objeto padre de PyQt.
        """
        super().__init__(parent)
        self._properties: Dict[str, Any] = {}
        self._commands: Dict[str, Callable[..., Awaitable[Any]]] = {}

    def _set_property(self, name: str, value: Any) -> None:
        """
        Establece el valor de una propiedad y emite la señal property_changed si el valor cambia.

        Args:
            name (str): El nombre de la propiedad.
            value (Any): El nuevo valor de la propiedad.
        """
        if name not in self._properties or self._properties[name] != value:
            self._properties[name] = value
            self.property_changed.emit(name, value)

    def _get_property(self, name: str, default: Any = None) -> Any:
        """
        Obtiene el valor de una propiedad.

        Args:
            name (str): El nombre de la propiedad.
            default (Any): Valor por defecto si la propiedad no existe.

        Returns:
            Any: El valor de la propiedad.
        """
        return self._properties.get(name, default)

    def register_command(self, name: str, command_func: Callable[..., Awaitable[Any]]) -> None:
        """
        Registra una función asíncrona como un comando.

        Args:
            name (str): El nombre del comando.
            command_func (Callable[..., Awaitable[Any]]): La función asíncrona a ejecutar.
        """
        self._commands[name] = command_func

    @pyqtSlot(str, object)
    def execute_command(self, command_name: str, *args: Any) -> None:
        """
        Ejecuta un comando registrado de forma asíncrona.

        Args:
            command_name (str): El nombre del comando a ejecutar.
            *args (Any): Argumentos para pasar al comando.
        """
        if command_name in self._commands:
            command_func = self._commands[command_name]
            asyncio.create_task(self._run_command_async(command_name, command_func, *args))
        else:
            self.error_occurred.emit(f"Comando '{command_name}' no registrado.")
            self.command_executed.emit(command_name, False, None)

    async def _run_command_async(self, command_name: str, command_func: Callable[..., Awaitable[Any]], *args: Any) -> None:
        """
        Ejecuta la función del comando de forma asíncrona y maneja los resultados/errores.
        """
        try:
            result = await command_func(*args)
            self.command_executed.emit(command_name, True, result)
        except Exception as e:
            self.error_occurred.emit(f"Error al ejecutar comando '{command_name}': {e}")
            self.command_executed.emit(command_name, False, str(e))

    async def _do_refresh(self) -> None:
        """
        Método de plantilla para ser sobrescrito por subclases para la lógica de refresco de datos.
        """
        pass

    @pyqtSlot()
    def refresh_data(self) -> None:
        """
        Inicia el proceso de refresco de datos de forma asíncrona.
        """
        asyncio.create_task(self._do_refresh())
