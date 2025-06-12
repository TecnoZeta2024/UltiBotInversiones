"""
Módulo que define los modelos de dominio puros relacionados con el trading.
Estos modelos son agnósticos a la infraestructura y no deben importar frameworks externos.
Utilizan Pydantic para la validación y serialización de datos.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any, Dict, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

# --- Enums y Tipos Básicos ---

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

# --- Modelos de Datos de Mercado ---

class TickerData(BaseModel):
    """Datos de un ticker de mercado."""
    symbol: str
    price: Decimal
    volume_24h: Decimal
    price_change_24h: Decimal
    timestamp: datetime = Field(default_factory=datetime.utcnow)
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

# --- Modelos de Órdenes y Trades ---

class Order(BaseModel):
    """Representación de una orden de trading."""
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(frozen=True)

class Trade(BaseModel):
    """Representación de un trade ejecutado."""
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    strategy_id: Optional[str] = None
    order_type: OrderType
    fee: Optional[Decimal] = None
    fee_asset: Optional[str] = None
    model_config = ConfigDict(frozen=True)

# --- Modelos de Estrategias y Señales ---

class BaseStrategyParameters(BaseModel):
    """Base para todos los parámetros de estrategia, incluye campos comunes."""
    name: str = Field(..., description="Nombre único de la instancia de la estrategia.")
    description: Optional[str] = Field(None, description="Descripción de la configuración de la estrategia.")
    position_size_pct: float = Field(0.01, ge=0, le=1, description="Porcentaje del capital a arriesgar por operación.")
    risk_reward_ratio: float = Field(2.0, gt=0, description="Ratio riesgo/recompensa para take profit.")
    model_config = ConfigDict(frozen=True)

class MACDRSIParameters(BaseStrategyParameters):
    """Parámetros para MACD RSI Trend Rider."""
    name: str = "MACD_RSI_Trend_Rider"
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    rsi_period: int = 14
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    min_trend_strength: float = 0.6

class BollingerSqueezeParameters(BaseStrategyParameters):
    """Parámetros para Bollinger Squeeze Breakout."""
    name: str = "Bollinger_Squeeze_Breakout"
    bollinger_period: int = 20
    bollinger_std_dev: float = 2.0
    keltner_period: int = 20
    keltner_multiplier: float = 1.5
    squeeze_threshold: float = 0.8
    breakout_confirmation_bars: int = 3
    min_breakout_strength: float = 0.7

class TriangularArbitrageParameters(BaseStrategyParameters):
    """Parámetros para Triangular Arbitrage."""
    name: str = "Triangular_Arbitrage"
    min_profit_percent: Decimal = Decimal("0.1")
    max_slippage_percent: Decimal = Decimal("0.05")
    arbitrage_pairs: List[tuple[str, str, str]]

class SuperTrendParameters(BaseStrategyParameters):
    """Parámetros para SuperTrend Volatility Filter."""
    name: str = "SuperTrend_Volatility_Filter"
    atr_period: int = 14
    atr_multiplier: float = 3.0
    min_volatility_percentile: float = 20.0
    max_volatility_percentile: float = 80.0
    volatility_lookback: int = 100
    min_trend_strength: float = 0.7

class VWAPParameters(BaseStrategyParameters):
    """Parámetros para VWAP Cross Strategy."""
    name: str = "VWAP_Cross_Strategy"
    vwap_period: int = 100
    volume_ma_period: int = 20
    min_volume_threshold: float = 1.5
    deviation_bands: bool = True
    deviation_multiplier: float = 2.0
    trend_confirmation_period: int = 10
    min_price_deviation: float = 0.002

# Alias táctico para resolver ImportError por refactorización incompleta
# StrategyParameters = Union[
#     MACDRSIParameters,
#     BollingerSqueezeParameters,
#     TriangularArbitrageParameters,
#     SuperTrendParameters,
#     VWAPParameters
# ]

class TradingSignal(BaseModel):
    """Señal de trading generada por una estrategia."""
    signal_id: UUID = Field(default_factory=uuid4)
    strategy_name: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    strength: SignalStrength = SignalStrength.MODERATE
    reasoning: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(frozen=True)

class AnalysisResult(BaseModel):
    """Resultado del análisis de una estrategia."""
    confidence: float = Field(ge=0, le=1)
    indicators: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    signal: Optional[TradingSignal] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(frozen=True)

# --- Modelos de Portfolio y Activos ---

class Asset(BaseModel):
    """Representa un activo en el portafolio."""
    symbol: str
    quantity: Decimal
    average_price: Decimal
    current_price: Optional[Decimal] = None
    total_value_usd: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    model_config = ConfigDict(frozen=True)

class Portfolio(BaseModel):
    """Representa el portafolio de un usuario."""
    user_id: str
    trading_mode: Optional[str] = None
    available_balance_usdt: Decimal = Decimal('0.0')
    total_assets_value_usd: Decimal = Decimal('0.0')
    total_portfolio_value_usd: Decimal = Decimal('0.0')
    assets: List[Asset] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(frozen=True)

# --- Modelos de Resultados y Oportunidades ---

class TradeResult(BaseModel):
    """Resultado de una operación de trading."""
    success: bool
    trade_id: Optional[UUID] = None
    message: Optional[str] = None
    executed_price: Optional[Decimal] = None
    executed_quantity: Optional[Decimal] = None
    model_config = ConfigDict(frozen=True)

class CommandResult(BaseModel):
    """Resultado de la ejecución de un comando."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    model_config = ConfigDict(frozen=True)

class ScanResult(BaseModel):
    """Resultado de un escaneo de mercado."""
    symbol: str
    score: float
    preset: str
    model_config = ConfigDict(frozen=True)

class TradingOpportunity(BaseModel):
    """Representa una oportunidad de trading detectada."""
    symbol: str
    opportunity_type: str
    confidence: float = Field(ge=0, le=1)
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(frozen=True)

class TradingDecision(BaseModel):
    """Representa una decisión de trading tomada por un servicio."""
    decision_id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    confidence: float = Field(ge=0, le=1)
    rationale: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_config = ConfigDict(frozen=True)

# Alias táctico para resolver ImportError por refactorización incompleta
Opportunity = TradingOpportunity
