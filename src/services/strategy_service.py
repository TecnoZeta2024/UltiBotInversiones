import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import ValidationError

from adapters.persistence_service import SupabasePersistenceService
from core.domain_models.trading_strategy_models import (
    BaseStrategyType,
    TradingStrategyConfig,
    StrategySpecificParameters,
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    CustomAIDrivenParameters,
    MCPSignalFollowerParameters,
    GridTradingParameters,
    DCAInvestingParameters,
)
from core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
)
from services.config_service import ConfigurationService

logger = logging.getLogger(__name__)


class StrategyService:
    def __init__(
        self,
        persistence_service: SupabasePersistenceService,
        configuration_service: ConfigurationService,
    ):
        self.persistence_service = persistence_service
        self.configuration_service = configuration_service

    async def _validate_ai_profile(self, user_id: str, ai_profile_id: str) -> bool:
        user_config = await self.configuration_service.get_user_configuration(user_id)
        if not user_config or not user_config.ai_strategy_configurations:
            return False
        return any(p.id == ai_profile_id for p in user_config.ai_strategy_configurations)

    async def create_strategy_config(self, user_id: str, strategy_data: Dict[str, Any]) -> TradingStrategyConfig:
        try:
            strategy_id = uuid.uuid4() # Generar UUID directamente
            
            # Ensure all required fields are present and correctly typed for TradingStrategyConfig
            full_strategy_data = {
                "id": str(strategy_id),
                "user_id": user_id,
                "config_name": strategy_data["config_name"], # Make sure this is always present
                "base_strategy_type": BaseStrategyType(strategy_data["base_strategy_type"]), # Convert to Enum
                "parameters": strategy_data.get("parameters", {}), # Default to empty dict if not provided
                "description": strategy_data.get("description"),
                "is_active_paper_mode": strategy_data.get("is_active_paper_mode", False),
                "is_active_real_mode": strategy_data.get("is_active_real_mode", False),
                "allowed_symbols": strategy_data.get("allowed_symbols"),
                "excluded_symbols": strategy_data.get("excluded_symbols"),
                "applicability_rules": strategy_data.get("applicability_rules"),
                "ai_analysis_profile_id": strategy_data.get("ai_analysis_profile_id"),
                "risk_parameters_override": strategy_data.get("risk_parameters_override"),
                "version": strategy_data.get("version", 1),
                "parent_config_id": strategy_data.get("parent_config_id"),
                "performance_metrics": strategy_data.get("performance_metrics"),
                "market_condition_filters": strategy_data.get("market_condition_filters"),
                "activation_schedule": strategy_data.get("activation_schedule"),
                "depends_on_strategies": strategy_data.get("depends_on_strategies"),
                "sharing_metadata": strategy_data.get("sharing_metadata"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            strategy_config = TradingStrategyConfig(**full_strategy_data)

            if strategy_config.ai_analysis_profile_id:
                if not await self._validate_ai_profile(user_id, strategy_config.ai_analysis_profile_id):
                    raise HTTPException(status_code=400, detail=f"AI analysis profile '{strategy_config.ai_analysis_profile_id}' does not exist")

            # Pasar el objeto TradingStrategyConfig directamente al servicio de persistencia
            await self.persistence_service.upsert_strategy_config(strategy_config)
            
            logger.info(f"Created strategy configuration {strategy_id} for user {user_id}")
            return strategy_config
        except HTTPException as e:
            # Re-raise HTTPExceptions that were intentionally raised
            raise e
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid strategy configuration: {e}")
        except Exception as e:
            logger.error(f"Error creating strategy configuration: {e}")
            raise HTTPException(status_code=500, detail="Failed to create strategy configuration")

    async def get_strategy_config(self, strategy_id: str, user_id: str) -> Optional[TradingStrategyConfig]:
        try:
            # El servicio de persistencia ya devuelve TradingStrategyConfig
            strategy_uuid = uuid.UUID(strategy_id)
            user_uuid = uuid.UUID(user_id)
            strategy_config = await self.persistence_service.get_strategy_config_by_id(strategy_uuid, user_uuid)
            return strategy_config
        except Exception as e:
            logger.error(f"Error retrieving strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve strategy configuration")

    async def list_strategy_configs(self, user_id: str) -> List[TradingStrategyConfig]:
        try:
            # El servicio de persistencia ya devuelve List[TradingStrategyConfig]
            user_uuid = uuid.UUID(user_id)
            strategies = await self.persistence_service.list_strategy_configs_by_user(user_uuid)
            return strategies
        except Exception as e:
            logger.error(f"Error listing strategies for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to list strategy configurations")

    async def update_strategy_config(self, strategy_id: str, user_id: str, strategy_data: Dict[str, Any]) -> Optional[TradingStrategyConfig]:
        try:
            existing_strategy_config = await self.persistence_service.get_strategy_config_by_id(uuid.UUID(strategy_id), uuid.UUID(user_id))
            if not existing_strategy_config:
                return None

            # Merge existing data with update_data to ensure all required fields are present
            # and to preserve fields not being updated.
            merged_data = existing_strategy_config.model_dump()
            merged_data.update(strategy_data)
            merged_data["id"] = strategy_id
            merged_data["user_id"] = user_id
            merged_data["updated_at"] = datetime.now(timezone.utc)
            
            strategy_config = TradingStrategyConfig(**merged_data)

            if strategy_config.ai_analysis_profile_id:
                if not await self._validate_ai_profile(user_id, strategy_config.ai_analysis_profile_id):
                    raise HTTPException(status_code=400, detail=f"AI analysis profile '{strategy_config.ai_analysis_profile_id}' does not exist")

            # Pasar el objeto TradingStrategyConfig directamente al servicio de persistencia
            await self.persistence_service.upsert_strategy_config(strategy_config)
            
            logger.info(f"Updated strategy configuration {strategy_id} for user {user_id}")
            return strategy_config
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid strategy configuration: {e}")
        except HTTPException as e:
            # Re-raise HTTPExceptions that were intentionally raised
            raise e
        except Exception as e:
            logger.error(f"Error updating strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update strategy configuration")

    async def delete_strategy_config(self, strategy_id: str, user_id: str) -> bool:
        try:
            deleted = await self.persistence_service.delete_strategy_config(uuid.UUID(strategy_id), uuid.UUID(user_id))
            if deleted:
                logger.info(f"Deleted strategy configuration {strategy_id} for user {user_id}")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete strategy configuration")

    async def activate_strategy(self, strategy_id: str, user_id: str, mode: str) -> Optional[TradingStrategyConfig]:
        if mode not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="Mode must be 'paper' or 'real'")
        
        strategy = await self.get_strategy_config(strategy_id, user_id)
        if not strategy:
            return None

        if mode == "paper":
            strategy.is_active_paper_mode = True
        else:
            strategy.is_active_real_mode = True
        
        return await self.update_strategy_config(strategy_id, user_id, strategy.model_dump())

    async def deactivate_strategy(self, strategy_id: str, user_id: str, mode: str) -> Optional[TradingStrategyConfig]:
        if mode not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="Mode must be 'paper' or 'real'")

        strategy = await self.get_strategy_config(strategy_id, user_id)
        if not strategy:
            return None

        if mode == "paper":
            strategy.is_active_paper_mode = False
        else:
            strategy.is_active_real_mode = False

        return await self.update_strategy_config(strategy_id, user_id, strategy.model_dump())

    async def strategy_can_operate_autonomously(self, strategy_id: str, user_id: str) -> bool:
        """Checks if a strategy is configured to operate without AI analysis."""
        strategy = await self.get_strategy_config(strategy_id, user_id)
        if not strategy:
            return False
        # A strategy can operate autonomously if it does not have an AI profile linked.
        return strategy.ai_analysis_profile_id is None

    async def get_active_strategies(self, user_id: str, mode: str) -> List[TradingStrategyConfig]:
        if mode not in ["paper", "real"]:
            raise HTTPException(status_code=400, detail="Mode must be 'paper' or 'real'")
            
        all_strategies = await self.list_strategy_configs(user_id)
        active_strategies = []
        for strategy in all_strategies:
            if mode == "paper" and strategy.is_active_paper_mode:
                active_strategies.append(strategy)
            elif mode == "real" and strategy.is_active_real_mode:
                active_strategies.append(strategy)
        return active_strategies

    # La función _strategy_config_to_db_format ya no es necesaria aquí
    # porque persistence_service.upsert_strategy_config ahora acepta TradingStrategyConfig directamente.

    def _db_format_to_strategy_config(self, db_record: Dict[str, Any]) -> TradingStrategyConfig:
        # Esta función ya no es estrictamente necesaria para la conversión principal
        # porque persistence_service.get_strategy_config_by_id y list_strategy_configs_by_user
        # ya devuelven TradingStrategyConfig.
        # Sin embargo, se mantiene para la lógica de conversión de parámetros si es necesario.
        record_copy = db_record.copy()
        
        # Asegurar que parameters_data sea un diccionario
        parameters_data = record_copy.get("parameters")
        if isinstance(parameters_data, str):
            try:
                parameters_data = json.loads(parameters_data)
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode parameters JSON for strategy {record_copy.get('id')}. Using empty dict.")
                parameters_data = {} # Usar un diccionario vacío si no se puede decodificar
        elif not isinstance(parameters_data, dict):
            # Si no es str ni dict, forzar a dict vacío
            logger.warning(f"Parameters data for strategy {record_copy.get('id')} is not a dict or str. Type: {type(parameters_data)}. Forcing to empty dict.")
            parameters_data = {}
        
        # Convertir base_strategy_type a Enum si es necesario para la validación interna
        base_strategy_type_str = record_copy.get("base_strategy_type")
        if isinstance(base_strategy_type_str, str):
            try:
                record_copy["base_strategy_type"] = BaseStrategyType(base_strategy_type_str)
            except ValueError:
                logger.error(f"Unknown BaseStrategyType value '{base_strategy_type_str}'. Defaulting to UNKNOWN.")
                record_copy["base_strategy_type"] = BaseStrategyType.UNKNOWN
        else:
            logger.error(f"Invalid or missing base_strategy_type in DB record: {base_strategy_type_str}. Defaulting to UNKNOWN.")
            record_copy["base_strategy_type"] = BaseStrategyType.UNKNOWN

        # Asegurar que parameters_data sea un diccionario antes de pasarlo a _convert_parameters_by_type
        # Esto ya se hizo al inicio de la función, pero se reitera para claridad si la lógica cambia.
        if not isinstance(parameters_data, dict):
            parameters_data = {}

        record_copy["parameters"] = self._convert_parameters_by_type(record_copy["base_strategy_type"], parameters_data)

        try:
            return TradingStrategyConfig(**record_copy)
        except ValidationError as e:
            logger.error(f"Failed to validate TradingStrategyConfig from DB record {record_copy.get('id')}: {e}. Record: {record_copy}")
            raise HTTPException(status_code=500, detail="Failed to load strategy configuration due to invalid data format.")
        except Exception as e:
            logger.error(f"Unexpected error creating TradingStrategyConfig from DB record {record_copy.get('id')}: {e}. Record: {record_copy}")
            raise HTTPException(status_code=500, detail="Failed to load strategy configuration due to unexpected error.")


    def _convert_parameters_by_type(self, strategy_type: BaseStrategyType, parameters_data: Dict[str, Any]) -> StrategySpecificParameters:
        param_map = {
            BaseStrategyType.SCALPING: ScalpingParameters,
            BaseStrategyType.DAY_TRADING: DayTradingParameters,
            BaseStrategyType.ARBITRAGE_SIMPLE: ArbitrageSimpleParameters,
            BaseStrategyType.CUSTOM_AI_DRIVEN: CustomAIDrivenParameters,
            BaseStrategyType.MCP_SIGNAL_FOLLOWER: MCPSignalFollowerParameters,
            BaseStrategyType.GRID_TRADING: GridTradingParameters,
            BaseStrategyType.DCA_INVESTING: DCAInvestingParameters,
            BaseStrategyType.UNKNOWN: None, # Usar None o un marcador para indicar que no se instancia
        }
        param_class = param_map.get(strategy_type)

        if strategy_type == BaseStrategyType.UNKNOWN:
            # Para UNKNOWN, el tipo esperado es Dict[str, Any], que ya es parameters_data
            return parameters_data 

        if param_class:
            try:
                return param_class(**parameters_data)
            except ValidationError as e:
                logger.warning(f"Failed to validate parameters for {strategy_type}: {e}. Returning raw data as Dict[str, Any].")
                # Si la validación falla, devolver los datos crudos como Dict[str, Any]
                return parameters_data
        
        logger.warning(f"No specific parameter class found for strategy type {strategy_type}. Returning raw data as Dict[str, Any].")
        return parameters_data

    async def is_strategy_applicable_to_symbol(self, strategy_id: str, user_id: str, symbol: str) -> bool:
        """
        Checks if a strategy is applicable to a given symbol based on its configuration.
        """
        strategy = await self.get_strategy_config(strategy_id, user_id)
        if not strategy:
            return False

        # If allowed_symbols is not empty, the symbol must be in the list.
        if strategy.allowed_symbols and symbol not in strategy.allowed_symbols:
            return False

        # If excluded_symbols is not empty, the symbol must not be in the list.
        if strategy.excluded_symbols and symbol in strategy.excluded_symbols:
            return False

        return True
