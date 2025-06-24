import asyncio
import logging
from typing import Optional, Callable, Coroutine

from PySide6.QtCore import QObject, Signal, Slot

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class ApiWorker(QObject):
    """
    Worker que ejecuta una corutina de API en un hilo separado, integrándose
    correctamente con el event loop de qasync.
    """
    result_ready = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self,
                 api_client: UltiBotAPIClient, # Cambiar a api_client
                 coroutine_factory: Optional[Callable[[UltiBotAPIClient], Coroutine]] = None):
        super().__init__()
        self.api_client = api_client # Usar la instancia de api_client
        self.coroutine_factory = coroutine_factory
        logger.debug(f"ApiWorker initialized with api_client: {api_client}, coroutine_factory: {'set' if coroutine_factory else 'not set'}")

    @Slot()
    def run(self):
        """
        Ejecuta la corutina de la API en un nuevo bucle de eventos
        dentro del hilo del worker.
        """
        logger.debug("ApiWorker: run method started.")
        if not self.coroutine_factory:
            logger.error("ApiWorker: coroutine_factory not set. Cannot run task.")
            self.error_occurred.emit("Error interno del Worker: Tarea no configurada.")
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Usar la instancia de api_client inyectada
        api_client = self.api_client

        try:
            # El cliente de API ya debe estar inicializado por la aplicación principal.
            logger.debug("ApiWorker: Creating coroutine from factory.")
            coroutine = self.coroutine_factory(api_client)
            logger.debug(f"ApiWorker: Coroutine created: {coroutine}. Running in event loop.")
            
            result = loop.run_until_complete(coroutine)
            
            logger.debug(f"ApiWorker: Coroutine finished. Result: {result}")
            self.result_ready.emit(result)
            logger.debug("ApiWorker: result_ready signal emitted.")
        except APIError as e_api:
            logger.error(f"ApiWorker: APIError: {e_api}", exc_info=True)
            self.error_occurred.emit(f"Error de API ({e_api.status_code}): {e_api.message}")
        except Exception as exc:
            logger.error(f"ApiWorker: Generic Exception: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
        finally:
            logger.debug("ApiWorker: Task finished, emitting 'finished' signal.")
            self.finished.emit()
            logger.debug("ApiWorker: run method finished.")
            # Cerrar el event loop creado en este hilo
            loop.close()


class StrategiesWorker(QObject):
    """
    Worker to fetch trading strategies asynchronously.
    """
    finished = Signal()
    strategies_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, parent=None): # Cambiar a api_client
        super().__init__(parent)
        self.api_client = api_client # Usar la instancia de api_client

    async def _fetch_strategies(self, api_client: UltiBotAPIClient):
        """Async method to get strategies."""
        # En el futuro, esto llamará a un endpoint real como:
        # return await api_client.get_strategies()
        
        logger.info("Fetching mock strategies...")
        await asyncio.sleep(1) # Simulate network delay
        mock_strategies = [
            {'id': 'strat_1', 'name': 'Momentum Breakout'},
            {'id': 'strat_2', 'name': 'Mean Reversion ETH'},
            {'id': 'strat_3', 'name': 'AI-Based Signal'},
        ]
        logger.info("Mock strategies fetched.")
        return mock_strategies

    @Slot()
    def run(self):
        """
        Executes the strategy fetching task in an event loop.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Usar la instancia de api_client inyectada
        api_client = self.api_client
        
        try:
            # El cliente de API ya debe estar inicializado por la aplicación principal.
            strategies = loop.run_until_complete(self._fetch_strategies(api_client))
            self.strategies_ready.emit(strategies)
        except Exception as e:
            logger.error(f"Error in StrategiesWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
            logger.info("StrategiesWorker finished.")
            # Cerrar el event loop creado en este hilo
            loop.close()


class PerformanceWorker(QObject):
    """
    Worker to fetch performance data asynchronously.
    """
    finished = Signal()
    performance_data_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client

    async def _fetch_performance_data(self):
        """Async method to get performance data."""
        # In a future step, this will be replaced with real API calls.
        logger.info("Fetching mock performance data...")
        await asyncio.sleep(1.5) # Simulate network delay
        
        mock_data = {
            "portfolio_evolution": [(0, 10000), (1, 10500), (2, 10300), (3, 10800), (4, 11200), (5, 11100)],
            "pnl_by_period": [200, -50, 150, 80, -30, 120],
            "metrics": {
                "sharpe_ratio": "1.85",
                "max_drawdown": "12.5%",
                "win_rate": "62%"
            }
        }
        logger.info("Mock performance data fetched.")
        return mock_data

    @Slot()
    def run(self):
        """
        Executes the performance data fetching task in an event loop.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            data = loop.run_until_complete(self._fetch_performance_data())
            self.performance_data_ready.emit(data)
        except Exception as e:
            logger.error(f"Error in PerformanceWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
            logger.info("PerformanceWorker finished.")
            # Cerrar el event loop creado en este hilo
            loop.close()


class OrdersWorker(QObject):
    """
    Worker to fetch order history asynchronously.
    """
    finished = Signal()
    orders_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client

    async def _fetch_orders(self):
        """Async method to get order history."""
        logger.info("Fetching mock order history...")
        await asyncio.sleep(0.5) # Simulate network delay
        
        mock_orders = [
            {'date': '2025-06-21 10:00:00', 'symbol': 'BTC/USDT', 'type': 'LIMIT', 'side': 'BUY', 'price': 60000.0, 'amount': 0.1, 'status': 'FILLED'},
            {'date': '2025-06-21 10:05:00', 'symbol': 'ETH/USDT', 'type': 'MARKET', 'side': 'BUY', 'price': 3500.0, 'amount': 2.0, 'status': 'FILLED'},
            {'date': '2025-06-21 10:15:00', 'symbol': 'BTC/USDT', 'type': 'LIMIT', 'side': 'SELL', 'price': 61000.0, 'amount': 0.1, 'status': 'CANCELED'},
        ]
        logger.info("Mock order history fetched.")
        return mock_orders

    @Slot()
    def run(self):
        """
        Executes the order fetching task in an event loop.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            orders = loop.run_until_complete(self._fetch_orders())
            self.orders_ready.emit(orders)
        except Exception as e:
            logger.error(f"Error in OrdersWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            loop.close() # Descomentado
            self.finished.emit()
            logger.info("OrdersWorker finished.")


class TradingTerminalWorker(QObject):
    """
    Worker to fetch real-time market data for the trading terminal.
    """
    price_updated = Signal(dict)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, symbol: str, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.symbol = symbol
        self._is_running = True

    async def _fetch_price_feed(self):
        """
        Simulates a real-time price feed. In a real implementation, this
        would connect to a WebSocket or use polling.
        """
        logger.info(f"Starting price feed for {self.symbol}...")
        base_price = 60000.0
        import random
        import time

        for i in range(30): # Simulate for 30 seconds
            if not self._is_running:
                break
            
            price = base_price + random.uniform(-100, 100)
            timestamp = time.time()
            
            self.price_updated.emit({'timestamp': timestamp, 'price': price})
            
            await asyncio.sleep(1) # Update every second

        logger.info(f"Price feed for {self.symbol} finished.")

    @Slot()
    def run(self):
        """
        Executes the price feed task in an event loop.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._fetch_price_feed())
        except Exception as e:
            logger.error(f"Error in TradingTerminalWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            loop.close() # Descomentado
            self.finished.emit()
            logger.info("TradingTerminalWorker finished.")

    def stop(self):
        self._is_running = False
        logger.info("TradingTerminalWorker stop requested.")
