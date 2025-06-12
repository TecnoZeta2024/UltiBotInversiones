"""
MCP Tools Adapters Package.

Este paquete contiene los adaptadores específicos para herramientas MCP,
cada uno implementando la interfaz BaseMCPAdapter.
"""

from .base_mcp_adapter import BaseMCPAdapter
from .market_sentiment_adapter import MarketSentimentAdapter
from .web3_research_adapter import Web3ResearchAdapter

__all__ = [
    "BaseMCPAdapter",
    "MarketSentimentAdapter", 
    "Web3ResearchAdapter"
]
