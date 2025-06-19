"""Configuration Service for managing user configuration settings.

This service provides CRUD operations for user configuration settings
including AI strategy configurations for Gemini integration.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils import custom_dumps
from ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
    ConfidenceThresholds,
)

logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing user configuration settings."""
    
    def __init__(self, session_factory: Callable[..., AsyncSession]):
        """Initialize the configuration service with a session factory.
        
        Args:
            session_factory: A callable that returns an AsyncSession.
        """
        self.session_factory = session_factory
    
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
            async with self.session_factory() as session:
                query = """
                SELECT * FROM user_configurations 
                WHERE user_id = :user_id;
                """
                result = await session.execute(query, {"user_id": user_id})
                db_record = result.fetchone()
                
                if not db_record:
                    return None
                
                db_record_dict = dict(db_record) if hasattr(db_record, '_asdict') else db_record
                
                return self._db_format_to_user_config(db_record_dict)
            
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
            async with self.session_factory() as session:
                config_data_copy = config_data.copy()
                config_data_copy.update({
                    "user_id": user_id,
                    "updated_at": datetime.now(timezone.utc),
                })
                
                existing_config = await self.get_user_configuration(user_id)
                if existing_config:
                    config_data_copy["id"] = existing_config.id
                    config_data_copy["created_at"] = existing_config.created_at
                else:
                    config_data_copy["id"] = str(uuid.uuid4())
                    config_data_copy["created_at"] = datetime.now(timezone.utc)
                
                user_config = UserConfiguration(**config_data_copy)
                
                db_data = self._user_config_to_db_format(user_config)
                
                query = """
                INSERT INTO user_configurations (
                    id, user_id, telegram_chat_id, notification_preferences, enable_telegram_notifications,
                    default_paper_trading_capital, paper_trading_active, watchlists, favorite_pairs,
                    risk_profile, risk_profile_settings, real_trading_settings, ai_strategy_configurations,
                    ai_analysis_confidence_thresholds, mcp_server_preferences, selected_theme,
                    dashboard_layout_profiles, active_dashboard_layout_profile_id, dashboard_layout_config,
                    cloud_sync_preferences, created_at, updated_at
                ) VALUES (
                    :id, :user_id, :telegram_chat_id, :notification_preferences, :enable_telegram_notifications,
                    :default_paper_trading_capital, :paper_trading_active, :watchlists, :favorite_pairs,
                    :risk_profile, :risk_profile_settings, :real_trading_settings, :ai_strategy_configurations,
                    :ai_analysis_confidence_thresholds, :mcp_server_preferences, :selected_theme,
                    :dashboard_layout_profiles, :active_dashboard_layout_profile_id, :dashboard_layout_config,
                    :cloud_sync_preferences, :created_at, :updated_at
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
                await session.execute(query, db_data)
                await session.commit()
                
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
                return custom_dumps([
                    item.model_dump_json() if hasattr(item, 'model_dump_json') else item 
                    for item in field_value
                ])
            elif isinstance(field_value, dict):
                return custom_dumps({
                    k: v.model_dump_json() if hasattr(v, 'model_dump_json') else v 
                    for k, v in field_value.items()
                })
            elif hasattr(field_value, 'model_dump_json'):
                return custom_dumps(field_value.model_dump_json())
            else:
                return custom_dumps(field_value)
        
        return {
            "id": config.id,
            "user_id": config.user_id,
            "telegram_chat_id": config.telegram_chat_id,
            "notification_preferences": to_json(config.notification_preferences),
            "enable_telegram_notifications": config.enable_telegram_notifications,
            "default_paper_trading_capital": config.default_paper_trading_capital,
            "paper_trading_active": config.paper_trading_active,
            "watchlists": to_json(config.watchlists),
            "favorite_pairs": custom_dumps(config.favorite_pairs) if config.favorite_pairs else None,
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
