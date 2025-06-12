"""
Módulo de inicialización para el paquete domain_models.
Define los modelos de dominio puros que representan las entidades de negocio
del sistema UltiBotInversiones. Estos modelos son agnósticos a la infraestructura
y no deben importar frameworks externos.
"""

from .trading import (
    TradeId, TickerData, KlineData, OrderSide, OrderType, Trade, Opportunity, TradeResult,
    CommandResult, TradingSignal, StrategyParameters, AnalysisResult
)
from .portfolio import (
    UserId, Portfolio, PortfolioSnapshot
)
from .market import (
    MarketSnapshot
)
from .ai_models import (
    AIAnalysisRequest, AIAnalysisResult
)
from .prompt_models import (
    PromptTemplate, PromptVersion
)
from .scan_presets import (
    ScanPreset, ScanResult
)
from .events import (
    BaseEvent, TradeExecutedEvent, PortfolioUpdatedEvent, StrategyActivatedEvent,
    AIAnalysisCompletedEvent, ToolExecutedEvent, PromptUpdatedEvent, ScanCompletedEvent
)
