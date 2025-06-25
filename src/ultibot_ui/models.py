from __future__ import annotations
import json
import logging
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator

from PySide6.QtCore import QThread  # pylint: disable=no-name-in-module

logger = logging.getLogger(__name__)

class BaseMainWindow:
    """
    Clase base para type hinting de MainWindow y evitar importaciones circulares.
    """
    def add_thread(self, thread: QThread):
        raise NotImplementedError

class UserConfiguration(BaseModel):
    """
    Modelo Pydantic para la configuración del usuario en la UI.
    Refleja la estructura de UserConfigurationORM del backend.
    """
    id: str
    user_id: str = Field(..., alias='userId')
    telegram_chat_id: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    enable_telegram_notifications: bool = False
    default_paper_trading_capital: Decimal = Field(Decimal("10000.0"), ge=0)
    paper_trading_active: bool = False
    paper_trading_assets: Optional[List[str]] = None
    watchlists: Optional[Union[List[Dict[str, Any]], Dict]] = None
    favorite_pairs: Optional[List[str]] = None
    risk_profile: Optional[Dict[str, Any]] = None
    risk_profile_settings: Optional[Dict[str, Any]] = None
    real_trading_settings: Optional[Dict[str, Any]] = None
    ai_strategy_configurations: Optional[Dict[str, Any]] = None
    ai_analysis_confidence_thresholds: Optional[Dict[str, Any]] = None
    mcp_server_preferences: Optional[Dict[str, Any]] = None
    selected_theme: Optional[str] = None
    dashboard_layout_profiles: Optional[Dict[str, Any]] = None
    active_dashboard_layout_profile_id: Optional[str] = None
    dashboard_layout_config: Optional[Dict[str, Any]] = None
    cloud_sync_preferences: Optional[Dict[str, Any]] = None

    class Config:
        # Permite la inicialización desde atributos de un objeto (ORM)
        from_attributes = True
        # Permite tipos arbitrarios (como Decimal)
        arbitrary_types_allowed = True

    @field_validator(
        'notification_preferences', 'paper_trading_assets', 'watchlists',
        'favorite_pairs', 'risk_profile', 'risk_profile_settings',
        'real_trading_settings', 'ai_strategy_configurations',
        'ai_analysis_confidence_thresholds', 'mcp_server_preferences',
        'dashboard_layout_profiles', 'dashboard_layout_config',
        'cloud_sync_preferences',
        check_fields=False
    )
    @classmethod
    def _parse_json_fields(cls, v: Optional[str]) -> Optional[Union[Dict, List]]:
        """
        Validador para deserializar campos de texto JSON a objetos Python.
        """
        if v is None or v == "":
            return None
        if isinstance(v, (dict, list)):
            return v
        try:
            # Si v es una lista vacía en formato string '[]', json.loads la convertirá a una lista vacía.
            return json.loads(v)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Could not decode JSON string: {v}. Returning as is.")
            return None # O manejar el error de otra forma

    @model_validator(mode='before')
    @classmethod
    def _convert_numerics(cls, data: Any) -> Any:
        """
        Validador a nivel de modelo para convertir tipos numéricos.
        """
        if isinstance(data, dict):
            # Convertir default_paper_trading_capital a Decimal si es necesario
            capital = data.get('default_paper_trading_capital')
            if capital is not None and not isinstance(capital, Decimal):
                try:
                    data['default_paper_trading_capital'] = Decimal(str(capital))
                except Exception as e:
                    logger.error(f"Could not convert capital '{capital}' to Decimal: {e}")
                    # Asignar un valor por defecto o lanzar un error
                    data['default_paper_trading_capital'] = Decimal("10000.0")
        return data
