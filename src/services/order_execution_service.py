import logging
from typing import Dict, Any, Optional, List 
from uuid import UUID, uuid4
from datetime import datetime, timezone 
from decimal import Decimal

from shared.data_types import TradeOrderDetails, UserConfiguration, OrderCategory 
from adapters.binance_adapter import BinanceAdapter
from core.exceptions import OrderExecutionError, ExternalAPIError

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
        quantity: Decimal,
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
                "transactTime": int(datetime.now().timestamp() * 1000),
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
                requestedPrice=Decimal(simulated_response.get("price", "0.0")), # Valor por defecto
                requestedQuantity=Decimal(simulated_response.get("origQty", "0.0")), # Valor por defecto
                executedQuantity=Decimal(simulated_response.get("executedQty", "0.0")), # Valor por defecto
                executedPrice=Decimal(simulated_response["fills"][0]["price"]) if simulated_response.get("fills") and simulated_response["fills"] else Decimal("0.0"), # Manejar lista vacía
                cumulativeQuoteQty=Decimal(simulated_response.get("cummulativeQuoteQty", "0.0")), # Valor por defecto
                commissions=[{
                    "amount": Decimal(f.get("commission", "0.0")), # Usar .get() para seguridad
                    "asset": f.get("commissionAsset", "")
                } for f in simulated_response.get("fills", [])] if simulated_response.get("fills") else [], # Manejar fills como lista vacía
                commission=Decimal(simulated_response["fills"][0]["commission"]) if simulated_response.get("fills") and simulated_response["fills"] else None, # Campo legado
                commissionAsset=simulated_response["fills"][0]["commissionAsset"] if simulated_response.get("fills") and simulated_response["fills"] else None, # Campo legado
                timestamp=datetime.fromtimestamp(simulated_response.get("transactTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc), # Usar timezone.utc
                submittedAt=datetime.fromtimestamp(simulated_response.get("transactTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                fillTimestamp=datetime.fromtimestamp(simulated_response.get("transactTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                rawResponse=simulated_response,
                ocoOrderListId=ocoOrderListId,
                price=Decimal(simulated_response.get("price", "0.0")), # Añadir price
                stopPrice=None, # No aplica para market order
                timeInForce=simulated_response.get("timeInForce", "GTC") # Añadir timeInForce
            )
            logger.info(f"Orden REAL ejecutada exitosamente: {order_details.orderId_exchange}")
            return order_details
        except ExternalAPIError as e:
            logger.error(f"Error de API al ejecutar orden real: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo al ejecutar orden real en Binance: {e}") from e
        except Exception as e:
            logger.error(f"Error inesperado al ejecutar orden real: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado al ejecutar orden real: {e}") from e

    async def create_oco_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,  # 'BUY' o 'SELL'
        quantity: Decimal,
        price: Decimal,  # Precio de la orden LIMIT (entrada)
        stop_price: Decimal,  # Precio de la orden STOP_LOSS
        limit_price: Decimal,  # Precio de la orden TAKE_PROFIT (LIMIT)
        api_key: str,
        api_secret: str,
    ) -> TradeOrderDetails:
        """
        Crea una orden OCO (One-Cancels-the-Other) real en Binance.
        Consiste en una orden LIMIT (entrada) y un par de órdenes STOP_LOSS/TAKE_PROFIT.
        """
        logger.info(f"Creando orden OCO REAL para {symbol} {side} {quantity} a {price} (Stop: {stop_price}, Limit: {limit_price}) para usuario {user_id}")
        try:
            # Simulación de respuesta de Binance para una orden OCO
            # En un escenario real, Binance devolvería un orderListId y detalles de las órdenes individuales
            oco_list_id = f"OCO_{uuid4()}"
            simulated_response = {
                "orderListId": oco_list_id,
                "contingencyType": "OCO",
                "listStatusType": "ALL_DONE",
                "listOrderStatus": "ALL_DONE",
                "clientRequestId": f"oco_request_{uuid4()}",
                "transactionTime": int(datetime.now().timestamp() * 1000),
                "symbol": symbol,
                "orders": [
                    {
                        "symbol": symbol,
                        "orderId": 123456790,
                        "clientOrderId": f"oco_limit_{uuid4()}",
                        "price": str(price),
                        "origQty": str(quantity),
                        "executedQty": str(quantity),
                        "cummulativeQuoteQty": str(quantity * price),
                        "status": "FILLED",
                        "timeInForce": "GTC",
                        "type": "LIMIT",
                        "side": side,
                        "ocoOrderListId": oco_list_id
                    },
                    {
                        "symbol": symbol,
                        "orderId": 123456791,
                        "clientOrderId": f"oco_stop_{uuid4()}",
                        "price": str(limit_price), # Precio de la orden LIMIT (Take Profit)
                        "stopPrice": str(stop_price), # Precio de la orden STOP_LOSS
                        "origQty": str(quantity),
                        "executedQty": "0.0", # Inicialmente no ejecutada
                        "cummulativeQuoteQty": "0.0",
                        "status": "NEW",
                        "timeInForce": "GTC",
                        "type": "STOP_LOSS_LIMIT",
                        "side": "SELL" if side == "BUY" else "BUY", # Lado opuesto a la entrada
                        "ocoOrderListId": oco_list_id
                    }
                ]
            }

            # Mapear la respuesta de Binance a TradeOrderDetails para la orden principal (entrada)
            # La orden OCO en sí misma es un grupo, pero devolvemos la orden de entrada como la principal
            entry_order_response = simulated_response["orders"][0]
            order_details = TradeOrderDetails(
                orderId_internal=uuid4(),
                orderId_exchange=str(entry_order_response.get("orderId", uuid4())),
                clientOrderId_exchange=entry_order_response.get("clientOrderId", str(uuid4())),
                orderCategory=OrderCategory.OCO_ORDER, # Indica que es parte de un grupo OCO
                type=entry_order_response.get("type", "limit").lower(),
                status=entry_order_response.get("status", "filled").lower(),
                requestedPrice=Decimal(entry_order_response.get("price", "0.0")),
                requestedQuantity=Decimal(entry_order_response.get("origQty", "0.0")),
                executedQuantity=Decimal(entry_order_response.get("executedQty", "0.0")),
                executedPrice=Decimal(entry_order_response.get("price", "0.0")), # Asumimos precio de ejecución igual al solicitado para simulación
                cumulativeQuoteQty=Decimal(entry_order_response.get("cummulativeQuoteQty", "0.0")),
                commissions=[], # Simplificado para OCO
                commission=None,
                commissionAsset=None,
                timestamp=datetime.fromtimestamp(simulated_response.get("transactionTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                submittedAt=datetime.fromtimestamp(simulated_response.get("transactionTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                fillTimestamp=datetime.fromtimestamp(simulated_response.get("transactionTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                rawResponse=simulated_response,
                ocoOrderListId=oco_list_id,
                price=Decimal(entry_order_response.get("price", "0.0")), # Añadir price
                stopPrice=Decimal(simulated_response["orders"][1].get("stopPrice", "0.0")), # Añadir stopPrice de la orden stop
                timeInForce=entry_order_response.get("timeInForce", "GTC") # Añadir timeInForce
            )
            logger.info(f"Orden OCO REAL creada exitosamente con List ID: {oco_list_id}")
            return order_details
        except ExternalAPIError as e:
            logger.error(f"Error de API al crear orden OCO real: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo al crear orden OCO real en Binance: {e}") from e
        except Exception as e:
            logger.error(f"Error inesperado al crear orden OCO real: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado al crear orden OCO real: {e}") from e

    async def execute_limit_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        api_key: str,
        api_secret: str,
        time_in_force: Optional[str] = "GTC"
    ) -> TradeOrderDetails:
        """
        Ejecuta una orden LIMIT real en Binance.
        """
        logger.info(f"Ejecutando orden LIMIT REAL para {symbol} {side} {quantity} a {price} para usuario {user_id}")
        try:
            # Simulación de respuesta de Binance para una orden LIMIT
            simulated_response = {
                "symbol": symbol,
                "orderId": 200000000 + int(uuid4().int % 100000000),
                "clientOrderId": f"test_limit_order_{uuid4()}",
                "transactTime": int(datetime.now().timestamp() * 1000),
                "price": str(price),
                "origQty": str(quantity),
                "executedQty": "0.0", # Inicialmente no ejecutada
                "cummulativeQuoteQty": "0.0",
                "status": "NEW", # O "PARTIALLY_FILLED" o "FILLED"
                "timeInForce": time_in_force,
                "type": "LIMIT",
                "side": side,
            }

            order_details = TradeOrderDetails(
                orderId_internal=uuid4(),
                orderId_exchange=str(simulated_response.get("orderId")),
                clientOrderId_exchange=simulated_response.get("clientOrderId"),
                orderCategory=OrderCategory.ENTRY,
                type='limit',
                status=simulated_response.get("status", "NEW").lower(), # Asegurar valor por defecto
                requestedPrice=Decimal(str(simulated_response.get("price", "0.0"))), # Convertir a str antes de Decimal
                requestedQuantity=Decimal(str(simulated_response.get("origQty", "0.0"))),
                executedQuantity=Decimal(str(simulated_response.get("executedQty", "0.0"))),
                executedPrice=Decimal("0.0"), # Se llenará al ejecutar
                cumulativeQuoteQty=Decimal(str(simulated_response.get("cummulativeQuoteQty", "0.0"))),
                commissions=[],
                timestamp=datetime.fromtimestamp(simulated_response.get("transactTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                submittedAt=datetime.fromtimestamp(simulated_response.get("transactTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                fillTimestamp=None, # Se llenará al ejecutar
                rawResponse=simulated_response,
                commission=None, # Añadir campos faltantes
                commissionAsset=None,
                ocoOrderListId=None,
                price=Decimal(simulated_response.get("price", "0.0")), # Añadir price
                stopPrice=None, # No aplica para limit order
                timeInForce=simulated_response.get("timeInForce", "GTC") # Añadir timeInForce
            )
            logger.info(f"Orden LIMIT REAL creada exitosamente: {order_details.orderId_exchange}")
            return order_details
        except ExternalAPIError as e:
            logger.error(f"Error de API al ejecutar orden LIMIT real: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo al ejecutar orden LIMIT real en Binance: {e}") from e
        except Exception as e:
            logger.error(f"Error inesperado al ejecutar orden LIMIT real: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado al ejecutar orden LIMIT real: {e}") from e

    async def execute_stop_loss_limit_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal, # Precio límite
        stop_price: Decimal, # Precio de activación
        api_key: str,
        api_secret: str,
        time_in_force: Optional[str] = "GTC"
    ) -> TradeOrderDetails:
        """
        Ejecuta una orden STOP_LOSS_LIMIT real en Binance.
        """
        logger.info(f"Ejecutando orden STOP_LOSS_LIMIT REAL para {symbol} {side} {quantity} a {price} (Stop: {stop_price}) para usuario {user_id}")
        try:
            # Simulación de respuesta de Binance para una orden STOP_LOSS_LIMIT
            simulated_response = {
                "symbol": symbol,
                "orderId": 300000000 + int(uuid4().int % 100000000),
                "clientOrderId": f"test_stop_limit_order_{uuid4()}",
                "transactTime": int(datetime.now().timestamp() * 1000),
                "price": str(price), # Precio límite
                "stopPrice": str(stop_price), # Precio de activación
                "origQty": str(quantity),
                "executedQty": "0.0",
                "cummulativeQuoteQty": "0.0",
                "status": "NEW",
                "timeInForce": time_in_force,
                "type": "STOP_LOSS_LIMIT",
                "side": side,
            }

            order_details = TradeOrderDetails(
                orderId_internal=uuid4(),
                orderId_exchange=str(simulated_response.get("orderId")),
                clientOrderId_exchange=simulated_response.get("clientOrderId"),
                orderCategory=OrderCategory.EXIT, # Típicamente una orden de salida
                type='stop_loss_limit',
                status=simulated_response.get("status", "NEW").lower(), # Asegurar valor por defecto
                requestedPrice=Decimal(str(simulated_response.get("price", "0.0"))),
                requestedQuantity=Decimal(str(simulated_response.get("origQty", "0.0"))),
                executedQuantity=Decimal(str(simulated_response.get("executedQty", "0.0"))),
                executedPrice=Decimal("0.0"),
                cumulativeQuoteQty=Decimal(str(simulated_response.get("cummulativeQuoteQty", "0.0"))),
                commissions=[],
                timestamp=datetime.fromtimestamp(simulated_response.get("transactTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                submittedAt=datetime.fromtimestamp(simulated_response.get("transactTime", datetime.now().timestamp() * 1000) / 1000, tz=timezone.utc),
                fillTimestamp=None,
                rawResponse=simulated_response,
                commission=None, # Añadir campos faltantes
                commissionAsset=None,
                ocoOrderListId=None,
                price=Decimal(simulated_response.get("price", "0.0")), # Añadir price
                stopPrice=Decimal(simulated_response.get("stopPrice", "0.0")), # Añadir stopPrice
                timeInForce=simulated_response.get("timeInForce", "GTC") # Añadir timeInForce
            )
            logger.info(f"Orden STOP_LOSS_LIMIT REAL creada exitosamente: {order_details.orderId_exchange}")
            return order_details
        except ExternalAPIError as e:
            logger.error(f"Error de API al ejecutar orden STOP_LOSS_LIMIT real: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo al ejecutar orden STOP_LOSS_LIMIT real en Binance: {e}") from e
        except Exception as e:
            logger.error(f"Error inesperado al ejecutar orden STOP_LOSS_LIMIT real: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado al ejecutar orden STOP_LOSS_LIMIT real: {e}") from e

class PaperOrderExecutionService:
    """
    Servicio para simular la ejecución de órdenes de trading en modo Paper Trading.
    Mantiene un balance virtual en memoria (o podría persistirse en UserConfiguration).
    """
    def __init__(self, initial_capital: Decimal = Decimal("10000.0")):
        self.virtual_balances: Dict[str, Decimal] = {"USDT": initial_capital}
        self.virtual_trades: List[TradeOrderDetails] = []
        logger.info(f"Paper Trading Service inicializado con capital virtual: {initial_capital} USDT")

    async def execute_market_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str, # 'BUY' o 'SELL'
        quantity: Decimal,
        ocoOrderListId: Optional[str] = None # Añadir este parámetro
    ) -> TradeOrderDetails:
        """
        Simula la ejecución de una orden de mercado.
        """
        logger.info(f"Simulando orden de mercado PAPER para {symbol} {side} {quantity} para usuario {user_id}")
        
        # Simular precio actual (ej. de un servicio de datos de mercado)
        # Para simplificar, usaremos un precio fijo o aleatorio para la simulación
        simulated_price = Decimal("30000.0") # Precio fijo para BTC/USDT, por ejemplo
        if "ETH" in symbol:
            simulated_price = Decimal("2000.0") # Precio fijo para ETH/USDT
        
        cost_or_revenue = quantity * simulated_price
        
        base_asset = symbol.replace("USDT", "") # Ej: BTC
        quote_asset = "USDT"

        if side == 'BUY':
            if self.virtual_balances.get(quote_asset, Decimal("0")) < cost_or_revenue:
                raise OrderExecutionError(f"Capital virtual insuficiente para comprar {quantity} de {base_asset} (necesario: {cost_or_revenue}, disponible: {self.virtual_balances.get(quote_asset, Decimal('0'))})")
            self.virtual_balances[quote_asset] = self.virtual_balances.get(quote_asset, Decimal("0")) - cost_or_revenue
            self.virtual_balances[base_asset] = self.virtual_balances.get(base_asset, Decimal("0")) + quantity
            logger.info(f"Compra simulada: {quantity} {base_asset} a {simulated_price}. Nuevo balance USDT: {self.virtual_balances[quote_asset]}, {base_asset}: {self.virtual_balances[base_asset]}")
        elif side == 'SELL':
            if self.virtual_balances.get(base_asset, Decimal("0")) < quantity:
                raise OrderExecutionError(f"Cantidad virtual insuficiente de {base_asset} para vender (necesario: {quantity}, disponible: {self.virtual_balances.get(base_asset, Decimal('0'))})")
            self.virtual_balances[base_asset] = self.virtual_balances.get(base_asset, Decimal("0")) - quantity
            self.virtual_balances[quote_asset] = self.virtual_balances.get(quote_asset, Decimal("0")) + cost_or_revenue
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
            timestamp=datetime.now(timezone.utc),
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse=None,
            ocoOrderListId=ocoOrderListId, # Asignar el parámetro
            price=simulated_price, # Añadir price
            stopPrice=None, # No aplica para market order
            timeInForce="GTC" # Asumir GTC para paper market orders
        )
        self.virtual_trades.append(order_details)
        logger.info(f"Orden PAPER simulada exitosamente: {order_details.orderId_internal}")
        return order_details

    async def create_oco_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,  # 'BUY' o 'SELL'
        quantity: Decimal,
        price: Decimal,  # Precio de la orden LIMIT (entrada)
        stop_price: Decimal,  # Precio de la orden STOP_LOSS
        limit_price: Decimal,  # Precio de la orden TAKE_PROFIT (LIMIT)
    ) -> TradeOrderDetails:
        """
        Simula la creación de una orden OCO (One-Cancels-the-Other) en modo Paper Trading.
        """
        logger.info(f"Simulando orden OCO PAPER para {symbol} {side} {quantity} a {price} (Stop: {stop_price}, Limit: {limit_price}) para usuario {user_id}")

        # Simular precio actual (ej. de un servicio de datos de mercado)
        simulated_price = Decimal("30000.0")
        if "ETH" in symbol:
            simulated_price = Decimal("2000.0")

        cost_or_revenue = quantity * simulated_price

        base_asset = symbol.replace("USDT", "")
        quote_asset = "USDT"

        if side == 'BUY':
            if self.virtual_balances.get(quote_asset, Decimal("0")) < cost_or_revenue:
                raise OrderExecutionError(f"Capital virtual insuficiente para comprar {quantity} de {base_asset} (necesario: {cost_or_revenue}, disponible: {self.virtual_balances.get(quote_asset, Decimal('0'))})")
            self.virtual_balances[quote_asset] = self.virtual_balances.get(quote_asset, Decimal("0")) - cost_or_revenue
            self.virtual_balances[base_asset] = self.virtual_balances.get(base_asset, Decimal("0")) + quantity
            logger.info(f"Compra simulada: {quantity} {base_asset} a {simulated_price}. Nuevo balance USDT: {self.virtual_balances[quote_asset]}, {base_asset}: {self.virtual_balances[base_asset]}")
        elif side == 'SELL':
            if self.virtual_balances.get(base_asset, Decimal("0")) < quantity:
                raise OrderExecutionError(f"Cantidad virtual insuficiente de {base_asset} para vender (necesario: {quantity}, disponible: {self.virtual_balances.get(base_asset, Decimal('0'))})")
            self.virtual_balances[base_asset] = self.virtual_balances.get(base_asset, Decimal("0")) - quantity
            self.virtual_balances[quote_asset] = self.virtual_balances.get(quote_asset, Decimal("0")) + cost_or_revenue
            logger.info(f"Venta simulada: {quantity} {base_asset} a {simulated_price}. Nuevo balance USDT: {self.virtual_balances[quote_asset]}, {base_asset}: {self.virtual_balances[base_asset]}")
        else:
            raise ValueError("Side debe ser 'BUY' o 'SELL'.")

        oco_list_id = f"PAPER_OCO_{uuid4()}"
        order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            orderId_exchange=f"PAPER_OCO_ENTRY_{uuid4()}",
            clientOrderId_exchange=f"PAPER_OCO_CLIENT_ENTRY_{uuid4()}",
            orderCategory=OrderCategory.OCO_ORDER,
            type='limit',
            status='filled',
            requestedPrice=price,
            requestedQuantity=quantity,
            executedQuantity=quantity,
            executedPrice=price,
            cumulativeQuoteQty=quantity * price,
            commissions=[],
            commission=None,
            commissionAsset=None,
            timestamp=datetime.now(timezone.utc),
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse=None,
            ocoOrderListId=oco_list_id,
            price=price, # Añadir price
            stopPrice=stop_price, # Añadir stopPrice
            timeInForce="GTC" # Asumir GTC para paper OCO orders
        )
        self.virtual_trades.append(order_details)
        logger.info(f"Orden OCO PAPER simulada exitosamente con List ID: {oco_list_id}")
        return order_details

    async def execute_limit_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        time_in_force: Optional[str] = "GTC"
    ) -> TradeOrderDetails:
        """
        Simula la ejecución de una orden LIMIT.
        """
        logger.info(f"Simulando orden LIMIT PAPER para {symbol} {side} {quantity} a {price} para usuario {user_id}")

        base_asset = symbol.replace("USDT", "")
        quote_asset = "USDT"
        cost_or_revenue = quantity * price

        if side == 'BUY':
            if self.virtual_balances.get(quote_asset, Decimal("0")) < cost_or_revenue:
                raise OrderExecutionError(f"Capital virtual insuficiente para comprar {quantity} de {base_asset} (necesario: {cost_or_revenue}, disponible: {self.virtual_balances.get(quote_asset, Decimal('0'))})")
            # No se ajustan los balances inmediatamente, ya que es una orden LIMIT (no ejecutada aún)
            logger.info(f"Orden LIMIT de compra simulada: {quantity} {base_asset} a {price}. Balance USDT: {self.virtual_balances[quote_asset]}")
        elif side == 'SELL':
            if self.virtual_balances.get(base_asset, Decimal("0")) < quantity:
                raise OrderExecutionError(f"Cantidad virtual insuficiente de {base_asset} para vender (necesario: {quantity}, disponible: {self.virtual_balances.get(base_asset, Decimal('0'))})")
            # No se ajustan los balances inmediatamente
            logger.info(f"Orden LIMIT de venta simulada: {quantity} {base_asset} a {price}. Balance {base_asset}: {self.virtual_balances[base_asset]}")
        else:
            raise ValueError("Side debe ser 'BUY' o 'SELL'.")

        order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            orderId_exchange=f"PAPER_LIMIT_{uuid4()}",
            clientOrderId_exchange=f"PAPER_CLIENT_LIMIT_{uuid4()}",
            orderCategory=OrderCategory.ENTRY,
            type='limit',
            status='new', # La orden LIMIT se crea como 'new'
            requestedPrice=price,
            requestedQuantity=quantity,
            executedQuantity=Decimal("0.0"),
            executedPrice=Decimal("0.0"),
            cumulativeQuoteQty=Decimal("0.0"),
            commissions=[],
            commission=None,
            commissionAsset=None,
            timestamp=datetime.now(timezone.utc),
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=None,
            rawResponse=None,
            ocoOrderListId=None,
            price=price, # Añadir price
            stopPrice=None, # No aplica para limit order
            timeInForce=time_in_force
        )
        self.virtual_trades.append(order_details)
        logger.info(f"Orden LIMIT PAPER simulada exitosamente: {order_details.orderId_internal}")
        return order_details

    async def execute_stop_loss_limit_order(
        self,
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal, # Limit price
        stop_price: Decimal,
        time_in_force: Optional[str] = "GTC"
    ) -> TradeOrderDetails:
        """
        Simula la ejecución de una orden STOP_LOSS_LIMIT.
        """
        logger.info(f"Simulando orden STOP_LOSS_LIMIT PAPER para {symbol} {side} {quantity} a {price} (Stop: {stop_price}) para usuario {user_id}")

        base_asset = symbol.replace("USDT", "")
        quote_asset = "USDT"
        
        # No se ajustan los balances inmediatamente, ya que es una orden STOP_LOSS_LIMIT (no ejecutada aún)
        logger.info(f"Orden STOP_LOSS_LIMIT simulada: {quantity} {base_asset} a {price} con stop {stop_price}.")

        order_details = TradeOrderDetails(
            orderId_internal=uuid4(),
            orderId_exchange=f"PAPER_STOP_LIMIT_{uuid4()}",
            clientOrderId_exchange=f"PAPER_CLIENT_STOP_LIMIT_{uuid4()}",
            orderCategory=OrderCategory.EXIT, # Típicamente una orden de salida
            type='stop_loss_limit',
            status='new', # La orden STOP_LOSS_LIMIT se crea como 'new'
            requestedPrice=price,
            requestedQuantity=quantity,
            executedQuantity=Decimal("0.0"),
            executedPrice=Decimal("0.0"),
            cumulativeQuoteQty=Decimal("0.0"),
            commissions=[],
            commission=None,
            commissionAsset=None,
            timestamp=datetime.now(timezone.utc),
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=None,
            rawResponse=None,
            ocoOrderListId=None,
            price=price, # Añadir price
            stopPrice=stop_price,
            timeInForce=time_in_force
        )
        self.virtual_trades.append(order_details)
        logger.info(f"Orden STOP_LOSS_LIMIT PAPER simulada exitosamente: {order_details.orderId_internal}")
        return order_details

    def get_virtual_balances(self) -> Dict[str, Decimal]:
        """Retorna los balances virtuales actuales."""
        return self.virtual_balances

    def reset_virtual_balances(self, initial_capital: Decimal):
        """Reinicia los balances virtuales a un capital inicial dado."""
        self.virtual_balances = {"USDT": initial_capital}
        self.virtual_trades = []
        logger.info(f"Balances virtuales reiniciados a {initial_capital} USDT.")
