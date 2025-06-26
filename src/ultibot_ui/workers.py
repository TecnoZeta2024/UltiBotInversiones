import asyncio
import logging
from typing import List, Dict, Any
from uuid import UUID
from decimal import Decimal

from ultibot_ui.services.api_client import UltiBotAPIClient
from shared.data_types import Trade, PerformanceMetrics, Ticker, UserConfiguration

logger = logging.getLogger(__name__)

# --- Funciones de Ayuda Asíncronas ---
# Este módulo ahora contiene funciones de corutina que pueden ser
# ejecutadas como tareas de asyncio directamente, eliminando la necesidad
# de QObject workers y QThreads para operaciones de red.

async def fetch_user_configuration(api_client: UltiBotAPIClient) -> Dict[str, Any]:
    """Obtiene la configuración del usuario desde la API."""
    logger.info("Fetching user configuration from API...")
    config = await api_client.get_user_configuration()
    logger.info("Fetched user configuration.")
    return config

async def update_user_configuration(api_client: UltiBotAPIClient, config: UserConfiguration) -> Dict[str, Any]:
    """Actualiza la configuración del usuario en la API."""
    logger.info("Updating user configuration via API...")
    config_data = config.model_dump(mode='json', by_alias=True, exclude_none=True)
    response = await api_client.update_user_configuration(config_data)
    logger.info("User configuration updated.")
    return response

async def activate_real_trading_mode(api_client: UltiBotAPIClient) -> Dict[str, Any]:
    """Activa el modo de operativa real."""
    logger.info("Activating real trading mode via API...")
    response = await api_client.activate_real_trading_mode()
    logger.info("Real trading mode activated.")
    return response

async def deactivate_real_trading_mode(api_client: UltiBotAPIClient) -> Dict[str, Any]:
    """Desactiva el modo de operativa real."""
    logger.info("Deactivating real trading mode via API...")
    response = await api_client.deactivate_real_trading_mode()
    logger.info("Real trading mode deactivated.")
    return response

async def fetch_strategies(api_client: UltiBotAPIClient) -> List[dict]:
    """Obtiene las estrategias de trading desde la API."""
    logger.info("Fetching strategies from API...")
    strategies = await api_client.get_strategies()
    logger.info(f"Fetched {len(strategies)} strategies.")
    return strategies

async def fetch_performance_data(api_client: UltiBotAPIClient) -> dict:
    """Obtiene y calcula los datos de rendimiento desde la API."""
    logger.info("Fetching performance data from API...")
    trades_data = await api_client.get_trades(trading_mode="paper", status="closed", limit=500)
    trades = [Trade.model_validate(t) for t in trades_data]

    total_trades = len(trades)
    winning_trades = 0
    losing_trades = 0
    total_pnl = Decimal('0.0')
    best_trade_pnl = Decimal('-999999999.0')
    worst_trade_pnl = Decimal('999999999.0')
    
    portfolio_evolution = []
    current_value = Decimal('10000.0') # Asumiendo un valor inicial
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

    win_rate = (Decimal(winning_trades) / Decimal(total_trades) * 100) if total_trades > 0 else Decimal('0.0')
    
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

    logger.info("Performance data fetched and calculated.")
    return {
        "portfolio_evolution": portfolio_evolution,
        "pnl_by_period": [],
        "metrics": metrics.model_dump(mode='json')
    }

async def fetch_orders(api_client: UltiBotAPIClient) -> List[dict]:
    """Obtiene el historial de órdenes desde la API."""
    logger.info("Fetching order history from API...")
    orders = await api_client.get_trades(trading_mode="paper", limit=100)
    logger.info(f"Fetched {len(orders)} orders.")
    return orders

async def price_feed_manager(api_client: UltiBotAPIClient, symbol: str, callback: callable):
    """
    Gestiona el feed de precios en tiempo real para un símbolo y llama a un callback con los datos.
    """
    logger.info(f"Starting real-time price feed for {symbol}...")
    while True:
        try:
            tickers_list = await api_client.get_market_data(symbols=[symbol])
            normalized_symbol = symbol.replace('/', '')
            
            found_ticker = next((t for t in tickers_list if t.get('symbol') == normalized_symbol), None)
            
            if found_ticker:
                ticker = Ticker.model_validate(found_ticker)
                callback({'timestamp': ticker.last_updated.timestamp(), 'price': ticker.price})
            else:
                logger.warning(f"No ticker data found for {symbol} in the API response.")
            
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info(f"Price feed for {symbol} was cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in price feed for {symbol}: {e}", exc_info=True)
            # Esperar antes de reintentar para no inundar de logs en caso de error persistente
            await asyncio.sleep(5)
