import asyncio
import logging
from typing import Optional, Callable, Coroutine, List, cast
from uuid import UUID

import PySide6.QtCore as QtCore

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from shared.data_types import Trade, PerformanceMetrics, Ticker
from decimal import Decimal

logger = logging.getLogger(__name__)

class ApiWorker(QtCore.QObject):
    """
    Worker que ejecuta una corutina de API de forma segura en el bucle de eventos
    principal de la aplicación (qasync), evitando conflictos de hilos.
    """
    result_ready = QtCore.Signal(object)
    error_occurred = QtCore.Signal(str)
    finished = QtCore.Signal()

    def __init__(self,
                 api_client: UltiBotAPIClient,
                 coroutine_factory: Optional[Callable[[UltiBotAPIClient], Coroutine]] = None):
        super().__init__()
        self.api_client = api_client
        self.coroutine_factory = coroutine_factory
        self._task: Optional[asyncio.Task] = None # Usar asyncio.Task
        logger.debug(f"ApiWorker initialized with api_client: {api_client}, coroutine_factory: {'set' if coroutine_factory else 'not set'}")

    @QtCore.Slot()
    def run(self):
        """
        Programa la corutina para que se ejecute en el bucle de eventos de asyncio
        principal de la aplicación.
        """
        logger.debug("ApiWorker: run method started in thread %s.", QtCore.QThread.currentThread().objectName() or str(QtCore.QThread.currentThread()))
        
        if not self.coroutine_factory:
            logger.error("ApiWorker: coroutine_factory not set. Cannot run task.")
            self.error_occurred.emit("Error interno del Worker: Tarea no configurada.")
            self.finished.emit()
            return

        try:
            coroutine = self.coroutine_factory(self.api_client)
            # Obtener el bucle de eventos principal y programar la corutina en él
            main_loop = asyncio.get_event_loop()
            self._task = cast(asyncio.Task, asyncio.run_coroutine_threadsafe(coroutine, main_loop)) # Cast a asyncio.Task
            self._task.add_done_callback(self._on_task_done)
            # self._task es un asyncio.Future aquí, no un Task, por lo que no tiene get_name().
            # El nombre se maneja correctamente en _on_task_done.
            logger.debug("ApiWorker: Coroutine scheduled on the main event loop.")
        except Exception as exc:
            logger.error(f"ApiWorker: Failed to schedule task: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
            self.finished.emit()

    def _on_task_done(self, future: asyncio.Future): # future es un asyncio.Future
        """
        Callback que se ejecuta en el hilo principal cuando la tarea de asyncio finaliza.
        """
        # future puede ser un Task o un Future. get_name() es un método de Task.
        task_name = future.get_name() if isinstance(future, asyncio.Task) else f"Future-{id(future)}"
        logger.debug(f"ApiWorker: Task {task_name} finished.")
        try:
            result = future.result()
            self.result_ready.emit(result)
            logger.debug("ApiWorker: result_ready signal emitted.")
        except asyncio.CancelledError:
            logger.info("ApiWorker: Task was cancelled.")
            self.error_occurred.emit("Operación cancelada.")
        except APIError as e_api:
            logger.error(f"ApiWorker: APIError: {e_api}", exc_info=True)
            self.error_occurred.emit(f"Error de API ({e_api.status_code}): {e_api.message}")
        except Exception as exc:
            logger.error(f"ApiWorker: Generic Exception in task: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
        finally:
            logger.debug("ApiWorker: Emitting 'finished' signal.")
            self.finished.emit()

    def stop(self):
        """
        Solicita la cancelación de la tarea de asyncio si se está ejecutando.
        """
        if self._task and not self._task.done():
            # Programar la cancelación en el bucle de eventos principal
            main_loop = asyncio.get_event_loop()
            main_loop.call_soon_threadsafe(self._task.cancel)
            logger.info("ApiWorker: Async task cancellation requested via threadsafe call.")
        else:
            logger.info("ApiWorker: No active task to cancel.")


class StrategiesWorker(QtCore.QObject):
    """
    Worker to fetch trading strategies asynchronously.
    """
    finished = QtCore.Signal()
    strategies_ready = QtCore.Signal(list)
    error_occurred = QtCore.Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, main_event_loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.main_event_loop = main_event_loop
        self._task: Optional[asyncio.Task] = None # Usar asyncio.Task

    async def _fetch_strategies(self):
        """Async method to get strategies."""
        logger.info("Fetching real strategies from API...")
        strategies = await self.api_client.get_strategies()
        logger.info(f"Fetched {len(strategies)} strategies from API.")
        return strategies

    @QtCore.Slot()
    def run(self):
        """
        Programa la corutina para que se ejecute en el bucle de eventos de asyncio
        principal de la aplicación.
        """
        logger.debug("StrategiesWorker: run method started in thread %s.", QtCore.QThread.currentThread().objectName() or str(QtCore.QThread.currentThread()))
        
        if not self.main_event_loop:
            logger.error("StrategiesWorker: No se encontró el bucle de eventos principal. No se puede programar la tarea.")
            self.error_occurred.emit("Error interno del Worker: Bucle de eventos no disponible.")
            self.finished.emit()
            return

        try:
            coroutine = self._fetch_strategies()
            self._task = cast(asyncio.Task, asyncio.run_coroutine_threadsafe(coroutine, self.main_event_loop)) # Usar el bucle de eventos pasado
            self._task.add_done_callback(self._on_task_done)
            logger.debug("StrategiesWorker: Coroutine scheduled on the main event loop.")
        except Exception as e:
            logger.error(f"Error scheduling StrategiesWorker task: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
            self.finished.emit()

    def _on_task_done(self, future: asyncio.Future):
        """Callback executed when the async task is done."""
        try:
            strategies = future.result()
            self.strategies_ready.emit(strategies)
        except asyncio.CancelledError:
            logger.info("StrategiesWorker: Task was cancelled.")
            self.error_occurred.emit("Operación cancelada.")
        except Exception as e:
            logger.error(f"Error in StrategiesWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
            logger.info("StrategiesWorker finished.")

    def stop(self):
        """
        Solicita la cancelación de la tarea de asyncio si se está ejecutando.
        """
        if self._task and not self._task.done():
            main_loop = asyncio.get_event_loop()
            main_loop.call_soon_threadsafe(self._task.cancel)
            logger.info("StrategiesWorker: Async task cancellation requested via threadsafe call.")
        else:
            logger.info("StrategiesWorker: No active task to cancel.")


class PerformanceWorker(QtCore.QObject):
    """
    Worker to fetch performance data asynchronously.
    """
    finished = QtCore.Signal()
    performance_data_ready = QtCore.Signal(dict)
    error_occurred = QtCore.Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, user_id: UUID, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.user_id = user_id
        self._task: Optional[asyncio.Task] = None # Usar asyncio.Task

    async def _fetch_performance_data(self):
        """Async method to get performance data."""
        logger.info("Fetching real performance data from API...")
        trades_data = await self.api_client.get_trades(user_id=self.user_id, trading_mode="paper", status="closed", limit=500)
        trades = [Trade.model_validate(t) for t in trades_data]

        total_trades = len(trades)
        winning_trades = 0
        losing_trades = 0
        total_pnl = Decimal('0.0')
        best_trade_pnl = Decimal('-999999999.0')
        worst_trade_pnl = Decimal('999999999.0')
        
        portfolio_evolution = []
        pnl_by_period = []

        current_value = Decimal('10000.0')
        for i, trade in enumerate(trades):
            if trade.pnl_usd is not None:
                total_pnl += trade.pnl_usd
                current_value += trade.pnl_usd
                if trade.pnl_usd > 0:
                    winning_trades += 1
                elif trade.pnl_usd < 0:
                    losing_trades += 1
                
                if trade.pnl_usd > best_trade_pnl:
                    best_trade_pnl = trade.pnl_usd
                if trade.pnl_usd < worst_trade_pnl:
                    worst_trade_pnl = trade.pnl_usd
            
            portfolio_evolution.append((i, float(current_value)))

        win_rate = Decimal('0.0')
        if total_trades > 0:
            win_rate = (Decimal(winning_trades) / Decimal(total_trades)) * 100
        
        sharpe_ratio = Decimal('0.0')
        max_drawdown = Decimal('0.0')

        metrics = PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            avg_pnl_per_trade=total_pnl / Decimal(total_trades) if total_trades > 0 else Decimal('0.0'),
            best_trade_pnl=best_trade_pnl if best_trade_pnl != Decimal('-999999999.0') else Decimal('0.0'),
            worst_trade_pnl=worst_trade_pnl if worst_trade_pnl != Decimal('999999999.0') else Decimal('0.0'),
            best_trade_symbol=None,
            worst_trade_symbol=None,
            period_start=None,
            period_end=None,
            total_volume_traded=Decimal('0.0')
        )

        logger.info("Real performance data fetched and calculated.")
        return {
            "portfolio_evolution": portfolio_evolution,
            "pnl_by_period": pnl_by_period,
            "metrics": metrics.model_dump(mode='json')
        }

    @QtCore.Slot()
    def run(self):
        """
        Programa la corutina para que se ejecute en el bucle de eventos de asyncio
        principal de la aplicación.
        """
        logger.debug("PerformanceWorker: run method started in thread %s.", QtCore.QThread.currentThread().objectName() or str(QtCore.QThread.currentThread()))
        
        try:
            coroutine = self._fetch_performance_data()
            main_loop = asyncio.get_event_loop()
            self._task = cast(asyncio.Task, asyncio.run_coroutine_threadsafe(coroutine, main_loop)) # Cast a asyncio.Task
            self._task.add_done_callback(self._on_task_done)
            logger.debug("PerformanceWorker: Coroutine scheduled on the main event loop.")
        except Exception as e:
            logger.error(f"Error scheduling PerformanceWorker task: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
            self.finished.emit()

    def _on_task_done(self, future: asyncio.Future):
        """Callback executed when the async task is done."""
        try:
            data = future.result()
            self.performance_data_ready.emit(data)
        except asyncio.CancelledError:
            logger.info("PerformanceWorker: Task was cancelled.")
            self.error_occurred.emit("Operación cancelada.")
        except Exception as e:
            logger.error(f"Error in PerformanceWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
            logger.info("PerformanceWorker finished.")


class OrdersWorker(QtCore.QObject):
    """
    Worker to fetch order history asynchronously.
    """
    finished = QtCore.Signal()
    orders_ready = QtCore.Signal(list)
    error_occurred = QtCore.Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, user_id: UUID, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.user_id = user_id
        self._task: Optional[asyncio.Task] = None # Usar asyncio.Task

    async def _fetch_orders(self):
        """Async method to get order history."""
        logger.info("Fetching real order history from API...")
        orders = await self.api_client.get_trades(user_id=self.user_id, trading_mode="paper", limit=100)
        logger.info(f"Fetched {len(orders)} orders from API.")
        return orders

    @QtCore.Slot()
    def run(self):
        """
        Programa la corutina para que se ejecute en el bucle de eventos de asyncio
        principal de la aplicación.
        """
        logger.debug("OrdersWorker: run method started in thread %s.", QtCore.QThread.currentThread().objectName() or str(QtCore.QThread.currentThread()))
        
        try:
            coroutine = self._fetch_orders()
            main_loop = asyncio.get_event_loop()
            self._task = cast(asyncio.Task, asyncio.run_coroutine_threadsafe(coroutine, main_loop)) # Cast a asyncio.Task
            self._task.add_done_callback(self._on_task_done)
            logger.debug("OrdersWorker: Coroutine scheduled on the main event loop.")
        except Exception as e:
            logger.error(f"Error scheduling OrdersWorker task: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
            self.finished.emit()

    def _on_task_done(self, future: asyncio.Future):
        """Callback executed when the async task is done."""
        try:
            orders = future.result()
            self.orders_ready.emit(orders)
        except asyncio.CancelledError:
            logger.info("OrdersWorker: Task was cancelled.")
            self.error_occurred.emit("Operación cancelada.")
        except Exception as e:
            logger.error(f"Error in OrdersWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
            logger.info("OrdersWorker finished.")


class TradingTerminalWorker(QtCore.QObject):
    """
    Worker to fetch real-time market data for the trading terminal.
    """
    price_updated = QtCore.Signal(dict)
    finished = QtCore.Signal()
    error_occurred = QtCore.Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, symbol: str, main_event_loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.symbol = symbol
        self.main_event_loop = main_event_loop
        self._is_running = True
        self._task: Optional[asyncio.Task] = None # Usar asyncio.Task

    async def _fetch_price_feed(self):
        """
        Fetches real-time price data from the API.
        """
        logger.info(f"Starting real-time price feed for {self.symbol}...")
        try:
            while self._is_running:
                tickers_data = await self.api_client.get_market_data(symbols=[self.symbol])
                if self.symbol in tickers_data:
                    ticker = Ticker.model_validate(tickers_data[self.symbol])
                    self.price_updated.emit({'timestamp': ticker.last_updated.timestamp(), 'price': ticker.price})
                else:
                    logger.warning(f"No ticker data found for {self.symbol}.")
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error fetching real-time price feed for {self.symbol}: {e}", exc_info=True)
            self.error_occurred.emit(f"Error en el feed de precios: {e}")
        finally:
            logger.info(f"Price feed for {self.symbol} finished.")

    @QtCore.Slot()
    def run(self):
        """
        Programa la corutina para que se ejecute en el bucle de eventos de asyncio
        principal de la aplicación.
        """
        logger.debug("TradingTerminalWorker: run method started in thread %s.", QtCore.QThread.currentThread().objectName() or str(QtCore.QThread.currentThread()))
        
        if not self.main_event_loop:
            logger.error("TradingTerminalWorker: No se encontró el bucle de eventos principal. No se puede programar la tarea.")
            self.error_occurred.emit("Error interno del Worker: Bucle de eventos no disponible.")
            self.finished.emit()
            return

        try:
            coroutine = self._fetch_price_feed()
            self._task = cast(asyncio.Task, asyncio.run_coroutine_threadsafe(coroutine, self.main_event_loop)) # Usar el bucle de eventos pasado
            self._task.add_done_callback(self._on_task_done)
            logger.debug("TradingTerminalWorker: Coroutine scheduled on the main event loop.")
        except Exception as e:
            logger.error(f"Error scheduling TradingTerminalWorker task: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
            self.finished.emit()

    def _on_task_done(self, future: asyncio.Future):
        """Callback executed when the async task is done."""
        try:
            future.result()
        except asyncio.CancelledError:
            logger.info(f"Price feed for {self.symbol} was cancelled.")
            self.error_occurred.emit("Operación cancelada.")
        except Exception as e:
            logger.error(f"Error in TradingTerminalWorker: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()
            logger.info("TradingTerminalWorker finished.")

    def stop(self):
        self._is_running = False
        logger.info("TradingTerminalWorker stop requested.")
        if self._task and not self._task.done():
            main_loop = asyncio.get_event_loop()
            main_loop.call_soon_threadsafe(self._task.cancel)
            logger.info("TradingTerminalWorker: Async task cancellation requested via threadsafe call.")
        else:
            logger.info("TradingTerminalWorker: No active task to cancel.")
