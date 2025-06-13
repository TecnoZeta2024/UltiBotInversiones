import logging
import logging
from typing import Dict, Any, Optional, List # Importar List
from uuid import UUID, uuid4
from datetime import datetime, timezone # Importar timezone

from shared.data_types import TradeOrderDetails, UserConfiguration, OrderCategory # Importar OrderCategory
from ultibot_backend.adapters.binance_adapter import BinanceAdapter
from ultibot_backend.core.exceptions import OrderExecutionError, ExternalAPIError

logger = logging.getLogger(__name__)

class OrderExecutionService:
    """
    Servicio para ejecutar órdenes de trading reales a través de la API de Binance.
    """
    def __init__(self, binance_adapter: BinanceAdapter):
        self.binance_adapter = binance_adapter

    async def execute_market_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str, # 'BUY' o 'SELL'
        quantity: float,
        api_key: str,
        api_secret: str,
        ocoOrderListId: Optional[str] = None # Añadir este parámetro
    ) -> TradeOrderDetails:
        """
        Ejecuta una orden de mercado real en Binance.
        """
        logger.info(f"Ejecutando orden de mercado REAL para {symbol} {side} {quantity} para usuario {user_id}")
        try:
            # Aquí iría la lógica real para interactuar con Binance
            # Por ahora, es un placeholder. Necesitaríamos un endpoint de Binance para crear órdenes.
            # Asumiendo un endpoint como /api/v3/order/test o /api/v3/order
            
            # Ejemplo de llamada a BinanceAdapter (esto es hipotético, el adaptador no tiene un método create_order aún)
            # response = await self.binance_adapter.create_order(
            #     api_key=api_key,
            #     api_secret=api_secret,
            #     symbol=symbol,
            #     side=side,
            #     type='MARKET',
            #     quantity=quantity
            # )
            
            # Simulación de respuesta de Binance para desarrollo
            simulated_response = {
                "symbol": symbol,
                "orderId": 123456789,
                "clientOrderId": f"test_order_{uuid4()}",
                "transactTime": int(datetime.now(timezone.utc).timestamp() * 1000), # MODIFIED
                "price": "0.00000000", # Precio de mercado, puede ser 0 para órdenes de mercado
                "origQty": str(quantity),
                "executedQty": str(quantity),
                "cummulativeQuoteQty": str(quantity * 30000), # Ejemplo de valor
                "status": "FILLED",
                "timeInForce": "GTC",
                "type": "MARKET",
                "side": side,
                "fills": [
                    {"price": "30000.00", "qty": str(quantity), "commission": "0.0001", "commissionAsset": "BNB"}
                ]
            }

            # Mapear la respuesta de Binance a TradeOrderDetails
            order_details = TradeOrderDetails(
                orderId_internal=uuid4(),
                orderId_exchange=str(simulated_response.get("orderId", uuid4())), # Proporcionar un valor por defecto
                clientOrderId_exchange=simulated_response.get("clientOrderId", str(uuid4())),
                orderCategory=OrderCategory.ENTRY, # Asignar un valor por defecto
                type='market',
                status=simulated_response.get("status", "filled").lower(), # Valor por defecto y .lower()
                requestedPrice=float(simulated_response.get("price", 0.0)), # Valor por defecto
                requestedQuantity=float(simulated_response.get("origQty", 0.0)), # Valor por defecto
                executedQuantity=float(simulated_response.get("executedQty", 0.0)), # Valor por defecto
                executedPrice=float(simulated_response["fills"][0]["price"]) if simulated_response.get("fills") and simulated_response["fills"] else 0.0, # Manejar lista vacía
                cumulativeQuoteQty=float(simulated_response.get("cummulativeQuoteQty", 0.0)), # Valor por defecto
                commissions=[{
                    "amount": float(f.get("commission", 0.0)), # Usar .get() para seguridad
                    "asset": f.get("commissionAsset", "")
                } for f in simulated_response.get("fills", [])] if simulated_response.get("fills") else [], # Manejar fills como lista vacía
                commission=float(simulated_response["fills"][0]["commission"]) if simulated_response.get("fills") and simulated_response["fills"] else None, # Campo legado
                commissionAsset=simulated_response["fills"][0]["commissionAsset"] if simulated_response.get("fills") and simulated_response["fills"] else None, # Campo legado
                timestamp=datetime.fromtimestamp(simulated_response.get("transactTime", int(datetime.now(timezone.utc).timestamp() * 1000)) / 1000, tz=timezone.utc), # MODIFIED
                submittedAt=datetime.fromtimestamp(simulated_response.get("transactTime", int(datetime.now(timezone.utc).timestamp() * 1000)) / 1000, tz=timezone.utc), # MODIFIED
                fillTimestamp=datetime.fromtimestamp(simulated_response.get("transactTime", int(datetime.now(timezone.utc).timestamp() * 1000)) / 1000, tz=timezone.utc), # MODIFIED
                rawResponse=simulated_response,
                ocoOrderListId=ocoOrderListId
            )
            logger.info(f"Orden REAL ejecutada exitosamente: {order_details.orderId_exchange}")
            return order_details
        except ExternalAPIError as e:
            logger.error(f"Error de API al ejecutar orden real: {e}", exc_info=True) # ExternalAPIError ya es una cadena
            raise OrderExecutionError(f"Fallo al ejecutar orden real en Binance: {e}") from e
        except Exception as e:
            logger.error(f"Error inesperado al ejecutar orden real: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado al ejecutar orden real: {e}") from e

