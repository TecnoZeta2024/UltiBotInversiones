import logging
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import Depends

# Importar modelos de dominio y tipos de datos compartidos
from src.shared.data_types import PortfolioSnapshot, PortfolioSummary, PortfolioAsset, AssetBalance, Trade
from src.ultibot_backend.core.domain_models.user_configuration_models import UserConfiguration, PaperTradingAsset
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.core.exceptions import UltiBotError, ConfigurationError, ExternalAPIError, PortfolioError

logger = logging.getLogger(__name__)

class PortfolioService:
    """
    Servicio para gestionar y proporcionar el estado del portafolio (paper trading y real).
    """
    def __init__(self, 
                 market_data_service: MarketDataService = Depends(MarketDataService), 
                 persistence_service: SupabasePersistenceService = Depends(SupabasePersistenceService)
                 ):
        self.market_data_service = market_data_service
        self.persistence_service = persistence_service
        self.paper_trading_balance: float = 0.0
        self.paper_trading_assets: Dict[str, PortfolioAsset] = {} # Símbolo -> PortfolioAsset
        self.user_id: Optional[UUID] = None

    async def _persist_paper_trading_assets(self, user_id: UUID):
        if not self.user_id or self.user_id != user_id:
            logger.warning(f"Intento de persistir activos para un usuario ({user_id}) no inicializado.")
            return

        try:
            config_data = await self.persistence_service.get_user_configuration()
            if not config_data:
                raise ConfigurationError(f"No se encontró configuración para el usuario {user_id}.")

            if 'id' in config_data and isinstance(config_data['id'], UUID):
                config_data['id'] = str(config_data['id'])
            if 'user_id' in config_data and isinstance(config_data['user_id'], UUID):
                config_data['user_id'] = str(config_data['user_id'])

            user_config = UserConfiguration(**config_data)
            
            persistent_assets = [
                PaperTradingAsset(
                    asset=asset.symbol,
                    quantity=asset.quantity,
                    entry_price=asset.entry_price
                )
                for asset in self.paper_trading_assets.values() if asset.entry_price is not None
            ]
            user_config.paper_trading_assets = persistent_assets
            
            await self.persistence_service.upsert_user_configuration(
                user_config.model_dump(mode='json', by_alias=True, exclude_none=True)
            )
            logger.info(f"Activos de paper trading persistidos para el usuario {user_id}.")
        except Exception as e:
            logger.critical(f"Error inesperado al persistir activos de paper trading para {user_id}: {e}", exc_info=True)
            
    async def initialize_portfolio(self, user_id: UUID):
        self.user_id = user_id
        self.paper_trading_assets = {}
        try:
            config_data = await self.persistence_service.get_user_configuration()
            if config_data:
                if 'id' in config_data and isinstance(config_data['id'], UUID):
                    config_data['id'] = str(config_data['id'])
                if 'user_id' in config_data and isinstance(config_data['user_id'], UUID):
                    config_data['user_id'] = str(config_data['user_id'])
                
                user_config = UserConfiguration(**config_data)
            else:
                user_config = None
            
            if user_config:
                self.paper_trading_balance = user_config.default_paper_trading_capital or 10000.0
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
                    logger.info(f"{len(self.paper_trading_assets)} activos de paper trading cargados para {user_id}.")
            else:
                self.paper_trading_balance = 10000.0
                logger.info(f"No se encontró configuración para {user_id}. Usando valores por defecto.")

            logger.info(f"Portafolio de paper trading inicializado para {user_id} con capital: {self.paper_trading_balance}")
        except Exception as e:
            logger.critical(f"Error inesperado al inicializar el portafolio para {user_id}: {e}", exc_info=True)
            self.paper_trading_balance = 10000.0
            raise UltiBotError(f"Error inesperado al inicializar el portafolio: {e}")

    async def get_portfolio_snapshot(self, user_id: UUID) -> PortfolioSnapshot:
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
        available_balance_usdt = 0.0
        total_assets_value_usd = 0.0
        market_data = {}

        try:
            binance_balances: List[AssetBalance] = await self.market_data_service.get_binance_spot_balances()
            assets_to_value = [f"{b.asset.upper()}USDT" for b in binance_balances if b.total > 0 and b.asset != "USDT"]
            
            if assets_to_value:
                unique_assets_to_value = sorted(list(set(assets_to_value)))
                market_data = await self.market_data_service.get_market_data_rest(unique_assets_to_value)

            for balance in binance_balances:
                if balance.asset == "USDT":
                    available_balance_usdt = balance.free
                elif balance.total > 0:
                    symbol_pair = f"{balance.asset.upper()}USDT"
                    price_info = market_data.get(symbol_pair)
                    
                    if price_info and "lastPrice" in price_info:
                        current_price = price_info["lastPrice"]
                        current_value = balance.total * current_price
                        total_assets_value_usd += current_value
                        real_assets.append(PortfolioAsset(symbol=balance.asset, quantity=balance.total, entry_price=None, current_price=current_price, current_value_usd=current_value, unrealized_pnl_usd=None, unrealized_pnl_percentage=None))
                    else:
                        logger.warning(f"No se pudo obtener el precio para {symbol_pair} en portafolio real.")
                        real_assets.append(PortfolioAsset(symbol=balance.asset, quantity=balance.total, entry_price=None, current_price=None, current_value_usd=None, unrealized_pnl_usd=None, unrealized_pnl_percentage=None))
            
            return PortfolioSummary(
                available_balance_usdt=available_balance_usdt,
                total_assets_value_usd=total_assets_value_usd,
                total_portfolio_value_usd=available_balance_usdt + total_assets_value_usd,
                assets=real_assets,
                error_message=None
            )
        except UltiBotError as e:
            logger.error(f"Error al obtener resumen de portafolio real para {user_id}: {e}")
            return PortfolioSummary(available_balance_usdt=0.0, total_assets_value_usd=0.0, total_portfolio_value_usd=0.0, assets=[], error_message=str(e))
        except Exception as e:
            logger.critical(f"Error inesperado al obtener resumen de portafolio real para {user_id}: {e}", exc_info=True)
            return PortfolioSummary(available_balance_usdt=0.0, total_assets_value_usd=0.0, total_portfolio_value_usd=0.0, assets=[], error_message="Error inesperado.")

    async def _get_paper_trading_summary(self) -> PortfolioSummary:
        total_assets_value_usd = 0.0
        paper_assets: List[PortfolioAsset] = []

        if self.paper_trading_assets:
            assets_to_value = [f"{asset.symbol}USDT" for asset in self.paper_trading_assets.values()]
            if assets_to_value:
                effective_user_id = self.user_id or UUID("00000000-0000-0000-0000-000000000001")
                market_data = await self.market_data_service.get_market_data_rest(assets_to_value)
                for symbol, asset in self.paper_trading_assets.items():
                    symbol_pair = f"{symbol}USDT"
                    price_info = market_data.get(symbol_pair)
                    if price_info and "lastPrice" in price_info:
                        current_price = price_info["lastPrice"]
                        current_value = asset.quantity * current_price
                        total_assets_value_usd += current_value
                        asset.current_price = current_price
                        asset.current_value_usd = current_value
                        if asset.entry_price and asset.quantity > 0 and asset.entry_price > 0:
                            pnl_usd = (current_price - asset.entry_price) * asset.quantity
                            asset.unrealized_pnl_usd = pnl_usd
                            denominator = asset.entry_price * asset.quantity
                            if denominator > 0:
                                asset.unrealized_pnl_percentage = (pnl_usd / denominator) * 100
                            else:
                                asset.unrealized_pnl_percentage = 0.0
                    else:
                        logger.warning(f"No se pudo obtener precio para {symbol_pair} en paper trading.")
                    paper_assets.append(asset)

        return PortfolioSummary(
            available_balance_usdt=self.paper_trading_balance,
            total_assets_value_usd=total_assets_value_usd,
            total_portfolio_value_usd=self.paper_trading_balance + total_assets_value_usd,
            assets=paper_assets,
            error_message=None
        )

    async def update_paper_trading_balance(self, user_id: UUID, amount: float):
        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        self.paper_trading_balance += amount
        try:
            config_data = await self.persistence_service.get_user_configuration()
            if config_data:
                if 'id' in config_data and isinstance(config_data['id'], UUID):
                    config_data['id'] = str(config_data['id'])
                if 'user_id' in config_data and isinstance(config_data['user_id'], UUID):
                    config_data['user_id'] = str(config_data['user_id'])
                user_config = UserConfiguration(**config_data)
            else:
                user_config = None

            if user_config:
                user_config.default_paper_trading_capital = self.paper_trading_balance
                await self.persistence_service.upsert_user_configuration(user_config.model_dump(mode='json', by_alias=True, exclude_none=True))
            else:
                raise ConfigurationError(f"No se encontró config para {user_id}.")
        except Exception as e:
            raise UltiBotError(f"Error al actualizar saldo de paper trading: {e}")

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
                if existing_asset.entry_price is not None and existing_asset.quantity > 0:
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
        logger.info(f"Portafolio de paper (entrada) actualizado para {user_id}. Balance: {self.paper_trading_balance}")

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
            logger.warning(f"Activo {symbol} no encontrado en paper portfolio al cerrar trade {trade.id}.")

        await self._persist_paper_trading_assets(user_id)
        logger.info(f"Portafolio de paper (salida) actualizado para {user_id}. Balance: {self.paper_trading_balance}")

    async def get_real_usdt_balance(self, user_id: UUID) -> float:
        try:
            binance_balances: List[AssetBalance] = await self.market_data_service.get_binance_spot_balances()
            usdt_balance = next((b.free for b in binance_balances if b.asset == "USDT"), 0.0)
            return usdt_balance
        except ExternalAPIError as e:
            raise PortfolioError(f"No se pudo obtener el saldo de USDT de Binance: {e}") from e
        except Exception as e:
            raise PortfolioError(f"Error inesperado al obtener el saldo de USDT: {e}") from e
