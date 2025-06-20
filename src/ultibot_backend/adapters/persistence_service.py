from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, async_sessionmaker
from sqlalchemy.sql import text, select, update # Importar update
from sqlalchemy.dialects import postgresql
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from typing_extensions import LiteralString
from datetime import datetime, timezone # Importar datetime y timezone
from uuid import UUID, uuid4
import json
from pydantic import BaseModel # Añadir esta importación para la función auxiliar

from ..core.ports.persistence_service import IPersistenceService
from ..core.domain_models.trade_models import Trade, PositionStatus # Importar Trade Pydantic model
from ..core.domain_models.user_configuration_models import UserConfiguration, NotificationPreference, RiskProfile, AIStrategyConfiguration, MCPServerPreference, DashboardLayoutProfile, CloudSyncPreferences # Importar UserConfiguration Pydantic model y sus sub-modelos
from ..core.domain_models.opportunity_models import OpportunityStatus, Opportunity, InitialSignal, AIAnalysis, SourceType # Importar OpportunityStatus, Opportunity, InitialSignal, AIAnalysis, SourceType
from ..core.domain_models.orm_models import TradeORM, UserConfigurationORM, PortfolioSnapshotORM, OpportunityORM # Importar modelos ORM y OpportunityORM
import asyncpg # Importar asyncpg para el tipo Pool