class PaperOrderExecutionService:
    """
    Servicio para simular la ejecución de órdenes de trading en modo Paper Trading.
    Mantiene un balance virtual en memoria (o podría persistirse en UserConfiguration).
    """
    def __init__(self, initial_capital: float = 10000.0):
        self.virtual_balances: Dict[str, float] = {"USDT": initial_capital}
        self.virtual_trades: List[TradeOrderDetails] = []
        logger.info(f"Paper Trading Service inicializado con capital virtual: {initial_capital} USDT")

    async def execute_market_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str, # 'BUY' o 'SELL'
        quantity: float,
        ocoOrderListId: Optional[str] = None # Añadir este parámetro
    ) -> TradeOrderDetails:
        """
        Simula la ejecución de una orden de mercado.
        """
        logger.info(f"Simulando orden de mercado PAPER para {symbol} {side} {quantity} para usuario {user_id}")
        
        # Simular precio actual (ej. de un servicio de datos de mercado)
        # Para simplificar, usaremos un precio fijo o aleatorio para la simulación
        simulated_price = 30000.0 # Precio fijo para BTC/USDT, por ejemplo
        if "ETH" in symbol:
            simulated_price = 2000.0 # Precio fijo para ETH/USDT
        
        cost_or_revenue = quantity * simulated_price
        
        base_asset = symbol.replace("USDT", "") # Ej: BTC
        quote_asset = "USDT"

        if side == 'BUY':
            if self.virtual_balances.get(quote_asset, 0) < cost_or_revenue:
                raise OrderExecutionError(f"Capital virtual insuficiente para comprar {quantity} de {base_asset} (necesario: {cost_or_revenue}, disponible: {self.virtual_balances.get(quote_asset, 0)})")
            self.virtual_balances[quote_asset] = self.virtual_balances.get(quote_asset, 0) - cost_or_revenue
            self.virtual_balances[base_asset] = self.virtual_balances.get(base_asset, 0) + quantity
            logger.info(f"Compra simulada: {quantity} {base_asset} a {simulated_price}. Nuevo balance USDT: {self.virtual_balances[quote_asset]}, {base_asset}: {self.virtual_balances[base_asset]}")
        elif side == 'SELL':
            if self.virtual_balances.get(base_asset, 0) < quantity:
                raise OrderExecutionError(f"Cantidad virtual insuficiente de {base_asset} para vender (necesario: {quantity}, disponible: {self.virtual_balances.get(base_asset, 0)})")
            self.virtual_balances[base_asset] = self.virtual_balances.get(base_asset, 0) - quantity
            self.virtual_balances[quote_asset] = self.virtual_balances.get(quote_asset, 0) + cost_or_revenue
            logger.info(f"Venta simulada: {quantity} {base_asset} a {simulated_price}. Nuevo balance USDT: {self.virtual_balances[quote_asset]}, {base_asset}: {self.virtual_balances[base_asset]}")
        else:
            raise ValueError("Side debe ser 'BUY' o 'SELL'.")

        # Crear un objeto TradeOrderDetails simulado
        order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            orderId_exchange=f"PAPER_{uuid4()}",
            clientOrderId_exchange=f"PAPER_CLIENT_{uuid4()}",
            orderCategory=OrderCategory.ENTRY, # Asignar un valor por defecto
            type='market',
            status='filled',
            requestedPrice=simulated_price,
            requestedQuantity=quantity,
            executedQuantity=quantity,
            executedPrice=simulated_price,
            cumulativeQuoteQty=cost_or_revenue,
            commissions=[], # Sin comisiones en paper trading por simplicidad
            commission=None, # Campo legado
            commissionAsset=None, # Campo legado
            timestamp=datetime.now(timezone.utc), # Already timezone aware
            submittedAt=datetime.now(timezone.utc), # Already timezone aware
            fillTimestamp=datetime.now(timezone.utc), # Already timezone aware
            rawResponse=None,
            ocoOrderListId=ocoOrderListId # Asignar el parámetro
        )
        self.virtual_trades.append(order_details)
        logger.info(f"Orden PAPER simulada exitosamente: {order_details.orderId_internal}")
        return order_details

    def get_virtual_balances(self) -> Dict[str, float]:
        """Retorna los balances virtuales actuales."""
        return self.virtual_balances

    def reset_virtual_balances(self, initial_capital: float):
        """Reinicia los balances virtuales a un capital inicial dado."""
        self.virtual_balances = {"USDT": initial_capital}
        self.virtual_trades = []
        logger.info(f"Balances virtuales reiniciados a {initial_capital} USDT.")
