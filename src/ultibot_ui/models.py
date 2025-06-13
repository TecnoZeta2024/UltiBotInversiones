from datetime import datetime, timezone # ADDED timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from uuid import UUID, uuid4

from PySide6.QtCore import QObject, Signal as pyqtSignal, Property, QAbstractListModel, QModelIndex, Qt, QByteArray
from pydantic import BaseModel, Field, ConfigDict

# --- Enums y Tipos Básicos (Duplicados para UI, idealmente compartidos via API) ---
# Estos deberían ser consumidos desde el backend API, pero se mantienen aquí para la UI
# si hay necesidad de modelos locales o para prototipado rápido.
# En una arquitectura final, la UI consumiría los modelos del backend a través de la API.

class TradingMode(str, Enum):
    """Define los modos de operación de trading."""
    SIMULATED = "SIMULATED"
    REAL = "REAL"

class OrderSide(str, Enum):
    """Lado de la orden (compra o venta)."""
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    """Tipo de orden (mercado, límite, etc.)."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"

class OrderStatus(str, Enum):
    """Estado de una orden."""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class SignalStrength(Enum):
    """Representa la fuerza o confianza de una señal de trading."""
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"

# --- Modelos de Datos de Mercado (Duplicados para UI) ---

class TickerData(BaseModel):
    """Datos de un ticker de mercado."""
    symbol: str
    price: Decimal
    volume_24h: Decimal
    price_change_24h: Decimal
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # MODIFIED
    model_config = ConfigDict(frozen=True)

class KlineData(BaseModel):
    """Datos de una vela (kline)."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    model_config = ConfigDict(frozen=True)

class MarketSnapshot(BaseModel):
    """Snapshot de datos de mercado en un momento dado."""
    symbol: str
    timestamp: datetime
    ticker_data: TickerData
    klines: List[KlineData]
    timeframe: str
    indicators: Dict[str, Any] = Field(default_factory=dict)
    volume_data: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(frozen=True)

# --- Modelos de Órdenes y Trades (Duplicados para UI) ---

class Order(BaseModel):
    """Representación de una orden de trading."""
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # MODIFIED
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # MODIFIED
    model_config = ConfigDict(frozen=True)

