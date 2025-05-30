import logging
from uuid import UUID
from typing import Optional

from src.shared.data_types import TradeOrderDetails, ServiceName
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService, PaperOrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import OrderExecutionError, ConfigurationError, CredentialError

logger = logging.getLogger(__name__)

class TradingEngineService:
    """
    Servicio central del motor de trading que decide si ejecutar órdenes
    en modo real o paper trading, basándose en la configuración del usuario.
    """
    def __init__(
        self,
        config_service: ConfigService,
        order_execution_service: OrderExecutionService,
        paper_order_execution_service: PaperOrderExecutionService,
        credential_service: CredentialService
    ):
        self.config_service = config_service
        self.order_execution_service = order_execution_service
        self.paper_order_execution_service = paper_order_execution_service
        self.credential_service = credential_service

    async def execute_trade(
        self,
        user_id: UUID,
        symbol: str,
        side: str, # 'BUY' o 'SELL'
        quantity: float,
        credential_label: str = "default_binance_spot" # Etiqueta de la credencial de Binance a usar
    ) -> TradeOrderDetails:
        """
        Ejecuta una operación de trading, decidiendo entre modo real o paper trading.
        """
        logger.info(f"Solicitud de ejecución de trade para usuario {user_id}: {side} {quantity} de {symbol}")
        
        try:
            user_config = await self.config_service.load_user_configuration(user_id)
            
            if user_config.paperTradingActive:
                logger.info(f"Modo Paper Trading ACTIVO para usuario {user_id}. Simulando orden.")
                order_details = await self.paper_order_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity
                )
            else:
                logger.info(f"Modo Real Trading ACTIVO para usuario {user_id}. Ejecutando orden real.")
                # Obtener credenciales de Binance
                binance_credential = await self.credential_service.get_credential(
                    user_id=user_id,
                    service_name=ServiceName.BINANCE_SPOT, # Asumimos SPOT por ahora
                    credential_label=credential_label
                )
                
                if not binance_credential:
                    raise CredentialError(f"No se encontraron credenciales de Binance con la etiqueta '{credential_label}' para el usuario {user_id}.")
                
                # Desencriptar credenciales para pasarlas al servicio de ejecución real
                api_key = self.credential_service.decrypt_data(binance_credential.encrypted_api_key)
                
                api_secret: Optional[str] = None
                if binance_credential.encrypted_api_secret:
                    api_secret = self.credential_service.decrypt_data(binance_credential.encrypted_api_secret)

                if not api_key or api_secret is None: # api_secret puede ser una cadena vacía si no hay secret
                    raise CredentialError(f"API Key o Secret de Binance no pudieron ser desencriptados para la credencial '{credential_label}'.")

                order_details = await self.order_execution_service.execute_market_order(
                    user_id=user_id,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    api_key=api_key,
                    api_secret=api_secret
                )
            
            logger.info(f"Trade ejecutado exitosamente en modo {'PAPER' if user_config.paperTradingActive else 'REAL'}: {order_details.orderId_internal}")
            return order_details

        except ConfigurationError as e:
            logger.error(f"Error de configuración para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo en el motor de trading debido a error de configuración: {e}") from e
        except CredentialError as e:
            logger.error(f"Error de credenciales para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Fallo en el motor de trading debido a error de credenciales: {e}") from e
        except OrderExecutionError as e:
            logger.error(f"Error de ejecución de orden para usuario {user_id}: {e}", exc_info=True)
            raise # Re-lanzar el error de ejecución de orden
        except Exception as e:
            logger.error(f"Error inesperado en el motor de trading para usuario {user_id}: {e}", exc_info=True)
            raise OrderExecutionError(f"Error inesperado en el motor de trading: {e}") from e
