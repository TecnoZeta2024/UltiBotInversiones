import pandas as pd
from typing import List, Dict, Any

from core.domain_models.market_data_models import MarketDataORM
from features import technical_indicators

class FeatureService:
    """
    Service responsible for calculating and providing features for market data.
    """

    def __init__(self):
        # In the future, this could hold configuration for which features to calculate
        pass

    def calculate_all_features(self, market_data: List[MarketDataORM]) -> Dict[str, Any]:
        """
        Calculates all available technical indicators for the given market data.
        """
        if not market_data:
            return {}

        features = {
            "sma_10": technical_indicators.calculate_sma(market_data, window=10),
            "sma_50": technical_indicators.calculate_sma(market_data, window=50),
            "ema_10": technical_indicators.calculate_ema(market_data, window=10),
            "ema_50": technical_indicators.calculate_ema(market_data, window=50),
            "volatility_10": technical_indicators.calculate_volatility(market_data, window=10),
            "volatility_50": technical_indicators.calculate_volatility(market_data, window=50),
            "roc_10": technical_indicators.calculate_roc(market_data, window=10),
            "rsi_14": technical_indicators.calculate_rsi(market_data, window=14),
            "macd": technical_indicators.calculate_macd(market_data)
        }
        
        return features
