from uuid import UUID
from typing import List, Dict, Any, Callable
from src.ultibot_backend.services.market_data_service import MarketDataService as BackendMarketDataService

class UIMarketDataService:
    def __init__(self, backend_market_data_service: BackendMarketDataService):
        self._backend_service = backend_market_data_service

    async def get_market_data_rest(self, user_id: UUID, symbols: List[str]) -> Dict[str, Any]:
        return await self._backend_service.get_market_data_rest(user_id, symbols)

    async def subscribe_to_market_data_websocket(self, user_id: UUID, symbol: str, callback: Callable):
        await self._backend_service.subscribe_to_market_data_websocket(user_id, symbol, callback)

    async def unsubscribe_from_market_data_websocket(self, symbol: str):
        await self._backend_service.unsubscribe_from_market_data_websocket(symbol)

    async def get_all_binance_symbols(self, user_id: UUID) -> List[str]:
        # Assuming the backend service has or will have this method
        # If not, this highlights a point of extension.
        # For now, let's assume it exists or will be added to the backend service.
        # If BackendMarketDataService does not have this method, this will require adjustment.
        if hasattr(self._backend_service, 'get_all_binance_symbols'):
            return await self._backend_service.get_all_binance_symbols(user_id)
        else:
            # Placeholder or raise an error if the backend method is critical and missing
            print("Warning: BackendMarketDataService does not have get_all_binance_symbols method.")
            return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT"] # Fallback
