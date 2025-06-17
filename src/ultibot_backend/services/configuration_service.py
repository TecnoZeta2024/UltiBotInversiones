"""Configuration Service for managing user configuration settings.

This service provides CRUD operations for user configuration settings
including AI strategy configurations for Gemini integration.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pydantic import ValidationError

from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
    ConfidenceThresholds,
)

logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing user configuration settings."""
    
    def __init__(self, persistence_service: SupabasePersistenceService):
        """Initialize the configuration service with persistence service dependency.
        
        Args:
            persistence_service: The persistence service for database operations.
        """
        self.persistence_service = persistence_service
    
    async def get_user_configuration(self, user_id: str) -> Optional[UserConfiguration]:
        """Get user configuration by user ID.
        
        Args:
            user_id: The user identifier.
            
        Returns:
            The UserConfiguration if found, None otherwise.
            
        Raises:
            HTTPException: If database operation fails.
        """
        try:
            db_record = await self._get_user_config_from_db(user_id)
            if not db_record:
                return None
            
            return self._db_format_to_user_config(db_record)
            
        except Exception as e:
            logger.error(f"Error retrieving user configuration for {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to retrieve user configuration"
            )
    
    async def create_or_update_user_configuration(
        self, 
        user_id: str, 
        config_data: Dict[str, Any]
    ) -> UserConfiguration:
        """Create or update user configuration.
        
        Args:
            user_id: The user identifier.
            config_data: Dictionary containing configuration data.
            
        Returns:
            The created or updated UserConfiguration.
            
        Raises:
            HTTPException: If validation fails or database operation fails.
        """
        try:
            # Prepare configuration data
            config_data_copy = config_data.copy()
            config_data_copy.update({
                "user_id": user_id,
                "updated_at": datetime.now(timezone.utc),
            })
            
            # Check if configuration exists
            existing_config = await self.get_user_configuration(user_id)
            if existing_config:
                # Update existing configuration
                config_data_copy["id"] = existing_config.id
                config_data_copy["created_at"] = existing_config.created_at
            else:
                # Create new configuration
                config_data_copy["id"] = str(uuid.uuid4())
                config_data_copy["created_at"] = datetime.now(timezone.utc)
            
            # Validate configuration
            user_config = UserConfiguration(**config_data_copy)
            
            # Convert to database format and save
            db_data = self._user_config_to_db_format(user_config)
            await self._save_user_config_to_db(db_data)
            
            logger.info(f"Saved user configuration for user {user_id}")
            return user_config
            
        except ValidationError as e:
            logger.error(f"Validation error saving user configuration: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid user configuration: {e}"
            )
        except Exception as e:
            logger.error(f"Error saving user configuration for {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to save user configuration"
            )
    
    async def get_ai_strategy_configuration(
        self, 
        user_id: str, 
        ai_config_id: str
    ) -> Optional[AIStrategyConfiguration]:
        """Get AI strategy configuration by ID.
        
        Args:
            user_id: The user identifier.
            ai_config_id: The AI configuration ID.
            
        Returns:
            The AIStrategyConfiguration if found, None otherwise.
        """
        user_config = await self.get_user_configuration(user_id)
        if not user_config:
            return None
        
        return user_config.get_ai_configuration_by_id(ai_config_id)
    
    async def get_effective_confidence_thresholds(
        self, 
        user_id: str, 
        ai_config_id: Optional[str] = None
    ) -> Optional[ConfidenceThresholds]:
        """Get effective confidence thresholds for a user.
        
        Args:
            user_id: The user identifier.
            ai_config_id: Optional AI configuration ID.
            
        Returns:
            Effective confidence thresholds.
        """
        user_config = await self.get_user_configuration(user_id)
        if not user_config:
            return None
        
        return user_config.get_effective_confidence_thresholds(ai_config_id)
    
    async def validate_ai_profile_exists(
        self, 
        user_id: str, 
        ai_profile_id: str
    ) -> bool:
        """Validate that an AI profile exists for a user.
        
        Args:
            user_id: The user identifier.
            ai_profile_id: The AI profile ID to validate.
            
        Returns:
            True if the AI profile exists, False otherwise.
        """
        ai_config = await self.get_ai_strategy_configuration(user_id, ai_profile_id)
        return ai_config is not None
    
    def _user_config_to_db_format(self, config: UserConfiguration) -> Dict[str, Any]:
        """Convert UserConfiguration to database format.
        
        Args:
            config: The UserConfiguration object.
            
        Returns:
            Dictionary with database column names and values.
        """
        def to_json(field_value):
            if field_value is None:
                return None
            if isinstance(field_value, list):
                return json.dumps([
                    item.dict() if hasattr(item, 'dict') else item 
                    for item in field_value
                ])
            elif isinstance(field_value, dict):
                return json.dumps({
                    k: v.dict() if hasattr(v, 'dict') else v 
                    for k, v in field_value.items()
                })
            elif hasattr(field_value, 'dict'):
                return json.dumps(field_value.dict())
            else:
                return json.dumps(field_value)
        
        return {
            "id": config.id,
            "user_id": config.user_id,
            "telegram_chat_id": config.telegram_chat_id,
            "notification_preferences": to_json(config.notification_preferences),
            "enable_telegram_notifications": config.enable_telegram_notifications,
            "default_paper_trading_capital": config.default_paper_trading_capital,
            "paper_trading_active": config.paper_trading_active,
            "watchlists": to_json(config.watchlists),
            "favorite_pairs": json.dumps(config.favorite_pairs) if config.favorite_pairs else None,
            "risk_profile": config.risk_profile,
            "risk_profile_settings": to_json(config.risk_profile_settings),
            "real_trading_settings": to_json(config.real_trading_settings),
            "ai_strategy_configurations": to_json(config.ai_strategy_configurations),
            "ai_analysis_confidence_thresholds": to_json(config.ai_analysis_confidence_thresholds),
            "mcp_server_preferences": to_json(config.mcp_server_preferences),
            "selected_theme": config.selected_theme,
            "dashboard_layout_profiles": to_json(config.dashboard_layout_profiles),
            "active_dashboard_layout_profile_id": config.active_dashboard_layout_profile_id,
            "dashboard_layout_config": to_json(config.dashboard_layout_config),
            "cloud_sync_preferences": to_json(config.cloud_sync_preferences),
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }
    
    def _db_format_to_user_config(self, db_record: Dict[str, Any]) -> UserConfiguration:
        """Convert database record to UserConfiguration.
        
        Args:
            db_record: Dictionary from database query.
            
        Returns:
            UserConfiguration object.
        """
        def from_json(json_value):
            if json_value is None:
                return None
            if isinstance(json_value, str):
                return json.loads(json_value)
            return json_value
        
        return UserConfiguration(
            id=db_record["id"],
            user_id=db_record["user_id"],
            telegram_chat_id=db_record.get("telegram_chat_id"),
            notification_preferences=from_json(db_record.get("notification_preferences")),
            enable_telegram_notifications=db_record.get("enable_telegram_notifications"),
            default_paper_trading_capital=db_record.get("default_paper_trading_capital"),
            paper_trading_active=db_record.get("paper_trading_active"),
            watchlists=from_json(db_record.get("watchlists")),
            favorite_pairs=from_json(db_record.get("favorite_pairs")),
            risk_profile=db_record.get("risk_profile"),
            risk_profile_settings=from_json(db_record.get("risk_profile_settings")),
            real_trading_settings=from_json(db_record.get("real_trading_settings")),
            ai_strategy_configurations=from_json(db_record.get("ai_strategy_configurations")),
            ai_analysis_confidence_thresholds=from_json(db_record.get("ai_analysis_confidence_thresholds")),
            mcp_server_preferences=from_json(db_record.get("mcp_server_preferences")),
            selected_theme=db_record.get("selected_theme"),
            dashboard_layout_profiles=from_json(db_record.get("dashboard_layout_profiles")),
            active_dashboard_layout_profile_id=db_record.get("active_dashboard_layout_profile_id"),
            dashboard_layout_config=from_json(db_record.get("dashboard_layout_config")),
            cloud_sync_preferences=from_json(db_record.get("cloud_sync_preferences")),
            created_at=db_record.get("created_at"),
            updated_at=db_record.get("updated_at"),
        )
    
    # Database interaction methods
    
    async def _get_user_config_from_db(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user configuration from database.
        
        Args:
            user_id: The user ID.
            
        Returns:
            Dictionary with user configuration data or None if not found.
        """
        await self.persistence_service._ensure_connection()
        
        query = """
        SELECT * FROM user_configurations 
        WHERE user_id = %s;
        """
        
        try:
            from psycopg.rows import dict_row
            from psycopg.sql import SQL
            
            async with self.persistence_service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query), (user_id,))
                record = await cur.fetchone()
                return dict(record) if record else None
        except Exception as e:
            logger.error(f"Database error getting user configuration {user_id}: {e}")
            raise
    
    async def _save_user_config_to_db(self, config_data: Dict[str, Any]) -> None:
        """Save user configuration to database.
        
        Args:
            config_data: Dictionary with configuration data in database format.
        """
        await self.persistence_service._ensure_connection()
        
        query = """
        INSERT INTO user_configurations (
            id, user_id, telegram_chat_id, notification_preferences, enable_telegram_notifications,
            default_paper_trading_capital, paper_trading_active, watchlists, favorite_pairs,
            risk_profile, risk_profile_settings, real_trading_settings, ai_strategy_configurations,
            ai_analysis_confidence_thresholds, mcp_server_preferences, selected_theme,
            dashboard_layout_profiles, active_dashboard_layout_profile_id, dashboard_layout_config,
            cloud_sync_preferences, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (user_id) DO UPDATE SET
            telegram_chat_id = EXCLUDED.telegram_chat_id,
            notification_preferences = EXCLUDED.notification_preferences,
            enable_telegram_notifications = EXCLUDED.enable_telegram_notifications,
            default_paper_trading_capital = EXCLUDED.default_paper_trading_capital,
            paper_trading_active = EXCLUDED.paper_trading_active,
            watchlists = EXCLUDED.watchlists,
            favorite_pairs = EXCLUDED.favorite_pairs,
            risk_profile = EXCLUDED.risk_profile,
            risk_profile_settings = EXCLUDED.risk_profile_settings,
            real_trading_settings = EXCLUDED.real_trading_settings,
            ai_strategy_configurations = EXCLUDED.ai_strategy_configurations,
            ai_analysis_confidence_thresholds = EXCLUDED.ai_analysis_confidence_thresholds,
            mcp_server_preferences = EXCLUDED.mcp_server_preferences,
            selected_theme = EXCLUDED.selected_theme,
            dashboard_layout_profiles = EXCLUDED.dashboard_layout_profiles,
            active_dashboard_layout_profile_id = EXCLUDED.active_dashboard_layout_profile_id,
            dashboard_layout_config = EXCLUDED.dashboard_layout_config,
            cloud_sync_preferences = EXCLUDED.cloud_sync_preferences,
            updated_at = EXCLUDED.updated_at;
        """
        
        try:
            from psycopg.rows import dict_row
            from psycopg.sql import SQL
            
            async with self.persistence_service.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    SQL(query),
                    (
                        config_data["id"],
                        config_data["user_id"],
                        config_data["telegram_chat_id"],
                        config_data["notification_preferences"],
                        config_data["enable_telegram_notifications"],
                        config_data["default_paper_trading_capital"],
                        config_data["paper_trading_active"],
                        config_data["watchlists"],
                        config_data["favorite_pairs"],
                        config_data["risk_profile"],
                        config_data["risk_profile_settings"],
                        config_data["real_trading_settings"],
                        config_data["ai_strategy_configurations"],
                        config_data["ai_analysis_confidence_thresholds"],
                        config_data["mcp_server_preferences"],
                        config_data["selected_theme"],
                        config_data["dashboard_layout_profiles"],
                        config_data["active_dashboard_layout_profile_id"],
                        config_data["dashboard_layout_config"],
                        config_data["cloud_sync_preferences"],
                        config_data["created_at"],
                        config_data["updated_at"],
                    )
                )
                await self.persistence_service.connection.commit()
        except Exception as e:
            await self.persistence_service.connection.rollback()
            logger.error(f"Database error saving user configuration: {e}")
            raise

