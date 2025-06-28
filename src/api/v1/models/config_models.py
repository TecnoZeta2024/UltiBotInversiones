from __future__ import annotations
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal # Importar Decimal
from pydantic import BaseModel, Field

# Es necesario importar todos los tipos anidados que UserConfiguration utiliza.
# Estos se encuentran principalmente en shared.data_types y user_configuration_models.
# Por simplicidad, asumiré que están disponibles en el scope o se importarán según sea necesario.
# Si UserConfiguration original está en shared.data_types, podemos basarnos en él.

from ultibot_backend.core.domain_models.user_configuration_models import (
    NotificationPreference,
    Watchlist,
    RiskProfileSettings,
    RealTradingSettings,
    ConfidenceThresholds as AIAnalysisConfidenceThresholds,
    AIStrategyConfiguration,
    MCPServerPreference,
    DashboardLayoutProfile,
    CloudSyncPreferences,
    RiskProfile,
    Theme,
)


class UserConfigurationUpdate(BaseModel):
    """
    Modelo para actualizar parcialmente la configuración del usuario.
    Todos los campos son opcionales y usan snake_case.
    """
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID for notifications")
    notification_preferences: Optional[List[NotificationPreference]] = Field(None, description="List of notification preferences")
    enable_telegram_notifications: Optional[bool] = Field(None, description="Master switch for Telegram notifications")
    default_paper_trading_capital: Optional[Decimal] = Field(None, gt=Decimal(0), description="Default capital for paper trading", alias="defaultPaperTradingCapital")
    paper_trading_active: Optional[bool] = Field(None, description="Whether paper trading is active", alias="paperTradingActive")
    
    watchlists: Optional[List[Watchlist]] = Field(None, description="List of trading pair watchlists")
    favorite_pairs: Optional[List[str]] = Field(None, description="List of favorite trading pairs")
    
    risk_profile: Optional[RiskProfile] = Field(None, description="General risk profile")
    risk_profile_settings: Optional[RiskProfileSettings] = Field(None, description="Custom risk profile settings")
    real_trading_settings: Optional[RealTradingSettings] = Field(None, description="Real trading mode settings")
    
    ai_strategy_configurations: Optional[List[AIStrategyConfiguration]] = Field(None, description="List of AI strategy configurations")
    ai_analysis_confidence_thresholds: Optional[AIAnalysisConfidenceThresholds] = Field(None, description="Global AI confidence thresholds")
    
    mcp_server_preferences: Optional[List[MCPServerPreference]] = Field(None, description="MCP server preferences")
    
    selected_theme: Optional[Theme] = Field(None, description="Selected UI theme")
    
    dashboard_layout_profiles: Optional[Dict[str, DashboardLayoutProfile]] = Field(None, description="Dashboard layout profiles")
    active_dashboard_layout_profile_id: Optional[str] = Field(None, description="Active dashboard layout profile ID")
    dashboard_layout_config: Optional[Dict[str, Any]] = Field(None, description="Current dashboard layout configuration")
    
    cloud_sync_preferences: Optional[CloudSyncPreferences] = Field(None, description="Cloud synchronization preferences")

    # Campos como 'id', 'user_id', 'createdAt', 'updatedAt' se excluyen intencionalmente
    # ya que no deberían ser actualizables a través de este modelo PATCH.

    class Config:
        extra = "ignore"  # Ignorar campos extra no definidos en este modelo
        validate_assignment = True # Para que las validaciones se ejecuten al asignar valores
        populate_by_name = True # Permitir tanto alias como nombres de campo
        arbitrary_types_allowed = True # Si se usan tipos complejos no Pydantic
