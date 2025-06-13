"""
Módulo que define el ViewModel para el Dashboard de la aplicación.
Gestiona los datos y la lógica de presentación para la vista principal del usuario.
"""

from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QObject # Importar QObject
from typing import Optional, List, Dict, Any
from decimal import Decimal
import asyncio
from uuid import UUID # Importar UUID directamente

from src.ultibot_ui.viewmodels.base_viewmodel import BaseViewModel
from src.ultibot_ui.services.api_client import APIClient
from src.ultibot_ui.models import Portfolio, Trade, TickerData, MarketSnapshot, KlineData, OrderSide, OrderType # Eliminar TradeId

class DashboardViewModel(BaseViewModel):
    """
    ViewModel para el Dashboard, responsable de exponer los datos del portfolio,
    trades activos y datos de mercado a la vista.
    """
    # Señales para notificar cambios en las propiedades
    portfolio_value_changed = pyqtSignal(Decimal)
    active_trades_changed = pyqtSignal(list)
    market_data_changed = pyqtSignal(TickerData)
    recent_klines_changed = pyqtSignal(list)

    def __init__(self, api_client: APIClient, parent: Optional[QObject] = None):
        """
        Inicializa el DashboardViewModel.

        Args:
            api_client (APIClient): Cliente API para comunicarse con el backend.
            parent (Optional[QObject]): El objeto padre de PyQt.
        """
        super().__init__(parent)
        self._api_client = api_client
        self._portfolio_value: Decimal = Decimal('0.0')
        self._active_trades: List[Trade] = []
        self._market_data: Optional[TickerData] = None
        self._recent_klines: List[KlineData] = []

        # Registrar comandos si es necesario
        # self.register_command("refresh_portfolio", self._refresh_portfolio_command)
        # self.register_command("refresh_market_data", self._refresh_market_data_command)

    @pyqtProperty(Decimal, notify=portfolio_value_changed)
    def portfolio_value(self) -> Decimal:
        """Valor total del portfolio en USD."""
        return self._portfolio_value

    @portfolio_value.setter
    def portfolio_value(self, value: Decimal) -> None:
        if self._portfolio_value != value:
            self._portfolio_value = value
            self.portfolio_value_changed.emit(value)
            self._set_property("portfolio_value", value) # Usar el método base para consistencia

    @pyqtProperty(list, notify=active_trades_changed)
    def active_trades(self) -> List[Trade]:
        """Lista de trades activos."""
        return self._active_trades

    @active_trades.setter
    def active_trades(self, value: List[Trade]) -> None:
        # Comparación simple, se podría mejorar para listas grandes
        if self._active_trades != value:
            self._active_trades = value
            self.active_trades_changed.emit(value)
            self._set_property("active_trades", value)

    @pyqtProperty(QObject, notify=market_data_changed) # QObject porque TickerData hereda de QObject
    def market_data(self) -> Optional[TickerData]:
        """Datos del ticker de mercado actual."""
        return self._market_data

    @market_data.setter
    def market_data(self, value: Optional[TickerData]) -> None:
        if self._market_data != value:
            self._market_data = value
            self.market_data_changed.emit(value)
            self._set_property("market_data", value)

    @pyqtProperty(list, notify=recent_klines_changed)
    def recent_klines(self) -> List[KlineData]:
        """Lista de las velas (klines) más recientes."""
        return self._recent_klines

    @recent_klines.setter
    def recent_klines(self, value: List[KlineData]) -> None:
        if self._recent_klines != value:
            self._recent_klines = value
            self.recent_klines_changed.emit(value)
            self._set_property("recent_klines", value)

    async def _do_refresh(self) -> None:
        """
        Implementación de la lógica de refresco de datos para el dashboard.
        """
        print("Refrescando datos del Dashboard...")
        await self._refresh_portfolio_data()
        await self._refresh_market_data()
        print("Datos del Dashboard refrescados.")

    async def _refresh_portfolio_data(self) -> None:
        """
        Refresca los datos del portfolio del usuario.
        """
        try:
            # Asumiendo un user_id fijo por ahora, o que se obtiene de un servicio de autenticación
            user_id = "some_fixed_user_id" # TODO: Obtener user_id real
            portfolio_data = await self._api_client.fetch_query("get_portfolio", {"user_id": user_id})
            
            # Convertir el diccionario a un objeto Portfolio
            # Esto asume que el backend devuelve un diccionario compatible con el constructor de Portfolio
            if portfolio_data:
                balances = {k: Decimal(str(v)) for k, v in portfolio_data.get("balances", {}).items()}
                total_value_usd = Decimal(str(portfolio_data.get("total_value_usd", '0.0')))
                
                # Convertir user_id a UUID si es necesario
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    user_uuid = uuid4() # Generar uno si el fijo no es UUID válido
                
                self.portfolio_value = total_value_usd
                self.active_trades = [
                    Trade(
                        id=UUID(t['id']['value']), # Usar UUID directamente
                        symbol=t['symbol'],
                        side=OrderSide(t['side']),
                        quantity=Decimal(str(t['quantity'])),
                        price=Decimal(str(t['price'])),
                        timestamp=datetime.fromisoformat(t['timestamp']),
                        order_type=OrderType(t['order_type']),
                        strategy_id=t.get('strategy_id'),
                        fee=Decimal(str(t['fee'])) if t.get('fee') else None,
                        fee_asset=t.get('fee_asset')
                    ) for t in portfolio_data.get("active_trades", [])
                ]
                print(f"Portfolio Value: {self.portfolio_value}")
                print(f"Active Trades: {len(self.active_trades)}")
            else:
                self.portfolio_value = Decimal('0.0')
                self.active_trades = []

        except Exception as e:
            self.error_occurred.emit(f"Error al refrescar portfolio: {e}")
            print(f"Error al refrescar portfolio: {e}")

    async def _refresh_market_data(self) -> None:
        """
        Refresca los datos de mercado (ticker y klines recientes).
        """
        try:
            # Ejemplo: Obtener datos para BTCUSDT
            symbol = "BTCUSDT" # TODO: Hacer configurable o dinámico
            ticker_data_raw = await self._api_client.fetch_query("get_ticker", {"symbol": symbol})
            klines_data_raw = await self._api_client.fetch_query("get_klines", {"symbol": symbol, "interval": "1h"})

            if ticker_data_raw:
                self.market_data = TickerData(
                    symbol=ticker_data_raw['symbol'],
                    price=Decimal(str(ticker_data_raw['price'])),
                    volume_24h=Decimal(str(ticker_data_raw['volume_24h'])),
                    price_change_24h=Decimal(str(ticker_data_raw['price_change_24h'])),
                    timestamp=datetime.fromisoformat(ticker_data_raw['timestamp'])
                )
                print(f"Market Data for {symbol}: Price={self.market_data.price}")

            if klines_data_raw:
                self.recent_klines = [
                    KlineData(
                        timestamp=datetime.fromisoformat(k['timestamp']),
                        open=Decimal(str(k['open'])),
                        high=Decimal(str(k['high'])),
                        low=Decimal(str(k['low'])),
                        close=Decimal(str(k['close'])),
                        volume=Decimal(str(k['volume']))
                    ) for k in klines_data_raw
                ]
                print(f"Recent Klines for {symbol}: {len(self.recent_klines)} klines")

        except Exception as e:
            self.error_occurred.emit(f"Error al refrescar datos de mercado: {e}")
            print(f"Error al refrescar datos de mercado: {e}")