class SupabasePersistenceService(IPersistenceService):
    """
    A SQLAlchemy-based persistence service.
    Can be initialized with an AsyncSession (for tests) or an AsyncEngine/asyncpg.Pool (for app).
    """

    def __init__(self, session: Optional[AsyncSession] = None, engine: Optional[AsyncEngine] = None, pool: Optional[asyncpg.Pool] = None, session_factory: Optional[async_sessionmaker[AsyncSession]] = None):
        self._session = session
        self._engine = engine
        self._pool = pool # Para compatibilidad con asyncpg si se usa directamente
        self._async_session_factory = session_factory # Usar la factoría si se inyecta

        if not (session or engine or pool or session_factory):
            raise ValueError("SupabasePersistenceService must be initialized with either a session, an engine, a pool, or a session_factory.")

        # Si se proporciona un motor y no una factoría, crear una factoría
        if self._engine and not self._async_session_factory:
            self._async_session_factory = async_sessionmaker(self._engine, expire_on_commit=False)
        # Si se proporciona una sesión directa, la factoría no es necesaria para _get_session
        elif self._session:
            self._async_session_factory = None

    def _pydantic_to_json_string(self, obj: Any) -> Optional[str]:
        if obj is None:
            return None
        if isinstance(obj, BaseModel):
            return obj.model_dump_json()
        if isinstance(obj, list) and all(isinstance(item, BaseModel) for item in obj):
            return json.dumps([item.model_dump() for item in obj])
        # Para otros tipos que ya son serializables a JSON (ej. List[str], Dict[str, Any])
        if isinstance(obj, (list, dict)):
            return json.dumps(obj)
        return str(obj) # Fallback para tipos simples si es necesario

    def _get_session(self):
        """Get a session context manager."""
        if self._async_session_factory:
            return self._async_session_factory()
        
        if self._session:
            # This path should ideally only be used in tests where the session
            # lifecycle is managed externally.
            class MockSessionManager:
                def __init__(self, session: AsyncSession):
                    self._session = session

                async def __aenter__(self) -> AsyncSession:
                    return self._session

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    # In a test context, we don't close the session here.
                    # It's managed by the test fixture.
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
            await session.commit()

    async def upsert(self, table_name: str, data: Dict[str, Any], on_conflict: List[str]) -> None:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{key}" for key in data.keys())
        
        conflict_columns = ", ".join(on_conflict)
        update_placeholders = ", ".join(f"{col} = EXCLUDED.{col}" for col in data.keys() if col not in on_conflict)

        # Using SQLite compatible upsert syntax
        query = f"""
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_columns}) DO UPDATE
            SET {update_placeholders};
        """
        async with self._get_session() as session:
            await session.execute(text(query), data)
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

    async def get_user_configuration(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM user_configurations WHERE user_id = :user_id LIMIT 1"
        async with self._get_session() as session:
            result = await session.execute(text(query), {"user_id": user_id})
            record = result.fetchone()
            return dict(record._mapping) if record else None

    async def upsert_trade(self, trade: Trade) -> None:
        async with self._get_session() as session:
            trade_orm = TradeORM(
                id=trade.id,
                user_id=trade.user_id,
                data=trade.model_dump_json(), # Convertir Pydantic a JSON string
                position_status=trade.positionStatus,
                mode=trade.mode,
                symbol=trade.symbol,
                created_at=trade.created_at,
                updated_at=trade.updated_at,
                closed_at=trade.closed_at
            )
            # Usar merge para upsert: inserta si no existe, actualiza si existe
            session.add(trade_orm)
            await session.commit()
            await session.refresh(trade_orm) # Refrescar para obtener cualquier valor generado por la BD

    async def execute_raw_sql(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with self._get_session() as session:
            result = await session.execute(text(query), params)
            records = result.fetchall()
            return [dict(record._mapping) for record in records]

    async def upsert_user_configuration(self, user_config: UserConfiguration) -> None:
        async with self._get_session() as session:
            # Generar un nuevo ID si no existe
            config_id = user_config.id if user_config.id is not None else str(uuid4())

            user_config_orm = UserConfigurationORM(
                id=config_id,
                user_id=user_config.user_id,
                telegram_chat_id=user_config.telegram_chat_id,
                notification_preferences=self._pydantic_to_json_string(user_config.notification_preferences),
                enable_telegram_notifications=user_config.enable_telegram_notifications,
                default_paper_trading_capital=user_config.default_paper_trading_capital,
                paper_trading_active=user_config.paper_trading_active,
                paper_trading_assets=self._pydantic_to_json_string(user_config.paper_trading_assets),
                watchlists=self._pydantic_to_json_string(user_config.watchlists),
                favorite_pairs=self._pydantic_to_json_string(user_config.favorite_pairs),
                risk_profile=self._pydantic_to_json_string(user_config.risk_profile),
                risk_profile_settings=self._pydantic_to_json_string(user_config.risk_profile_settings),
                real_trading_settings=self._pydantic_to_json_string(user_config.real_trading_settings),
                ai_strategy_configurations=self._pydantic_to_json_string(user_config.ai_strategy_configurations),
                ai_analysis_confidence_thresholds=self._pydantic_to_json_string(user_config.ai_analysis_confidence_thresholds),
                mcp_server_preferences=self._pydantic_to_json_string(user_config.mcp_server_preferences),
                selected_theme=user_config.selected_theme,
                dashboard_layout_profiles=self._pydantic_to_json_string(user_config.dashboard_layout_profiles),
                active_dashboard_layout_profile_id=user_config.active_dashboard_layout_profile_id,
                dashboard_layout_config=self._pydantic_to_json_string(user_config.dashboard_layout_config),
                cloud_sync_preferences=self._pydantic_to_json_string(user_config.cloud_sync_preferences),
                created_at=user_config.created_at,
                updated_at=user_config.updated_at
            )
            await session.merge(user_config_orm)
            await session.commit()

    async def update_opportunity_status(self, opportunity_id: UUID, new_status: OpportunityStatus, status_reason: str) -> None:
        async with self._get_session() as session:
            stmt = (
                update(OpportunityORM)
                .where(OpportunityORM.id == opportunity_id)
                .values(
                    status=new_status.value,
                    status_reason_code=status_reason, # Usar status_reason como reason_code
                    status_reason_text=status_reason, # Usar status_reason como reason_text
                    updated_at=datetime.now(timezone.utc)
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[Opportunity]:
        async with self._get_session() as session:
            result = await session.execute(
                select(OpportunityORM).where(OpportunityORM.id == opportunity_id)
            )
            opportunity_orm = result.scalars().first()
            if opportunity_orm:
                # Deserializar los campos JSON a sus modelos Pydantic correspondientes
                initial_signal_obj = InitialSignal.model_validate_json(cast(str, opportunity_orm.initial_signal)) if opportunity_orm.initial_signal is not None else None
                ai_analysis_obj = AIAnalysis.model_validate_json(cast(str, opportunity_orm.ai_analysis)) if opportunity_orm.ai_analysis is not None else None
                
                # Mapear los campos de OpportunityORM a Opportunity
                full_opportunity_data = {
                    "id": opportunity_orm.id,
                    "user_id": opportunity_orm.user_id,
                    "symbol": opportunity_orm.symbol,
                    "detected_at": opportunity_orm.detected_at,
                    "source_type": SourceType(opportunity_orm.source_type), # Convertir a enum
                    "source_name": opportunity_orm.source_name,
                    "source_data": json.loads(cast(str, opportunity_orm.source_data)) if opportunity_orm.source_data is not None else None, # source_data es un JSON string
                    "initial_signal": initial_signal_obj,
                    "system_calculated_priority_score": opportunity_orm.system_calculated_priority_score,
                    "last_priority_calculation_at": opportunity_orm.last_priority_calculation_at,
                    "status": OpportunityStatus(opportunity_orm.status), # Convertir a enum
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

    async def get_closed_trades(self, user_id: UUID, symbol: Optional[str] = None,
                                start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                                mode: Optional[str] = None) -> List[Trade]:
        async with self._get_session() as session:
            query = select(TradeORM).where(
                TradeORM.user_id == user_id,
                TradeORM.position_status == PositionStatus.CLOSED.value # Usar el valor del enum
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
            
            # Convertir TradeORM a Trade Pydantic model
            trades = []
            for trade_orm in trade_orms:
                try:
                    # Deserializar el JSON 'data'
                    trade_data_from_json = json.loads(cast(str, trade_orm.data))

                    # Combinar con los campos directamente de TradeORM
                    full_trade_data = {
                        "id": trade_orm.id,
                        "user_id": trade_orm.user_id,
                        "positionStatus": PositionStatus(trade_orm.position_status),
                        "mode": trade_orm.mode,
                        "symbol": trade_orm.symbol,
                        "created_at": trade_orm.created_at,
                        "updated_at": trade_orm.updated_at,
                        "closed_at": trade_orm.closed_at,
                        **trade_data_from_json # Añadir el resto de los datos del JSON
                    }
                    
                    # Validar y crear el modelo Pydantic
                    trade_pydantic = Trade.model_validate(full_trade_data)
                    
                    trades.append(trade_pydantic)
                except Exception as e:
                    print(f"Error al validar Trade Pydantic desde ORM: {e}")
            # Opcional: loggear el trade_orm.data para depuración
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
            query = select(TradeORM).where(
                TradeORM.user_id == UUID(user_id),
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
                    # Asegurarse de que los campos del ORM sobreescriben los del JSON si hay conflicto
                    trade_data.update({
                        "id": str(trade_orm_instance.id),
                        "user_id": str(trade_orm_instance.user_id),
                        "positionStatus": trade_orm_instance.position_status,
                        "mode": trade_orm_instance.mode,
                        "symbol": trade_orm_instance.symbol,
                        "created_at": trade_orm_instance.created_at.isoformat(),
                        "updated_at": trade_orm_instance.updated_at.isoformat(),
                        "closed_at": trade_orm_instance.closed_at.isoformat() if trade_orm_instance.closed_at is not None else None,
                    })
                    trades.append(Trade.model_validate(trade_data))
                except Exception as e:
                    # Log del error, idealmente con un logger real
                    print(f"Error procesando trade desde la BD: {e}")
            return trades
