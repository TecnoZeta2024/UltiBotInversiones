from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from typing_extensions import LiteralString
from ..core.ports.persistence_service import IPersistenceService
import asyncpg # Importar asyncpg para el tipo Pool

class SupabasePersistenceService(IPersistenceService):
    """
    A SQLAlchemy-based persistence service.
    Can be initialized with an AsyncSession (for tests) or an AsyncEngine/asyncpg.Pool (for app).
    """

    def __init__(self, session: Optional[AsyncSession] = None, engine: Optional[AsyncEngine] = None, pool: Optional[asyncpg.Pool] = None):
        self._session = session
        self._engine = engine
        self._pool = pool # Para compatibilidad con asyncpg si se usa directamente

        if not (session or engine or pool):
            raise ValueError("SupabasePersistenceService must be initialized with either a session, an engine, or a pool.")

        if self._engine:
            self._async_session_factory = sessionmaker(bind=self._engine, class_=AsyncSession, expire_on_commit=False)
        else:
            self._async_session_factory = None # Se usará la sesión inyectada directamente

    async def _get_session(self) -> AsyncSession:
        if self._session:
            return self._session
        elif self._async_session_factory:
            # Cuando se usa un engine, creamos una sesión a partir de él
            # La gestión de la conexión y transacción se hará en el contexto de la llamada
            return self._async_session_factory()
        else:
            raise RuntimeError("No session or engine/pool provided to create a session.")

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
        async with await self._get_session() as session:
            result = await session.execute(text(query), params)
            record = result.fetchone()
            return dict(record._mapping) if record else None

    async def fetch_all(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with await self._get_session() as session:
            result = await session.execute(text(query), params)
            records = result.fetchall()
            return [dict(record._mapping) for record in records]

    async def execute(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> None:
        async with await self._get_session() as session:
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
        async with await self._get_session() as session:
            await session.execute(text(query), data)
            await session.commit()

    async def get_all(self, table_name: str, condition: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        async with await self._get_session() as session:
            result = await session.execute(text(query), params)
            records = result.fetchall()
            return [dict(record._mapping) for record in records]

    async def get_one(self, table_name: str, condition: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM {table_name} WHERE {condition} LIMIT 1"
        async with await self._get_session() as session:
            result = await session.execute(text(query), params)
            record = result.fetchone()
            return dict(record._mapping) if record else None

    async def delete(self, table_name: str, condition: str, params: Optional[Dict[str, Any]] = None) -> None:
        query = f"DELETE FROM {table_name} WHERE {condition}"
        async with await self._get_session() as session:
            await session.execute(text(query), params)
            await session.commit()

    async def get_user_configuration(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM user_configurations WHERE user_id = :user_id LIMIT 1"
        async with await self._get_session() as session:
            result = await session.execute(text(query), {"user_id": user_id})
            record = result.fetchone()
            return dict(record._mapping) if record else None

    async def upsert_trade(self, trade_data: Dict[str, Any]) -> None:
        await self.upsert("trades", trade_data, on_conflict=["id"])

    async def execute_raw_sql(self, query: LiteralString, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        async with await self._get_session() as session:
            result = await session.execute(text(query), params)
            records = result.fetchall()
            return [dict(record._mapping) for record in records]

    async def upsert_user_configuration(self, user_config_data: Dict[str, Any]) -> None:
        await self.upsert("user_configurations", user_config_data, on_conflict=["id"])