class Trade(QObject):
    """Representación de un trade ejecutado."""
    _id: UUID
    _symbol: str
    _side: OrderSide
    _quantity: Decimal
    _price: Decimal
    _timestamp: datetime
    _order_type: OrderType
    _strategy_id: Optional[str]
    _fee: Optional[Decimal]
    _fee_asset: Optional[str]

    def __init__(self, id: UUID, symbol: str, side: OrderSide, quantity: Decimal, price: Decimal, timestamp: datetime, order_type: OrderType, strategy_id: Optional[str] = None, fee: Optional[Decimal] = None, fee_asset: Optional[str] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._id = id
        self._symbol = symbol
        self._side = side
        self._quantity = quantity
        self._price = price
        self._timestamp = timestamp
        self._order_type = order_type
        self._strategy_id = strategy_id
        self._fee = fee
        self._fee_asset = fee_asset

    def get_id(self) -> UUID: return self._id
    def get_symbol(self) -> str: return self._symbol
    def get_side(self) -> OrderSide: return self._side
    def get_quantity(self) -> Decimal: return self._quantity
    def get_price(self) -> Decimal: return self._price
    def get_timestamp(self) -> datetime: return self._timestamp
    def get_order_type(self) -> OrderType: return self._order_type
    def get_strategy_id(self) -> Optional[str]: return self._strategy_id
    def get_fee(self) -> Optional[Decimal]: return self._fee
    def get_fee_asset(self) -> Optional[str]: return self._fee_asset

    id = Property(UUID, fget=get_id, constant=True)
    symbol = Property(str, fget=get_symbol, constant=True)
    side = Property(OrderSide, fget=get_side, constant=True)
    quantity = Property(Decimal, fget=get_quantity, constant=True)
    price = Property(Decimal, fget=get_price, constant=True)
    timestamp = Property(datetime, fget=get_timestamp, constant=True)
    order_type = Property(OrderType, fget=get_order_type, constant=True)
    strategy_id = Property(str, fget=get_strategy_id, constant=True)
    fee = Property(Decimal, fget=get_fee, constant=True)
    fee_asset = Property(str, fget=get_fee_asset, constant=True)

class TradeResult(QObject):
    """Resultado de una operación de trading."""
    _success: bool
    _trade_id: Optional[UUID]
    _message: Optional[str]
    _executed_price: Optional[Decimal]
    _executed_quantity: Optional[Decimal]

    def __init__(self, success: bool, trade_id: Optional[UUID] = None, message: Optional[str] = None, executed_price: Optional[Decimal] = None, executed_quantity: Optional[Decimal] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._success = success
        self._trade_id = trade_id
        self._message = message
        self._executed_price = executed_price
        self._executed_quantity = executed_quantity

    def get_success(self) -> bool: return self._success
    def get_trade_id(self) -> Optional[UUID]: return self._trade_id
    def get_message(self) -> Optional[str]: return self._message
    def get_executed_price(self) -> Optional[Decimal]: return self._executed_price
    def get_executed_quantity(self) -> Optional[Decimal]: return self._executed_quantity

    success = Property(bool, fget=get_success, constant=True)
    trade_id = Property(UUID, fget=get_trade_id, constant=True)
    message = Property(str, fget=get_message, constant=True)
    executed_price = Property(Decimal, fget=get_executed_price, constant=True)
    executed_quantity = Property(Decimal, fget=get_executed_quantity, constant=True)

# --- Modelos de Portfolio y Activos (Duplicados para UI) ---

class Asset(QObject):
    """Representa un activo en el portafolio."""
    _symbol: str
    _quantity: Decimal
    _average_price: Decimal
    _current_price: Optional[Decimal]
    _total_value_usd: Optional[Decimal]
    _unrealized_pnl: Optional[Decimal]

    def __init__(self, symbol: str, quantity: Decimal, average_price: Decimal, current_price: Optional[Decimal] = None, total_value_usd: Optional[Decimal] = None, unrealized_pnl: Optional[Decimal] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._symbol = symbol
        self._quantity = quantity
        self._average_price = average_price
        self._current_price = current_price
        self._total_value_usd = total_value_usd
        self._unrealized_pnl = unrealized_pnl

    def get_symbol(self) -> str: return self._symbol
    def get_quantity(self) -> Decimal: return self._quantity
    def get_average_price(self) -> Decimal: return self._average_price
    def get_current_price(self) -> Optional[Decimal]: return self._current_price
    def get_total_value_usd(self) -> Optional[Decimal]: return self._total_value_usd
    def get_unrealized_pnl(self) -> Optional[Decimal]: return self._unrealized_pnl

    symbol = Property(str, fget=get_symbol, constant=True)
    quantity = Property(Decimal, fget=get_quantity, constant=True)
    average_price = Property(Decimal, fget=get_average_price, constant=True)
    current_price = Property(Decimal, fget=get_current_price, constant=True)
    total_value_usd = Property(Decimal, fget=get_total_value_usd, constant=True)
    unrealized_pnl = Property(Decimal, fget=get_unrealized_pnl, constant=True)

class Portfolio(QObject):
    """Representa el portafolio de un usuario."""
    _user_id: str
    _trading_mode: Optional[str]
    _available_balance_usdt: Decimal
    _total_assets_value_usd: Decimal
    _total_portfolio_value_usd: Decimal
    _assets: List[Asset]
    _last_updated: datetime

    def __init__(self, user_id: str, trading_mode: Optional[str], available_balance_usdt: Decimal, total_assets_value_usd: Decimal, total_portfolio_value_usd: Decimal, assets: List[Asset], last_updated: datetime, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._user_id = user_id
        self._trading_mode = trading_mode
        self._available_balance_usdt = available_balance_usdt
        self._total_assets_value_usd = total_assets_value_usd
        self._total_portfolio_value_usd = total_portfolio_value_usd
        self._assets = assets
        self._last_updated = last_updated

    def get_user_id(self) -> str: return self._user_id
    def get_trading_mode(self) -> Optional[str]: return self._trading_mode
    def get_available_balance_usdt(self) -> Decimal: return self._available_balance_usdt
    def get_total_assets_value_usd(self) -> Decimal: return self._total_assets_value_usd
    def get_total_portfolio_value_usd(self) -> Decimal: return self._total_portfolio_value_usd
    def get_assets(self) -> List[Asset]: return self._assets
    def get_last_updated(self) -> datetime: return self._last_updated

    user_id = Property(str, fget=get_user_id, constant=True)
    trading_mode = Property(str, fget=get_trading_mode, constant=True)
    available_balance_usdt = Property(Decimal, fget=get_available_balance_usdt, constant=True)
    total_assets_value_usd = Property(Decimal, fget=get_total_assets_value_usd, constant=True)
    total_portfolio_value_usd = Property(Decimal, fget=get_total_portfolio_value_usd, constant=True)
    assets = Property(list, fget=get_assets, constant=True) # QML doesn't directly support List[Asset]
    last_updated = Property(datetime, fget=get_last_updated, constant=True)

class PortfolioModel(QAbstractListModel):
    """Modelo de lista para el portafolio en QML."""
    UserIdRole = Qt.ItemDataRole.UserRole + 1
    TradingModeRole = Qt.ItemDataRole.UserRole + 2
    AvailableBalanceUsdtRole = Qt.ItemDataRole.UserRole + 3
    TotalAssetsValueUsdRole = Qt.ItemDataRole.UserRole + 4
    TotalPortfolioValueUsdRole = Qt.ItemDataRole.UserRole + 5
    AssetsRole = Qt.ItemDataRole.UserRole + 6
    LastUpdatedRole = Qt.ItemDataRole.UserRole + 7

    def __init__(self, portfolio: Optional[Portfolio] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._portfolio = portfolio if portfolio else Portfolio(
            user_id="default",
            trading_mode=TradingMode.SIMULATED.value,
            available_balance_usdt=Decimal('0.0'),
            total_assets_value_usd=Decimal('0.0'),
            total_portfolio_value_usd=Decimal('0.0'),
            assets=[],
            last_updated=datetime.now(timezone.utc) # MODIFIED
        )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return 1 # Always one portfolio object

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= self.rowCount():
            return None

        if role == self.UserIdRole:
            return self._portfolio.user_id
        elif role == self.TradingModeRole:
            return self._portfolio.trading_mode
        elif role == self.AvailableBalanceUsdtRole:
            return float(self._portfolio.available_balance_usdt)
        elif role == self.TotalAssetsValueUsdRole:
            return float(self._portfolio.total_assets_value_usd)
        elif role == self.TotalPortfolioValueUsdRole:
            return float(self._portfolio.total_portfolio_value_usd)
        elif role == self.AssetsRole:
            # Return a list of Asset QObjects for QML to consume
            return [asset for asset in self._portfolio.assets]
        elif role == self.LastUpdatedRole:
            return self._portfolio.last_updated.isoformat()
        return None

    def roleNames(self) -> Dict[int, QByteArray]:
        roles = {
            self.UserIdRole: QByteArray(b"userId"),
            self.TradingModeRole: QByteArray(b"tradingMode"),
            self.AvailableBalanceUsdtRole: QByteArray(b"availableBalanceUsdt"),
            self.TotalAssetsValueUsdRole: QByteArray(b"totalAssetsValueUsd"),
            self.TotalPortfolioValueUsdRole: QByteArray(b"totalPortfolioValueUsd"),
            self.AssetsRole: QByteArray(b"assets"),
            self.LastUpdatedRole: QByteArray(b"lastUpdated"),
        }
        return roles

    def set_portfolio(self, portfolio: Portfolio):
        self.beginResetModel()
        self._portfolio = portfolio
        self.endResetModel()

class AssetModel(QAbstractListModel):
    """Modelo de lista para activos individuales en QML."""
    SymbolRole = Qt.ItemDataRole.UserRole + 1
    QuantityRole = Qt.ItemDataRole.UserRole + 2
    AveragePriceRole = Qt.ItemDataRole.UserRole + 3
    CurrentPriceRole = Qt.ItemDataRole.UserRole + 4
    TotalValueUsdRole = Qt.ItemDataRole.UserRole + 5
    UnrealizedPnlRole = Qt.ItemDataRole.UserRole + 6

    def __init__(self, assets: List[Asset] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._assets = assets if assets is not None else []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._assets)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._assets)):
            return None

        asset = self._assets[index.row()]
        if role == self.SymbolRole:
            return asset.symbol
        elif role == self.QuantityRole:
            return float(asset.quantity)
        elif role == self.AveragePriceRole:
            return float(asset.average_price)
        elif role == self.CurrentPriceRole:
            return float(asset.current_price) if asset.current_price is not None else 0.0
        elif role == self.TotalValueUsdRole:
            return float(asset.total_value_usd) if asset.total_value_usd is not None else 0.0
        elif role == self.UnrealizedPnlRole:
            return float(asset.unrealized_pnl) if asset.unrealized_pnl is not None else 0.0
        return None

    def roleNames(self) -> Dict[int, QByteArray]:
        roles = {
            self.SymbolRole: QByteArray(b"symbol"),
            self.QuantityRole: QByteArray(b"quantity"),
            self.AveragePriceRole: QByteArray(b"averagePrice"),
            self.CurrentPriceRole: QByteArray(b"currentPrice"),
            self.TotalValueUsdRole: QByteArray(b"totalValueUsd"),
            self.UnrealizedPnlRole: QByteArray(b"unrealizedPnl"),
        }
        return roles

    def set_assets(self, assets: List[Asset]):
        self.beginResetModel()
        self._assets = assets
        self.endResetModel()

class TradeModel(QAbstractListModel):
    """Modelo de lista para trades en QML."""
    IdRole = Qt.ItemDataRole.UserRole + 1
    SymbolRole = Qt.ItemDataRole.UserRole + 2
    SideRole = Qt.ItemDataRole.UserRole + 3
    QuantityRole = Qt.ItemDataRole.UserRole + 4
    PriceRole = Qt.ItemDataRole.UserRole + 5
    TimestampRole = Qt.ItemDataRole.UserRole + 6
    OrderTypeRole = Qt.ItemDataRole.UserRole + 7
    StrategyIdRole = Qt.ItemDataRole.UserRole + 8
    FeeRole = Qt.ItemDataRole.UserRole + 9
    FeeAssetRole = Qt.ItemDataRole.UserRole + 10

    def __init__(self, trades: List[Trade] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._trades = trades if trades is not None else []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._trades)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._trades)):
            return None

        trade = self._trades[index.row()]
        if role == self.IdRole:
            return str(trade.id) # Convert UUID to string for QML
        elif role == self.SymbolRole:
            return trade.symbol
        elif role == self.SideRole:
            return trade.side.value
        elif role == self.QuantityRole:
            return float(trade.quantity)
        elif role == self.PriceRole:
            return float(trade.price)
        elif role == self.TimestampRole:
            return trade.timestamp.isoformat()
        elif role == self.OrderTypeRole:
            return trade.order_type.value
        elif role == self.StrategyIdRole:
            return trade.strategy_id
        elif role == self.FeeRole:
            return float(trade.fee) if trade.fee is not None else 0.0
        elif role == self.FeeAssetRole:
            return trade.fee_asset
        return None

    def roleNames(self) -> Dict[int, QByteArray]:
        roles = {
            self.IdRole: QByteArray(b"id"),
            self.SymbolRole: QByteArray(b"symbol"),
            self.SideRole: QByteArray(b"side"),
            self.QuantityRole: QByteArray(b"quantity"),
            self.PriceRole: QByteArray(b"price"),
            self.TimestampRole: QByteArray(b"timestamp"),
            self.OrderTypeRole: QByteArray(b"orderType"),
            self.StrategyIdRole: QByteArray(b"strategyId"),
            self.FeeRole: QByteArray(b"fee"),
            self.FeeAssetRole: QByteArray(b"feeAsset"),
        }
        return roles

    def set_trades(self, trades: List[Trade]):
        self.beginResetModel()
        self._trades = trades
        self.endResetModel()
