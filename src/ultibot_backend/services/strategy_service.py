import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import ValidationError

from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.core.domain_models.trading_strategy_models import (
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
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
)
from src.ultibot_backend.services.config_service import ConfigurationService

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
        if not user_config or not user_config.aiStrategyConfigurations:
            return False
        return any(p.id == ai_profile_id for p in user_config.aiStrategyConfigurations)

    async def create_strategy_config(self, user_id: str, strategy_data: Dict[str, Any]) -> TradingStrategyConfig:
        try:
            strategy_id = str(uuid.uuid4())
            strategy_data.update({
                "id": strategy_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })

            strategy_config = TradingStrategyConfig(**strategy_data)

            if strategy_config.ai_analysis_profile_id:
                if not await self._validate_ai_profile(user_id, strategy_config.ai_analysis_profile_id):
                    raise HTTPException(status_code=400, detail=f"AI analysis profile '{strategy_config.ai_analysis_profile_id}' does not exist")

            db_data = self._strategy_config_to_db_format(strategy_config)
            await self.persistence_service.upsert_strategy_config(db_data)
            
            logger.info(f"Created strategy configuration {strategy_id} for user {user_id}")
            return strategy_config
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid strategy configuration: {e}")
        except Exception as e:
            logger.error(f"Error creating strategy configuration: {e}")
            raise HTTPException(status_code=500, detail="Failed to create strategy configuration")

    async def get_strategy_config(self, strategy_id: str, user_id: str) -> Optional[TradingStrategyConfig]:
        try:
            db_record = await self.persistence_service.get_strategy_config_by_id(uuid.UUID(strategy_id), uuid.UUID(user_id))
            if not db_record:
                return None
            return self._db_format_to_strategy_config(db_record)
        except Exception as e:
            logger.error(f"Error retrieving strategy {strategy_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve strategy configuration")

    async def list_strategy_configs(self, user_id: str) -> List[TradingStrategyConfig]:
        try:
            db_records = await self.persistence_service.list_strategy_configs_by_user(uuid.UUID(user_id))
            configs = []
            for record in db_records:
                try:
                    config = self._db_format_to_strategy_config(record)
                    if config:
                        configs.append(config)
                    # If _db_format_to_strategy_config returns None, it means deserialization failed
                    # and it has already logged the error.
                except Exception as e: # Catch any unexpected error during processing a single record
                    strategy_id_for_log = record.get('id', 'UNKNOWN_ID')
                    logger.error(f"Unexpected error processing strategy record {strategy_id_for_log} for user {user_id}: {e}", exc_info=True)
            return configs
        except Exception as e: # Catch errors from persistence_service call or other broad issues
            logger.error(f"Error listing strategies for user {user_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to list strategy configurations")

    async def update_strategy_config(self, strategy_id: str, user_id: str, strategy_data: Dict[str, Any]) -> Optional[TradingStrategyConfig]:
        try:
            existing_record = await self.persistence_service.get_strategy_config_by_id(uuid.UUID(strategy_id), uuid.UUID(user_id))
            if not existing_record:
                return None

            update_data = strategy_data.copy()
            update_data.update({
                "id": strategy_id,
                "user_id": user_id,
                "created_at": existing_record.get("created_at"),
                "updated_at": datetime.now(timezone.utc),
            })
            
            strategy_config = TradingStrategyConfig(**update_data)

            if strategy_config.ai_analysis_profile_id:
                if not await self._validate_ai_profile(user_id, strategy_config.ai_analysis_profile_id):
                    raise HTTPException(status_code=400, detail=f"AI analysis profile '{strategy_config.ai_analysis_profile_id}' does not exist")

            db_data = self._strategy_config_to_db_format(strategy_config)
            await self.persistence_service.upsert_strategy_config(db_data)
            
            logger.info(f"Updated strategy configuration {strategy_id} for user {user_id}")
            return strategy_config
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid strategy configuration: {e}")
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

    def _strategy_config_to_db_format(self, strategy: TradingStrategyConfig) -> Dict[str, Any]:
        db_dict = strategy.model_dump(by_alias=True)
        for key, value in db_dict.items():
            if isinstance(value, (dict, list)):
                db_dict[key] = json.dumps(value)
            elif isinstance(value, BaseStrategyType):
                db_dict[key] = value.value
        return db_dict

    def _db_format_to_strategy_config(self, db_record: Dict[str, Any]) -> Optional[TradingStrategyConfig]:
        record_copy = db_record.copy()
        strategy_id_for_log = record_copy.get('id', 'UNKNOWN_ID') # For logging

        try:
            for key, value in record_copy.items():
                if isinstance(value, str):
                    try:
                        if value.startswith('{') or value.startswith('['):
                            record_copy[key] = json.loads(value)
                    except json.JSONDecodeError:
                        # Log if a field expected to be JSON is not, but might not be critical for all fields
                        logger.warning(f"Strategy {strategy_id_for_log}: Field '{key}' looks like JSON but failed to parse: {value[:100]}")
                        # Depending on the field, you might want to raise an error or handle it
                        pass # Silently allow non-JSON strings for now, Pydantic will catch if type is wrong

            strategy_type_str = record_copy.get("base_strategy_type")
            if not strategy_type_str:
                logger.error(f"Strategy {strategy_id_for_log}: 'base_strategy_type' is missing from DB record.")
                return None

            try:
                strategy_type = BaseStrategyType(strategy_type_str)
            except ValueError:
                logger.error(f"Strategy {strategy_id_for_log}: Invalid 'base_strategy_type' value '{strategy_type_str}' in DB record.")
                return None

            parameters_data_raw = record_copy.get("parameters", "{}") # Default to empty JSON string if missing
            if isinstance(parameters_data_raw, str):
                try:
                    parameters_data = json.loads(parameters_data_raw)
                except json.JSONDecodeError as je:
                    logger.error(f"Strategy {strategy_id_for_log}: Failed to parse 'parameters' JSON string: {je}. Data: {parameters_data_raw[:200]}")
                    return None # Critical parsing failure
            elif isinstance(parameters_data_raw, dict):
                parameters_data = parameters_data_raw # Already a dict
            else:
                logger.error(f"Strategy {strategy_id_for_log}: 'parameters' field is of unexpected type {type(parameters_data_raw)}.")
                return None

            # This call will now re-raise ValidationError if conversion fails
            converted_parameters = self._convert_parameters_by_type(strategy_type, parameters_data, strategy_id_for_log)
            record_copy["parameters"] = converted_parameters

            # Perform final model validation
            return TradingStrategyConfig(**record_copy)

        except ValidationError as ve:
            # This catches validation errors from TradingStrategyConfig(**record_copy)
            # or from _convert_parameters_by_type if re-raised and not caught locally.
            logger.error(f"Strategy {strategy_id_for_log}: Validation error during final model creation: {ve}", exc_info=True)
            return None
        except Exception as e:
            # Catch any other unexpected errors during the conversion of this specific record
            logger.error(f"Strategy {strategy_id_for_log}: Unexpected error during conversion: {e}", exc_info=True)
            return None

    def _convert_parameters_by_type(self, strategy_type: BaseStrategyType, parameters_data: dict, strategy_id_for_log: str) -> StrategySpecificParameters:
        param_class_map = {
            BaseStrategyType.SCALPING: ScalpingParameters,
            BaseStrategyType.DAY_TRADING: DayTradingParameters,
            BaseStrategyType.ARBITRAGE_SIMPLE: ArbitrageSimpleParameters,
            BaseStrategyType.CUSTOM_AI_DRIVEN: CustomAIDrivenParameters,
            BaseStrategyType.MCP_SIGNAL_FOLLOWER: MCPSignalFollowerParameters,
            BaseStrategyType.GRID_TRADING: GridTradingParameters,
            BaseStrategyType.DCA_INVESTING: DCAInvestingParameters,
        }
        param_class = param_class_map.get(strategy_type)

        if not param_class:
            logger.warning(f"Strategy {strategy_id_for_log}: No specific parameter model defined for strategy type '{strategy_type.value}'. Returning raw parameters dictionary.")
            # Depending on strictness, you might want to raise an error here if all strategies MUST have specific param models.
            # For now, returning the dict as per previous behavior if no class, but this should ideally be an error or handled.
            return parameters_data

        try:
            return param_class(**parameters_data)
        except ValidationError as e:
            # Log the detailed error from Pydantic, then re-raise to be caught by the caller.
            # The strategy_id_for_log is included here for direct context.
            logger.error(f"Strategy {strategy_id_for_log}: Parameter validation failed for type '{strategy_type.value}' with data {parameters_data}. Error: {e}")
            raise  # Re-raise the ValidationError
