import logging
import json
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, ValidationError

from ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    CustomAIDrivenParameters,
    MCPSignalFollowerParameters,
    GridTradingParameters,
    DCAInvestingParameters,
    StrategySpecificParameters
)
from ultibot_backend.core.exceptions import ConfigurationError
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService

logger = logging.getLogger(__name__)

STRATEGY_TYPE_MAP: Dict[str, Type[BaseModel]] = {
    "SCALPING": ScalpingParameters,
    "DAY_TRADING": DayTradingParameters,
    "ARBITRAGE_SIMPLE": ArbitrageSimpleParameters,
    "CUSTOM_AI_DRIVEN": CustomAIDrivenParameters,
    "MCP_SIGNAL_FOLLOWER": MCPSignalFollowerParameters,
    "GRID_TRADING": GridTradingParameters,
    "DCA_INVESTING": DCAInvestingParameters,
}

class StrategyService:
    """
    Servicio para gestionar las configuraciones de las estrategias de trading.
    """

    def __init__(self, persistence_service: SupabasePersistenceService):
        self.db = persistence_service

    async def create_strategy_config(self, strategy_config: TradingStrategyConfig) -> UUID:
        """Crea una nueva configuración de estrategia en la base de datos."""
        try:
            strategy_dict = strategy_config.model_dump(mode='json')
            await self.db.upsert_strategy_config(strategy_dict)
            logger.info(f"Strategy config '{strategy_config.config_name}' created/updated with ID: {strategy_config.id}")
            return strategy_config.id
        except Exception as e:
            logger.error(f"Error creating strategy config: {e}", exc_info=True)
            raise ConfigurationError(f"Database error while creating strategy: {e}")

    async def list_strategy_configs(self, user_id: UUID) -> List[TradingStrategyConfig]:
        """Obtiene todas las configuraciones de estrategias para un usuario."""
        try:
            rows = await self.db.list_strategy_configs_by_user()
            return [TradingStrategyConfig(**row) for row in rows if row]
        except Exception as e:
            logger.error(f"Error listing strategy configs for user {user_id}: {e}", exc_info=True)
            return []

    async def get_strategy_config(self, strategy_id: UUID) -> Optional[TradingStrategyConfig]:
        """Obtiene una configuración de estrategia por su ID."""
        try:
            row = await self.db.get_strategy_config_by_id(strategy_id)
            return TradingStrategyConfig(**row) if row else None
        except Exception as e:
            logger.error(f"Error getting strategy config {strategy_id}: {e}", exc_info=True)
            return None

    async def update_strategy_config(self, strategy_id: UUID, updates: Dict[str, Any]) -> bool:
        """Actualiza una configuración de estrategia."""
        try:
            existing_config = await self.get_strategy_config(strategy_id)
            if not existing_config:
                return False
            
            updated_config = existing_config.model_copy(update=updates)
            await self.db.upsert_strategy_config(updated_config.model_dump(mode='json'))
            logger.info(f"Strategy config {strategy_id} updated successfully.")
            return True
        except Exception as e:
            logger.error(f"Error updating strategy config {strategy_id}: {e}", exc_info=True)
            return False

    async def activate_strategy(self, strategy_id: UUID, paper_mode: bool = False, real_mode: bool = False) -> bool:
        """Activa o desactiva una estrategia para un modo de trading específico."""
        logger.info(f"Setting strategy {strategy_id} active status: paper={paper_mode}, real={real_mode}.")
        return await self.update_strategy_config(strategy_id, {"is_active_paper_mode": paper_mode, "is_active_real_mode": real_mode})

    async def deactivate_strategy(self, strategy_id: UUID) -> bool:
        """Desactiva una estrategia en ambos modos."""
        logger.info(f"Deactivating strategy {strategy_id}.")
        return await self.update_strategy_config(strategy_id, {"is_active_paper_mode": False, "is_active_real_mode": False})
