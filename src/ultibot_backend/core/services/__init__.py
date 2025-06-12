"""
Módulo de inicialización para el paquete services.
Define los servicios del núcleo que contienen la lógica de negocio pura.
Estos servicios interactúan con los puertos definidos en `core.ports`.
"""

from .trading_engine import TradingEngineService
from .portfolio_manager import PortfolioManagerService
from .event_broker import AsyncEventBroker as EventBroker
# Los siguientes servicios se añadirán en fases posteriores
# from .prompt_manager import PromptManager
# from .mcp_tool_hub import MCPToolHub
# from .market_scanner import MarketScannerService
# from .performance_monitor import PerformanceMonitor
