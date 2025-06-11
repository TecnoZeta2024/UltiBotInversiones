from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

class OperatingMode(str, Enum):
    PAPER = "paper"
    REAL = "real"

class StrategyPerformanceData(BaseModel):
    strategy_id: UUID = Field(..., alias="strategyId", description="The unique identifier of the strategy.")
    strategy_name: str = Field(..., alias="strategyName", description="The name of the strategy.")
    mode: OperatingMode = Field(..., description="The operating mode (paper or real).")
    total_operations: int = Field(..., alias="totalOperations", ge=0, description="Total number of operations executed.")
    total_pnl: float = Field(..., alias="totalPnl", description="Total Profit & Loss generated.")
    win_rate: float = Field(..., ge=0, le=100, description="Percentage of winning operations (0-100).")

    class Config:
        populate_by_name = True # Allows using alias for field population
        use_enum_values = True  # Ensures enum values are used in serialization

# For API responses that return a list of these objects
StrategyPerformanceResponse = List[StrategyPerformanceData]
