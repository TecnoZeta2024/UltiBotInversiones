import logging # Importar logging
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy.sql import text, select, update, delete
from sqlalchemy.dialects import postgresql
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from typing_extensions import LiteralString
from datetime import datetime, timezone
from uuid import UUID, uuid4
from decimal import Decimal
import json
from pydantic import BaseModel

logger = logging.getLogger(__name__) # Configurar logger

from shared.data_types import MarketData
from ..core.ports.persistence_service import IPersistenceService
from ..core.domain_models.trade_models import Trade, PositionStatus, TradeMode # Importar TradeMode
from ..core.domain_models.user_configuration_models import UserConfiguration, NotificationPreference, RiskProfile, Theme, AIStrategyConfiguration, MCPServerPreference, DashboardLayoutProfile, CloudSyncPreferences, ConfidenceThresholds
from ..core.domain_models.opportunity_models import OpportunityStatus, Opportunity, InitialSignal, AIAnalysis, SourceType
from ..core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType
from ..core.domain_models.orm_models import TradeORM, UserConfigurationORM, PortfolioSnapshotORM, OpportunityORM, StrategyConfigORM
import asyncpg

class SupabasePersistenceService(IPersistenceService):
    """
    A SQLAlchemy-based persistence service.
    Can be initialized with an AsyncSession (for tests) or an AsyncEngine/asyncpg.Pool (for app).
    """

    def __init__(self, session: Optional[AsyncSession] = None, engine: Optional[AsyncEngine] = None, pool: Optional[asyncpg.Pool] = None, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self._session = session
        self._engine = engine
        self._pool = pool
        self._async_session_factory = session_factory

        if not (session or engine or pool or session_factory):
            raise ValueError("SupabasePersistenceService must be initialized with either a session, an engine, a pool, or a session_factory.")

        if self._engine and not self._async_session_factory:
            self._async_session_factory = async_sessionmaker(self._engine, expire_on_commit=False)
        elif self._session:
            self._async_session_factory = None

    def _pydantic_to_json_string(self, obj: Any) -> Optional[str]:
        if obj is None:
            return None
        if isinstance(obj, BaseModel):
            return obj.model_dump_json()
        if isinstance(obj, list) and all(isinstance(item, BaseModel) for item in obj):
            return json.dumps([item.model_dump() for item in obj])
        if isinstance(obj, (list, dict)):
            return json.dumps(obj)
        return str(obj)

    def _get_session(self):
        """Get a session context manager."""
        if self._async_session_factory:
            return self._async_session_factory()
        
        if self._session:
            class MockSessionManager:
                def __init__(self, session: AsyncSession):
                    self._session = session

                async def __aenter__(self) -> AsyncSession:
                    return self._session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return MockSessionManager(self._session)

        raise RuntimeError("No async_session_factory or session provided.")

    async def initialize(self):
        pass

    async def close(self):
        if self._session:
            await self._session.close()
        if self._engine:
            await self._engine.dispose()
        if self._pool:
            await self._pool.close()

    async def test_connection(self) -> bool:
        """
        Tests the database connection by executing a simple query.
        Returns True if the connection is successful, False otherwise.
        """
        try:
            async with self._get_session() as session:
                await session.execute(text("SELECT 1"))
            logger.info("Database connection test successful.")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    async def fetch_one(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        async with self._get_session() as session:
            result = await session.execute(text(query), params)
            record = result.fetchone()
            return dict(record._mapping) if record else None

    async def fetch_all(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with self._get_session() as session:
            result = await session.execute(text(query), params)
            records = result.fetchall()
            return [dict(record._mapping) for record in records]

    async def execute(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> None:
        async with self._get_session() as session:
            await session.execute(text(query), params)
            if self._async_session_factory: # Solo hacer commit si la sesión es gestionada por el servicio
                await session.commit()

    async def upsert(self, table_name: str, data: Dict[str, Any], on_conflict: List[str]) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{key}" for key in data.keys())
        
        conflict_columns = ", ".join(on_conflict)
        update_placeholders = ", ".join(f"{col} = EXCLUDED.{col}" for col in data.keys() if col not in on_conflict)

        query = f"""
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_columns}) DO UPDATE
            SET {update_placeholders};
        """
        async with self._get_session() as session:
            await session.execute(text(query), data)
            if self._async_session_factory: # Solo hacer commit si la sesión es gestionada por el servicio
                await session.commit()

    async def upsert_all(self, items: List[BaseModel]) -> None:
        if not items:
            return

        # Asumimos que todos los items son del mismo tipo y para la misma tabla.
        # Esta es una implementación simplificada. Una real podría necesitar más lógica.
        model_type = type(items[0])
        table_name = model_type.__name__.lower() + "s" # Asunción simple
        if model_type == MarketData:
            table_name = "market_data"
            on_conflict = ["symbol", "timestamp"]
        else:
            # Lógica de fallback o error si el tipo no es esperado
            logger.error(f"Tipo de modelo no soportado para upsert_all: {model_type}")
            return

        data_list = [item.model_dump(mode='json') for item in items]

        if not data_list:
            return

        first_item = data_list[0]
        columns = ", ".join(f'"{key}"' for key in first_item.keys())
        
        conflict_columns = ", ".join(f'"{key}"' for key in on_conflict)
        update_placeholders = ", ".join(f'"{col}" = EXCLUDED."{col}"' for col in first_item.keys() if col not in on_conflict)
        
        placeholders = ", ".join(f":{key}" for key in first_item.keys())

        query = f"""
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_columns}) DO UPDATE
            SET {update_placeholders};
        """
        
        async with self._get_session() as session:
            await session.execute(text(query), data_list)
            if self._async_session_factory:
                await session.commit()

    async def get_all(self, table_name: str, condition: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        async with self._get_session() as session:
            result = await session.execute(text(query), params)
            records = result.fetchall()
            return [dict(record._mapping) for record in records]

    async def get_one(self, table_name: str, condition: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {table_name} WHERE {condition} LIMIT 1"
        async with self._get_session() as session:
            result = await session.execute(text(query), params)
            record = result.fetchone()
            return dict(record._mapping) if record else None

    async def delete(self, table_name: str, condition: str, params: Optional[Dict[str, Any]] = None) -> None:
        query = f"DELETE FROM {table_name} WHERE {condition}"
        async with self._get_session() as session:
            await session.execute(text(query), params)
            await session.commit()

    async def get_user_configuration(self, user_id: str) -> Optional[UserConfiguration]:
        async with self._get_session() as session:
            result = await session.execute(
                select(UserConfigurationORM).where(UserConfigurationORM.user_id == user_id)
            )
            user_config_orm = result.scalars().first()
            if user_config_orm:
                notification_preferences_obj = json.loads(cast(str, user_config_orm.notification_preferences)) if user_config_orm.notification_preferences is not None else None
                paper_trading_assets_obj = json.loads(cast(str, user_config_orm.paper_trading_assets)) if user_config_orm.paper_trading_assets is not None else None
                watchlists_obj = json.loads(cast(str, user_config_orm.watchlists)) if user_config_orm.watchlists is not None else None
                favorite_pairs_obj = json.loads(cast(str, user_config_orm.favorite_pairs)) if user_config_orm.favorite_pairs is not None else None
                risk_profile_obj = RiskProfile(user_config_orm.risk_profile) if user_config_orm.risk_profile is not None else None
                risk_profile_settings_obj = json.loads(cast(str, user_config_orm.risk_profile_settings)) if user_config_orm.risk_profile_settings is not None else None
                real_trading_settings_obj = json.loads(cast(str, user_config_orm.real_trading_settings)) if user_config_orm.real_trading_settings is not None else None
                # Deserializar ai_strategy_configurations como lista de AIStrategyConfiguration objects
                ai_strategy_configurations_obj = None
                if user_config_orm.ai_strategy_configurations is not None:
                    ai_strategy_configs_json = json.loads(cast(str, user_config_orm.ai_strategy_configurations))
                    if ai_strategy_configs_json:
                        ai_strategy_configurations_obj = [AIStrategyConfiguration.model_validate(config) for config in ai_strategy_configs_json]
                
                # Deserializar ai_analysis_confidence_thresholds como ConfidenceThresholds object
                ai_analysis_confidence_thresholds_obj = None
                if user_config_orm.ai_analysis_confidence_thresholds is not None:
                    confidence_thresholds_json = json.loads(cast(str, user_config_orm.ai_analysis_confidence_thresholds))
                    if confidence_thresholds_json:
                        ai_analysis_confidence_thresholds_obj = ConfidenceThresholds.model_validate(confidence_thresholds_json)
                mcp_server_preferences_obj = json.loads(cast(str, user_config_orm.mcp_server_preferences)) if user_config_orm.mcp_server_preferences is not None else None
                dashboard_layout_profiles_obj = json.loads(cast(str, user_config_orm.dashboard_layout_profiles)) if user_config_orm.dashboard_layout_profiles is not None else None
                dashboard_layout_config_obj = json.loads(cast(str, user_config_orm.dashboard_layout_config)) if user_config_orm.dashboard_layout_config is not None else None
                cloud_sync_preferences_obj = json.loads(cast(str, user_config_orm.cloud_sync_preferences)) if user_config_orm.cloud_sync_preferences is not None else None

                full_user_config_data = {
                    "id": user_config_orm.id,
                    "user_id": user_config_orm.user_id,
                    "telegram_chat_id": user_config_orm.telegram_chat_id,
                    "notification_preferences": notification_preferences_obj,
                    "enable_telegram_notifications": user_config_orm.enable_telegram_notifications,
                    "default_paper_trading_capital": user_config_orm.default_paper_trading_capital,
                    "paper_trading_active": user_config_orm.paper_trading_active,
                    "paper_trading_assets": paper_trading_assets_obj,
                    "watchlists": watchlists_obj,
                    "favorite_pairs": favorite_pairs_obj,
                    "risk_profile": risk_profile_obj,
                    "risk_profile_settings": risk_profile_settings_obj,
                    "real_trading_settings": real_trading_settings_obj,
                    "ai_strategy_configurations": ai_strategy_configurations_obj,
                    "ai_analysis_confidence_thresholds": ai_analysis_confidence_thresholds_obj,
                    "mcp_server_preferences": mcp_server_preferences_obj,
                    "selected_theme": user_config_orm.selected_theme,
                    "dashboard_layout_profiles": dashboard_layout_profiles_obj,
                    "active_dashboard_layout_profile_id": user_config_orm.active_dashboard_layout_profile_id,
                    "dashboard_layout_config": dashboard_layout_config_obj,
                    "cloud_sync_preferences": cloud_sync_preferences_obj,
                    "created_at": user_config_orm.created_at,
                    "updated_at": user_config_orm.updated_at
                }
                return UserConfiguration.model_validate(full_user_config_data)
            return None

    async def upsert_trade(self, trade: Trade) -> None:
        async with self._get_session() as session:
            trade_orm = TradeORM(
                id=trade.id,
                user_id=trade.user_id,
                data=trade.model_dump_json(),
                position_status=trade.positionStatus,
                mode=trade.mode,
                symbol=trade.symbol,
                side=trade.side.value, # Asegurar que el valor del enum se pase como string
                created_at=trade.created_at,
                updated_at=trade.updated_at,
                closed_at=trade.closed_at
            )
            session.add(trade_orm)
            if self._async_session_factory: # Solo hacer commit si la sesión es gestionada por el servicio
                await session.commit()
                await session.refresh(trade_orm) # Refresh solo si se hizo commit
            else:
                # Si no hay commit, la instancia ya está en la sesión y no necesita refresh inmediato
                pass 

    async def execute_raw_sql(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with self._get_session() as session:
            result = await session.execute(text(query), params)
            records = result.fetchall()
            return [dict(record._mapping) for record in records]

    async def upsert_user_configuration(self, user_config: UserConfiguration) -> None:
        async with self._get_session() as session:
            result = await session.execute(
                select(UserConfigurationORM).where(UserConfigurationORM.user_id == user_config.user_id)
            )
            existing_config = result.scalars().first()

            if existing_config:
                # Update existing configuration
                existing_config.telegram_chat_id = user_config.telegram_chat_id
                existing_config.notification_preferences = self._pydantic_to_json_string(user_config.notification_preferences)
                existing_config.enable_telegram_notifications = user_config.enable_telegram_notifications if user_config.enable_telegram_notifications is not None else False
                existing_config.default_paper_trading_capital = user_config.default_paper_trading_capital if user_config.default_paper_trading_capital is not None else Decimal("10000.0")
                existing_config.paper_trading_active = user_config.paper_trading_active if user_config.paper_trading_active is not None else False
                existing_config.paper_trading_assets = self._pydantic_to_json_string(user_config.paper_trading_assets)
                existing_config.watchlists = self._pydantic_to_json_string(user_config.watchlists)
                existing_config.favorite_pairs = self._pydantic_to_json_string(user_config.favorite_pairs)
                
                # Robust handling of enums
                if user_config.risk_profile:
                    existing_config.risk_profile = user_config.risk_profile.value if isinstance(user_config.risk_profile, RiskProfile) else user_config.risk_profile
                else:
                    existing_config.risk_profile = None

                existing_config.risk_profile_settings = self._pydantic_to_json_string(user_config.risk_profile_settings)
                existing_config.real_trading_settings = self._pydantic_to_json_string(user_config.real_trading_settings)
                existing_config.ai_strategy_configurations = self._pydantic_to_json_string(user_config.ai_strategy_configurations)
                existing_config.ai_analysis_confidence_thresholds = self._pydantic_to_json_string(user_config.ai_analysis_confidence_thresholds)
                existing_config.mcp_server_preferences = self._pydantic_to_json_string(user_config.mcp_server_preferences)

                if user_config.selected_theme:
                    existing_config.selected_theme = user_config.selected_theme.value if isinstance(user_config.selected_theme, Theme) else user_config.selected_theme
                else:
                    existing_config.selected_theme = None

                existing_config.dashboard_layout_profiles = self._pydantic_to_json_string(user_config.dashboard_layout_profiles)
                existing_config.active_dashboard_layout_profile_id = user_config.active_dashboard_layout_profile_id
                existing_config.dashboard_layout_config = self._pydantic_to_json_string(user_config.dashboard_layout_config)
                existing_config.cloud_sync_preferences = self._pydantic_to_json_string(user_config.cloud_sync_preferences)
                existing_config.updated_at = datetime.now(timezone.utc)
            else:
                # Create new configuration
                new_config_orm = UserConfigurationORM(
                    id=user_config.id if user_config.id is not None else uuid4(),
                    user_id=user_config.user_id,
                    telegram_chat_id=user_config.telegram_chat_id,
                    notification_preferences=self._pydantic_to_json_string(user_config.notification_preferences),
                    enable_telegram_notifications=user_config.enable_telegram_notifications,
                    default_paper_trading_capital=user_config.default_paper_trading_capital,
                    paper_trading_active=user_config.paper_trading_active,
                    paper_trading_assets=self._pydantic_to_json_string(user_config.paper_trading_assets),
                    watchlists=self._pydantic_to_json_string(user_config.watchlists),
                    favorite_pairs=self._pydantic_to_json_string(user_config.favorite_pairs),
                    
                    risk_profile=user_config.risk_profile.value if isinstance(user_config.risk_profile, RiskProfile) else user_config.risk_profile,
                    
                    risk_profile_settings=self._pydantic_to_json_string(user_config.risk_profile_settings),
                    real_trading_settings=self._pydantic_to_json_string(user_config.real_trading_settings),
                    ai_strategy_configurations=self._pydantic_to_json_string(user_config.ai_strategy_configurations),
                    ai_analysis_confidence_thresholds=self._pydantic_to_json_string(user_config.ai_analysis_confidence_thresholds),
                    mcp_server_preferences=self._pydantic_to_json_string(user_config.mcp_server_preferences),

                    selected_theme=user_config.selected_theme.value if isinstance(user_config.selected_theme, Theme) else user_config.selected_theme,

                    dashboard_layout_profiles=self._pydantic_to_json_string(user_config.dashboard_layout_profiles),
                    active_dashboard_layout_profile_id=user_config.active_dashboard_layout_profile_id,
                    dashboard_layout_config=self._pydantic_to_json_string(user_config.dashboard_layout_config),
                    cloud_sync_preferences=self._pydantic_to_json_string(user_config.cloud_sync_preferences),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(new_config_orm)
            
            if self._async_session_factory: # Solo hacer commit si la sesión es gestionada por el servicio
                await session.commit()

    async def upsert_strategy_config(self, strategy_config: TradingStrategyConfig) -> None:
        async with self._get_session() as session:
            strategy_orm = StrategyConfigORM(
                id=strategy_config.id,
                user_id=strategy_config.user_id,
                data=strategy_config.model_dump_json(),
                config_name=strategy_config.config_name,
                base_strategy_type=strategy_config.base_strategy_type,
                is_active_paper_mode=strategy_config.is_active_paper_mode,
                is_active_real_mode=strategy_config.is_active_real_mode,
                created_at=strategy_config.created_at,
                updated_at=strategy_config.updated_at
            )
            await session.merge(strategy_orm)
            if self._async_session_factory: # Solo hacer commit si la sesión es gestionada por el servicio
                await session.commit()

    async def get_strategy_config_by_id(self, strategy_id: UUID, user_id: UUID) -> Optional[TradingStrategyConfig]:
        async with self._get_session() as session:
            result = await session.execute(
                select(StrategyConfigORM).where(
                    StrategyConfigORM.id == strategy_id,
                    StrategyConfigORM.user_id == user_id
                )
            )
            strategy_orm = result.scalars().first()
            if strategy_orm:
                strategy_data = json.loads(cast(str, strategy_orm.data))
                # Asegurar que los campos del ORM se usen para la construcción del modelo Pydantic
                # y que los tipos sean correctos (UUID a str, datetime a isoformat, Enum a valor)
                strategy_data.update({
                    "id": str(strategy_orm.id),
                    "user_id": str(strategy_orm.user_id),
                    "config_name": strategy_orm.config_name,
                    "base_strategy_type": BaseStrategyType(strategy_orm.base_strategy_type), # Convertir a Enum
                    "is_active_paper_mode": strategy_orm.is_active_paper_mode,
                    "is_active_real_mode": strategy_orm.is_active_real_mode,
                    "created_at": strategy_orm.created_at,
                    "updated_at": strategy_orm.updated_at,
                })
                return TradingStrategyConfig.model_validate(strategy_data)
            return None

    async def list_strategy_configs_by_user(self, user_id: UUID) -> List[TradingStrategyConfig]:
        async with self._get_session() as session:
            result = await session.execute(
                select(StrategyConfigORM).where(StrategyConfigORM.user_id == user_id)
            )
            strategy_orms = result.scalars().all()
            strategies = []
            for strategy_orm in strategy_orms:
                strategy_data = json.loads(cast(str, strategy_orm.data))
                strategy_data.update({
                    "id": str(strategy_orm.id),
                    "user_id": str(strategy_orm.user_id),
                    "config_name": strategy_orm.config_name,
                    "base_strategy_type": BaseStrategyType(strategy_orm.base_strategy_type), # Convertir a Enum
                    "is_active_paper_mode": strategy_orm.is_active_paper_mode,
                    "is_active_real_mode": strategy_orm.is_active_real_mode,
                    "created_at": strategy_orm.created_at,
                    "updated_at": strategy_orm.updated_at,
                })
                strategies.append(TradingStrategyConfig.model_validate(strategy_data))
            return strategies

    async def delete_strategy_config(self, strategy_id: UUID, user_id: UUID) -> bool:
        async with self._get_session() as session:
            stmt = delete(StrategyConfigORM).where(
                StrategyConfigORM.id == strategy_id,
                StrategyConfigORM.user_id == user_id
            )
            result = await session.execute(stmt)
            if self._async_session_factory: # Solo hacer commit si la sesión es gestionada por el servicio
                await session.commit()
            return result.rowcount > 0

    async def update_opportunity_status(self, opportunity_id: UUID, new_status: OpportunityStatus, status_reason: str) -> None:
        async with self._get_session() as session:
            stmt = (
                update(OpportunityORM)
                .where(OpportunityORM.id == opportunity_id)
                .values(
                    status=new_status.value,
                    status_reason_code=status_reason,
                    status_reason_text=status_reason,
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await session.execute(stmt)
            if self._async_session_factory: # Solo hacer commit si la sesión es gestionada por el servicio
                await session.commit()

    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[Opportunity]:
        async with self._get_session() as session:
            result = await session.execute(
                select(OpportunityORM).where(OpportunityORM.id == opportunity_id)
            )
            opportunity_orm = result.scalars().first()
            if opportunity_orm:
                initial_signal_obj = InitialSignal.model_validate_json(cast(str, opportunity_orm.initial_signal)) if opportunity_orm.initial_signal is not None else None
                ai_analysis_obj = AIAnalysis.model_validate_json(cast(str, opportunity_orm.ai_analysis)) if opportunity_orm.ai_analysis is not None else None
                
                full_opportunity_data = {
                    "id": opportunity_orm.id,
                    "user_id": opportunity_orm.user_id,
                    "symbol": opportunity_orm.symbol,
                    "detected_at": opportunity_orm.detected_at,
                    "source_type": SourceType(opportunity_orm.source_type),
                    "source_name": opportunity_orm.source_name,
                    "source_data": json.loads(cast(str, opportunity_orm.source_data)) if opportunity_orm.source_data is not None else None,
                    "initial_signal": initial_signal_obj,
                    "system_calculated_priority_score": opportunity_orm.system_calculated_priority_score,
                    "last_priority_calculation_at": opportunity_orm.last_priority_calculation_at,
                    "status": OpportunityStatus(opportunity_orm.status),
                    "status_reason_code": opportunity_orm.status_reason_code,
                    "status_reason_text": opportunity_orm.status_reason_text,
                    "ai_analysis": ai_analysis_obj,
                    "investigation_details": json.loads(cast(str, opportunity_orm.investigation_details)) if opportunity_orm.investigation_details is not None else None,
                    "user_feedback": json.loads(cast(str, opportunity_orm.user_feedback)) if opportunity_orm.user_feedback is not None else None,
                    "linked_trade_ids": json.loads(cast(str, opportunity_orm.linked_trade_ids)) if opportunity_orm.linked_trade_ids is not None else None,
                    "expires_at": opportunity_orm.expires_at,
                    "expiration_logic": json.loads(cast(str, opportunity_orm.expiration_logic)) if opportunity_orm.expiration_logic is not None else None,
                    "post_trade_feedback": json.loads(cast(str, opportunity_orm.post_trade_feedback)) if opportunity_orm.post_trade_feedback is not None else None,
                    "post_facto_simulation_results": json.loads(cast(str, opportunity_orm.post_facto_simulation_results)) if opportunity_orm.post_facto_simulation_results is not None else None,
                    "created_at": opportunity_orm.created_at,
                    "updated_at": opportunity_orm.updated_at,
                    "strategy_id": opportunity_orm.strategy_id
                }
                return Opportunity.model_validate(full_opportunity_data)
            return None

    async def get_closed_trades(self, user_id: str, symbol: Optional[str] = None,
                                start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                                mode: Optional[str] = None) -> List[Trade]:
        async with self._get_session() as session:
            logger.debug(f"get_closed_trades - user_id: {user_id}, mode: {mode}, symbol: {symbol}, start_date: {start_date}, end_date: {end_date}")
            query = select(TradeORM).where(
                TradeORM.user_id == user_id,
                TradeORM.position_status == PositionStatus.CLOSED.value
            )

            if symbol:
                query = query.where(TradeORM.symbol == symbol)
            if mode:
                query = query.where(TradeORM.mode == mode)
            if start_date:
                query = query.where(TradeORM.closed_at >= start_date)
            if end_date:
                query = query.where(TradeORM.closed_at <= end_date)

            result = await session.execute(query)
            trade_orms = result.scalars().all()
            
            trades = []
            for trade_orm in trade_orms:
                try:
                    trade_data_from_json = json.loads(cast(str, trade_orm.data))
                    logger.debug(f"get_closed_trades - trade_orm.data: {trade_orm.data}") # Debugging
                    logger.debug(f"get_closed_trades - trade_data_from_json: {trade_data_from_json}") # Debugging

                    # Asegurar que pnl_usd se convierta a Decimal si viene como float o str del JSON
                    if "pnl_usd" in trade_data_from_json and not isinstance(trade_data_from_json["pnl_usd"], Decimal):
                        try:
                            trade_data_from_json["pnl_usd"] = Decimal(str(trade_data_from_json["pnl_usd"]))
                        except Exception:
                            logger.warning(f"No se pudo convertir pnl_usd a Decimal: {trade_data_from_json['pnl_usd']}")
                            trade_data_from_json["pnl_usd"] = None # O manejar como error

                    full_trade_data = {
                        "id": trade_orm.id,
                        "user_id": trade_orm.user_id,
                        "positionStatus": trade_orm.position_status, # Mantener como str
                        "mode": trade_orm.mode, # Mantener como str
                        "symbol": trade_orm.symbol,
                        "created_at": trade_orm.created_at,
                        "updated_at": trade_orm.updated_at,
                        "closed_at": trade_orm.closed_at,
                        **trade_data_from_json
                    }
                    
                    trade_pydantic = Trade.model_validate(full_trade_data)
                    
                    trades.append(trade_pydantic)
                except Exception as e:
                    logger.error(f"Error al validar Trade Pydantic desde ORM: {e}")
            logger.debug(f"get_closed_trades - Trades recuperados: {len(trades)}")
            return trades

    async def get_trades_with_filters(
        self,
        user_id: str,
        trading_mode: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Trade]:
        """
        Recupera trades con filtros dinámicos.
        """
        async with self._get_session() as session:
            logger.debug(f"get_trades_with_filters - user_id: {user_id}, trading_mode: {trading_mode}, status: {status}, symbol: {symbol}, start_date: {start_date}, end_date: {end_date}, limit: {limit}, offset: {offset}")
            query = select(TradeORM).where(
                TradeORM.user_id == user_id,
                TradeORM.mode == trading_mode
            )

            if status:
                query = query.where(TradeORM.position_status == status)
            if symbol:
                query = query.where(TradeORM.symbol == symbol)
            if start_date:
                query = query.where(TradeORM.created_at >= start_date)
            if end_date:
                query = query.where(TradeORM.created_at <= end_date)

            query = query.order_by(TradeORM.created_at.desc()).limit(limit).offset(offset)

            result = await session.execute(query)
            trade_orms = result.scalars().all()

            trades = []
            for trade_orm_instance in trade_orms:
                try:
                    trade_data = json.loads(cast(str, trade_orm_instance.data))
                    logger.debug(f"get_trades_with_filters - trade_orm_instance.data: {trade_orm_instance.data}") # Debugging
                    logger.debug(f"get_trades_with_filters - trade_data: {trade_data}") # Debugging
                    trade_data.update({
                        "id": str(trade_orm_instance.id),
                        "user_id": str(trade_orm_instance.user_id),
                        "positionStatus": trade_orm_instance.position_status, # Mantener como str
                        "mode": trade_orm_instance.mode, # Mantener como str
                        "symbol": trade_orm_instance.symbol,
                        "created_at": trade_orm_instance.created_at.isoformat(),
                        "updated_at": trade_orm_instance.updated_at.isoformat(),
                        "closed_at": trade_orm_instance.closed_at.isoformat() if trade_orm_instance.closed_at is not None else None,
                    })
                    trades.append(Trade.model_validate(trade_data))
                except Exception as e:
                    logger.error(f"Error procesando trade desde la BD: {e}")
            logger.debug(f"get_trades_with_filters - Trades recuperados: {len(trades)}")
            return trades
