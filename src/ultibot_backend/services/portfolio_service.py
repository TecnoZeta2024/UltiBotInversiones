import logging
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from src.shared.data_types import PortfolioSnapshot, PortfolioSummary, PortfolioAsset, AssetBalance, UserConfiguration
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.core.exceptions import UltiBotError, ConfigurationError, ExternalAPIError

logger = logging.getLogger(__name__)

class PortfolioService:
    """
    Servicio para gestionar y proporcionar el estado del portafolio (paper trading y real).
    """
    def __init__(self, market_data_service: MarketDataService, config_service: ConfigService):
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.paper_trading_balance: float = 0.0
        self.paper_trading_assets: Dict[str, PortfolioAsset] = {} # Símbolo -> PortfolioAsset
        self.user_id: Optional[UUID] = None # Se establecerá al inicializar o cargar la configuración

    async def initialize_portfolio(self, user_id: UUID):
        """
        Inicializa el portafolio de paper trading cargando la configuración del usuario.
        """
        self.user_id = user_id
        try:
            user_config = await self.config_service.load_user_configuration(user_id)
            self.paper_trading_balance = user_config.defaultPaperTradingCapital or 10000.0 # Usar valor por defecto si no está configurado
            logger.info(f"Portafolio de paper trading inicializado para el usuario {user_id} con capital: {self.paper_trading_balance}")
            # TODO: Cargar activos de paper trading persistidos si aplica (para futuras historias)
        except ConfigurationError as e:
            logger.error(f"Error al cargar la configuración del usuario para inicializar el portafolio: {e}")
            self.paper_trading_balance = 10000.0 # Fallback a un valor por defecto
            raise UltiBotError(f"No se pudo inicializar el portafolio de paper trading debido a un error de configuración: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al inicializar el portafolio para el usuario {user_id}: {e}", exc_info=True)
            self.paper_trading_balance = 10000.0 # Fallback
            raise UltiBotError(f"Error inesperado al inicializar el portafolio: {e}")

    async def get_portfolio_snapshot(self, user_id: UUID) -> PortfolioSnapshot:
        """
        Obtiene un snapshot completo del portafolio, incluyendo paper trading y real.
        """
        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id) # Asegurar que el portafolio esté inicializado para el usuario correcto

        real_trading_summary = await self._get_real_trading_summary(user_id)
        paper_trading_summary = await self._get_paper_trading_summary()

        return PortfolioSnapshot(
            paper_trading=paper_trading_summary,
            real_trading=real_trading_summary,
            last_updated=datetime.utcnow()
        )

    async def _get_real_trading_summary(self, user_id: UUID) -> PortfolioSummary:
        """
        Obtiene el resumen del portafolio real de Binance.
        """
        real_assets: List[PortfolioAsset] = []
        available_balance_usdt = 0.0
        total_assets_value_usd = 0.0

        try:
            binance_balances: List[AssetBalance] = await self.market_data_service.get_binance_spot_balances(user_id)
            
            assets_to_value: List[str] = []
            for balance in binance_balances:
                if balance.asset == "USDT":
                    available_balance_usdt = balance.free # Solo el saldo disponible de USDT
                elif balance.total > 0:
                    assets_to_value.append(f"{balance.asset}USDT") # Asumimos pares con USDT para valoración

            # Obtener precios de mercado para los activos no-USDT
            if assets_to_value:
                market_data = await self.market_data_service.get_market_data_rest(user_id, assets_to_value)
                for balance in binance_balances:
                    if balance.asset != "USDT" and balance.total > 0:
                        symbol_pair = f"{balance.asset}USDT"
                        price_info = market_data.get(symbol_pair)
                        
                        if price_info and "lastPrice" in price_info:
                            current_price = price_info["lastPrice"]
                            current_value = balance.total * current_price
                            total_assets_value_usd += current_value
                            real_assets.append(PortfolioAsset(
                                symbol=balance.asset,
                                quantity=balance.total,
                                current_price=current_price,
                                current_value_usd=current_value,
                                entry_price=None, # No disponible de Binance API directamente
                                unrealized_pnl_usd=None,
                                unrealized_pnl_percentage=None
                            ))
                        else:
                            logger.warning(f"No se pudo obtener el precio para {symbol_pair} para el portafolio real.")
                            real_assets.append(PortfolioAsset(
                                symbol=balance.asset,
                                quantity=balance.total,
                                current_price=None,
                                current_value_usd=None,
                                entry_price=None,
                                unrealized_pnl_usd=None,
                                unrealized_pnl_percentage=None
                            ))
            
            total_portfolio_value_usd = available_balance_usdt + total_assets_value_usd

            return PortfolioSummary(
                available_balance_usdt=available_balance_usdt,
                total_assets_value_usd=total_assets_value_usd,
                total_portfolio_value_usd=total_portfolio_value_usd,
                assets=real_assets,
                error_message=None # Pasar explícitamente None
            )
        except UltiBotError as e:
            logger.error(f"Error al obtener el resumen del portafolio real para el usuario {user_id}: {e}")
            # Retornar un resumen vacío o con valores por defecto en caso de error
            return PortfolioSummary(
                available_balance_usdt=0.0,
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=0.0,
                assets=[],
                error_message=str(e) # Pasar explícitamente el mensaje de error
            )
        except Exception as e:
            logger.critical(f"Error inesperado al obtener el resumen del portafolio real para el usuario {user_id}: {e}", exc_info=True)
            return PortfolioSummary(
                available_balance_usdt=0.0,
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=0.0,
                assets=[],
                error_message="Error inesperado al cargar el portafolio real." # Pasar explícitamente el mensaje de error
            )

    async def _get_paper_trading_summary(self) -> PortfolioSummary:
        """
        Obtiene el resumen del portafolio de paper trading.
        """
        total_assets_value_usd = 0.0
        paper_assets: List[PortfolioAsset] = []

        if self.paper_trading_assets:
            assets_to_value = [f"{asset.symbol}USDT" for asset in self.paper_trading_assets.values()]
            if assets_to_value:
                effective_user_id = self.user_id if self.user_id else UUID("00000000-0000-0000-0000-000000000001")
                market_data = await self.market_data_service.get_market_data_rest(effective_user_id, assets_to_value)
                for symbol, asset in self.paper_trading_assets.items():
                    symbol_pair = f"{symbol}USDT"
                    price_info = market_data.get(symbol_pair)
                    if price_info and "lastPrice" in price_info:
                        current_price = price_info["lastPrice"]
                        current_value = asset.quantity * current_price
                        total_assets_value_usd += current_value
                        asset.current_price = current_price
                        asset.current_value_usd = current_value
                        if asset.entry_price is not None and asset.quantity > 0 and asset.entry_price > 0:
                            asset.unrealized_pnl_usd = (current_price - asset.entry_price) * asset.quantity
                            if asset.unrealized_pnl_usd is not None: # Asegurar que unrealized_pnl_usd no es None
                                asset.unrealized_pnl_percentage = (asset.unrealized_pnl_usd / (asset.entry_price * asset.quantity)) * 100
                            else:
                                asset.unrealized_pnl_percentage = None
                        else:
                            asset.unrealized_pnl_usd = None
                            asset.unrealized_pnl_percentage = None
                        paper_assets.append(asset)
                    else:
                        logger.warning(f"No se pudo obtener el precio para {symbol_pair} para el portafolio de paper trading.")
                        # No pasar error_message a PortfolioAsset, ya que no lo tiene
                        paper_assets.append(PortfolioAsset(
                            symbol=asset.symbol,
                            quantity=asset.quantity,
                            current_price=None,
                            current_value_usd=None,
                            entry_price=asset.entry_price,
                            unrealized_pnl_usd=None,
                            unrealized_pnl_percentage=None
                        ))

        total_portfolio_value_usd = self.paper_trading_balance + total_assets_value_usd

        return PortfolioSummary(
            available_balance_usdt=self.paper_trading_balance,
            total_assets_value_usd=total_assets_value_usd,
            total_portfolio_value_usd=total_portfolio_value_usd,
            assets=paper_assets,
            error_message=None # Pasar explícitamente None
        )

    async def update_paper_trading_balance(self, user_id: UUID, amount: float):
        """
        Actualiza el saldo de paper trading y lo persiste.
        """
        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        self.paper_trading_balance += amount
        try:
            user_config = await self.config_service.load_user_configuration(user_id)
            user_config.defaultPaperTradingCapital = self.paper_trading_balance
            await self.config_service.save_user_configuration(user_id, user_config)
            logger.info(f"Saldo de paper trading actualizado a {self.paper_trading_balance} para el usuario {user_id}.")
        except ConfigurationError as e:
            logger.error(f"Error al persistir el saldo de paper trading para el usuario {user_id}: {e}")
            raise UltiBotError(f"No se pudo persistir el saldo de paper trading: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al actualizar y persistir el saldo de paper trading para el usuario {user_id}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al actualizar el saldo de paper trading: {e}")

    async def add_paper_trading_asset(self, user_id: UUID, symbol: str, quantity: float, entry_price: float):
        """
        Añade un activo al portafolio de paper trading.
        """
        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        if symbol in self.paper_trading_assets:
            existing_asset = self.paper_trading_assets[symbol]
            total_quantity = existing_asset.quantity + quantity
            
            # Calcular new_entry_price de forma segura
            if existing_asset.entry_price is not None and existing_asset.quantity > 0:
                new_entry_price = ((existing_asset.entry_price * existing_asset.quantity) + (entry_price * quantity)) / total_quantity
            else:
                new_entry_price = entry_price

            existing_asset.quantity = total_quantity
            existing_asset.entry_price = new_entry_price
            logger.info(f"Activo {symbol} actualizado en paper trading. Cantidad: {total_quantity}, Precio de entrada: {new_entry_price}")
        else:
            self.paper_trading_assets[symbol] = PortfolioAsset(
                symbol=symbol,
                quantity=quantity,
                entry_price=entry_price,
                current_price=None,
                current_value_usd=None,
                unrealized_pnl_usd=None,
                unrealized_pnl_percentage=None
            )
            logger.info(f"Activo {symbol} añadido a paper trading. Cantidad: {quantity}, Precio de entrada: {entry_price}")
        # TODO: Persistir activos de paper trading (para futuras historias)

    async def remove_paper_trading_asset(self, user_id: UUID, symbol: str, quantity: float):
        """
        Remueve una cantidad de un activo del portafolio de paper trading.
        """
        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        if symbol not in self.paper_trading_assets:
            logger.warning(f"Intento de remover activo {symbol} de paper trading que no existe.")
            return

        asset = self.paper_trading_assets[symbol]
        if quantity >= asset.quantity:
            del self.paper_trading_assets[symbol]
            logger.info(f"Activo {symbol} completamente removido de paper trading.")
        else:
            asset.quantity -= quantity
            logger.info(f"Cantidad de {quantity} de {symbol} removida de paper trading. Restante: {asset.quantity}")
        # TODO: Persistir activos de paper trading (para futuras historias)
