"""Strategy Service for managing trading strategy configurations.

This service provides CRUD operations for trading strategy configurations
and handles activation/deactivation of strategies in paper and real trading modes.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from fastapi import HTTPException
from pydantic import ValidationError

if TYPE_CHECKING:
    from .configuration_service import ConfigurationService

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
    AIStrategyConfiguration,
    ConfidenceThresholds,
)

logger = logging.getLogger(__name__)


class StrategyService:
    """Service for managing trading strategy configurations."""
    
    def __init__(
        self, 
        persistence_service: SupabasePersistenceService,
        configuration_service: Optional['ConfigurationService'] = None
    ):
        """Initialize the strategy service with dependencies.
        
        Args:
            persistence_service: The persistence service for database operations.
            configuration_service: The configuration service for AI profile validation.
        """
        self.persistence_service = persistence_service
        self.configuration_service = configuration_service
    
    async def create_strategy_config(
        self, 
        user_id: str, 
        strategy_data: Dict[str, Any]
    ) -> TradingStrategyConfig:
        """Create a new trading strategy configuration.
        
        Args:
            user_id: The user identifier.
            strategy_data: Dictionary containing strategy configuration data.
            
        Returns:
            The created TradingStrategyConfig.
            
        Raises:
            HTTPException: If validation fails or database operation fails.
        """
        try:
            # Generate UUID for new strategy
            strategy_id = str(uuid.uuid4())
            
            # Prepare strategy data with required fields
            strategy_data_copy = strategy_data.copy()
            strategy_data_copy.update({
                "id": strategy_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            })
            
            # Validate and create TradingStrategyConfig instance
            strategy_config = TradingStrategyConfig(**strategy_data_copy)
            
            # Validate AI profile if specified
            if strategy_config.ai_analysis_profile_id and self.configuration_service:
                ai_profile_exists = await self.configuration_service.validate_ai_profile_exists(
                    user_id, 
                    strategy_config.ai_analysis_profile_id
                )
                if not ai_profile_exists:
                    raise HTTPException(
                        status_code=400,
                        detail=f"AI analysis profile '{strategy_config.ai_analysis_profile_id}' does not exist"
                    )
            
            # Convert to database format
            db_data = self._strategy_config_to_db_format(strategy_config)
            
            # Save to database
            await self._save_strategy_to_db(db_data)
            
            logger.info(f"Created strategy configuration {strategy_id} for user {user_id}")
            return strategy_config
            
        except ValidationError as e:
            logger.error(f"Validation error creating strategy: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid strategy configuration: {e}"
            )
        except Exception as e:
            logger.error(f"Error creating strategy configuration: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to create strategy configuration"
            )
    
    async def get_strategy_config(
        self, 
        strategy_id: str, 
        user_id: str
    ) -> Optional[TradingStrategyConfig]:
        """Retrieve a trading strategy configuration by ID.
        
        Args:
            strategy_id: The strategy configuration ID.
            user_id: The user identifier for authorization.
            
        Returns:
            The TradingStrategyConfig if found, None otherwise.
            
        Raises:
            HTTPException: If database operation fails.
        """
        try:
            db_record = await self._get_strategy_from_db(strategy_id, user_id)
            if not db_record:
                return None
            
            return self._db_format_to_strategy_config(db_record)
            
        except Exception as e:
            logger.error(f"Error retrieving strategy {strategy_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to retrieve strategy configuration"
            )
    
    async def list_strategy_configs(
        self, 
        user_id: str,
        active_only: bool = False,
        strategy_type: Optional[BaseStrategyType] = None
    ) -> List[TradingStrategyConfig]:
        """List all trading strategy configurations for a user.
        
        Args:
            user_id: The user identifier.
            active_only: Whether to return only active strategies.
            strategy_type: Optional filter by strategy type.
            
        Returns:
            List of TradingStrategyConfig objects.
            
        Raises:
            HTTPException: If database operation fails.
        """
        try:
            db_records = await self._list_strategies_from_db(
                user_id, 
                active_only, 
                strategy_type
            )
            
            strategies = []
            for record in db_records:
                try:
                    strategy = self._db_format_to_strategy_config(record)
                    strategies.append(strategy)
                except Exception as e:
                    logger.warning(f"Skipping invalid strategy record {record.get('id')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(strategies)} strategies for user {user_id}")
            return strategies
            
        except Exception as e:
            logger.error(f"Error listing strategies for user {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to list strategy configurations"
            )
    
    async def update_strategy_config(
        self, 
        strategy_id: str, 
        user_id: str, 
        strategy_data: Dict[str, Any]
    ) -> Optional[TradingStrategyConfig]:
        """Update an existing trading strategy configuration.
        
        Args:
            strategy_id: The strategy configuration ID.
            user_id: The user identifier for authorization.
            strategy_data: Dictionary containing updated strategy data.
            
        Returns:
            The updated TradingStrategyConfig if successful, None if not found.
            
        Raises:
            HTTPException: If validation fails or database operation fails.
        """
        try:
            # Check if strategy exists and belongs to user
            existing_record = await self._get_strategy_from_db(strategy_id, user_id)
            if not existing_record:
                return None
            
            # Prepare updated strategy data
            strategy_data_copy = strategy_data.copy()
            strategy_data_copy.update({
                "id": strategy_id,
                "user_id": user_id,
                "updated_at": datetime.now(timezone.utc),
            })
            
            # Keep original created_at if not provided
            if "created_at" not in strategy_data_copy:
                strategy_data_copy["created_at"] = existing_record.get("created_at")
            
            # Validate updated configuration
            strategy_config = TradingStrategyConfig(**strategy_data_copy)
            
            # Validate AI profile if specified
            if strategy_config.ai_analysis_profile_id and self.configuration_service:
                ai_profile_exists = await self.configuration_service.validate_ai_profile_exists(
                    user_id, 
                    strategy_config.ai_analysis_profile_id
                )
                if not ai_profile_exists:
                    raise HTTPException(
                        status_code=400,
                        detail=f"AI analysis profile '{strategy_config.ai_analysis_profile_id}' does not exist"
                    )
            
            # Convert to database format and save
            db_data = self._strategy_config_to_db_format(strategy_config)
            await self._save_strategy_to_db(db_data)
            
            logger.info(f"Updated strategy configuration {strategy_id} for user {user_id}")
            return strategy_config
            
        except ValidationError as e:
            logger.error(f"Validation error updating strategy {strategy_id}: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid strategy configuration: {e}"
            )
        except Exception as e:
            logger.error(f"Error updating strategy {strategy_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to update strategy configuration"
            )
    
    async def delete_strategy_config(
        self, 
        strategy_id: str, 
        user_id: str
    ) -> bool:
        """Delete a trading strategy configuration.
        
        Args:
            strategy_id: The strategy configuration ID.
            user_id: The user identifier for authorization.
            
        Returns:
            True if deleted successfully, False if not found.
            
        Raises:
            HTTPException: If database operation fails.
        """
        try:
            # Check if strategy exists and belongs to user
            existing_record = await self._get_strategy_from_db(strategy_id, user_id)
            if not existing_record:
                return False
            
            # Delete from database
            deleted = await self._delete_strategy_from_db(strategy_id, user_id)
            
            if deleted:
                logger.info(f"Deleted strategy configuration {strategy_id} for user {user_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting strategy {strategy_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to delete strategy configuration"
            )
    
    async def activate_strategy(
        self, 
        strategy_id: str, 
        user_id: str, 
        mode: str
    ) -> Optional[TradingStrategyConfig]:
        """Activate a strategy in the specified mode (paper or real).
        
        Args:
            strategy_id: The strategy configuration ID.
            user_id: The user identifier for authorization.
            mode: The trading mode ("paper" or "real").
            
        Returns:
            The updated TradingStrategyConfig if successful, None if not found.
            
        Raises:
            HTTPException: If mode is invalid or database operation fails.
        """
        if mode not in ["paper", "real"]:
            raise HTTPException(
                status_code=400, 
                detail="Mode must be 'paper' or 'real'"
            )
        
        try:
            # Get current strategy configuration
            existing_record = await self._get_strategy_from_db(strategy_id, user_id)
            if not existing_record:
                return None
            
            # Update activation status
            if mode == "paper":
                existing_record["is_active_paper_mode"] = True
            else:  # mode == "real"
                existing_record["is_active_real_mode"] = True
            
            existing_record["updated_at"] = datetime.now(timezone.utc)
            
            # Save updated configuration
            await self._save_strategy_to_db(existing_record)
            
            # Return updated configuration
            updated_strategy = self._db_format_to_strategy_config(existing_record)
            
            logger.info(f"Activated strategy {strategy_id} in {mode} mode for user {user_id}")
            return updated_strategy
            
        except Exception as e:
            logger.error(f"Error activating strategy {strategy_id} in {mode} mode: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to activate strategy in {mode} mode"
            )
    
    async def deactivate_strategy(
        self, 
        strategy_id: str, 
        user_id: str, 
        mode: str
    ) -> Optional[TradingStrategyConfig]:
        """Deactivate a strategy in the specified mode (paper or real).
        
        Args:
            strategy_id: The strategy configuration ID.
            user_id: The user identifier for authorization.
            mode: The trading mode ("paper" or "real").
            
        Returns:
            The updated TradingStrategyConfig if successful, None if not found.
            
        Raises:
            HTTPException: If mode is invalid or database operation fails.
        """
        if mode not in ["paper", "real"]:
            raise HTTPException(
                status_code=400, 
                detail="Mode must be 'paper' or 'real'"
            )
        
        try:
            # Get current strategy configuration
            existing_record = await self._get_strategy_from_db(strategy_id, user_id)
            if not existing_record:
                return None
            
            # Update activation status
            if mode == "paper":
                existing_record["is_active_paper_mode"] = False
            else:  # mode == "real"
                existing_record["is_active_real_mode"] = False
            
            existing_record["updated_at"] = datetime.now(timezone.utc)
            
            # Save updated configuration
            await self._save_strategy_to_db(existing_record)
            
            # Return updated configuration
            updated_strategy = self._db_format_to_strategy_config(existing_record)
            
            logger.info(f"Deactivated strategy {strategy_id} in {mode} mode for user {user_id}")
            return updated_strategy
            
        except Exception as e:
            logger.error(f"Error deactivating strategy {strategy_id} in {mode} mode: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to deactivate strategy in {mode} mode"
            )
    
    async def get_active_strategies(
        self, 
        user_id: str, 
        mode: str
    ) -> List[TradingStrategyConfig]:
        """Get all active strategies for a user in the specified mode.
        
        Args:
            user_id: The user identifier.
            mode: The trading mode ("paper" or "real").
            
        Returns:
            List of active TradingStrategyConfig objects.
            
        Raises:
            HTTPException: If mode is invalid or database operation fails.
        """
        if mode not in ["paper", "real"]:
            raise HTTPException(
                status_code=400, 
                detail="Mode must be 'paper' or 'real'"
            )
        
        try:
            db_records = await self._get_active_strategies_from_db(user_id, mode)
            
            strategies = []
            for record in db_records:
                try:
                    strategy = self._db_format_to_strategy_config(record)
                    strategies.append(strategy)
                except Exception as e:
                    logger.warning(f"Skipping invalid active strategy record {record.get('id')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(strategies)} active {mode} strategies for user {user_id}")
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting active {mode} strategies for user {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to get active {mode} strategies"
            )
    
    def _strategy_config_to_db_format(self, strategy: TradingStrategyConfig) -> Dict[str, Any]:
        """Convert TradingStrategyConfig to database format.
        
        Args:
            strategy: The TradingStrategyConfig object.
            
        Returns:
            Dictionary with database column names and values.
        """
        # Convert parameters to JSON
        parameters_json = strategy.parameters
        if isinstance(parameters_json, dict):
            parameters_json = json.dumps(parameters_json)
        elif hasattr(parameters_json, 'dict'):
            parameters_json = json.dumps(parameters_json.dict())
        else:
            parameters_json = json.dumps(parameters_json)
        
        # Convert optional fields to JSON
        def to_json(field_value):
            if field_value is None:
                return None
            if isinstance(field_value, dict):
                return json.dumps(field_value)
            elif hasattr(field_value, 'dict'):
                return json.dumps(field_value.dict())
            else:
                return json.dumps(field_value)
        
        return {
            "id": strategy.id,
            "user_id": strategy.user_id,
            "config_name": strategy.config_name,
            "base_strategy_type": strategy.base_strategy_type.value,
            "description": strategy.description,
            "is_active_paper_mode": strategy.is_active_paper_mode,
            "is_active_real_mode": strategy.is_active_real_mode,
            "parameters": parameters_json,
            "applicability_rules": to_json(strategy.applicability_rules),
            "ai_analysis_profile_id": strategy.ai_analysis_profile_id,
            "risk_parameters_override": to_json(strategy.risk_parameters_override),
            "version": strategy.version,
            "parent_config_id": strategy.parent_config_id,
            "performance_metrics": to_json(strategy.performance_metrics),
            "market_condition_filters": to_json(strategy.market_condition_filters),
            "activation_schedule": to_json(strategy.activation_schedule),
            "depends_on_strategies": to_json(strategy.depends_on_strategies),
            "sharing_metadata": to_json(strategy.sharing_metadata),
            "created_at": strategy.created_at,
            "updated_at": strategy.updated_at,
        }
    
    def _db_format_to_strategy_config(self, db_record: Dict[str, Any]) -> TradingStrategyConfig:
        """Convert database record to TradingStrategyConfig.
        
        Args:
            db_record: Dictionary from database query.
            
        Returns:
            TradingStrategyConfig object.
        """
        # Convert JSON fields back to objects
        def from_json(json_value):
            if json_value is None:
                return None
            if isinstance(json_value, str):
                return json.loads(json_value)
            return json_value
        
        # Handle parameters based on strategy type
        parameters_data = from_json(db_record.get("parameters"))
        strategy_type = BaseStrategyType(db_record["base_strategy_type"])
        
        # Convert parameters to appropriate type
        parameters = self._convert_parameters_by_type(strategy_type, parameters_data)
        
        return TradingStrategyConfig(
            id=db_record["id"],
            user_id=db_record["user_id"],
            config_name=db_record["config_name"],
            base_strategy_type=strategy_type,
            description=db_record.get("description"),
            is_active_paper_mode=db_record["is_active_paper_mode"],
            is_active_real_mode=db_record["is_active_real_mode"],
            parameters=parameters,
            applicability_rules=from_json(db_record.get("applicability_rules")),
            ai_analysis_profile_id=db_record.get("ai_analysis_profile_id"),
            risk_parameters_override=from_json(db_record.get("risk_parameters_override")),
            version=db_record.get("version", 1),
            parent_config_id=db_record.get("parent_config_id"),
            performance_metrics=from_json(db_record.get("performance_metrics")),
            market_condition_filters=from_json(db_record.get("market_condition_filters")),
            activation_schedule=from_json(db_record.get("activation_schedule")),
            depends_on_strategies=from_json(db_record.get("depends_on_strategies")),
            sharing_metadata=from_json(db_record.get("sharing_metadata")),
            created_at=db_record.get("created_at"),
            updated_at=db_record.get("updated_at"),
        )
    
    def _convert_parameters_by_type(
        self, 
        strategy_type: BaseStrategyType, 
        parameters_data: Dict[str, Any]
    ) -> StrategySpecificParameters:
        """Convert parameters data to the appropriate type based on strategy type.
        
        Args:
            strategy_type: The strategy type.
            parameters_data: The parameters data as dictionary.
            
        Returns:
            Typed parameters object.
        """
        if not parameters_data:
            return {}
        
        try:
            if strategy_type == BaseStrategyType.SCALPING:
                return ScalpingParameters(**parameters_data)
            elif strategy_type == BaseStrategyType.DAY_TRADING:
                return DayTradingParameters(**parameters_data)
            elif strategy_type == BaseStrategyType.ARBITRAGE_SIMPLE:
                return ArbitrageSimpleParameters(**parameters_data)
            elif strategy_type == BaseStrategyType.CUSTOM_AI_DRIVEN:
                return CustomAIDrivenParameters(**parameters_data)
            elif strategy_type == BaseStrategyType.MCP_SIGNAL_FOLLOWER:
                return MCPSignalFollowerParameters(**parameters_data)
            elif strategy_type == BaseStrategyType.GRID_TRADING:
                return GridTradingParameters(**parameters_data)
            elif strategy_type == BaseStrategyType.DCA_INVESTING:
                return DCAInvestingParameters(**parameters_data)
            else:
                # Return as dict for unknown types
                return parameters_data
        except ValidationError as e:
            logger.warning(f"Failed to validate parameters for {strategy_type}: {e}")
            return parameters_data
    
    # Database interaction methods
    
    async def _save_strategy_to_db(self, strategy_data: Dict[str, Any]) -> None:
        """Save strategy configuration to database.
        
        Args:
            strategy_data: Dictionary with strategy data in database format.
        """
        await self.persistence_service._ensure_connection()
        
        query = """
        INSERT INTO trading_strategy_configs (
            id, user_id, config_name, base_strategy_type, description,
            is_active_paper_mode, is_active_real_mode, parameters,
            applicability_rules, ai_analysis_profile_id, risk_parameters_override,
            version, parent_config_id, performance_metrics, market_condition_filters,
            activation_schedule, depends_on_strategies, sharing_metadata,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (id) DO UPDATE SET
            config_name = EXCLUDED.config_name,
            base_strategy_type = EXCLUDED.base_strategy_type,
            description = EXCLUDED.description,
            is_active_paper_mode = EXCLUDED.is_active_paper_mode,
            is_active_real_mode = EXCLUDED.is_active_real_mode,
            parameters = EXCLUDED.parameters,
            applicability_rules = EXCLUDED.applicability_rules,
            ai_analysis_profile_id = EXCLUDED.ai_analysis_profile_id,
            risk_parameters_override = EXCLUDED.risk_parameters_override,
            version = EXCLUDED.version,
            parent_config_id = EXCLUDED.parent_config_id,
            performance_metrics = EXCLUDED.performance_metrics,
            market_condition_filters = EXCLUDED.market_condition_filters,
            activation_schedule = EXCLUDED.activation_schedule,
            depends_on_strategies = EXCLUDED.depends_on_strategies,
            sharing_metadata = EXCLUDED.sharing_metadata,
            updated_at = EXCLUDED.updated_at;
        """
        
        try:
            from psycopg.rows import dict_row
            from psycopg.sql import SQL
            
            async with self.persistence_service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    SQL(query),
                    (
                        strategy_data["id"],
                        strategy_data["user_id"],
                        strategy_data["config_name"],
                        strategy_data["base_strategy_type"],
                        strategy_data["description"],
                        strategy_data["is_active_paper_mode"],
                        strategy_data["is_active_real_mode"],
                        strategy_data["parameters"],
                        strategy_data["applicability_rules"],
                        strategy_data["ai_analysis_profile_id"],
                        strategy_data["risk_parameters_override"],
                        strategy_data["version"],
                        strategy_data["parent_config_id"],
                        strategy_data["performance_metrics"],
                        strategy_data["market_condition_filters"],
                        strategy_data["activation_schedule"],
                        strategy_data["depends_on_strategies"],
                        strategy_data["sharing_metadata"],
                        strategy_data["created_at"],
                        strategy_data["updated_at"],
                    )
                )
                await self.persistence_service.connection.commit()
        except Exception as e:
            await self.persistence_service.connection.rollback()
            logger.error(f"Database error saving strategy: {e}")
            raise
    
    async def _get_strategy_from_db(
        self, 
        strategy_id: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get strategy configuration from database.
        
        Args:
            strategy_id: The strategy ID.
            user_id: The user ID for authorization.
            
        Returns:
            Dictionary with strategy data or None if not found.
        """
        await self.persistence_service._ensure_connection()
        
        query = """
        SELECT * FROM trading_strategy_configs 
        WHERE id = %s AND user_id = %s;
        """
        
        try:
            from psycopg.rows import dict_row
            from psycopg.sql import SQL
            
            async with self.persistence_service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query), (strategy_id, user_id))
                record = await cur.fetchone()
                return dict(record) if record else None
        except Exception as e:
            logger.error(f"Database error getting strategy {strategy_id}: {e}")
            raise
    
    async def _list_strategies_from_db(
        self, 
        user_id: str,
        active_only: bool = False,
        strategy_type: Optional[BaseStrategyType] = None
    ) -> List[Dict[str, Any]]:
        """List strategy configurations from database.
        
        Args:
            user_id: The user ID.
            active_only: Whether to return only active strategies.
            strategy_type: Optional filter by strategy type.
            
        Returns:
            List of strategy dictionaries.
        """
        await self.persistence_service._ensure_connection()
        
        # Build query with filters
        conditions = ["user_id = %s"]
        params = [user_id]
        
        if active_only:
            conditions.append("(is_active_paper_mode = true OR is_active_real_mode = true)")
        
        if strategy_type:
            conditions.append("base_strategy_type = %s")
            params.append(strategy_type.value)
        
        query = f"""
        SELECT * FROM trading_strategy_configs 
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC;
        """
        
        try:
            from psycopg.rows import dict_row
            from psycopg.sql import SQL
            
            async with self.persistence_service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query), params)
                records = await cur.fetchall()
                return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Database error listing strategies for user {user_id}: {e}")
            raise
    
    async def _delete_strategy_from_db(
        self, 
        strategy_id: str, 
        user_id: str
    ) -> bool:
        """Delete strategy configuration from database.
        
        Args:
            strategy_id: The strategy ID.
            user_id: The user ID for authorization.
            
        Returns:
            True if deleted, False if not found.
        """
        await self.persistence_service._ensure_connection()
        
        query = """
        DELETE FROM trading_strategy_configs 
        WHERE id = %s AND user_id = %s;
        """
        
        try:
            from psycopg.rows import dict_row
            from psycopg.sql import SQL
            
            async with self.persistence_service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query), (strategy_id, user_id))
                await self.persistence_service.connection.commit()
                return cur.rowcount > 0
        except Exception as e:
            await self.persistence_service.connection.rollback()
            logger.error(f"Database error deleting strategy {strategy_id}: {e}")
            raise
    
    async def _get_active_strategies_from_db(
        self, 
        user_id: str, 
        mode: str
    ) -> List[Dict[str, Any]]:
        """Get active strategies from database for specified mode.
        
        Args:
            user_id: The user ID.
            mode: The trading mode ("paper" or "real").
            
        Returns:
            List of active strategy dictionaries.
        """
        await self.persistence_service._ensure_connection()
        
        # Determine which column to check based on mode
        active_column = "is_active_paper_mode" if mode == "paper" else "is_active_real_mode"
        
        query = f"""
        SELECT * FROM trading_strategy_configs 
        WHERE user_id = %s AND {active_column} = true
        ORDER BY created_at DESC;
        """
        
        try:
            from psycopg.rows import dict_row
            from psycopg.sql import SQL
            
            async with self.persistence_service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query), (user_id,))
                records = await cur.fetchall()
                return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Database error getting active {mode} strategies for user {user_id}: {e}")
            raise
    
    # AI Configuration Integration Methods
    
    async def validate_ai_profile_for_strategy(
        self, 
        strategy: TradingStrategyConfig
    ) -> bool:
        """Validate that a strategy's AI profile exists and is valid.
        
        Args:
            strategy: The trading strategy configuration.
            
        Returns:
            True if AI profile is valid or not required, False if invalid.
        """
        if not strategy.ai_analysis_profile_id:
            # No AI profile specified - this is valid (strategy can run without AI)
            return True
        
        if not self.configuration_service:
            logger.warning("Configuration service not available for AI profile validation")
            return False
        
        try:
            ai_config = await self.configuration_service.get_ai_strategy_configuration(
                strategy.user_id, 
                strategy.ai_analysis_profile_id
            )
            return ai_config is not None
        except Exception as e:
            logger.error(f"Error validating AI profile {strategy.ai_analysis_profile_id}: {e}")
            return False
    
    async def get_ai_configuration_for_strategy(
        self, 
        strategy: TradingStrategyConfig
    ) -> Optional[AIStrategyConfiguration]:
        """Get AI configuration for a strategy.
        
        Args:
            strategy: The trading strategy configuration.
            
        Returns:
            The AIStrategyConfiguration if found and valid, None otherwise.
        """
        if not strategy.ai_analysis_profile_id or not self.configuration_service:
            return None
        
        try:
            return await self.configuration_service.get_ai_strategy_configuration(
                strategy.user_id, 
                strategy.ai_analysis_profile_id
            )
        except Exception as e:
            logger.error(f"Error getting AI configuration for strategy {strategy.id}: {e}")
            return None
    
    async def get_effective_confidence_thresholds_for_strategy(
        self, 
        strategy: TradingStrategyConfig
    ) -> Optional[ConfidenceThresholds]:
        """Get effective confidence thresholds for a strategy.
        
        Args:
            strategy: The trading strategy configuration.
            
        Returns:
            Effective confidence thresholds.
        """
        if not self.configuration_service:
            return None
        
        try:
            return await self.configuration_service.get_effective_confidence_thresholds(
                strategy.user_id, 
                strategy.ai_analysis_profile_id
            )
        except Exception as e:
            logger.error(f"Error getting confidence thresholds for strategy {strategy.id}: {e}")
            return None
    
    async def strategy_requires_ai_analysis(self, strategy: TradingStrategyConfig) -> bool:
        """Check if a strategy requires AI analysis.
        
        Args:
            strategy: The trading strategy configuration.
            
        Returns:
            True if strategy requires AI analysis, False otherwise.
        """
        if not strategy.ai_analysis_profile_id:
            return False
        
        ai_config = await self.get_ai_configuration_for_strategy(strategy)
        return ai_config is not None
    
    async def strategy_can_operate_autonomously(self, strategy: TradingStrategyConfig) -> bool:
        """Check if a strategy can operate without AI analysis.
        
        Args:
            strategy: The trading strategy configuration.
            
        Returns:
            True if strategy can operate autonomously, False if it depends on AI.
        """
        # If no AI profile is specified, strategy operates autonomously
        if not strategy.ai_analysis_profile_id:
            return True
        
        # If AI profile is specified but not found/invalid, 
        # strategy should still be able to operate (degraded mode)
        ai_config = await self.get_ai_configuration_for_strategy(strategy)
        if not ai_config:
            logger.warning(
                f"Strategy {strategy.id} has AI profile {strategy.ai_analysis_profile_id} "
                "but configuration not found. Operating in autonomous mode."
            )
            return True
        
        # If AI config exists, check if it's optional or required
        # For now, AI is always optional - strategies can fall back to autonomous operation
        return True
    
    async def get_strategies_with_valid_ai_config(
        self, 
        user_id: str,
        mode: Optional[str] = None
    ) -> List[TradingStrategyConfig]:
        """Get strategies with valid AI configurations.
        
        Args:
            user_id: The user identifier.
            mode: Optional mode filter ("paper" or "real").
            
        Returns:
            List of strategies with valid AI configurations.
        """
        # Get all strategies
        if mode:
            strategies = await self.get_active_strategies(user_id, mode)
        else:
            strategies = await self.list_strategy_configs(user_id)
        
        # Filter strategies with valid AI configurations
        valid_ai_strategies = []
        for strategy in strategies:
            if strategy.ai_analysis_profile_id:
                is_valid = await self.validate_ai_profile_for_strategy(strategy)
                if is_valid:
                    valid_ai_strategies.append(strategy)
        
        return valid_ai_strategies
