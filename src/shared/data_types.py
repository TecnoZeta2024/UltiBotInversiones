"""
Este archivo contendrá definiciones de tipos de datos compartidos,
por ejemplo, modelos Pydantic comunes si la UI los consume directamente
o si hay tipos de datos que tanto el backend como la UI necesitan conocer.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

class Kline(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_asset_volume: float
    number_of_trades: int
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float


class MarketData(BaseModel):
    id: Optional[int] = None
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class Ticker(BaseModel):
    symbol: str
    price: float
    price_change_percent_24h: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    quote_volume_24h: Optional[float] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ServiceName(str, Enum):
    BINANCE_SPOT = "BINANCE_SPOT"
    BINANCE_FUTURES = "BINANCE_FUTURES"
    TELEGRAM_BOT = "TELEGRAM_BOT"
    GEMINI_API = "GEMINI_API"
    MOBULA_API = "MOBULA_API"
    N8N_WEBHOOK = "N8N_WEBHOOK"
    SUPABASE_CLIENT = "SUPABASE_CLIENT"
    MCP_GENERIC = "MCP_GENERIC"
    MCP_DOGGYBEE_CCXT = "MCP_DOGGYBEE_CCXT"
    MCP_METATRADER_BRIDGE = "MCP_METATRADER_BRIDGE"
    MCP_WEB3_RESEARCH = "MCP_WEB3_RESEARCH"
    CUSTOM_SERVICE = "CUSTOM_SERVICE"


class APICredential(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    service_name: ServiceName
    credential_label: str

    encrypted_api_key: str
    encrypted_api_secret: Optional[str] = None
    encrypted_other_details: Optional[str] = None  # JSON encriptado para detalles adicionales

    status: str = "verification_pending"  # 'active' | 'inactive' | 'revoked' | 'verification_pending' | 'verification_failed' | 'expired'
    last_verified_at: Optional[datetime] = None

    permissions: Optional[List[str]] = None
    permissions_checked_at: Optional[datetime] = None

    expires_at: Optional[datetime] = None
    rotation_reminder_policy_days: Optional[int] = None

    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    purpose_description: Optional[str] = None
    tags: Optional[List[str]] = None

    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(use_enum_values=True, arbitrary_types_allowed=True)


class TelegramConnectionStatus(BaseModel):
    is_connected: bool = Field(..., description="True si la conexión con Telegram está activa y verificada.")
    last_verified_at: Optional[datetime] = Field(None, description="Marca de tiempo de la última verificación exitosa.")
    status_message: str = Field(..., description="Mensaje descriptivo del estado de la conexión (éxito o error).")
    status_code: Optional[str] = Field(None, description="Código de error si la conexión falló.")


class BinanceConnectionStatus(BaseModel):
    is_connected: bool = Field(..., description="True si la conexión con Binance está activa y verificada.")
    last_verified_at: Optional[datetime] = Field(None, description="Marca de tiempo de la última verificación exitosa.")
    status_message: str = Field(..., description="Mensaje descriptivo del estado de la conexión (éxito o error).")
    status_code: Optional[str] = Field(None, description="Código de error si la conexión falló.")
    account_permissions: Optional[List[str]] = Field(
        None, description="Lista de permisos de la API Key de Binance (ej. 'SPOT_TRADING', 'MARGIN_TRADING')."
    )


class AssetBalance(BaseModel):
    asset: str = Field(..., description="Símbolo del activo (ej. 'USDT', 'BTC').")
    free: float = Field(..., description="Cantidad disponible para trading.")
    locked: float = Field(..., description="Cantidad bloqueada en órdenes.")
    total: float = Field(..., description="Cantidad total (free + locked).")


class PortfolioAsset(BaseModel):
    symbol: str = Field(..., description="Símbolo del activo (ej. 'BTC', 'ETH').")
    quantity: float = Field(..., description="Cantidad del activo poseído.")
    entry_price: Optional[float] = Field(None, description="Precio promedio de entrada del activo.")
    current_price: Optional[float] = Field(None, description="Precio actual de mercado del activo.")
    current_value_usd: Optional[float] = Field(None, description="Valor actual del activo en USD.")
    unrealized_pnl_usd: Optional[float] = Field(None, description="Ganancia/Pérdida no realizada en USD.")
    unrealized_pnl_percentage: Optional[float] = Field(None, description="Ganancia/Pérdida no realizada en porcentaje.")


class PortfolioSummary(BaseModel):
    available_balance_usdt: float = Field(..., description="Saldo disponible en USDT.")
    total_assets_value_usd: float = Field(..., description="Valor total de los activos poseídos en USD.")
    total_portfolio_value_usd: float = Field(
        ..., description="Valor total del portafolio (saldo + valor de activos) en USD."
    )
    assets: List[PortfolioAsset] = Field(default_factory=list, description="Lista de activos poseídos.")
    error_message: Optional[str] = Field(None, description="Mensaje de error si hubo un problema al obtener el resumen.")


class PortfolioSnapshot(BaseModel):
    paper_trading: PortfolioSummary = Field(..., description="Resumen del portafolio de Paper Trading.")
    real_trading: PortfolioSummary = Field(..., description="Resumen del portafolio Real.")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Marca de tiempo de la última actualización.")


class NotificationPreference(BaseModel):
    eventType: str
    channel: str
    isEnabled: bool
    minConfidence: Optional[float] = None
    minProfitability: Optional[float] = None


class Watchlist(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    pairs: List[str]
    defaultAlertProfileId: Optional[str] = None
    defaultAiAnalysisProfileId: Optional[str] = None


class RiskProfileSettings(BaseModel):
    dailyCapitalRiskPercentage: Optional[float] = None
    perTradeCapitalRiskPercentage: Optional[float] = None
    maxDrawdownPercentage: Optional[float] = None
    takeProfitPercentage: Optional[float] = Field(0.02, description="Porcentaje de ganancia objetivo para Take Profit (ej. 0.02 para 2%).")
    trailingStopLossPercentage: Optional[float] = Field(0.01, description="Porcentaje de pérdida inicial para Trailing Stop Loss (ej. 0.01 para 1%).")
    trailingStopCallbackRate: Optional[float] = Field(0.005, description="Porcentaje de retroceso para el Trailing Stop (ej. 0.005 para 0.5%).")


class RealTradingSettings(BaseModel):
    real_trading_mode_active: bool = Field(default=False, description="Indica si el modo de operativa real limitada está activo.")
    real_trades_executed_count: int = Field(default=0, description="Contador de operaciones reales ejecutadas en el modo limitado.")
    max_real_trades: int = Field(5, description="Número máximo de operaciones reales permitidas en el modo limitado.")
    daily_capital_risked_usd: float = Field(
        default=0.0, description="Capital total en USD arriesgado en operaciones reales en el día actual."
    )
    last_daily_reset: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Marca de tiempo del último reinicio del contador diario de capital arriesgado.")
    maxConcurrentOperations: Optional[int] = None
    dailyLossLimitAbsolute: Optional[float] = None
    dailyProfitTargetAbsolute: Optional[float] = None
    assetSpecificStopLoss: Optional[Dict[str, Dict[str, float]]] = None
    autoPauseTradingConditions: Optional[Dict[str, Any]] = None


class AIAnalysisConfidenceThresholds(BaseModel):
    paperTrading: Optional[float] = Field(0.70, description="Umbral para paper trading (0.0 a 1.0).")
    realTrading: Optional[float] = Field(0.95, description="Umbral para operativa real (0.0 a 1.0).")
    dataVerificationPriceDiscrepancyPercent: Optional[float] = Field(
        5.0, description="Porcentaje máximo de discrepancia de precio permitido entre fuentes de datos para verificación."
    )
    dataVerificationMinVolumeQuote: Optional[float] = Field(
        1000.0, description="Volumen mínimo en la moneda de cotización para que un activo sea considerado líquido para verificación."
    )


class AiStrategyConfiguration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    appliesToStrategies: Optional[List[str]] = None
    appliesToPairs: Optional[List[str]] = None
    geminiModelName: Optional[str] = None
    geminiPromptTemplate: Optional[str] = None
    indicatorWeights: Optional[Dict[str, float]] = None
    confidenceThresholds: Optional[AIAnalysisConfidenceThresholds] = None
    maxContextWindowTokens: Optional[int] = None


class McpServerPreference(BaseModel):
    id: str
    type: str
    url: Optional[str] = None
    credentialId: Optional[UUID] = None
    isEnabled: Optional[bool] = None
    queryFrequencySeconds: Optional[int] = None
    reliabilityWeight: Optional[float] = None
    customParameters: Optional[Dict[str, Any]] = None


class DashboardLayoutProfile(BaseModel):
    name: str
    configuration: Any


class CloudSyncPreferences(BaseModel):
    isEnabled: Optional[bool] = None
    lastSuccessfulSync: Optional[datetime] = None


class UserConfiguration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    telegramChatId: Optional[str] = None
    notificationPreferences: Optional[List[NotificationPreference]] = None
    enableTelegramNotifications: Optional[bool] = True
    defaultPaperTradingCapital: Optional[float] = None
    paperTradingActive: Optional[bool] = False
    watchlists: Optional[List[Watchlist]] = None
    favoritePairs: Optional[List[str]] = None
    riskProfile: Optional[str] = None
    riskProfileSettings: Optional[RiskProfileSettings] = None
    aiStrategyConfigurations: Optional[List[AiStrategyConfiguration]] = None
    aiAnalysisConfidenceThresholds: Optional[AIAnalysisConfidenceThresholds] = None
    mcpServerPreferences: Optional[List[McpServerPreference]] = None
    selectedTheme: Optional[str] = "dark"
    dashboardLayoutProfiles: Optional[Dict[str, DashboardLayoutProfile]] = None
    activeDashboardLayoutProfileId: Optional[str] = None
    dashboardLayoutConfig: Optional[Any] = None
    cloudSyncPreferences: Optional[CloudSyncPreferences] = None
    createdAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True, arbitrary_types_allowed=True)


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationAction(BaseModel):
    label: str
    actionType: str
    actionValue: Optional[Any] = None
    requiresConfirmation: Optional[bool] = False
    confirmationMessage: Optional[str] = None


class Notification(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    userId: Optional[UUID] = None
    eventType: str
    channel: str
    titleKey: Optional[str] = None
    messageKey: Optional[str] = None
    messageParams: Optional[Dict[str, Any]] = None
    title: str
    message: str
    priority: Optional[NotificationPriority] = NotificationPriority.MEDIUM
    status: str = "new"
    snoozedUntil: Optional[datetime] = None
    dataPayload: Optional[Dict[str, Any]] = None
    actions: Optional[List[NotificationAction]] = None
    correlationId: Optional[str] = None
    isSummary: Optional[bool] = False
    summarizedNotificationIds: Optional[List[UUID]] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    readAt: Optional[datetime] = None
    sentAt: Optional[datetime] = None
    statusHistory: Optional[List[Dict[str, Any]]] = None
    generatedBy: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True, arbitrary_types_allowed=True)


class OpportunitySourceType(str, Enum):
    MCP_SIGNAL = "mcp_signal"
    MANUAL_ENTRY = "manual_entry"
    AI_GENERATED = "ai_generated"
    STRATEGY_TRIGGER = "strategy_trigger"


class OpportunityStatus(str, Enum):
    NEW = "new"
    PENDING_AI_ANALYSIS = "pending_ai_analysis"
    AI_ANALYSIS_IN_PROGRESS = "ai_analysis_in_progress"
    AI_ANALYSIS_COMPLETE = "ai_analysis_complete"
    AI_ANALYSIS_FAILED = "ai_analysis_failed"
    REJECTED_BY_AI = "rejected_by_ai"
    PENDING_EXECUTION = "pending_execution"
    EXECUTING = "executing"
    EXECUTED_PARTIALLY = "executed_partially"
    EXECUTED_FULLY = "executed_fully"
    EXECUTION_FAILED = "execution_failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    COMPLETED_PROFIT = "completed_profit"
    COMPLETED_LOSS = "completed_loss"
    COMPLETED_BREAKEVEN = "completed_breakeven"
    PENDING_USER_CONFIRMATION_REAL = "pending_user_confirmation_real"
    CONVERTED_TO_TRADE_REAL = "converted_to_trade_real"


class AIAnalysis(BaseModel):
    calculatedConfidence: Optional[float] = Field(None, description="Nivel de confianza numérico (0.0 a 1.0) de la IA.")
    suggestedAction: Optional[str] = Field(None, description="Dirección sugerida por la IA (ej. 'BUY', 'SELL', 'HOLD', 'REJECT').")
    reasoning_ai: Optional[str] = Field(None, description="Justificación del análisis de la IA.")
    rawAiOutput: Optional[str] = Field(None, description="Salida cruda completa del modelo de IA.")
    dataVerification: Optional[Dict[str, Any]] = Field(None, description="Resultados de la verificación de datos de activos.")
    ai_model_used: Optional[str] = Field(None, description="Nombre del modelo de IA utilizado para el análisis.")


class Opportunity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    source_type: OpportunitySourceType
    source_name: Optional[str] = None
    source_data: Optional[str] = None
    status: OpportunityStatus = OpportunityStatus.NEW
    status_reason: Optional[str] = None
    symbol: Optional[str] = None
    asset_type: Optional[str] = None
    exchange: Optional[str] = None
    predicted_direction: Optional[str] = None
    predicted_price_target: Optional[float] = None
    predicted_stop_loss: Optional[float] = None
    prediction_timeframe: Optional[str] = None
    ai_analysis: Optional[AIAnalysis] = None
    confidence_score: Optional[float] = None
    suggested_action: Optional[str] = None
    ai_model_used: Optional[str] = None
    executed_at: Optional[datetime] = None
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    related_order_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


class PerformanceMetrics(BaseModel):
    total_trades: int = Field(0, description="Número total de operaciones cerradas")
    winning_trades: int = Field(0, description="Número de operaciones con ganancia")
    losing_trades: int = Field(0, description="Número de operaciones con pérdida")
    win_rate: float = Field(0.0, description="Porcentaje de operaciones ganadoras sobre el total (excluyendo break-even)")
    total_pnl: float = Field(0.0, description="Ganancia/Pérdida neta total")
    avg_pnl_per_trade: float = Field(0.0, description="Ganancia/Pérdida promedio por operación")
    best_trade_pnl: float = Field(0.0, description="PnL de la mejor operación")
    worst_trade_pnl: float = Field(0.0, description="PnL de la peor operación")
    best_trade_symbol: Optional[str] = Field(None, description="Símbolo de la mejor operación")
    worst_trade_symbol: Optional[str] = Field(None, description="Símbolo de la peor operación")
    period_start: Optional[datetime] = Field(None, description="Fecha de inicio del periodo analizado")
    period_end: Optional[datetime] = Field(None, description="Fecha de fin del periodo analizado")
    total_volume_traded: float = Field(0.0, description="Volumen total operado (en USDT)")

    model_config = ConfigDict(populate_by_name=True)


class ConfirmRealTradeRequest(BaseModel):
    opportunity_id: UUID = Field(..., description="ID de la oportunidad de trading a confirmar.")
    user_id: UUID = Field(..., description="ID del usuario que confirma la operación.")


class CapitalManagementStatus(BaseModel):
    total_capital_usd: float = Field(0.0, description="Capital total gestionado en USD.")
    available_for_new_trades_usd: float = Field(0.0, description="Capital disponible para nuevas operaciones.")
    daily_capital_committed_usd: float = Field(0.0, description="Capital ya comprometido en el día actual.")
    daily_capital_limit_usd: float = Field(0.0, description="Límite de capital diario que se puede arriesgar.")
    high_risk_positions_count: int = Field(0, description="Número de posiciones consideradas de alto riesgo.")


# Type aliases for common data structures
ConfigDict = Dict[str, Any]
MetricsDict = Dict[str, Union[int, float, str]]
HeadersDict = Dict[str, str]
ParamsDict = Dict[str, Union[str, int, float, bool]]
JSONData = Dict[str, Any]
QueryParams = Dict[str, Union[str, int, float, bool, List[str]]]

# Generic types
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class ProcessingResult(BaseModel, Generic[T]):
    """Result of a processing operation"""

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper"""

    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None
    status_code: int = 200
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LogLevel(Enum):
    """Logging levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ValidationResult(Enum):
    """Validation result types"""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    PENDING = "pending"


class ProcessingStatus(Enum):
    """Processing status types"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SystemMetrics(BaseModel):
    """System performance metrics"""

    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationError(BaseModel):
    """Validation error details"""

    field: str
    message: str
    code: Optional[str] = None
    value: Optional[Any] = None


