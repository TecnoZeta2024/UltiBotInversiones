import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from PySide6.QtCore import QThread  # pylint: disable=no-name-in-module  # Falso positivo: PySide6 módulos compilados

from ultibot_ui.views.trading_terminal_view import TradingTerminalView
from ultibot_ui.services.api_client import UltiBotAPIClient
from ultibot_ui.workers import TradingTerminalWorker, ApiWorker

# Test para verificar la inicialización y limpieza de TradingTerminalView
@pytest.mark.asyncio
async def test_trading_terminal_view_cleanup(qapp, mock_api_client, event_loop):
    # Crear la vista
    view = TradingTerminalView(api_client=mock_api_client)
    view.show()

    # Simular un breve período de actividad para que los hilos se inicien
    await asyncio.sleep(0.1) # Dar tiempo para que el hilo de price_feed se inicie

    # Verificar que el hilo de price_feed se haya iniciado
    assert view.worker_thread is not None
    assert view.worker_thread.isRunning()
    assert view.price_worker is not None

    # Simular la creación de un hilo de orden (sin iniciar el worker real)
    # Esto es para asegurar que la limpieza maneje múltiples hilos
    mock_order_thread = MagicMock(spec=QThread)
    mock_order_thread.isRunning.return_value = True
    mock_order_thread.objectName.return_value = "MockOrderThread"
    mock_order_thread.quit = MagicMock()
    mock_order_thread.wait = MagicMock(return_value=True)
    
    # Parchear QThread para que no se elimine automáticamente en el test
    with patch('PySide6.QtCore.QThread.deleteLater'):
        view.thread_created.emit(mock_order_thread) # Emitir la señal para que MainWindow lo capture

        # Llamar al método cleanup de la vista
        view.cleanup()

        # Verificar que el price_worker haya recibido la señal de stop
        assert view.price_worker is None # Debería ser None después de cleanup
        assert view.worker_thread is None # Debería ser None después de cleanup

        # Verificar que el mock_order_thread no haya sido quitado por la vista
        # La vista solo debe emitir la señal, MainWindow es quien lo quita
        mock_order_thread.quit.assert_not_called()
        mock_order_thread.wait.assert_not_called()

    # Simular el cierre de la aplicación (esto lo haría MainWindow)
    # Aquí es donde MainWindow llamaría a quit() y wait() en los hilos rastreados.
    # Para este test unitario, solo nos enfocamos en la vista.
    # La prueba de MainWindow se haría en un test de integración.

    # Asegurarse de que no haya errores de objetos C++ eliminados al final del test
    # Esto se verifica implícitamente si el test no lanza un RuntimeError.
    print("Test de limpieza de TradingTerminalView completado sin RuntimeError.")

    # Cerrar la vista
    view.close()
    await asyncio.sleep(0.05) # Pequeña pausa para que Qt procese el cierre
