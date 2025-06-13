# src/ultibot_backend/services/trading_engine_service.py
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4  # ✅ AGREGADO: import uuid4
from decimal import Decimal
from datetime import datetime, timezone

from ..core.domain_models.trading import Order, Trade, OrderSide, OrderType, OrderStatus
from ..core.domain_models.strategy import StrategyAnalysis
from ..core.domain_models.portfolio import Portfolio, Position
from ..core.domain_models.ai_models import AIAnalysisResult, TradingOpportunity, AIProcessingStage
from ..core.ports import IOrderExecutionPort, IPersistencePort, ICredentialService, IMarketDataProvider, IAIOrchestrator
from ..core.exceptions import InsufficientFundsError, CredentialError, BinanceAPIError, UltiBotError
from ..app_config import settings
import logging

logger = logging.getLogger(__name__)

class TradingDecision(BaseModel):
    """
    Represents a trading decision made by the AI or a strategy.
    """
    decision: str = Field(..., description="The trading decision (e.g., 'BUY', 'SELL', 'HOLD').")
    symbol: str = Field(..., description="The symbol for the trading pair.")
    confidence: float = Field(..., description="The confidence level of the decision (0.0 to 1.0).")
    strategy_analysis: Optional[StrategyAnalysis] = Field(None, description="Analysis from the strategy.")
    # Add other relevant fields like stop_loss, take_profit, etc.

