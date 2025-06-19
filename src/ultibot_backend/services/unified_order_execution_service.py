import logging
from typing import Optional, Literal
from uuid import UUID
from decimal import Decimal

from shared.data_types import TradeOrderDetails
from ultibot_backend.services.order_execution_service import OrderExecutionService, PaperOrderExecutionService
from ultibot_backend.core.exceptions import OrderExecutionError, ConfigurationError

logger = logging.getLogger(__name__)

# Type alias for trading modes
TradingMode = Literal["paper", "real"]

class UnifiedOrderExecutionService:
    """
    Service that routes order execution to either paper trading or real trading
    based on the specified trading mode.
    """
    
    def __init__(
        self, 
        real_execution_service: OrderExecutionService,
        paper_execution_service: PaperOrderExecutionService
    ):
        self.real_execution_service = real_execution_service
        self.paper_execution_service = paper_execution_service
        logger.info("UnifiedOrderExecutionService initialized with both real and paper execution services")

    async def execute_market_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,  # 'BUY' or 'SELL'
        quantity: Decimal,
        trading_mode: TradingMode,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        oco_order_list_id: Optional[str] = None
    ) -> TradeOrderDetails:
        """
        Execute a market order in the specified trading mode.
        
        Args:
            user_id: User identifier
            symbol: Trading symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            trading_mode: Trading mode ('paper' or 'real')
            api_key: API key for real trading (required for real mode)
            api_secret: API secret for real trading (required for real mode)
            oco_order_list_id: OCO order list ID if applicable
            
        Returns:
            TradeOrderDetails with execution results
            
        Raises:
            OrderExecutionError: If execution fails
            ConfigurationError: If required parameters are missing for real trading
        """
        logger.info(f"Executing {trading_mode} market order for {symbol} {side} {quantity} for user {user_id}")
        
        try:
            if trading_mode == "paper":
                # Execute in paper trading mode
                return await self.paper_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    ocoOrderListId=oco_order_list_id
                )
                
            elif trading_mode == "real":
                # Validate required parameters for real trading
                if not api_key or not api_secret:
                    raise ConfigurationError(
                        "API key and secret are required for real trading mode"
                    )
                
                # Execute in real trading mode
                return await self.real_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    api_key=api_key,
                    api_secret=api_secret,
                    ocoOrderListId=oco_order_list_id
                )
                
            else:
                raise OrderExecutionError(f"Invalid trading mode: {trading_mode}. Must be 'paper' or 'real'")
                
        except (OrderExecutionError, ConfigurationError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            # Wrap other exceptions
            logger.error(f"Unexpected error executing {trading_mode} order: {e}", exc_info=True)
            raise OrderExecutionError(f"Unexpected error executing {trading_mode} order: {e}") from e

    async def create_oco_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        stop_price: Decimal,
        limit_price: Decimal, # Corregido: stop_limit_price a limit_price
        trading_mode: TradingMode,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> TradeOrderDetails: # Corregido: tipo de retorno de dict a TradeOrderDetails
        # Asegurar que limit_price se pasa correctamente a los servicios subyacentes
        logger.info(f"Creating {trading_mode} OCO order for {symbol} {side} {quantity} for user {user_id}")
        if trading_mode == "real":
            if not api_key or not api_secret:
                raise ConfigurationError("API key and secret are required for real trading mode")
            return await self.real_execution_service.create_oco_order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                limit_price=limit_price,
                api_key=api_key,
                api_secret=api_secret,
            )
        elif trading_mode == "paper":
            return await self.paper_execution_service.create_oco_order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                limit_price=limit_price,
            )
        else:
            raise OrderExecutionError(f"Invalid trading mode: {trading_mode}")

    async def get_virtual_balances(self) -> dict:
        """
        Get virtual balances from paper trading service.
        
        Returns:
            Dictionary with virtual balances
        """
        return self.paper_execution_service.get_virtual_balances()

    def reset_virtual_balances(self, initial_capital: Decimal):
        """
        Reset virtual balances for paper trading.
        
        Args:
            initial_capital: Initial capital amount
        """
        self.paper_execution_service.reset_virtual_balances(initial_capital)
        logger.info(f"Virtual balances reset to {initial_capital} USDT")

    def get_supported_trading_modes(self) -> list[TradingMode]:
        """
        Get list of supported trading modes.
        
        Returns:
            List of supported trading modes
        """
        return ["paper", "real"]

    def validate_trading_mode(self, trading_mode: str) -> bool:
        """
        Validate if the provided trading mode is supported.
        
        Args:
            trading_mode: Trading mode to validate
            
        Returns:
            True if valid, False otherwise
        """
        return trading_mode in self.get_supported_trading_modes()

    async def execute_order(
        self,
        order_details: TradeOrderDetails,
        user_id: UUID,
        trading_mode: TradingMode,
        symbol: str,
        side: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ) -> TradeOrderDetails:
        """
        Execute an order based on its type and the specified trading mode.
        Currently, only supports MARKET orders.

        Args:
            order_details: The details of the order to execute.
            user_id: User identifier.
            trading_mode: Trading mode ('paper' or 'real').
            symbol: Trading symbol.
            side: Order side ('BUY' or 'SELL').
            api_key: API key for real trading.
            api_secret: API secret for real trading.

        Returns:
            TradeOrderDetails with execution results.

        Raises:
            OrderExecutionError: If execution fails or order type is not supported.
            ConfigurationError: If required parameters are missing for real trading.
        """
        logger.info(
            f"UnifiedOrderExecutionService: Attempting to execute {order_details.type} order " # Corregido: .value eliminado
            f"ID {order_details.orderId_internal} for {symbol} {side} " # Corregido: order_id_internal a orderId_internal
            f"in {trading_mode} mode for user {user_id}."
        )

        if order_details.type == "market":
            # Delegar a execute_market_order
            return await self.execute_market_order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                quantity=order_details.requestedQuantity, # Corregido: requested_quantity a requestedQuantity
                trading_mode=trading_mode,
                api_key=api_key,
                api_secret=api_secret,
                oco_order_list_id=order_details.ocoOrderListId # Corregido: oco_group_id_exchange a ocoOrderListId
            )
        # TODO: Añadir manejo para otros tipos de órdenes (LIMIT, STOP_LOSS, etc.)
        # elif order_details.type == OrderType.LIMIT:
        #     # Lógica para órdenes LIMIT
        #     pass
        else:
            error_msg = f"Order type '{order_details.type}' not yet supported by UnifiedOrderExecutionService."
            logger.error(error_msg)
            raise OrderExecutionError(error_msg)