class PaginationInfo(BaseModel):
    """Pagination information"""

    page: int = 1
    page_size: int = 10
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False


class SearchCriteria(BaseModel):
    """Search criteria for queries"""

    query: Optional[str] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # "asc" or "desc"
    pagination: Optional[PaginationInfo] = None


class BusinessProfile(BaseModel):
    """Business profile information"""

    business_id: str
    name: str
    category: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    hours: Dict[str, str] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    coordinates: Optional[Tuple[float, float]] = None  # (latitude, longitude)
    verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Union types for flexibility
ConfigValue = Union[str, int, float, bool, List[str], Dict[str, Any]]
DataSource = Union[str, Dict[str, Any], Path]
ProcessingInput = Union[str, Dict[str, Any], List[Any]]
ProcessingOutput = Union[str, Dict[str, Any], List[Any]]
Identifier = Union[str, int]
Timestamp = Union[datetime, str, int, float]

# Callback types
CallbackFunction = Union[callable, None]
ValidationFunction = callable
ProcessingFunction = callable


class TaskInfo(BaseModel):
    """Task information for background processing"""

    task_id: str
    name: str
    status: ProcessingStatus
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CacheConfig(BaseModel):
    """Cache configuration"""

    enabled: bool = True
    ttl: int = 3600  # Time to live in seconds
    max_size: int = 1000
    backend: str = "memory"  # "memory", "redis", "file"


