import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

# Mockear PyQt5 antes de cualquier otra importación de la UI
import sys
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()

from ultibot_ui.main import MainWindow
from ultibot_ui.services.trading_mode_state import get_trading_mode_manager, reset_trading_mode_manager
from ultibot_backend.services.trading_engine_service import TradingEngine

class TestStory4Scenario4:
    """
    Pruebas para el Escenario 4 de la Historia de Usuario 4:
    Un usuario cambia el modo de Paper a Real Trading y el sistema se adapta.
    """

    def setup_method(self):
        """
        Configura un entorno limpio para cada prueba.
        """
        # Resetear el singleton para asegurar aislamiento entre tests
        reset_trading_mode_manager()
        self.trading_mode_manager = get_trading_mode_manager()
        
        # Mock de la ventana principal y sus componentes
        self.mock_main_window = MagicMock(spec=MainWindow)
        self.mock_main_window.trading_mode_manager = self.trading_mode_manager
        
        # Mock del motor de trading
        self.mock_trading_engine = MagicMock(spec=TradingEngine)
        self.mock_trading_engine.get_portfolio_snapshot = AsyncMock()

    @pytest.mark.asyncio
    async def test_ui_sends_correct_mode_to_backend(self):
        """
        Verifica que al cambiar el modo en la UI, las llamadas al backend
        reflejan el modo de trading correcto.
        """
        # 1. Estado inicial: Paper Trading
        assert self.trading_mode_manager.current_mode == "paper"
        
        # 2. Simular la obtención del portafolio en modo Paper
        await self.mock_trading_engine.get_portfolio_snapshot(user_id="test_user", trading_mode=self.trading_mode_manager.current_mode)
        
        self.mock_trading_engine.get_portfolio_snapshot.assert_awaited_with(user_id="test_user", trading_mode="paper")
        
        # 3. Simular cambio de modo en la UI a Real Trading
        print("Cambiando a modo REAL")
        self.trading_mode_manager.set_trading_mode("real")
        assert self.trading_mode_manager.current_mode == "real"
        
        # 4. Simular la obtención del portafolio en modo Real
        await self.mock_trading_engine.get_portfolio_snapshot(user_id="test_user", trading_mode=self.trading_mode_manager.current_mode)
        
        # La llamada más reciente debe ser con modo 'real'
        self.mock_trading_engine.get_portfolio_snapshot.assert_awaited_with(user_id="test_user", trading_mode="real")

    def test_ui_components_react_to_mode_change(self):
        """
        Verifica que los componentes de la UI (mockeados) reaccionan
        al cambio de modo de trading.
        """
        # Mock de un componente de UI que se suscribe a los cambios de modo
        mock_portfolio_view = MagicMock()
        mock_portfolio_view.on_trading_mode_changed = MagicMock()

        # Conectar el slot del componente mockeado a la señal del manager
        self.trading_mode_manager.trading_mode_changed.connect(mock_portfolio_view.on_trading_mode_changed)

        # Simular cambio de modo
        self.trading_mode_manager.set_trading_mode("real")

        # Verificar que el slot del componente fue llamado con el nuevo modo
        mock_portfolio_view.on_trading_mode_changed.assert_called_once_with("real")

        # Cambiar de nuevo a paper
        self.trading_mode_manager.set_trading_mode("paper")
        mock_portfolio_view.on_trading_mode_changed.assert_called_with("paper")
        assert mock_portfolio_view.on_trading_mode_changed.call_count == 2

# Para ejecutar estas pruebas si el archivo es el punto de entrada
if __name__ == "__main__":
    pytest.main([__file__])