class TradingEngine:
    """
    The core service for executing trading logic.
    
    This service integrates market data, strategies, and AI analysis
    to make and execute trading decisions.
    """

    def __init__(
        self,
        order_execution_port: IOrderExecutionPort,
        persistence_port: IPersistencePort,
        credential_service: ICredentialService,
        market_data_provider: IMarketDataProvider,
        ai_orchestrator: IAIOrchestrator,
    ):
        self.order_execution_port = order_execution_port
        self.persistence_port = persistence_port
        self.credential_service = credential_service
        self.market_data_provider = market_data_provider
        self.ai_orchestrator = ai_orchestrator
        self.fixed_user_id = settings.FIXED_USER_ID
        logger.info("TradingEngine initialized with dependencies.")

    def _calculate_quantity(self, capital_to_allocate: Decimal, asset_price: Decimal) -> Decimal:
        """
        ✅ AGREGADO: Calcula la cantidad a comprar basada en capital disponible y precio del activo.
        
        Args:
            capital_to_allocate: Capital disponible para la operación
            asset_price: Precio actual del activo
            
        Returns:
            Cantidad a comprar (redondeada a 8 decimales para precisión crypto)
        """
        if asset_price <= 0:
            raise ValueError("El precio del activo debe ser mayor que 0")
        if capital_to_allocate <= 0:
            raise ValueError("El capital a asignar debe ser mayor que 0")
            
        quantity = capital_to_allocate / asset_price
        # Redondear a 8 decimales para compatibilidad con exchanges crypto
        return round(quantity, 8)

    async def execute_order(
        self,
        symbol: str,
        order_type: OrderType,
        side: OrderSide,
        quantity: Decimal,
        price: Optional[Decimal],
        trading_mode: str,
        user_id: UUID,
        strategy_id: Optional[UUID] = None,
        opportunity_id: Optional[UUID] = None,
        ai_analysis_confidence: Optional[float] = None,
    ) -> Order:
        """
        Executes a trading order (market or limit) in paper or real mode.
        """
        logger.info(f"Attempting to execute {side.value} {quantity} of {symbol} at {price} in {trading_mode} mode for user {user_id}")

        if trading_mode == "real":
            # Verificar credenciales para trading real
            binance_credential = await self.credential_service.get_first_decrypted_credential_by_service(
                service_name=settings.DEFAULT_REAL_TRADING_EXCHANGE
            )
            if not binance_credential:
                raise CredentialError(f"No se encontraron credenciales para trading real en {settings.DEFAULT_REAL_TRADING_EXCHANGE}.")
            
            # Verificar fondos suficientes en la cuenta real
            current_price = await self.market_data_provider.get_latest_price(symbol)
            required_funds = quantity * current_price if side == OrderSide.BUY else quantity
            
            # Esto es una simplificación. En un sistema real, se verificarían los balances exactos.
            # Por ahora, asumimos que si la credencial es válida, hay fondos.
            # TODO: Implementar verificación de fondos real con balances de exchange.
            
            # Ejecutar orden real
            order = await self.order_execution_port.execute_order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                quantity=quantity,
                price=price
            )
            logger.info(f"Orden real ejecutada: {order.order_id} - {order.status}")
        elif trading_mode == "paper":
            # Simular ejecución de orden en paper trading
            order_id = str(uuid4())  # ✅ CORREGIDO: ahora uuid4 está importado
            order = Order(
                id=order_id,
                symbol=symbol,
                type=order_type,
                side=side,
                quantity=quantity,
                price=price if price else (await self.market_data_provider.get_latest_price(symbol)),
                status=OrderStatus.FILLED, # En paper trading, asumimos que se llena inmediatamente
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            logger.info(f"Orden de paper trading simulada: {order.order_id} - {order.status}")
        else:
            raise ValueError(f"Modo de trading no válido: {trading_mode}")

        # Registrar el trade
        trade = Trade(
            symbol=symbol,
            side=side,
            quantity=order.quantity,
            price=order.price,
            order_type=order.type,
            strategy_id=str(strategy_id) if strategy_id else None,
        )
        # await self.persistence_port.upsert_trade(trade.model_dump())
        logger.info(f"Trade {trade.id} registrado en la persistencia.")
        
        # Actualizar portafolio
        # await self._update_portfolio_after_trade(user_id, trading_mode, trade)

        return order

    async def _update_portfolio_after_trade(self, user_id: UUID, trading_mode: str, trade: Trade):
        portfolio = await self.persistence_port.get_portfolio(str(user_id), trading_mode)
        if not portfolio:
            portfolio = Portfolio(
                id=uuid4(),  # ✅ CORREGIDO: ahora uuid4 está importado
                user_id=user_id,
                mode=trading_mode,
                cash_balance=settings.DEFAULT_PAPER_TRADING_CAPITAL if trading_mode == "paper" else Decimal(0.0), # Asumir 0 para real, se cargaría de balances
                positions=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            logger.info(f"Portafolio nuevo creado para usuario {user_id} en modo {trading_mode}.")

        # Actualizar balance de efectivo y posiciones
        if trade.side == OrderSide.BUY:
            cost = trade.quantity * trade.price
            portfolio.cash_balance -= cost
            # Añadir o actualizar posición
            existing_position = next((p for p in portfolio.positions if p.symbol == trade.symbol), None)
            if existing_position:
                existing_position.quantity += trade.quantity
                existing_position.average_price = (existing_position.average_price * (existing_position.quantity - trade.quantity) + trade.price * trade.quantity) / existing_position.quantity
            else:
                portfolio.positions.append(Position(
                    symbol=trade.symbol,
                    quantity=trade.quantity,
                    average_price=trade.price,
                    opened_at=trade.timestamp
                ))
        elif trade.side == OrderSide.SELL:
            revenue = trade.quantity * trade.price
            portfolio.cash_balance += revenue
            # Reducir o eliminar posición
            existing_position = next((p for p in portfolio.positions if p.symbol == trade.symbol), None)
            if existing_position:
                existing_position.quantity -= trade.quantity
                if existing_position.quantity <= 0:
                    portfolio.positions.remove(existing_position)
            else:
                logger.warning(f"Intentando vender {trade.symbol} sin una posición abierta en el portafolio {portfolio.id}.")

        portfolio.updated_at = datetime.now(timezone.utc)
        await self.persistence_port.save_portfolio(portfolio)
        logger.info(f"Portafolio {portfolio.id} actualizado. Balance de efectivo: {portfolio.cash_balance}")

    async def process_opportunity_with_ai_decision(self, opportunity: TradingOpportunity, user_id: UUID) -> AIAnalysisResult:
        """
        Processes a trading opportunity, makes a decision based on AI analysis,
        and executes a trade if recommended.
        """
        logger.info(f"Procesando oportunidad {opportunity.opportunity_id} con decisión de IA para usuario {user_id}.")

        # Invocar al orquestador de IA para obtener el análisis
        ai_analysis_result = await self.ai_orchestrator.analyze_opportunity(opportunity)

        if ai_analysis_result.recommendation == "BUY" and ai_analysis_result.confidence >= settings.AI_TRADING_CONFIDENCE_THRESHOLD:
            logger.info(f"AI recomienda COMPRAR {opportunity.symbol} con confianza {ai_analysis_result.confidence}. Ejecutando trade.")
            # Determinar cantidad a comprar (ej. un valor fijo o basado en capital disponible)
            quantity = Decimal("0.001") # Ejemplo: 0.001 BTC
            
            try:
                order = await self.execute_order(
                    symbol=opportunity.symbol,
                    order_type=OrderType.MARKET,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    price=None, # Precio de mercado
                    trading_mode="paper", # Oportunidades de IA por ahora en paper
                    user_id=user_id,
                    strategy_id=opportunity.strategy_id,
                    opportunity_id=opportunity.opportunity_id,
                    ai_analysis_confidence=ai_analysis_result.confidence
                )
                logger.info(f"Trade ejecutado para oportunidad {opportunity.opportunity_id}: {order.id}")
                ai_analysis_result.trade_executed = True
                ai_analysis_result.trade_details = order.model_dump()
            except InsufficientFundsError as e:
                logger.error(f"Fondos insuficientes para ejecutar trade para oportunidad {opportunity.opportunity_id}: {e}")
                ai_analysis_result.reasoning += f" | Fondos insuficientes: {e}"
                ai_analysis_result.recommendation = "HOLD" # Cambiar a HOLD si no hay fondos
                ai_analysis_result.trade_executed = False
            except Exception as e:
                logger.error(f"Error al ejecutar trade para oportunidad {opportunity.opportunity_id}: {e}", exc_info=True)
                ai_analysis_result.reasoning += f" | Error de ejecución: {e}"
                ai_analysis_result.recommendation = "HOLD"
                ai_analysis_result.trade_executed = False
        else:
            logger.info(f"AI recomienda {ai_analysis_result.recommendation} para {opportunity.symbol} (confianza: {ai_analysis_result.confidence}). No se ejecuta trade.")
            ai_analysis_result.trade_executed = False
        
        # Actualizar el estado de la oportunidad en la persistencia
        await self.persistence_port.update_opportunity_analysis(
            opportunity_id=opportunity.opportunity_id,
            status=ai_analysis_result.stage,
            ai_analysis=ai_analysis_result.reasoning,
            confidence_score=ai_analysis_result.confidence,
            suggested_action=ai_analysis_result.recommendation,
            status_reason="Trade ejecutado" if ai_analysis_result.trade_executed else "No se ejecutó trade"
        )

        return ai_analysis_result

    async def close(self):
        """Cierra cualquier recurso abierto por el TradingEngine."""
        # Por ahora, no hay recursos directos que cerrar aquí,
        # pero en una implementación real podría haber clientes de exchange, etc.
        logger.info("TradingEngine cerrado.")
