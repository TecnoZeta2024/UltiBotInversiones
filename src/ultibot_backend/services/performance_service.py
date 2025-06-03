import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from collections import defaultdict
from enum import Enum # Añadido para Enum

from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.api.v1.models.performance_models import (
    StrategyPerformanceData,
    OperatingMode,
    StrategyPerformanceResponse
)
from src.shared.data_types import Trade # Cambiada la importación de Trade
from src.ultibot_backend.core.domain_models.trade_models import PositionStatus # PositionStatus ya estaba aquí, se mantiene

logger = logging.getLogger(__name__)

class PerformanceService:
    def __init__(
        self,
        persistence_service: SupabasePersistenceService,
        strategy_service: StrategyService,
    ):
        self.persistence_service = persistence_service
        self.strategy_service = strategy_service

    async def get_all_strategies_performance(
        self, user_id: UUID, mode_filter: Optional[OperatingMode] = None
    ) -> StrategyPerformanceResponse:
        """
        Calculates and returns performance metrics for all strategies of a user.
        """
        logger.info(f"Fetching performance data for user {user_id}, mode_filter: {mode_filter}")

        # Subtarea 1.2.1: Obtener los datos de trades desde DataPersistenceService
        # El método get_all_trades_for_user ya puede filtrar por modo si se le pasa mode_filter.value
        all_user_trades: List[Trade] = await self.persistence_service.get_all_trades_for_user(
            user_id, mode_filter.value if mode_filter else None
        )

        # Filtrar solo trades cerrados
        closed_trades = [
            trade for trade in all_user_trades if trade.positionStatus == PositionStatus.CLOSED.value and trade.strategyId is not None
        ]

        if not closed_trades:
            logger.info(f"No closed trades found for user {user_id} with mode_filter: {mode_filter}")
            return []

        # Subtarea 1.2.2: Agrupar trades por strategyId y mode
        # (Aunque mode ya está filtrado si se proveyó mode_filter, agrupamos por el 'mode' del trade para consistencia)
        grouped_trades: Dict[tuple[UUID, str], List[Trade]] = defaultdict(list)
        for trade in closed_trades:
            if trade.strategyId: # Asegurarse de que strategyId no sea None
                 # El 'mode' del trade debe ser un string simple ('paper' o 'real')
                trade_mode_value = trade.mode.value if isinstance(trade.mode, Enum) else str(trade.mode)
                grouped_trades[(trade.strategyId, trade_mode_value)].append(trade)

        performance_data_list: StrategyPerformanceResponse = []

        for (strategy_id, trade_mode_str), trades_for_strategy_mode in grouped_trades.items():
            if not trades_for_strategy_mode:
                continue

            # Subtarea 1.2.3: Calcular P&L total, número de operaciones, y número de operaciones ganadoras
            total_pnl = sum(trade.pnl_usd if trade.pnl_usd is not None else 0.0 for trade in trades_for_strategy_mode)
            total_operations = len(trades_for_strategy_mode)
            winning_operations = sum(1 for trade in trades_for_strategy_mode if trade.pnl_usd is not None and trade.pnl_usd > 0)

            # Subtarea 1.2.4: Calcular el Win Rate
            win_rate = (winning_operations / total_operations) * 100 if total_operations > 0 else 0.0

            # Subtarea 1.2.5: Obtener los nombres de las estrategias
            strategy_config = await self.strategy_service.get_strategy_config(str(strategy_id), str(user_id))
            strategy_name = strategy_config.config_name if strategy_config else "Estrategia Desconocida" # Corregido a config_name
            
            # Convertir trade_mode_str de nuevo a OperatingMode Enum para el modelo de respuesta
            try:
                current_operating_mode = OperatingMode(trade_mode_str)
            except ValueError:
                logger.warning(f"Modo de operación desconocido '{trade_mode_str}' para la estrategia {strategy_id}. Omitiendo.")
                continue


            # Subtarea 1.2.6: Formatear los datos para la respuesta de la API
            performance_entry = StrategyPerformanceData(
                strategyId=strategy_id, # Pydantic se encargará del alias strategy_id
                strategyName=strategy_name,
                mode=current_operating_mode, # Usar el enum
                totalOperations=total_operations,
                totalPnl=total_pnl,
                win_rate=win_rate, # Corregido a win_rate
            )
            performance_data_list.append(performance_entry)
            
        logger.info(f"Generated {len(performance_data_list)} performance entries for user {user_id}")
        return performance_data_list
