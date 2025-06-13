"""
Módulo que implementa el servicio de gestión de portfolio.
Contiene la lógica de negocio pura para gestionar los activos y el valor del portfolio,
interactuando con el puerto de persistencia y publicando eventos de actualización.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timezone # MODIFIED

from ultibot_backend.core.ports import IPersistencePort, IEventPublisher, IMarketDataProvider
from ultibot_backend.core.domain_models.portfolio import Portfolio, UserId, Asset, PortfolioSnapshot
from ultibot_backend.core.domain_models.events import PortfolioUpdatedEvent
from ultibot_backend.core.domain_models.trading import Trade, TickerData, OrderSide

class PortfolioManagerService:
    """
    Servicio que gestiona el portfolio de los usuarios, incluyendo balances y P&L.
    """
    def __init__(
        self,
        persistence_port: IPersistencePort,
        event_publisher: IEventPublisher,
        market_provider: IMarketDataProvider
    ):
        """
        Inicializa el PortfolioManagerService.

        Args:
            persistence_port (IPersistencePort): Puerto de persistencia para guardar y recuperar portfolios.
            event_publisher (IEventPublisher): Publicador de eventos para notificar actualizaciones del portfolio.
            market_provider (IMarketDataProvider): Proveedor de datos de mercado para obtener precios actuales.
        """
        self._persistence_port = persistence_port
        self._event_publisher = event_publisher
        self._market_provider = market_provider

    async def get_user_portfolio(self, user_id: UserId) -> Portfolio:
        """
        Obtiene el portfolio actual de un usuario.

        Args:
            user_id (UserId): El ID del usuario.

        Returns:
            Portfolio: El objeto Portfolio del usuario.
        """
        portfolio = await self._persistence_port.get_portfolio(user_id)
        return portfolio

    async def update_portfolio_from_trade(self, trade: Trade, user_id: UserId) -> Portfolio:
        """
        Actualiza el portfolio de un usuario basándose en un trade ejecutado.

        Args:
            trade (Trade): El trade ejecutado.
            user_id (UserId): El ID del usuario.

        Returns:
            Portfolio: El portfolio actualizado.
        """
        portfolio = await self._persistence_port.get_portfolio(user_id)
        updated_assets = dict(portfolio.assets) # Crear una copia mutable

        # Calcular el impacto del trade en el activo
        symbol = trade.symbol
        quantity_change = trade.quantity
        cost_or_revenue = trade.quantity * trade.price

        if trade.side == OrderSide.BUY:
            if symbol in updated_assets:
                existing_asset = updated_assets[symbol]
                new_quantity = existing_asset.quantity + quantity_change
                new_total_cost = (existing_asset.quantity * existing_asset.average_buy_price) + cost_or_revenue
                new_average_buy_price = new_total_cost / new_quantity
                updated_assets[symbol] = Asset(
                    symbol=symbol,
                    quantity=new_quantity,
                    average_buy_price=new_average_buy_price,
                    current_price=existing_asset.current_price, # Se actualizará con el precio actual más tarde
                    last_updated=datetime.now(timezone.utc) # MODIFIED
                )
            else:
                updated_assets[symbol] = Asset(
                    symbol=symbol,
                    quantity=quantity_change,
                    average_buy_price=trade.price,
                    current_price=trade.price, # Se actualizará con el precio actual más tarde
                    last_updated=datetime.now(timezone.utc) # MODIFIED
                )
            # Reducir balance disponible
            new_available_balance = portfolio.available_balance_usd - cost_or_revenue
        else: # SELL
            if symbol not in updated_assets or updated_assets[symbol].quantity < quantity_change:
                # Esto debería ser manejado por el OrderExecutionPort o TradingEngine antes
                raise ValueError(f"Intento de vender más {symbol} de lo disponible o activo no encontrado.")
            
            existing_asset = updated_assets[symbol]
            new_quantity = existing_asset.quantity - quantity_change
            if new_quantity == Decimal('0.0'):
                del updated_assets[symbol]
            else:
                updated_assets[symbol] = Asset(
                    symbol=symbol,
                    quantity=new_quantity,
                    average_buy_price=existing_asset.average_buy_price,
                    current_price=existing_asset.current_price,
                    last_updated=datetime.now(timezone.utc) # MODIFIED
                )
            # Aumentar balance disponible
            new_available_balance = portfolio.available_balance_usd + cost_or_revenue

        # Actualizar precios actuales y valor total del portfolio
        total_value = Decimal('0.0')
        assets_snapshot: Dict[str, Decimal] = {}
        for sym, asset in updated_assets.items():
            current_ticker: TickerData = await self._market_provider.get_ticker(sym)
            updated_assets[sym] = asset.model_copy(update={'current_price': current_ticker.price})
            total_value += updated_assets[sym].quantity * updated_assets[sym].current_price
            assets_snapshot[sym] = updated_assets[sym].quantity

        updated_portfolio = Portfolio(
            user_id=user_id,
            assets=updated_assets,
            total_value_usd=total_value,
            available_balance_usd=new_available_balance,
            last_updated=datetime.now(timezone.utc) # MODIFIED
        )

        # Persistir el portfolio actualizado
        await self._persistence_port.save_portfolio(updated_portfolio)
        
        await self._event_publisher.publish(PortfolioUpdatedEvent(
            user_id=user_id,
            total_value_usd=updated_portfolio.total_value_usd,
            asset_updates=assets_snapshot # O un diff más granular
        ))

        return updated_portfolio

    async def get_portfolio_snapshot(self, user_id: UserId) -> PortfolioSnapshot:
        """
        Obtiene una instantánea del portfolio actual de un usuario.

        Args:
            user_id (UserId): El ID del usuario.

        Returns:
            PortfolioSnapshot: Una instantánea del portfolio.
        """
        portfolio = await self.get_user_portfolio(user_id)
        assets_snapshot = {sym: asset.quantity for sym, asset in portfolio.assets.items()}
        return PortfolioSnapshot(
            user_id=user_id,
            total_value_usd=portfolio.total_value_usd,
            assets_snapshot=assets_snapshot
        )

    async def get_trade_history(self, user_id: UserId, symbol: Optional[str] = None) -> List[Trade]:
        """
        Obtiene el historial de trades para un usuario, opcionalmente filtrado por símbolo.

        Args:
            user_id (UserId): ID del usuario.
            symbol (Optional[str]): Símbolo para filtrar (opcional).

        Returns:
            List[Trade]: Lista de objetos Trade.
        """
        return await self._persistence_port.get_trade_history(user_id, symbol)
