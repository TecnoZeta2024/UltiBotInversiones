import logging
import json
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from fastapi import Depends

from shared.data_types import PortfolioSnapshot, PortfolioSummary, PortfolioAsset, AssetBalance, Trade
from core.domain_models.user_configuration_models import UserConfiguration, PaperTradingAsset, Theme, RiskProfile
from services.market_data_service import MarketDataService
from core.ports.persistence_service import IPersistenceService
from core.exceptions import UltiBotError, ConfigurationError, ExternalAPIError, PortfolioError

logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(self, 
                 market_data_service: MarketDataService, 
                 persistence_service: IPersistenceService):
        self.market_data_service = market_data_service
        self._persistence_service = persistence_service
        self.paper_trading_balance: Decimal = Decimal("0.0")
        self.paper_trading_assets: Dict[str, PortfolioAsset] = {}
        self.user_id: Optional[UUID] = None

    async def _persist_paper_trading_assets(self, user_id: UUID):
        if not self.user_id or self.user_id != user_id:
            logger.warning(f"Attempt to persist assets for uninitialized user {user_id}.")
            return

        try:
            user_config_dict = await self._persistence_service.get_one("user_configurations", f"user_id = '{user_id}'")
            if not user_config_dict:
                raise ConfigurationError(f"No configuration found for user {user_id}.")
            
            user_config = UserConfiguration(**user_config_dict)

            persistent_assets = [
                PaperTradingAsset(
                    asset=asset.symbol,
                    quantity=asset.quantity,
                    entry_price=asset.entry_price
                )
                for asset in self.paper_trading_assets.values() if asset.entry_price is not None
            ]
            user_config.paper_trading_assets = persistent_assets
            
            await self._persistence_service.upsert_user_configuration(user_config.model_dump())
            logger.info(f"Paper trading assets persisted for user {user_id}.")
        except Exception as e:
            logger.critical(f"Unexpected error persisting paper trading assets for {user_id}: {e}", exc_info=True)
            
    async def initialize_portfolio(self, user_id: UUID):
        self.user_id = user_id
        self.paper_trading_assets = {}
        try:
            user_config_dict = await self._persistence_service.get_one("user_configurations", f"user_id = '{user_id}'")
            
            if user_config_dict:
                for key in ['risk_profile_settings', 'paper_trading_assets', 'notification_preferences', 'watchlists', 'favorite_pairs', 'real_trading_settings', 'ai_strategy_configurations', 'ai_analysis_confidence_thresholds', 'mcp_server_preferences', 'dashboard_layout_profiles', 'dashboard_layout_config', 'cloud_sync_preferences']:
                    if key in user_config_dict and isinstance(user_config_dict[key], str):
                        try:
                            user_config_dict[key] = json.loads(user_config_dict[key])
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON for key {key}, setting to None.")
                            user_config_dict[key] = None
                
                user_config = UserConfiguration(**user_config_dict)
                self.paper_trading_balance = user_config.default_paper_trading_capital or Decimal("10000.0")
                if user_config.paper_trading_assets:
                    for asset_data in user_config.paper_trading_assets:
                        self.paper_trading_assets[asset_data.asset] = PortfolioAsset(
                            symbol=asset_data.asset,
                            quantity=asset_data.quantity,
                            entry_price=asset_data.entry_price,
                            current_price=None,
                            current_value_usd=None,
                            unrealized_pnl_usd=None,
                            unrealized_pnl_percentage=None
                        )
                    logger.info(f"Loaded {len(self.paper_trading_assets)} paper trading assets for {user_id}.")
            else:
                self.paper_trading_balance = Decimal("10000.0")
                logger.info(f"No configuration found for {user_id}. Using default values.")

            logger.info(f"Paper trading portfolio initialized for {user_id} with capital: {self.paper_trading_balance}")
        except Exception as e:
            logger.critical(f"Unexpected error initializing portfolio for {user_id}: {e}", exc_info=True)
            self.paper_trading_balance = Decimal("10000.0")
            raise UltiBotError(f"Unexpected error initializing portfolio: {e}")

    async def get_portfolio_snapshot(self, user_id: UUID, trading_mode: str = "both") -> PortfolioSnapshot:
        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        real_trading_summary = await self._get_real_trading_summary(user_id)
        paper_trading_summary = await self._get_paper_trading_summary()

        return PortfolioSnapshot(
            paper_trading=paper_trading_summary,
            real_trading=real_trading_summary,
            last_updated=datetime.utcnow()
        )

    async def _get_real_trading_summary(self, user_id: UUID) -> PortfolioSummary:
        real_assets: List[PortfolioAsset] = []
        available_balance_usdt = Decimal("0.0")
        total_assets_value_usd = Decimal("0.0")
        market_data = {}

        try:
            binance_balances: List[AssetBalance] = await self.market_data_service.get_binance_spot_balances()
            assets_to_value = [f"{b.asset.upper()}USDT" for b in binance_balances if b.total > 0 and b.asset != "USDT"]
            
            if assets_to_value:
                unique_assets_to_value = sorted(list(set(assets_to_value)))
                market_data = await self.market_data_service.get_market_data_rest(unique_assets_to_value)

            for balance in binance_balances:
                if balance.asset == "USDT":
                    available_balance_usdt = Decimal(str(balance.free))
                elif balance.total > 0:
                    symbol_pair = f"{balance.asset.upper()}USDT"
                    price_info = market_data.get(symbol_pair)
                    
                    if price_info and "lastPrice" in price_info:
                        current_price = Decimal(str(price_info["lastPrice"]))
                        current_value = Decimal(str(balance.total)) * current_price
                        total_assets_value_usd += current_value
                        real_assets.append(PortfolioAsset(symbol=balance.asset, quantity=balance.total, entry_price=None, current_price=current_price, current_value_usd=current_value, unrealized_pnl_usd=None, unrealized_pnl_percentage=None))
                    else:
                        logger.warning(f"Could not get price for {symbol_pair} in real portfolio.")
                        real_assets.append(PortfolioAsset(symbol=balance.asset, quantity=balance.total, entry_price=None, current_price=None, current_value_usd=None, unrealized_pnl_usd=None, unrealized_pnl_percentage=None))
            
            return PortfolioSummary(
                available_balance_usdt=available_balance_usdt,
                total_assets_value_usd=total_assets_value_usd,
                total_portfolio_value_usd=available_balance_usdt + total_assets_value_usd,
                assets=real_assets,
                error_message=None
            )
        except UltiBotError as e:
            logger.error(f"Error getting real portfolio summary for {user_id}: {e}")
            return PortfolioSummary(available_balance_usdt=Decimal("0.0"), total_assets_value_usd=Decimal("0.0"), total_portfolio_value_usd=Decimal("0.0"), assets=[], error_message=str(e))
        except Exception as e:
            logger.critical(f"Unexpected error getting real portfolio summary for {user_id}: {e}", exc_info=True)
            return PortfolioSummary(available_balance_usdt=Decimal("0.0"), total_assets_value_usd=Decimal("0.0"), total_portfolio_value_usd=Decimal("0.0"), assets=[], error_message="Unexpected error.")

    async def _get_paper_trading_summary(self) -> PortfolioSummary:
        total_assets_value_usd = Decimal("0.0")
        paper_assets: List[PortfolioAsset] = []

        if self.paper_trading_assets:
            assets_to_value = [f"{asset.symbol}USDT" for asset in self.paper_trading_assets.values()]
            if assets_to_value:
                market_data = await self.market_data_service.get_market_data_rest(assets_to_value)
                for symbol, asset in self.paper_trading_assets.items():
                    symbol_pair = f"{symbol}USDT"
                    price_info = market_data.get(symbol_pair)
                    if price_info and "lastPrice" in price_info:
                        current_price = Decimal(str(price_info["lastPrice"]))
                        current_value = asset.quantity * current_price
                        total_assets_value_usd += current_value
                        asset.current_price = current_price
                        asset.current_value_usd = current_value
                        if asset.entry_price and asset.quantity > Decimal("0") and asset.entry_price > Decimal("0"):
                            pnl_usd = (current_price - asset.entry_price) * asset.quantity
                            asset.unrealized_pnl_usd = pnl_usd
                            denominator = asset.entry_price * asset.quantity
                            if denominator > Decimal("0"):
                                asset.unrealized_pnl_percentage = (pnl_usd / denominator) * Decimal("100")
                            else:
                                asset.unrealized_pnl_percentage = Decimal("0.0")
                    else:
                        logger.warning(f"Could not get price for {symbol_pair} in paper trading.")
                    paper_assets.append(asset)

        return PortfolioSummary(
            available_balance_usdt=self.paper_trading_balance,
            total_assets_value_usd=total_assets_value_usd,
            total_portfolio_value_usd=self.paper_trading_balance + total_assets_value_usd,
            assets=paper_assets,
            error_message=None
        )

    async def update_paper_trading_balance(self, user_id: UUID, amount: Decimal):
        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        self.paper_trading_balance += amount
        try:
            user_config_dict = await self._persistence_service.get_one("user_configurations", f"user_id = '{user_id}'")
            if not user_config_dict:
                user_config = UserConfiguration(
                    user_id=str(user_id),
                    defaultPaperTradingCapital=self.paper_trading_balance,
                    id=str(UUID(int=0)),
                    telegramChatId=None,
                    notificationPreferences=[],
                    enableTelegramNotifications=False,
                    paperTradingActive=True,
                    paperTradingAssets=[],
                    watchlists=[],
                    favoritePairs=[],
                    riskProfile=RiskProfile.MODERATE,
                    riskProfileSettings=None,
                    realTradingSettings=None,
                    aiStrategyConfigurations=[],
                    aiAnalysisConfidenceThresholds=None,
                    mcpServerPreferences=[],
                    selectedTheme=Theme.DARK,
                    dashboardLayoutProfiles={},
                    activeDashboardLayoutProfileId=None,
                    dashboardLayoutConfig={},
                    cloudSyncPreferences=None,
                    createdAt=datetime.utcnow(),
                    updatedAt=datetime.utcnow()
                )
                await self._persistence_service.upsert_user_configuration(user_config.model_dump())
            else:
                user_config = UserConfiguration(**user_config_dict)
                user_config.default_paper_trading_capital = self.paper_trading_balance
                await self._persistence_service.upsert_user_configuration(user_config.model_dump())
        except Exception as e:
            raise UltiBotError(f"Error updating paper trading balance: {e}")

    async def update_paper_portfolio_after_entry(self, trade: Trade):
        user_id = trade.user_id
        symbol = trade.symbol
        quantity = trade.entryOrder.executedQuantity
        executed_price = trade.entryOrder.executedPrice
        side = trade.side

        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        trade_value = quantity * executed_price
        self.paper_trading_balance -= trade_value

        if symbol in self.paper_trading_assets:
            existing_asset = self.paper_trading_assets[symbol]
            if side == 'BUY':
                total_quantity = existing_asset.quantity + quantity
                if existing_asset.entry_price is not None and existing_asset.quantity > Decimal("0"):
                    new_entry_price = ((existing_asset.entry_price * existing_asset.quantity) + (executed_price * quantity)) / total_quantity
                else:
                    new_entry_price = executed_price
                existing_asset.quantity = total_quantity
                existing_asset.entry_price = new_entry_price
            elif side == 'SELL':
                existing_asset.quantity -= quantity
        else:
            initial_quantity = quantity if side == 'BUY' else -quantity
            self.paper_trading_assets[symbol] = PortfolioAsset(
                symbol=symbol, 
                quantity=initial_quantity, 
                entry_price=executed_price,
                current_price=None,
                current_value_usd=None,
                unrealized_pnl_usd=None,
                unrealized_pnl_percentage=None
            )

        await self._persist_paper_trading_assets(user_id)
        logger.info(f"Paper portfolio (entry) updated for {user_id}. Balance: {self.paper_trading_balance}")

    async def update_paper_portfolio_after_exit(self, trade: Trade):
        user_id = trade.user_id
        symbol = trade.symbol
        quantity = trade.entryOrder.executedQuantity
        pnl_usd = trade.pnl_usd
        side = trade.side

        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        if pnl_usd is not None:
            self.paper_trading_balance += pnl_usd

        if symbol in self.paper_trading_assets:
            asset = self.paper_trading_assets[symbol]
            if side == 'BUY':
                if asset.quantity <= quantity:
                    del self.paper_trading_assets[symbol]
                else:
                    asset.quantity -= quantity
            elif side == 'SELL':
                if asset.quantity >= -quantity:
                     del self.paper_trading_assets[symbol]
                else:
                    asset.quantity += quantity
        else:
            logger.warning(f"Asset {symbol} not found in paper portfolio when closing trade {trade.id}.")

        await self._persist_paper_trading_assets(user_id)
        logger.info(f"Paper portfolio (exit) updated for {user_id}. Balance: {self.paper_trading_balance}")

    async def get_real_usdt_balance(self, user_id: UUID) -> Decimal:
        try:
            binance_balances: List[AssetBalance] = await self.market_data_service.get_binance_spot_balances()
            usdt_balance = next((b.free for b in binance_balances if b.asset == "USDT"), Decimal("0.0"))
            return usdt_balance
        except ExternalAPIError as e:
            raise PortfolioError(f"Could not get USDT balance from Binance: {e}") from e
        except Exception as e:
            raise PortfolioError(f"Unexpected error getting USDT balance: {e}") from e
