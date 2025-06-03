import logging
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import Depends # Añadido

from src.shared.data_types import PortfolioSnapshot, PortfolioSummary, PortfolioAsset, AssetBalance, UserConfiguration, Trade
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
        self.user_id: Optional[UUID] = None # Se establecerá al inicializar o cargar la configuración

    async def initialize_portfolio(self, user_id: UUID):
        """
        Inicializa el portafolio de paper trading cargando la configuración del usuario.
        """
        self.user_id = user_id
        try:
            # Obtener la configuración directamente del servicio de persistencia
            config_data = await self.persistence_service.get_user_configuration(user_id)
            user_config = UserConfiguration(**config_data) if config_data else None
            
            if user_config and user_config.defaultPaperTradingCapital is not None:
                self.paper_trading_balance = user_config.defaultPaperTradingCapital
            else:
                self.paper_trading_balance = 10000.0 # Valor por defecto si no está configurado o no se encuentra
                logger.info(f"No se encontró defaultPaperTradingCapital para el usuario {user_id}. Usando valor por defecto: {self.paper_trading_balance}")

            logger.info(f"Portafolio de paper trading inicializado para el usuario {user_id} con capital: {self.paper_trading_balance}")
            # TODO: Cargar activos de paper trading persistidos si aplica (para futuras historias)
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
                    asset_name = balance.asset.upper() # Convertir a mayúsculas para la comparación
                    if asset_name.endswith("USDT"):
                        pair_to_query = asset_name
                    # Considerar si el activo es USDC u otra stablecoin que se quiera valorar contra USDT
                    elif asset_name == "USDC":
                        pair_to_query = "USDCUSDT" # Par para obtener el precio de USDC en USDT
                    else:
                        pair_to_query = f"{asset_name}USDT"
                    assets_to_value.append(pair_to_query)

            # Obtener precios de mercado para los activos no-USDT
            if assets_to_value:
                # Eliminar duplicados de assets_to_value antes de la llamada a la API
                unique_assets_to_value = sorted(list(set(assets_to_value)))
                market_data = await self.market_data_service.get_market_data_rest(user_id, unique_assets_to_value)

                for balance in binance_balances:
                    if balance.asset != "USDT" and balance.total > 0:
                        asset_name = balance.asset.upper() # Convertir a mayúsculas
                        # Reconstruir el par de la misma manera para la búsqueda en market_data
                        if asset_name.endswith("USDT"):
                            symbol_pair = asset_name
                        elif asset_name == "USDC":
                            symbol_pair = "USDCUSDT"
                        else:
                            symbol_pair = f"{asset_name}USDT"
                        
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
            # Obtener la configuración directamente del servicio de persistencia
            config_data = await self.persistence_service.get_user_configuration(user_id)
            user_config = UserConfiguration(**config_data) if config_data else None

            if user_config:
                user_config.defaultPaperTradingCapital = self.paper_trading_balance
                await self.persistence_service.upsert_user_configuration(user_id, user_config.model_dump(mode='json', by_alias=True, exclude_none=True))
                logger.info(f"Saldo de paper trading actualizado a {self.paper_trading_balance} para el usuario {user_id}.")
            else:
                logger.error(f"No se encontró la configuración de usuario para {user_id}. No se pudo persistir el capital de paper trading.")
                raise ConfigurationError(f"No se encontró la configuración de usuario para {user_id}.")
        except Exception as e:
            logger.critical(f"Error inesperado al actualizar y persistir el saldo de paper trading para el usuario {user_id}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al actualizar el saldo de paper trading: {e}")

    async def update_paper_portfolio_after_entry(self, trade: Trade):
        """
        Actualiza el portafolio de paper trading después de una orden de entrada simulada.
        AC2: Actualizar el saldo de totalCashBalance en el PortfolioSnapshot de Paper Trading, restando el valor de la operación.
        AC3: Añadir el activo comprado/vendido a assetHoldings en el PortfolioSnapshot de Paper Trading.
        AC4: Persistir el PortfolioSnapshot actualizado utilizando PersistenceService.
        """
        user_id = trade.user_id
        symbol = trade.symbol
        quantity = trade.entryOrder.executedQuantity
        executed_price = trade.entryOrder.executedPrice
        side = trade.side

        logger.info(f"Actualizando portafolio de paper trading para trade {trade.id}: {side} {quantity} de {symbol} @ {executed_price}")

        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        # 2.2: Actualizar el saldo de totalCashBalance
        trade_value = quantity * executed_price
        if side == 'BUY':
            self.paper_trading_balance -= trade_value
        elif side == 'SELL':
            # En una orden de entrada 'SELL' en paper trading, asumimos que estamos "vendiendo en corto"
            # o que estamos abriendo una posición corta. Esto no añade efectivo, sino que crea una deuda
            # o una posición negativa. Para simplificar en v1.0, solo restaremos el valor del capital
            # como si fuera una compra, pero esto debería ser revisado para una gestión de cortos más robusta.
            # Por ahora, para mantener la simetría con BUY en términos de impacto en el capital inicial:
            self.paper_trading_balance -= trade_value # Esto simula que el capital se "compromete"
        else:
            logger.error(f"Side de trade desconocido: {side} para trade {trade.id}. No se actualizó el balance.")
            raise PortfolioError(f"Side de trade desconocido: {side}")

        # 2.3: Añadir/actualizar el activo en assetHoldings
        if symbol in self.paper_trading_assets:
            existing_asset = self.paper_trading_assets[symbol]
            if side == 'BUY':
                total_quantity = existing_asset.quantity + quantity
                new_entry_price = ((existing_asset.entry_price * existing_asset.quantity) + (executed_price * quantity)) / total_quantity if existing_asset.entry_price is not None else executed_price
                existing_asset.quantity = total_quantity
                existing_asset.entry_price = new_entry_price
            elif side == 'SELL':
                # Para una venta en corto, la cantidad se vuelve negativa.
                # Esto es una simplificación. Una gestión real de cortos es más compleja.
                existing_asset.quantity -= quantity
                # El precio de entrada para cortos es el precio de venta.
                # Si ya teníamos una posición larga, esto la reduce.
                # Si no teníamos, o si la cantidad excede la larga, se convierte en corta.
                # Para v1.0, simplificamos a solo restar la cantidad.
            logger.info(f"Activo {symbol} actualizado en paper trading. Cantidad: {existing_asset.quantity}, Precio de entrada: {existing_asset.entry_price}")
        else:
            # Si el activo no existe, lo creamos. Para 'SELL', la cantidad inicial es negativa.
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
            logger.info(f"Activo {symbol} añadido a paper trading. Cantidad: {initial_quantity}, Precio de entrada: {executed_price}")

        # 2.4: Persistir el PortfolioSnapshot actualizado
        # Por ahora, solo persistimos el capital actualizado en la configuración del usuario.
        # La persistencia de assetHoldings de paper trading se pospone.
        try:
            user_config_dict = await self.persistence_service.get_user_configuration(user_id)
            if user_config_dict:
                user_config = UserConfiguration(**user_config_dict)
                user_config.defaultPaperTradingCapital = self.paper_trading_balance
                await self.persistence_service.upsert_user_configuration(user_id, user_config.model_dump(mode='json', by_alias=True, exclude_none=True))
                logger.info(f"Capital de paper trading persistido: {self.paper_trading_balance}")
            else:
                logger.error(f"No se encontró la configuración de usuario para {user_id}. No se pudo persistir el capital de paper trading.")
        except Exception as e:
            logger.error(f"Error al persistir el capital de paper trading para usuario {user_id} tras cierre de trade: {e}", exc_info=True)
            raise PortfolioError(f"Fallo al persistir el capital de paper trading tras cierre: {e}")

        logger.info(f"Portafolio de paper trading actualizado. Nuevo balance: {self.paper_trading_balance}")

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

    async def update_paper_portfolio_after_exit(self, trade: Trade):
        """
        Actualiza el portafolio de paper trading después de una orden de salida simulada.
        AC2: Actualizar el saldo de totalCashBalance en el PortfolioSnapshot de Paper Trading, sumando/restando el P&L de la operación.
        AC3: Eliminar o ajustar el AssetHolding correspondiente en el PortfolioSnapshot de Paper Trading.
        AC4: Persistir el PortfolioSnapshot actualizado utilizando PersistenceService.
        """
        user_id = trade.user_id
        symbol = trade.symbol
        quantity = trade.entryOrder.executedQuantity # Cantidad original de la posición
        pnl_usd = trade.pnl_usd
        side = trade.side
        closing_reason = trade.closingReason

        logger.info(f"Actualizando portafolio de paper trading para trade {trade.id} cerrado por {closing_reason}. P&L: {pnl_usd:.2f} USD")

        if self.user_id is None or self.user_id != user_id:
            await self.initialize_portfolio(user_id)

        # Subtask 2.2: Actualizar el saldo de totalCashBalance
        if pnl_usd is not None:
            self.paper_trading_balance += pnl_usd
            logger.info(f"Saldo de paper trading ajustado por P&L. Nuevo balance: {self.paper_trading_balance:.2f}")
        else:
            logger.warning(f"Trade {trade.id} cerrado sin P&L definido. No se ajustó el balance de paper trading.")

        # Subtask 2.3: Eliminar o ajustar el AssetHolding correspondiente
        if symbol in self.paper_trading_assets:
            asset = self.paper_trading_assets[symbol]
            if side == 'BUY':
                # Si era una posición larga (BUY), al cerrar se elimina el activo
                # Asumimos que la cantidad de salida es igual a la de entrada para un cierre completo
                if asset.quantity == quantity:
                    del self.paper_trading_assets[symbol]
                    logger.info(f"Activo {symbol} completamente removido del portafolio de paper trading.")
                else:
                    # Si la cantidad no coincide (cierre parcial, no esperado en esta historia), ajustar
                    asset.quantity -= quantity
                    logger.warning(f"Cierre parcial o cantidad no coincidente para {symbol}. Cantidad restante: {asset.quantity}")
            elif side == 'SELL':
                # Si era una posición corta (SELL), al cerrar se "compra de vuelta" el activo
                # Esto significa que la cantidad negativa se reduce o se vuelve cero
                if asset.quantity == -quantity: # Si la cantidad negativa coincide con la cantidad de entrada
                    del self.paper_trading_assets[symbol]
                    logger.info(f"Posición corta de {symbol} completamente cerrada en paper trading.")
                else:
                    asset.quantity += quantity # Sumar la cantidad para reducir la posición corta
                    logger.warning(f"Cierre parcial o cantidad no coincidente para posición corta de {symbol}. Cantidad restante: {asset.quantity}")
        else:
            logger.warning(f"Activo {symbol} no encontrado en el portafolio de paper trading al intentar cerrar trade {trade.id}.")

        # Subtask 2.4: Persistir el PortfolioSnapshot actualizado
        # Por ahora, solo persistimos el capital actualizado en la configuración del usuario.
        # La persistencia de assetHoldings de paper trading se pospone.
        try:
            user_config_dict = await self.persistence_service.get_user_configuration(user_id)
            if user_config_dict:
                user_config = UserConfiguration(**user_config_dict)
                user_config.defaultPaperTradingCapital = self.paper_trading_balance
                await self.persistence_service.upsert_user_configuration(user_id, user_config.model_dump(mode='json', by_alias=True, exclude_none=True))
                logger.info(f"Capital de paper trading persistido: {self.paper_trading_balance}")
            else:
                logger.error(f"No se encontró la configuración de usuario para {user_id}. No se pudo persistir el capital de paper trading.")
        except Exception as e:
            logger.error(f"Error al persistir el capital de paper trading para usuario {user_id} tras cierre de trade: {e}", exc_info=True)
            raise PortfolioError(f"Fallo al persistir el capital de paper trading tras cierre: {e}")

        logger.info(f"Portafolio de paper trading actualizado tras cierre de trade {trade.id}. Nuevo balance: {self.paper_trading_balance}")

    async def update_real_portfolio_after_exit(self, trade: Trade):
        """
        Actualiza el portafolio real después de una orden de salida real.
        Dado que el portafolio real se consulta directamente de Binance,
        este método principalmente sirve para fines de logging y para
        gatillar una posible re-consulta o notificación.
        """
        logger.info(f"Trade real {trade.id} cerrado. Se recomienda re-consultar el balance de Binance para el estado más reciente del portafolio real.")
        # No se requiere lógica de actualización de estado interno aquí,
        # ya que el PortfolioService consulta el estado real de Binance.
        # Futuras mejoras podrían incluir un mecanismo de caché o eventos.

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

    async def get_real_usdt_balance(self, user_id: UUID) -> float:
        """
        Obtiene el saldo disponible de USDT en la cuenta real de Binance para un usuario.
        Lanza PortfolioError si hay un problema al obtener el saldo.
        """
        try:
            binance_balances: List[AssetBalance] = await self.market_data_service.get_binance_spot_balances(user_id)
            usdt_balance = 0.0
            for balance in binance_balances:
                if balance.asset == "USDT":
                    usdt_balance = balance.free
                    break
            logger.info(f"Saldo de USDT real para el usuario {user_id}: {usdt_balance}")
            return usdt_balance
        except ExternalAPIError as e:
            logger.error(f"Error de API externa al obtener el saldo de USDT para el usuario {user_id}: {str(e)}", exc_info=True)
            raise PortfolioError(f"No se pudo obtener el saldo de USDT de Binance: {str(e)}") from e
        except Exception as e:
            logger.critical(f"Error inesperado al obtener el saldo de USDT para el usuario {user_id}: {str(e)}", exc_info=True)
            raise PortfolioError(f"Error inesperado al obtener el saldo de USDT: {str(e)}") from e
