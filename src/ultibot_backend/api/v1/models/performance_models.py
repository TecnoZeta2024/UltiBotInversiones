from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

class OperatingMode(str, Enum):
    PAPER = "paper"
    REAL = "real"

class StrategyPerformanceData(BaseModel):
    strategyId: UUID = Field(..., description="The unique identifier of the strategy.")
    strategyName: str = Field(..., description="The name of the strategy.")
    mode: OperatingMode = Field(..., description="The operating mode (paper or real).")
    totalOperations: int = Field(..., ge=0, description="Total number of operations executed.")
    totalPnl: float = Field(..., description="Total Profit & Loss generated.")
    win_rate: float = Field(..., ge=0, le=100, description="Percentage of winning operations (0-100).")

    class Config:
        use_enum_values = True

# For API responses that return a list of these objects
StrategyPerformanceResponse = List[StrategyPerformanceData]
