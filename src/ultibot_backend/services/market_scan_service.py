"""Market Scan Service.

This module provides services for market scanning, filtering, and preset management
for the UltiBotInversiones trading system.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from ..core.domain_models.user_configuration_models import (
    MarketScanConfiguration,
    ScanPreset,
    AssetTradingParameters,
    MarketCapRange,
    VolumeFilter,
    TrendDirection
)
from ..adapters.binance_adapter import BinanceAdapter
from ..adapters.mobula_adapter import MobulaAdapter
from ..adapters.persistence_service import SupabasePersistenceService

logger = logging.getLogger(__name__)


class MarketScanService:
    """Service for market scanning and filtering operations."""
    
    def __init__(
        self,
        binance_adapter: BinanceAdapter,
        mobula_adapter: MobulaAdapter,
        persistence_service: SupabasePersistenceService
    ):
        """Initialize the market scan service.
        
        Args:
            binance_adapter: Binance API adapter for trading data.
            mobula_adapter: Mobula API adapter for market data.
            persistence_service: Service for data persistence.
        """
        self.binance_adapter = binance_adapter
        self.mobula_adapter = mobula_adapter
        self.persistence_service = persistence_service
        
    async def scan_market_with_config(
        self, 
        scan_config: MarketScanConfiguration,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Execute market scan using specified configuration.
        
        Args:
            scan_config: The scan configuration to apply.
            user_id: User identifier for logging and caching.
            
        Returns:
            List of market opportunities matching the scan criteria.
            
        Raises:
            Exception: If scan execution fails.
        """
        try:
            logger.info(f"Starting market scan '{scan_config.name}' for user {user_id}")
            
            # Get base market data from Binance
            market_data = await self._get_base_market_data(scan_config)
            
            # Apply price movement filters
            filtered_data = self._apply_price_filters(market_data, scan_config)
            
            # Apply volume filters
            filtered_data = await self._apply_volume_filters(filtered_data, scan_config)
            
            # Apply market cap filters
            filtered_data = await self._apply_market_cap_filters(filtered_data, scan_config)
            
            # Apply technical analysis filters
            filtered_data = await self._apply_technical_filters(filtered_data, scan_config)
            
            # Apply exclusion filters
            filtered_data = self._apply_exclusion_filters(filtered_data, scan_config)
            
            # Sort and limit results
            results = self._sort_and_limit_results(filtered_data, scan_config)
            
            logger.info(f"Market scan completed: {len(results)} opportunities found")
            
            return results
            
        except Exception as e:
            logger.error(f"Market scan failed: {str(e)}")
            raise
    
    async def scan_with_preset(
        self, 
        preset_id: str, 
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Execute market scan using a preset configuration.
        
        Args:
            preset_id: ID of the preset to use.
            user_id: User identifier.
            
        Returns:
            List of market opportunities.
            
        Raises:
            ValueError: If preset is not found.
        """
        preset = await self.get_scan_preset(preset_id, user_id)
        if not preset:
            raise ValueError(f"Scan preset '{preset_id}' not found")
        
        # Update usage statistics
        await self._update_preset_usage(preset_id, user_id)
        
        return await self.scan_market_with_config(preset.market_scan_configuration, user_id)
    
    async def create_scan_preset(
        self, 
        preset: ScanPreset, 
        user_id: str
    ) -> ScanPreset:
        """Create a new scan preset.
        
        Args:
            preset: The preset to create.
            user_id: User identifier.
            
        Returns:
            The created preset with generated ID and timestamps.
        """
        if not preset.id:
            preset.id = str(uuid4())
        
        preset.created_at = datetime.utcnow()
        preset.updated_at = preset.created_at
        
        # Ensure the market scan configuration has proper timestamps too
        if not preset.market_scan_configuration.created_at:
            preset.market_scan_configuration.created_at = preset.created_at
        preset.market_scan_configuration.updated_at = preset.created_at
        
        await self.persistence_service.save_scan_preset(preset, user_id)
        
        logger.info(f"Created scan preset '{preset.name}' (ID: {preset.id}) for user {user_id}")
        
        return preset
    
    async def update_scan_preset(
        self, 
        preset: ScanPreset, 
        user_id: str
    ) -> ScanPreset:
        """Update an existing scan preset.
        
        Args:
            preset: The preset to update.
            user_id: User identifier.
            
        Returns:
            The updated preset.
            
        Raises:
            ValueError: If preset is not found.
        """
        existing_preset = await self.get_scan_preset(preset.id, user_id)
        if not existing_preset:
            raise ValueError(f"Scan preset '{preset.id}' not found")
        
        preset.updated_at = datetime.utcnow()
        preset.market_scan_configuration.updated_at = preset.updated_at
        
        await self.persistence_service.update_scan_preset(preset, user_id)
        
        logger.info(f"Updated scan preset '{preset.name}' (ID: {preset.id}) for user {user_id}")
        
        return preset
    
    async def delete_scan_preset(self, preset_id: str, user_id: str) -> bool:
        """Delete a scan preset.
        
        Args:
            preset_id: ID of the preset to delete.
            user_id: User identifier.
            
        Returns:
            True if deleted successfully, False if not found.
        """
        result = await self.persistence_service.delete_scan_preset(preset_id, user_id)
        
        if result:
            logger.info(f"Deleted scan preset '{preset_id}' for user {user_id}")
        else:
            logger.warning(f"Scan preset '{preset_id}' not found for deletion")
        
        return result
    
    async def get_scan_preset(self, preset_id: str, user_id: str) -> Optional[ScanPreset]:
        """Get a scan preset by ID.
        
        Args:
            preset_id: ID of the preset to retrieve.
            user_id: User identifier.
            
        Returns:
            The scan preset if found, None otherwise.
        """
        return await self.persistence_service.get_scan_preset(preset_id, user_id)
    
    async def list_scan_presets(self, user_id: str) -> List[ScanPreset]:
        """List all scan presets for a user.
        
        Args:
            user_id: User identifier.
            
        Returns:
            List of scan presets.
        """
        return await self.persistence_service.list_scan_presets(user_id)
    
    async def get_system_presets(self) -> List[ScanPreset]:
        """Get system-provided scan presets.
        
        Returns:
            List of system scan presets.
        """
        return await self._create_default_system_presets()
    
    async def _get_base_market_data(
        self, 
        scan_config: MarketScanConfiguration
    ) -> List[Dict[str, Any]]:
        """Get base market data from Binance.
        
        Args:
            scan_config: Scan configuration for filtering quote currencies.
            
        Returns:
            List of market data with 24h ticker information.
        """
        try:
            # Get 24h ticker data from Binance
            tickers = await self.binance_adapter.get_24hr_ticker_data()
            
            # Filter by allowed quote currencies
            allowed_quotes = scan_config.allowed_quote_currencies or ["USDT", "BUSD", "BTC", "ETH"]
            
            filtered_tickers = []
            for ticker in tickers:
                symbol = ticker.get('symbol', '')
                # Check if symbol ends with any allowed quote currency
                if any(symbol.endswith(quote) for quote in allowed_quotes):
                    filtered_tickers.append(ticker)
            
            logger.debug(f"Retrieved {len(filtered_tickers)} tickers matching quote currencies")
            
            return filtered_tickers
            
        except Exception as e:
            logger.error(f"Failed to get base market data: {str(e)}")
            raise
    
    def _apply_price_filters(
        self, 
        market_data: List[Dict[str, Any]], 
        scan_config: MarketScanConfiguration
    ) -> List[Dict[str, Any]]:
        """Apply price movement filters to market data.
        
        Args:
            market_data: Raw market data from exchange.
            scan_config: Scan configuration with price filters.
            
        Returns:
            Filtered market data.
        """
        filtered_data = []
        
        for ticker in market_data:
            try:
                price_change_24h = float(ticker.get('priceChangePercent', 0))
                
                # Apply 24h price change filters
                if scan_config.min_price_change_24h_percent is not None:
                    if price_change_24h < scan_config.min_price_change_24h_percent:
                        continue
                
                if scan_config.max_price_change_24h_percent is not None:
                    if price_change_24h > scan_config.max_price_change_24h_percent:
                        continue
                
                filtered_data.append(ticker)
                
            except (ValueError, TypeError):
                # Skip tickers with invalid price data
                continue
        
        logger.debug(f"Price filters applied: {len(filtered_data)} tickers remaining")
        
        return filtered_data
    
    async def _apply_volume_filters(
        self, 
        market_data: List[Dict[str, Any]], 
        scan_config: MarketScanConfiguration
    ) -> List[Dict[str, Any]]:
        """Apply volume filters to market data.
        
        Args:
            market_data: Market data to filter.
            scan_config: Scan configuration with volume filters.
            
        Returns:
            Volume-filtered market data.
        """
        if scan_config.volume_filter_type == VolumeFilter.NO_FILTER:
            return market_data
        
        filtered_data = []
        
        for ticker in market_data:
            try:
                volume_24h = float(ticker.get('quoteVolume', 0))
                
                # Apply minimum volume filter
                if scan_config.min_volume_24h_usd is not None:
                    if volume_24h < scan_config.min_volume_24h_usd:
                        continue
                
                # For volume multiplier filter, we would need historical data
                # For now, we'll implement basic volume filtering
                if scan_config.volume_filter_type == VolumeFilter.HIGH_VOLUME:
                    # Define high volume as > 10M USD
                    if volume_24h < 10_000_000:
                        continue
                
                filtered_data.append(ticker)
                
            except (ValueError, TypeError):
                continue
        
        logger.debug(f"Volume filters applied: {len(filtered_data)} tickers remaining")
        
        return filtered_data
    
    async def _apply_market_cap_filters(
        self, 
        market_data: List[Dict[str, Any]], 
        scan_config: MarketScanConfiguration
    ) -> List[Dict[str, Any]]:
        """Apply market cap filters using Mobula data.
        
        Args:
            market_data: Market data to filter.
            scan_config: Scan configuration with market cap filters.
            
        Returns:
            Market cap filtered data.
        """
        if not scan_config.market_cap_ranges or MarketCapRange.ALL in scan_config.market_cap_ranges:
            return market_data
        
        filtered_data = []
        
        for ticker in market_data:
            try:
                symbol = ticker.get('symbol', '')
                base_asset = self._extract_base_asset(symbol)
                
                # Get market cap data from Mobula
                market_cap_data = await self.mobula_adapter.get_asset_market_cap(base_asset)
                
                if not market_cap_data:
                    continue
                
                market_cap = market_cap_data.get('market_cap', 0)
                
                # Apply market cap range filters
                if self._passes_market_cap_filter(market_cap, scan_config):
                    ticker['market_cap'] = market_cap
                    filtered_data.append(ticker)
                
            except Exception:
                # Skip assets where we can't get market cap data
                continue
        
        logger.debug(f"Market cap filters applied: {len(filtered_data)} tickers remaining")
        
        return filtered_data
    
    async def _apply_technical_filters(
        self, 
        market_data: List[Dict[str, Any]], 
        scan_config: MarketScanConfiguration
    ) -> List[Dict[str, Any]]:
        """Apply technical analysis filters.
        
        Args:
            market_data: Market data to filter.
            scan_config: Scan configuration with technical filters.
            
        Returns:
            Technically filtered data.
        """
        # For now, implement basic technical filters
        # In a full implementation, you would integrate with technical analysis libraries
        
        filtered_data = []
        
        for ticker in market_data:
            try:
                # RSI filtering (would need historical data for real RSI calculation)
                # For now, use price change as proxy
                price_change = float(ticker.get('priceChangePercent', 0))
                
                # Simple trend direction filtering based on price change
                if scan_config.trend_direction == TrendDirection.BULLISH:
                    if price_change <= 0:
                        continue
                elif scan_config.trend_direction == TrendDirection.BEARISH:
                    if price_change >= 0:
                        continue
                
                filtered_data.append(ticker)
                
            except (ValueError, TypeError):
                continue
        
        logger.debug(f"Technical filters applied: {len(filtered_data)} tickers remaining")
        
        return filtered_data
    
    def _apply_exclusion_filters(
        self, 
        market_data: List[Dict[str, Any]], 
        scan_config: MarketScanConfiguration
    ) -> List[Dict[str, Any]]:
        """Apply exclusion filters to market data.
        
        Args:
            market_data: Market data to filter.
            scan_config: Scan configuration with exclusion filters.
            
        Returns:
            Filtered market data.
        """
        filtered_data = []
        
        excluded_symbols = scan_config.excluded_symbols or []
        
        for ticker in market_data:
            symbol = ticker.get('symbol', '')
            base_asset = self._extract_base_asset(symbol)
            
            # Skip excluded symbols
            if symbol in excluded_symbols or base_asset in excluded_symbols:
                continue
            
            filtered_data.append(ticker)
        
        logger.debug(f"Exclusion filters applied: {len(filtered_data)} tickers remaining")
        
        return filtered_data
    
    def _sort_and_limit_results(
        self, 
        market_data: List[Dict[str, Any]], 
        scan_config: MarketScanConfiguration
    ) -> List[Dict[str, Any]]:
        """Sort and limit scan results.
        
        Args:
            market_data: Filtered market data.
            scan_config: Scan configuration with result limits.
            
        Returns:
            Sorted and limited results.
        """
        # Sort by 24h price change percentage (descending)
        sorted_data = sorted(
            market_data,
            key=lambda x: float(x.get('priceChangePercent', 0)),
            reverse=True
        )
        
        # Apply result limit
        max_results = scan_config.max_results or 50
        limited_results = sorted_data[:max_results]
        
        logger.debug(f"Results sorted and limited to {len(limited_results)} items")
        
        return limited_results
    
    def _extract_base_asset(self, symbol: str) -> str:
        """Extract base asset from trading symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT').
            
        Returns:
            Base asset symbol (e.g., 'BTC').
        """
        # Simple implementation - would need more sophisticated logic for all cases
        common_quotes = ['USDT', 'BUSD', 'BTC', 'ETH', 'BNB']
        
        for quote in common_quotes:
            if symbol.endswith(quote):
                return symbol[:-len(quote)]
        
        return symbol
    
    def _passes_market_cap_filter(
        self, 
        market_cap: float, 
        scan_config: MarketScanConfiguration
    ) -> bool:
        """Check if asset passes market cap filters.
        
        Args:
            market_cap: Asset market cap in USD.
            scan_config: Scan configuration.
            
        Returns:
            True if passes filters, False otherwise.
        """
        # Apply absolute min/max filters
        if scan_config.min_market_cap_usd and market_cap < scan_config.min_market_cap_usd:
            return False
        
        if scan_config.max_market_cap_usd and market_cap > scan_config.max_market_cap_usd:
            return False
        
        # Apply range filters
        if scan_config.market_cap_ranges and MarketCapRange.ALL not in scan_config.market_cap_ranges:
            cap_range = self._get_market_cap_range(market_cap)
            if cap_range not in scan_config.market_cap_ranges:
                return False
        
        return True
    
    def _get_market_cap_range(self, market_cap: float) -> MarketCapRange:
        """Determine market cap range for given value.
        
        Args:
            market_cap: Market cap value in USD.
            
        Returns:
            Corresponding market cap range.
        """
        if market_cap < 300_000_000:
            return MarketCapRange.MICRO
        elif market_cap < 2_000_000_000:
            return MarketCapRange.SMALL
        elif market_cap < 10_000_000_000:
            return MarketCapRange.MID
        elif market_cap < 200_000_000_000:
            return MarketCapRange.LARGE
        else:
            return MarketCapRange.MEGA
    
    async def _update_preset_usage(self, preset_id: str, user_id: str) -> None:
        """Update usage statistics for a preset.
        
        Args:
            preset_id: ID of the preset used.
            user_id: User identifier.
        """
        try:
            preset = await self.get_scan_preset(preset_id, user_id)
            if preset:
                preset.usage_count = (preset.usage_count or 0) + 1
                preset.updated_at = datetime.utcnow()
                await self.persistence_service.update_scan_preset(preset, user_id)
        except Exception as e:
            logger.warning(f"Failed to update preset usage: {str(e)}")
    
    async def _create_default_system_presets(self) -> List[ScanPreset]:
        """Create default system presets for common scenarios.
        
        Returns:
            List of default system presets.
        """
        presets = []
        
        # Momentum Breakout Preset
        momentum_config = MarketScanConfiguration(
            id="system_momentum_breakout",
            name="Momentum Breakout",
            description="Find assets with strong upward momentum",
            min_price_change_24h_percent=5.0,
            max_price_change_24h_percent=50.0,
            volume_filter_type=VolumeFilter.HIGH_VOLUME,
            trend_direction=TrendDirection.BULLISH,
            market_cap_ranges=[MarketCapRange.SMALL, MarketCapRange.MID, MarketCapRange.LARGE],
            max_results=25
        )
        
        momentum_preset = ScanPreset(
            id="system_momentum_breakout",
            name="Momentum Breakout",
            description="Identifies assets experiencing strong upward momentum with high volume",
            category="momentum",
            market_scan_configuration=momentum_config,
            recommended_strategies=["momentum_strategy", "breakout_strategy"],
            is_system_preset=True
        )
        
        presets.append(momentum_preset)
        
        # Value Discovery Preset
        value_config = MarketScanConfiguration(
            id="system_value_discovery",
            name="Value Discovery",
            description="Find undervalued assets with growth potential",
            min_price_change_24h_percent=-10.0,
            max_price_change_24h_percent=5.0,
            volume_filter_type=VolumeFilter.ABOVE_AVERAGE,
            market_cap_ranges=[MarketCapRange.SMALL, MarketCapRange.MID],
            exclude_new_listings_days=30,
            max_results=30
        )
        
        value_preset = ScanPreset(
            id="system_value_discovery",
            name="Value Discovery", 
            description="Discovers potentially undervalued assets with solid fundamentals",
            category="value",
            market_scan_configuration=value_config,
            recommended_strategies=["value_strategy", "contrarian_strategy"],
            is_system_preset=True
        )
        
        presets.append(value_preset)
        
        return presets
