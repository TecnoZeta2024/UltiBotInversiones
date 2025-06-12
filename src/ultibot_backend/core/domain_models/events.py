import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from ultibot_backend.core.domain_models.trading import Order, Trade

class BaseEvent(BaseModel):
    """
    Base class for all events in the system.
    """
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    event_type: str

    class Config:
        frozen = True

class OpportunityDetectedEvent(BaseEvent):
    """
    Event published when a trading opportunity is detected.
    """
    event_type: str = "OpportunityDetected"
    symbol: str
    opportunity_details: Dict[str, Any]

class OrderPlacedEvent(BaseEvent):
    """
    Event published when an order has been placed.
    """
    event_type: str = "OrderPlaced"
    order: Order

class TradeExecutedEvent(BaseEvent):
    """
    Event published when a trade has been successfully executed.
    """
    event_type: str = "TradeExecuted"
    trade: Trade
    order: Order

class OrderStatusChangedEvent(BaseEvent):
    """
    Event published when the status of an order changes.
    """
    event_type: str = "OrderStatusChanged"
    order_id: str
    new_status: str
    details: Optional[Dict[str, Any]] = None

class PortfolioChangedEvent(BaseEvent):
    """
    Event published when the portfolio composition changes.
    """
    event_type: str = "PortfolioChanged"
    portfolio_snapshot: Dict[str, Any]

class AlertTriggeredEvent(BaseEvent):
    """
    Event published when a user-defined alert is triggered.
    """
    event_type: str = "AlertTriggered"
    alert_name: str
    symbol: str
    message: str

class PortfolioUpdatedEvent(BaseEvent):
    """
    Event published when the portfolio has been updated.
    """
    event_type: str = "PortfolioUpdated"
    portfolio_data: Dict[str, Any]

class StrategyActivatedEvent(BaseEvent):
    """
    Event published when a strategy is activated.
    """
    event_type: str = "StrategyActivated"
    strategy_name: str
    details: Dict[str, Any]

class AIAnalysisCompletedEvent(BaseEvent):
    """
    Event published when an AI analysis cycle is complete.
    """
    event_type: str = "AIAnalysisCompleted"
    symbol: str
    analysis_result: Dict[str, Any]
    decision: str

class ToolExecutedEvent(BaseEvent):
    """
    Event published when a tool from the MCPToolHub has been executed.
    """
    event_type: str = "ToolExecuted"
    tool_name: str
    parameters: Dict[str, Any]
    result: Any

class PromptUpdatedEvent(BaseEvent):
    """
    Event published when a prompt is updated in the system.
    """
    event_type: str = "PromptUpdated"
    prompt_name: str
    new_content: str

class ScanCompletedEvent(BaseEvent):
    """
    Event published when a market scan is completed.
    """
    event_type: str = "ScanCompleted"
    preset_name: str
    opportunities_found: int
    symbols_scanned: List[str]

class AIAnalysisTriggeredEvent(BaseEvent):
    """
    Event published when an AI analysis is triggered for a trading opportunity.
    """
    event_type: str = "AIAnalysisTriggered"
    symbol: str
    opportunity_id: str
    analysis_request_id: str
    trigger_reason: str
