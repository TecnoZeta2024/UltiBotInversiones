import logging
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from collections import defaultdict
from enum import Enum
from datetime import datetime

from core.ports.persistence_service import IPersistenceService
from services.strategy_service import StrategyService
from api.v1.models.performance_models import (
    StrategyPerformanceData,
    OperatingMode,
    StrategyPerformanceResponse
)
from shared.data_types import PerformanceMetrics
from core.domain_models.trade_models import Trade, PositionStatus

logger = logging.getLogger(__name__)

class PerformanceService:
    def __init__(
        self,
        strategy_service: StrategyService,
        persistence_service: IPersistenceService,
    ):
        self.strategy_service = strategy_service
        self._persistence_service = persistence_service
        logger.info(f"PerformanceService initialized. PersistenceService instance: {self._persistence_service}")

    async def get_trade_performance_metrics(
        self,
        user_id: UUID,
        trading_mode: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PerformanceMetrics:
        """
        Calculates and returns aggregated performance metrics for trades.
        """
        logger.info(f"Fetching trade performance metrics for user {user_id}, mode: {trading_mode}")
        
        # Siempre usar el persistence_service inyectado. Si no se inyecta, esto fallará en producción,
        # lo cual es el comportamiento esperado para una dependencia requerida.
        # En tests, se asegura que el mock sea inyectado.
        if self._persistence_service is None:
            raise RuntimeError("PersistenceService no ha sido inyectado en PerformanceService.")
        
        persistence_service = self._persistence_service
        logger.info(f"Using injected persistence_service: {persistence_service}")
        
        all_trades: List[Trade] = await persistence_service.get_trades_with_filters(user_id=str(user_id), trading_mode=trading_mode, status=PositionStatus.CLOSED.value, start_date=start_date, end_date=end_date)
        
        if start_date:
            all_trades = [t for t in all_trades if t.created_at and t.created_at >= start_date]
        if end_date:
            all_trades = [t for t in all_trades if t.created_at and t.created_at <= end_date]

        closed_trades = [trade for trade in all_trades if hasattr(trade, 'positionStatus') and trade.positionStatus == PositionStatus.CLOSED.value]

        if not closed_trades:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                avg_pnl_per_trade=0.0,
                best_trade_pnl=0.0,
                worst_trade_pnl=0.0,
                best_trade_symbol=None,
                worst_trade_symbol=None,
                period_start=start_date,
                period_end=end_date,
                total_volume_traded=0.0,
            )

        total_trades = len(closed_trades)
        winning_trades = sum(1 for trade in closed_trades if hasattr(trade, 'pnl_usd') and trade.pnl_usd is not None and trade.pnl_usd > 0)
        losing_trades = sum(1 for trade in closed_trades if hasattr(trade, 'pnl_usd') and trade.pnl_usd is not None and trade.pnl_usd < 0)
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        total_pnl = sum(trade.pnl_usd for trade in closed_trades if hasattr(trade, 'pnl_usd') and trade.pnl_usd is not None)
        
        avg_pnl_per_trade = total_pnl / total_trades if total_trades > 0 else 0.0
        
        best_trade = max(closed_trades, key=lambda t: t.pnl_usd or -float('inf'), default=None)
        worst_trade = min(closed_trades, key=lambda t: t.pnl_usd or float('inf'), default=None)
        
        total_volume_traded = sum(
            order.executedPrice * order.executedQuantity
            for trade in closed_trades
            for order in ([trade.entryOrder] + trade.exitOrders if hasattr(trade, 'entryOrder') and hasattr(trade, 'exitOrders') else [])
            if hasattr(order, 'executedPrice') and hasattr(order, 'executedQuantity') and order.executedPrice is not None and order.executedQuantity is not None
        )

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=float(total_pnl),
            avg_pnl_per_trade=float(avg_pnl_per_trade),
            best_trade_pnl=float(best_trade.pnl_usd) if best_trade and hasattr(best_trade, 'pnl_usd') and best_trade.pnl_usd is not None else 0.0,
            worst_trade_pnl=float(worst_trade.pnl_usd) if worst_trade and hasattr(worst_trade, 'pnl_usd') and worst_trade.pnl_usd is not None else 0.0,
            best_trade_symbol=best_trade.symbol if best_trade and hasattr(best_trade, 'symbol') else None,
            worst_trade_symbol=worst_trade.symbol if worst_trade and hasattr(worst_trade, 'symbol') else None,
            period_start=start_date,
            period_end=end_date,
            total_volume_traded=float(total_volume_traded),
        )

    async def get_all_strategies_performance(
        self, user_id: UUID, mode_filter: Optional[OperatingMode] = None
    ) -> StrategyPerformanceResponse:
        """
        Calculates and returns performance metrics for all strategies of a user.
        """
        logger.info(f"Fetching performance data for user {user_id}, mode_filter: {mode_filter}")

        # Siempre usar el persistence_service inyectado. Si no se inyecta, esto fallará en producción,
        # lo cual es el comportamiento esperado para una dependencia requerida.
        # En tests, se asegura que el mock sea inyectado.
        if self._persistence_service is None:
            raise RuntimeError("PersistenceService no ha sido inyectado en PerformanceService.")
        
        persistence_service = self._persistence_service
        logger.info(f"Using injected persistence_service: {persistence_service}")
        
        all_user_trades: List[Trade] = await persistence_service.get_trades_with_filters(
            user_id=str(user_id), trading_mode=mode_filter.value if mode_filter else "", status=PositionStatus.CLOSED.value
        )

        closed_trades = [
            trade for trade in all_user_trades if hasattr(trade, 'positionStatus') and trade.positionStatus == PositionStatus.CLOSED.value and hasattr(trade, 'strategyId') and trade.strategyId is not None
        ]

        if not closed_trades:
            logger.info(f"No closed trades found for user {user_id} with mode_filter: {mode_filter}")
            return []

        grouped_trades: Dict[tuple[UUID, str], List[Trade]] = defaultdict(list)
        for trade in closed_trades:
            if hasattr(trade, 'strategyId') and trade.strategyId:
                trade_mode_value = trade.mode
                grouped_trades[(trade.strategyId, trade_mode_value)].append(trade)

        performance_data_list: List[StrategyPerformanceData] = []

        for (strategy_id, trade_mode_str), trades_for_strategy_mode in grouped_trades.items():
            if not trades_for_strategy_mode:
                continue

            total_pnl = sum(trade.pnl_usd if hasattr(trade, 'pnl_usd') and trade.pnl_usd is not None else 0.0 for trade in trades_for_strategy_mode)
            total_operations = len(trades_for_strategy_mode)
            winning_operations = sum(1 for trade in trades_for_strategy_mode if hasattr(trade, 'pnl_usd') and trade.pnl_usd is not None and trade.pnl_usd > 0)

            win_rate = (winning_operations / total_operations) * 100 if total_operations > 0 else 0.0

            # TODO: Refactorizar para obtener el nombre de la estrategia sin depender de StrategyService
            #       o ajustar el modelo de respuesta para que no lo requiera.
            strategy_name = "Estrategia Desconocida"
            
            try:
                current_operating_mode = OperatingMode(trade_mode_str)
            except ValueError:
                logger.warning(f"Modo de operación desconocido '{trade_mode_str}' para la estrategia {strategy_id}. Omitiendo.")
                continue

            performance_entry = StrategyPerformanceData(
                strategyId=strategy_id,
                strategyName=strategy_name,
                mode=current_operating_mode,
                totalOperations=total_operations,
                totalPnl=float(total_pnl),
                win_rate=win_rate,
            )
            performance_data_list.append(performance_entry)
            
        logger.info(f"Generated {len(performance_data_list)} performance entries for user {user_id}")
        return performance_data_list
