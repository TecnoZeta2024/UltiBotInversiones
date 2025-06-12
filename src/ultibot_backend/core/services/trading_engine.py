"""
Módulo que implementa el servicio del motor de trading.
Contiene la lógica de negocio pura para la ejecución de trades,
interactuando con los puertos de datos de mercado, persistencia y publicación de eventos.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID # Importar UUID directamente

from ..ports import (
    IMarketDataProvider, IPersistencePort, IEventPublisher, IOrderExecutionPort
)
from ..domain_models.trading import (
    Opportunity, TradeResult, Trade, OrderSide, OrderType, TickerData
)
from ..domain_models.events import TradeExecutedEvent
from ..exceptions import TradeExecutionError, InsufficientFundsError

class TradingEngineService:
    """
    Servicio del motor de trading que gestiona la lógica central de ejecución de operaciones.
    """
    def __init__(
        self,
        market_provider: IMarketDataProvider,
        persistence_port: IPersistencePort,
        event_publisher: IEventPublisher,
        order_execution_port: IOrderExecutionPort
    ):
        """
        Inicializa el TradingEngineService.

        Args:
            market_provider (IMarketDataProvider): Proveedor de datos de mercado.
            persistence_port (IPersistencePort): Puerto de persistencia para guardar trades.
            event_publisher (IEventPublisher): Publicador de eventos para notificar trades ejecutados.
            order_execution_port (IOrderExecutionPort): Puerto para ejecutar órdenes en el exchange.
        """
        self._market_provider = market_provider
        self._persistence_port = persistence_port
        self._event_publisher = event_publisher
        self._order_execution_port = order_execution_port

    async def execute_trade(self, opportunity: Opportunity, user_id: Optional[str] = None) -> TradeResult:
        """
        Ejecuta un trade basado en una oportunidad de trading.

        Args:
            opportunity (Opportunity): La oportunidad de trading a ejecutar.
            user_id (Optional[str]): ID del usuario que ejecuta el trade (opcional).

        Returns:
            TradeResult: El resultado de la ejecución del trade.

        Raises:
            TradeExecutionError: Si ocurre un error durante la ejecución del trade.
            InsufficientFundsError: Si no hay fondos suficientes para el trade.
        """
        try:
            # Lógica pura de negocio para determinar el trade
            # Esto es una simplificación; en un sistema real, se harían más validaciones
            # y cálculos basados en la oportunidad y el estado del portfolio.

            # Obtener el precio actual para órdenes de mercado o validar para órdenes límite
            current_ticker: TickerData = await self._market_provider.get_ticker(opportunity.symbol)
            
            # Determinar el precio de ejecución
            executed_price = opportunity.details.get("price", current_ticker.price)
            
            # Determinar la cantidad a ejecutar
            executed_quantity = opportunity.details.get("quantity")
            if not executed_quantity:
                raise TradeExecutionError("Cantidad de trade no especificada en la oportunidad.")

            # Simular la ejecución de la orden a través del puerto de ejecución
            trade_result = await self._order_execution_port.place_order(opportunity)

            if not trade_result.success:
                raise TradeExecutionError(f"Fallo al colocar la orden: {trade_result.message}")

            # Crear el objeto Trade con los datos reales de ejecución
            trade = Trade(
                symbol=opportunity.symbol,
                side=opportunity.details.get("side", OrderSide.BUY), # Asumir BUY si no se especifica
                quantity=trade_result.executed_quantity or Decimal(str(executed_quantity)),
                price=trade_result.executed_price or Decimal(str(executed_price)),
                strategy_id=opportunity.details.get("strategy_id"),
                order_type=opportunity.details.get("order_type", OrderType.MARKET), # Asumir MARKET
                fee=trade_result.fee,
                fee_asset=trade_result.fee_asset
            )

            # Persistir el trade
            trade_id: UUID = await self._persistence_port.save_trade(trade) # Asegurar que trade_id es UUID
            trade = trade.model_copy(update={'id': trade_id}) # Actualizar el ID del trade

            # Publicar el evento de Trade Ejecutado
            await self._event_publisher.publish(TradeExecutedEvent(
                trade_id=trade.id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                price=trade.price,
                strategy_id=trade.strategy_id,
                order_type=trade.order_type,
                fee=trade.fee,
                fee_asset=trade.fee_asset
            ))

            return TradeResult(
                success=True,
                trade_id=trade.id,
                message="Trade ejecutado y registrado exitosamente.",
                executed_price=trade.price,
                executed_quantity=trade.quantity
            )

        except InsufficientFundsError as e:
            return TradeResult(success=False, message=f"Fondos insuficientes: {e}")
        except TradeExecutionError as e:
            return TradeResult(success=False, message=f"Error de ejecución de trade: {e}")
        except Exception as e:
            # Captura cualquier otra excepción inesperada
            return TradeResult(success=False, message=f"Error inesperado al ejecutar trade: {e}")

    async def cancel_existing_order(self, order_id: str) -> bool:
        """
        Cancela una orden existente a través del puerto de ejecución de órdenes.

        Args:
            order_id (str): El ID de la orden a cancelar.

        Returns:
            bool: True si la cancelación fue exitosa, False en caso contrario.
        """
        return await self._order_execution_port.cancel_order(order_id)