class RetryConfig(BaseModel):
    """Retry configuration for operations"""

    max_attempts: int = 3
    delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    exceptions: Tuple[Type[Exception], ...] = (Exception,)


# Exportar los modelos de dominio para que otros módulos puedan usarlos
__all__ = [
    "Kline",
    "MarketData",
    "Ticker",
    "ServiceName",
    "APICredential",
    "TelegramConnectionStatus",
    "BinanceConnectionStatus",
    "AssetBalance",
    "PortfolioAsset",
    "PortfolioSummary",
    "PortfolioSnapshot",
    "NotificationPreference",
    "Watchlist",
    "RiskProfileSettings",
    "RealTradingSettings",
    "AIAnalysisConfidenceThresholds",
    "AiStrategyConfiguration",
    "McpServerPreference",
    "DashboardLayoutProfile",
    "CloudSyncPreferences",
    "UserConfiguration",
    "NotificationPriority",
    "NotificationAction",
    "Notification",
    "OpportunitySourceType",
    "OpportunityStatus",
    "AIAnalysis",
    "Opportunity",
    "PerformanceMetrics",
    "ConfirmRealTradeRequest",
    "CapitalManagementStatus",
    "ProcessingResult",
    "APIResponse",
    "LogLevel",
    "ValidationResult",
    "ProcessingStatus",
    "SystemMetrics",
    "ValidationError",
    "PaginationInfo",
    "SearchCriteria",
    "BusinessProfile",
    "TaskInfo",
    "CacheConfig",
    "RetryConfig",
    "ConfigValue",
    "DataSource",
    "ProcessingInput",
    "ProcessingOutput",
    "Identifier",
    "Timestamp",
    "CallbackFunction",
    "ValidationFunction",
    "ProcessingFunction",
]
