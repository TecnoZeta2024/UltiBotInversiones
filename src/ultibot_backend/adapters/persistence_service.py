import asyncio
import sys
import psycopg
import aiosqlite # Importar aiosqlite
from psycopg_pool import AsyncConnectionPool
import logging
import os
from urllib.parse import urlparse, unquote
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union
from uuid import UUID
from datetime import datetime, timezone
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier, Literal, Composed, Composable
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
import json

# Solución para Windows ProactorEventLoop con psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from ultibot_backend.app_config import settings
from ultibot_backend.core.domain_models.opportunity_models import Opportunity, OpportunityStatus
from ultibot_backend.core.domain_models.trade_models import Trade, TradeOrderDetails
from ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig
from shared.data_types import APICredential, ServiceName, Notification, MarketData

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass

# Definir type hints para uso en el módulo
OpportunityTypeHint = Opportunity
OpportunityStatusTypeHint = OpportunityStatus

class SupabasePersistenceService:
    def __init__(self):
        self.pool: Optional[AsyncConnectionPool] = None
        self.sqlite_conn: Optional[aiosqlite.Connection] = None # Conexión SQLite
        self._is_sqlite: bool = False # Bandera para saber si es SQLite
        self.db_url: Optional[str] = os.getenv("DATABASE_URL")
        if not self.db_url:
            logger.error("DATABASE_URL no se encontró en las variables de entorno durante la inicialización.")
        self.fixed_user_id = settings.FIXED_USER_ID

    async def connect(self):
        if self._is_sqlite:
            if self.sqlite_conn:
                try:
                    # Intenta ejecutar una consulta simple para verificar si la conexión está activa
                    await self.sqlite_conn.execute("SELECT 1")
                    logger.info("La conexión SQLite ya está activa.")
                    return
                except aiosqlite.Error:
                    logger.warning("La conexión SQLite existente no es válida. Intentando reconectar...")
                    await self.sqlite_conn.close()
                    self.sqlite_conn = None
            
            if not self.db_url:
                logger.error("DATABASE_URL no está configurada. No se puede inicializar la conexión a la base de datos.")
                raise ValueError("DATABASE_URL no está configurada en las variables de entorno.")

            parsed_url = urlparse(self.db_url)
            conn_str = parsed_url.path
            if conn_str.startswith('/'):
                conn_str = conn_str[1:] # Eliminar el '/' inicial si existe
            
            self.sqlite_conn = await aiosqlite.connect(conn_str)
            self.sqlite_conn.row_factory = aiosqlite.Row # Para obtener resultados como diccionarios
            logger.info(f"Conectado a SQLite en: {conn_str}.")
            return
        
        # Lógica para PostgreSQL/Supabase
        if self.pool and not self.pool.closed:
            logger.info("El pool de conexiones de PostgreSQL ya está activo.")
            return

        if not self.db_url:
            logger.error("DATABASE_URL no está configurada. No se puede inicializar la conexión a la base de datos.")
            raise ValueError("DATABASE_URL no está configurada en las variables de entorno.")

        try:
            parsed_url = urlparse(self.db_url)
            if parsed_url.scheme == "sqlite": # Esto ya debería ser manejado por el if anterior
                self._is_sqlite = True
                # Esto es un fallback, pero la lógica principal de SQLite está arriba
                conn_str = parsed_url.path
                if conn_str.startswith('/'):
                    conn_str = conn_str[1:]
                self.sqlite_conn = await aiosqlite.connect(conn_str)
                self.sqlite_conn.row_factory = aiosqlite.Row
                logger.info(f"Conectado a SQLite en: {conn_str}.")
                return
            else:
                self._is_sqlite = False
                min_size = getattr(settings, "DB_POOL_MIN_SIZE", 2)
                max_size = getattr(settings, "DB_POOL_MAX_SIZE", 10)
                
                conn_info_dict = {
                    "host": parsed_url.hostname,
                    "port": parsed_url.port,
                    "user": parsed_url.username,
                    "password": parsed_url.password,
                    "dbname": parsed_url.path.lstrip("/"),
                    "sslmode": "verify-full",
                    "sslrootcert": "supabase/prod-ca-2021.crt"
                }
                conn_info_dict = {k: v for k, v in conn_info_dict.items() if v is not None}
                conn_str = make_conninfo(**conn_info_dict)
                logger.info("Conectando a PostgreSQL/Supabase. Incluyendo parámetros SSL.")
                
                self.pool = AsyncConnectionPool(
                    conninfo=conn_str,
                    min_size=min_size,
                    max_size=max_size,
                    name="supabase_pool"
                )
                await self.pool.open()
                logger.info(f"Pool de conexiones a Supabase (psycopg_pool) establecido exitosamente. Min: {min_size}, Max: {max_size}")
        except Exception as e:
            logger.error(f"Error al establecer la conexión a la base de datos: {e}", exc_info=True)
            self.pool = None
            self.sqlite_conn = None
            raise

    async def disconnect(self):
        if self._is_sqlite:
            if self.sqlite_conn:
                await self.sqlite_conn.close()
                logger.info("Conexión SQLite cerrada.")
                self.sqlite_conn = None
        elif self.pool:
            if not self.pool.closed:
                await self.pool.close()
                logger.info("Pool de conexiones a Supabase (psycopg_pool) cerrado.")
            self.pool = None

    async def _check_pool(self):
        """Verifica la salud de la conexión y la reconecta si es necesario."""
        if self._is_sqlite:
            if not self.sqlite_conn:
                logger.warning("La conexión SQLite no existe. Intentando reconectar...")
                await self.connect()

            if not self.sqlite_conn:
                logger.critical("Fallo crítico: la conexión SQLite es None después de intentar conectar.")
                raise ConnectionError("No se pudo establecer la conexión con la base de datos SQLite.")

            try:
                # Intenta ejecutar una consulta simple para verificar la salud de la conexión SQLite
                await self.sqlite_conn.execute("SELECT 1")
            except aiosqlite.Error as e:
                logger.error(f"Fallo en la comprobación de salud de la conexión SQLite. Intentando reconectar. Error: {e}")
                await self.disconnect()
                await self.connect()
                assert self.sqlite_conn is not None, "Fallo crítico al reconectar la conexión SQLite."
        else:
            if not self.pool or self.pool.closed:
                logger.warning("El pool de conexiones de PostgreSQL está cerrado o no existe. Intentando reconectar...")
                await self.connect()
            assert self.pool is not None and not self.pool.closed, "Fallo crítico al reconectar el pool de PostgreSQL."
            
            try:
                await self.pool.check()
            except Exception as e:
                logger.error(f"Fallo en la comprobación de salud del pool de PostgreSQL. Intentando reconectar. Error: {e}")
                await self.disconnect()
                await self.connect()
                assert self.pool is not None and not self.pool.closed, "Fallo crítico al reconectar el pool de PostgreSQL después de un check fallido."

    async def save_market_data(self, data_to_save: List[MarketData]):
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    for data in data_to_save:
                        await cur.execute(query, (data.symbol, data.timestamp.isoformat(), data.open, data.high, data.low, data.close, data.volume))
                await self.sqlite_conn.commit()
                logger.info(f"Se guardaron {len(data_to_save)} registros de datos de mercado en SQLite.")
            except Exception as e:
                logger.error(f"Error al guardar datos de mercado en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            query = SQL("COPY market_data (symbol, timestamp, open, high, low, close, volume) FROM STDIN")

            async def data_generator():
                for data in data_to_save:
                    yield f"{data.symbol}\t{data.timestamp.isoformat()}\t{data.open}\t{data.high}\t{data.low}\t{data.close}\t{data.volume}\n".encode('utf-8')

            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        async with cur.copy(query) as copy:
                            async for chunk in data_generator():
                                await copy.write(chunk)
                logger.info(f"Se guardaron {len(data_to_save)} registros de datos de mercado en PostgreSQL.")
            except Exception as e:
                logger.error(f"Error al guardar datos de mercado con COPY en PostgreSQL: {e}", exc_info=True)
                raise

    async def get_market_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[MarketData]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT * FROM market_data WHERE symbol = ? AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (symbol, start_date.isoformat(), end_date.isoformat()))
                    records = await cur.fetchall()
                    return [MarketData(**dict(record)) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener datos de mercado para {symbol} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            query = SQL("SELECT * FROM market_data WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s ORDER BY timestamp ASC;")

            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (symbol, start_date, end_date))
                        records = await cur.fetchall()
                        return [MarketData(**record) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener datos de mercado para {symbol} en PostgreSQL: {e}", exc_info=True)
                raise

    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[Opportunity]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT * FROM opportunities WHERE id = ? AND user_id = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(opportunity_id), str(self.fixed_user_id)))
                    record = await cur.fetchone()
                if record:
                    return Opportunity(**dict(record))
                return None
            except Exception as e:
                logger.error(f"Error al obtener oportunidad por ID {opportunity_id} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            query = SQL("SELECT * FROM opportunities WHERE id = %s AND user_id = %s;")

            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (opportunity_id, self.fixed_user_id))
                        record = await cur.fetchone()
                    
                    if record:
                        return Opportunity(**record)
                    return None
            except Exception as e:
                logger.error(f"Error al obtener oportunidad por ID {opportunity_id} (psycopg_pool): {e}", exc_info=True)
                raise

    async def update_opportunity_status(self, opportunity_id: UUID, new_status: OpportunityStatus, status_reason: Optional[str] = None) -> Optional[Opportunity]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query_str: str = """
            UPDATE opportunities
            SET status = ?, status_reason = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            RETURNING *;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    updated_at = datetime.now(timezone.utc).isoformat()
                    await cur.execute(query_str, (new_status.value, status_reason, updated_at, str(opportunity_id), str(self.fixed_user_id)))
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    # Para simplificar, asumimos que la actualización fue exitosa y devolvemos la oportunidad actualizada
                    # o se puede hacer un SELECT * FROM opportunities WHERE id = ?
                    record = await cur.execute("SELECT * FROM opportunities WHERE id = ? AND user_id = ?", (str(opportunity_id), str(self.fixed_user_id)))
                    updated_record = await record.fetchone()
                    if updated_record:
                        return Opportunity(**dict(updated_record))
                return None
            except Exception as e:
                logger.error(f"Error al actualizar estado de oportunidad {opportunity_id} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            query_str: str = """
            UPDATE opportunities
            SET status = %s, status_reason = %s, updated_at = timezone('utc'::text, now())
            WHERE id = %s AND user_id = %s
            RETURNING *;
            """
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(SQL(query_str), (new_status.value, status_reason, opportunity_id, self.fixed_user_id))
                        record = await cur.fetchone()
                        if record:
                            return Opportunity(**record)
                return None
            except Exception as e:
                logger.error(f"Error al actualizar estado de oportunidad {opportunity_id} (psycopg_pool): {e}", exc_info=True)
                raise
    
    async def save_credential(self, credential: APICredential) -> APICredential:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query_str: str = """
            INSERT INTO api_credentials (
                id, user_id, service_name, credential_label, 
                encrypted_api_key, encrypted_api_secret, encrypted_other_details, 
                status, last_verified_at, permissions, permissions_checked_at, 
                expires_at, rotation_reminder_policy_days, usage_count, last_used_at, 
                purpose_description, tags, notes, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT (user_id, service_name, credential_label) DO UPDATE SET
                encrypted_api_key = EXCLUDED.encrypted_api_key,
                encrypted_api_secret = EXCLUDED.encrypted_api_secret,
                encrypted_other_details = EXCLUDED.encrypted_other_details,
                status = EXCLUDED.status,
                last_verified_at = EXCLUDED.last_verified_at,
                permissions = EXCLUDED.permissions,
                permissions_checked_at = EXCLUDED.permissions_checked_at,
                expires_at = EXCLUDED.expires_at,
                rotation_reminder_policy_days = EXCLUDED.rotation_reminder_policy_days,
                usage_count = EXCLUDED.usage_count,
                last_used_at = EXCLUDED.last_used_at,
                purpose_description = EXCLUDED.purpose_description,
                tags = EXCLUDED.tags,
                notes = EXCLUDED.notes,
                updated_at = ?
            RETURNING *;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    now_utc = datetime.now(timezone.utc).isoformat()
                    await cur.execute(
                        query_str,
                        (
                            str(credential.id), str(self.fixed_user_id), credential.service_name.value, credential.credential_label,
                            credential.encrypted_api_key, credential.encrypted_api_secret, credential.encrypted_other_details,
                            credential.status, credential.last_verified_at.isoformat() if credential.last_verified_at else None, 
                            json.dumps(credential.permissions) if credential.permissions else None, 
                            credential.permissions_checked_at.isoformat() if credential.permissions_checked_at else None,
                            credential.expires_at.isoformat() if credential.expires_at else None, 
                            credential.rotation_reminder_policy_days, credential.usage_count, 
                            credential.last_used_at.isoformat() if credential.last_used_at else None,
                            credential.purpose_description, 
                            json.dumps(credential.tags) if credential.tags else None, 
                            credential.notes, 
                            credential.created_at.isoformat() if credential.created_at else None, 
                            now_utc, # updated_at
                        )
                    )
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    record = await cur.execute("SELECT * FROM api_credentials WHERE id = ? AND user_id = ?", (str(credential.id), str(self.fixed_user_id)))
                    returned_record = await record.fetchone()
                    if returned_record:
                        return APICredential(**dict(returned_record))
                raise ValueError("No se pudo guardar/actualizar la credencial y obtener el registro de retorno en SQLite.")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar credencial en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query_str: str = """
            INSERT INTO api_credentials (
                id, user_id, service_name, credential_label, 
                encrypted_api_key, encrypted_api_secret, encrypted_other_details, 
                status, last_verified_at, permissions, permissions_checked_at, 
                expires_at, rotation_reminder_policy_days, usage_count, last_used_at, 
                purpose_description, tags, notes, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (user_id, service_name, credential_label) DO UPDATE SET
                encrypted_api_key = EXCLUDED.encrypted_api_key,
                encrypted_api_secret = EXCLUDED.encrypted_api_secret,
                encrypted_other_details = EXCLUDED.encrypted_other_details,
                status = EXCLUDED.status,
                last_verified_at = EXCLUDED.last_verified_at,
                permissions = EXCLUDED.permissions,
                permissions_checked_at = EXCLUDED.permissions_checked_at,
                expires_at = EXCLUDED.expires_at,
                rotation_reminder_policy_days = EXCLUDED.rotation_reminder_policy_days,
                usage_count = EXCLUDED.usage_count,
                last_used_at = EXCLUDED.last_used_at,
                purpose_description = EXCLUDED.purpose_description,
                tags = EXCLUDED.tags,
                notes = EXCLUDED.notes,
                updated_at = timezone('utc'::text, now())
            RETURNING *;
            """
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(
                            SQL(query_str),
                            (
                                credential.id, self.fixed_user_id, credential.service_name.value, credential.credential_label,
                                credential.encrypted_api_key, credential.encrypted_api_secret, credential.encrypted_other_details,
                                credential.status, credential.last_verified_at, credential.permissions, credential.permissions_checked_at,
                                credential.expires_at, credential.rotation_reminder_policy_days, credential.usage_count, credential.last_used_at,
                                credential.purpose_description, credential.tags, credential.notes, credential.created_at, credential.updated_at
                            )
                        )
                        record = await cur.fetchone()
                        if record:
                            return APICredential(**record)
                raise ValueError("No se pudo guardar/actualizar la credencial y obtener el registro de retorno (psycopg_pool).")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar credencial (psycopg_pool): {e}")
                raise

    async def get_credentials_by_service(self, service_name: ServiceName) -> List[APICredential]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT * FROM api_credentials WHERE user_id = ? AND service_name = ? ORDER BY created_at ASC;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id), service_name.value))
                    records = await cur.fetchall()
                    return [APICredential(**dict(record)) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener credenciales por servicio para usuario {self.fixed_user_id} y servicio {service_name.value} en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("SELECT * FROM api_credentials WHERE user_id = %s AND service_name = %s ORDER BY created_at ASC;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id, service_name.value))
                        records = await cur.fetchall()
                        return [APICredential(**record) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener credenciales por servicio para usuario {self.fixed_user_id} y servicio {service_name.value} (psycopg_pool): {e}")
                raise

    async def get_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT * FROM api_credentials WHERE id = ? AND user_id = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(credential_id), str(self.fixed_user_id)))
                    record = await cur.fetchone()
                    if record:
                        return APICredential(**dict(record))
                return None
            except Exception as e:
                logger.error(f"Error al obtener credencial por ID {credential_id} para usuario {self.fixed_user_id} en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("SELECT * FROM api_credentials WHERE id = %s AND user_id = %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (credential_id, self.fixed_user_id))
                        record = await cur.fetchone()
                        if record:
                            return APICredential(**record)
                return None
            except Exception as e:
                logger.error(f"Error al obtener credencial por ID {credential_id} para usuario {self.fixed_user_id} (psycopg_pool): {e}")
                raise

    async def get_credential_by_service_label(self, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT * FROM api_credentials WHERE user_id = ? AND service_name = ? AND credential_label = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id), service_name.value, credential_label))
                    record = await cur.fetchone()
                    if record:
                        return APICredential(**dict(record))
                return None
            except Exception as e:
                logger.error(f"Error al obtener credencial por servicio y etiqueta en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("SELECT * FROM api_credentials WHERE user_id = %s AND service_name = %s AND credential_label = %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id, service_name.value, credential_label))
                        record = await cur.fetchone()
                        if record:
                            return APICredential(**record)
                return None
            except Exception as e:
                logger.error(f"Error al obtener credencial por servicio y etiqueta (psycopg_pool): {e}")
                raise

    async def update_credential_status(self, credential_id: UUID, new_status: str, last_verified_at: Optional[datetime] = None) -> Optional[APICredential]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = """
            UPDATE api_credentials 
            SET status = ?, last_verified_at = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            RETURNING *;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    updated_at = datetime.now(timezone.utc).isoformat()
                    await cur.execute(query, (new_status, last_verified_at.isoformat() if last_verified_at else None, updated_at, str(credential_id), str(self.fixed_user_id)))
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    record = await cur.execute("SELECT * FROM api_credentials WHERE id = ? AND user_id = ?", (str(credential_id), str(self.fixed_user_id)))
                    updated_record = await record.fetchone()
                    if updated_record:
                        return APICredential(**dict(updated_record))
                return None
            except Exception as e:
                logger.error(f"Error al actualizar estado de credencial {credential_id} para usuario {self.fixed_user_id} en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("""
            UPDATE api_credentials 
            SET status = %s, last_verified_at = %s, updated_at = timezone('utc'::text, now())
            WHERE id = %s AND user_id = %s
            RETURNING *;
            """)
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (new_status, last_verified_at, credential_id, self.fixed_user_id))
                        record = await cur.fetchone()
                        if record:
                            return APICredential(**record)
                return None
            except Exception as e:
                logger.error(f"Error al actualizar estado de credencial {credential_id} para usuario {self.fixed_user_id} (psycopg_pool): {e}")
                raise

    async def delete_credential(self, credential_id: UUID) -> bool:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "DELETE FROM api_credentials WHERE id = ? AND user_id = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(credential_id), str(self.fixed_user_id)))
                    await self.sqlite_conn.commit()
                    return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Error al eliminar credencial {credential_id} para usuario {self.fixed_user_id} en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("DELETE FROM api_credentials WHERE id = %s AND user_id = %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (credential_id, self.fixed_user_id))
                        return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Error al eliminar credencial {credential_id} para usuario {self.fixed_user_id} (psycopg_pool): {e}")
                raise

    async def get_user_configuration(self) -> Optional[Dict[str, Any]]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT * FROM user_configurations WHERE user_id = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id),))
                    record = await cur.fetchone()
                    if record:
                        # Deserializar campos JSON si es necesario
                        config_dict = dict(record)
                        for key in ["notification_preferences", "watchlists", "favorite_pairs", "risk_profile_settings",
                                    "real_trading_settings", "ai_strategy_configurations", "ai_analysis_confidence_thresholds",
                                    "mcp_server_preferences", "dashboard_layout_profiles", "dashboard_layout_config", "cloud_sync_preferences"]:
                            if key in config_dict and isinstance(config_dict[key], str):
                                try:
                                    config_dict[key] = json.loads(config_dict[key])
                                except json.JSONDecodeError:
                                    logger.warning(f"Error al decodificar JSON para {key} en configuración de usuario.")
                        return config_dict
                return None
            except Exception as e:
                logger.error(f"Error al obtener configuración de usuario para {self.fixed_user_id} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            query = SQL("SELECT * FROM user_configurations WHERE user_id = %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id,))
                        record = await cur.fetchone()
                        if record:
                            return dict(record)
                return None
            except Exception as e:
                logger.error(f"Error al obtener configuración de usuario para {self.fixed_user_id} (psycopg_pool): {e}", exc_info=True)
                raise

    async def upsert_user_configuration(self, config_data: Dict[str, Any]):
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            config_to_save = config_data.copy()
            config_to_save.pop('id', None)
            config_to_save.pop('createdAt', None)
            config_to_save.pop('updatedAt', None)

            db_columns_map = {
                "telegramChatId": "telegram_chat_id", "notificationPreferences": "notification_preferences",
                "enableTelegramNotifications": "enable_telegram_notifications", "defaultPaperTradingCapital": "default_paper_trading_capital",
                "paperTradingActive": "paper_trading_active",
                "watchlists": "watchlists", "favoritePairs": "favorite_pairs", "riskProfile": "risk_profile",
                "riskProfileSettings": "risk_profile_settings", "realTradingSettings": "real_trading_settings",
                "aiStrategyConfigurations": "ai_strategy_configurations", "aiAnalysisConfidenceThresholds": "ai_analysis_confidence_thresholds",
                "mcpServerPreferences": "mcp_server_preferences", "selectedTheme": "selected_theme",
                "dashboardLayoutProfiles": "dashboard_layout_profiles", "activeDashboardLayoutProfileId": "active_dashboard_layout_profile_id",
                "dashboardLayoutConfig": "dashboard_layout_config", "cloudSyncPreferences": "cloud_sync_preferences",
            }

            def serialize_if_needed(value):
                if value is None:
                    return None
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return value

            insert_values_dict = {db_columns_map.get(k, k): serialize_if_needed(v) for k, v in config_to_save.items()}
            insert_values_dict['user_id'] = str(self.fixed_user_id) # Convertir UUID a str para SQLite

            # Columnas JSON que deben ser serializadas
            json_columns = [
                "notification_preferences", "watchlists", "favorite_pairs", "risk_profile_settings",
                "real_trading_settings", "ai_strategy_configurations", "ai_analysis_confidence_thresholds",
                "mcp_server_preferences", "dashboard_layout_profiles", "dashboard_layout_config", "cloud_sync_preferences"
            ]

            for col in json_columns:
                if col in insert_values_dict and insert_values_dict[col] is not None and not isinstance(insert_values_dict[col], str):
                    insert_values_dict[col] = json.dumps(insert_values_dict[col])

            columns_str = ", ".join(insert_values_dict.keys())
            placeholders_str = ", ".join(["?"] * len(insert_values_dict))
            update_set_parts_str = ", ".join([f"{col} = ?" for col in insert_values_dict if col != 'user_id'])

            query = f"""
                INSERT INTO user_configurations ({columns_str})
                VALUES ({placeholders_str})
                ON CONFLICT (user_id) DO UPDATE SET
                    {update_set_parts_str},
                    updated_at = ?;
            """
            try:
                values = list(insert_values_dict.values())
                # Añadir valores para el UPDATE SET (excluyendo user_id)
                values.extend([v for k, v in insert_values_dict.items() if k != 'user_id'])
                values.append(datetime.now(timezone.utc).isoformat()) # updated_at

                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, tuple(values))
                await self.sqlite_conn.commit()
                logger.info(f"Configuración de usuario para {self.fixed_user_id} guardada/actualizada exitosamente en SQLite.")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar configuración de usuario para {self.fixed_user_id} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            from psycopg import sql
            
            config_to_save = config_data.copy()
            config_to_save.pop('id', None)
            config_to_save.pop('createdAt', None)
            config_to_save.pop('updatedAt', None)

            db_columns_map = {
                "telegramChatId": "telegram_chat_id", "notificationPreferences": "notification_preferences",
                "enableTelegramNotifications": "enable_telegram_notifications", "defaultPaperTradingCapital": "default_paper_trading_capital",
                "paperTradingActive": "paper_trading_active",
                "watchlists": "watchlists", "favoritePairs": "favorite_pairs", "riskProfile": "risk_profile",
                "riskProfileSettings": "risk_profile_settings", "realTradingSettings": "real_trading_settings",
                "aiStrategyConfigurations": "ai_strategy_configurations", "aiAnalysisConfidenceThresholds": "ai_analysis_confidence_thresholds",
                "mcpServerPreferences": "mcp_server_preferences", "selectedTheme": "selected_theme",
                "dashboardLayoutProfiles": "dashboard_layout_profiles", "activeDashboardLayoutProfileId": "active_dashboard_layout_profile_id",
                "dashboardLayoutConfig": "dashboard_layout_config", "cloudSyncPreferences": "cloud_sync_preferences",
            }

            def serialize_if_needed(value):
                if value is None:
                    return None
                if isinstance(value, (dict, list)):
                    return json.dumps(value)
                return value

            insert_values_dict = {db_columns_map.get(k, k): serialize_if_needed(v) for k, v in config_to_save.items()}
            insert_values_dict['user_id'] = self.fixed_user_id

            json_columns = [
                "notification_preferences", "watchlists", "favorite_pairs", "risk_profile_settings",
                "real_trading_settings", "ai_strategy_configurations", "ai_analysis_confidence_thresholds",
                "mcp_server_preferences", "dashboard_layout_profiles", "dashboard_layout_config", "cloud_sync_preferences"
            ]

            for col in json_columns:
                if col in insert_values_dict and insert_values_dict[col] is not None and not isinstance(insert_values_dict[col], str):
                    insert_values_dict[col] = json.dumps(insert_values_dict[col])

            columns = [sql.Identifier(col) for col in insert_values_dict.keys()]
            placeholders = [sql.Placeholder() for _ in insert_values_dict]
            update_set_parts = [
                sql.SQL("{} = EXCLUDED.{}" ).format(sql.Identifier(col), sql.Identifier(col))
                for col in insert_values_dict if col != 'user_id'
            ]
            update_set_str = sql.SQL(", ").join(update_set_parts)

            query = sql.SQL("""
                INSERT INTO user_configurations ({columns})
                VALUES ({placeholders})
                ON CONFLICT (user_id) DO UPDATE SET
                    {update_set},
                    updated_at = timezone('utc'::text, now())
                RETURNING *;
            """).format(
                columns=sql.SQL(', ').join(columns),
                placeholders=sql.SQL(', ').join(placeholders),
                update_set=update_set_str
            )
            try:
                values = tuple(insert_values_dict.values())
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, values)
                logger.info(f"Configuración de usuario para {self.fixed_user_id} guardada/actualizada exitosamente (psycopg_pool).")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar configuración de usuario para {self.fixed_user_id} (psycopg_pool): {e}", exc_info=True)
                raise

    async def update_credential_permissions(self, credential_id: UUID, permissions: List[str], permissions_checked_at: datetime) -> Optional[APICredential]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = """
            UPDATE api_credentials 
            SET permissions = ?, permissions_checked_at = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            RETURNING *;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    updated_at = datetime.now(timezone.utc).isoformat()
                    await cur.execute(query, (json.dumps(permissions) if permissions else None, permissions_checked_at.isoformat() if permissions_checked_at else None, updated_at, str(credential_id), str(self.fixed_user_id)))
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    record = await cur.execute("SELECT * FROM api_credentials WHERE id = ? AND user_id = ?", (str(credential_id), str(self.fixed_user_id)))
                    updated_record = await record.fetchone()
                    if updated_record:
                        return APICredential(**dict(updated_record))
                return None
            except Exception as e:
                logger.error(f"Error al actualizar permisos de credencial {credential_id} para usuario {self.fixed_user_id} en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("""
            UPDATE api_credentials 
            SET permissions = %s, permissions_checked_at = %s, updated_at = timezone('utc'::text, now())
            WHERE id = %s AND user_id = %s
            RETURNING *;
            """)
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (permissions, permissions_checked_at, credential_id, self.fixed_user_id))
                        record = await cur.fetchone()
                        if record:
                            return APICredential(**record)
                return None
            except Exception as e:
                logger.error(f"Error al actualizar permisos de credencial {credential_id} para usuario {self.fixed_user_id} (psycopg_pool): {e}")
                raise

    async def save_notification(self, notification: Notification) -> Notification:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query: str = """
            INSERT INTO notifications (
                id, user_id, event_type, channel, title_key, message_key, message_params,
                title, message, priority, status, snoozed_until, data_payload, actions,
                correlation_id, is_summary, summarized_notification_ids, created_at,
                read_at, sent_at, status_history, generated_by
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id, event_type = EXCLUDED.event_type, channel = EXCLUDED.channel,
                title_key = EXCLUDED.title_key, message_key = EXCLUDED.message_key, message_params = EXCLUDED.message_params,
                title = EXCLUDED.title, message = EXCLUDED.message, priority = EXCLUDED.priority,
                status = EXCLUDED.status, snoozed_until = EXCLUDED.snoozed_until, data_payload = EXCLUDED.data_payload,
                actions = EXCLUDED.actions, correlation_id = EXCLUDED.correlation_id, is_summary = EXCLUDED.is_summary,
                summarized_notification_ids = EXCLUDED.summarized_notification_ids, read_at = EXCLUDED.read_at,
                sent_at = EXCLUDED.sent_at, status_history = EXCLUDED.status_history, generated_by = EXCLUDED.generated_by,
                created_at = EXCLUDED.created_at;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(
                        query,
                        (
                            str(notification.id), str(self.fixed_user_id), notification.eventType,
                            notification.channel,
                            notification.titleKey, notification.messageKey, json.dumps(notification.messageParams) if notification.messageParams else None,
                            notification.title, notification.message,
                            notification.priority,
                            notification.status,
                            notification.snoozedUntil.isoformat() if notification.snoozedUntil else None, json.dumps(notification.dataPayload) if notification.dataPayload else None, json.dumps(notification.actions) if notification.actions else None,
                            notification.correlationId, notification.isSummary, json.dumps(notification.summarizedNotificationIds) if notification.summarizedNotificationIds else None,
                            notification.createdAt.isoformat() if notification.createdAt else None, notification.readAt.isoformat() if notification.readAt else None, notification.sentAt.isoformat() if notification.sentAt else None,
                            json.dumps(notification.statusHistory) if notification.statusHistory else None, notification.generatedBy
                        )
                    )
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    record = await cur.execute("SELECT * FROM notifications WHERE id = ? AND user_id = ?", (str(notification.id), str(self.fixed_user_id)))
                    returned_record = await record.fetchone()
                    if returned_record:
                        return Notification(**dict(returned_record))
                raise ValueError("No se pudo guardar/actualizar la notificación y obtener el registro de retorno en SQLite.")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar notificación en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query: str = """
            INSERT INTO notifications (
                id, user_id, event_type, channel, title_key, message_key, message_params,
                title, message, priority, status, snoozed_until, data_payload, actions,
                correlation_id, is_summary, summarized_notification_ids, created_at,
                read_at, sent_at, status_history, generated_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id, event_type = EXCLUDED.event_type, channel = EXCLUDED.channel,
                title_key = EXCLUDED.title_key, message_key = EXCLUDED.message_key, message_params = EXCLUDED.message_params,
                title = EXCLUDED.title, message = EXCLUDED.message, priority = EXCLUDED.priority,
                status = EXCLUDED.status, snoozed_until = EXCLUDED.snoozed_until, data_payload = EXCLUDED.data_payload,
                actions = EXCLUDED.actions, correlation_id = EXCLUDED.correlation_id, is_summary = EXCLUDED.is_summary,
                summarized_notification_ids = EXCLUDED.summarized_notification_ids, read_at = EXCLUDED.read_at,
                sent_at = EXCLUDED.sent_at, status_history = EXCLUDED.status_history, generated_by = EXCLUDED.generated_by,
                created_at = EXCLUDED.created_at
            RETURNING *;
            """
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(
                            SQL(query),
                            (
                                notification.id, self.fixed_user_id, notification.eventType,
                                notification.channel,
                                notification.titleKey, notification.messageKey, notification.messageParams,
                                notification.title, notification.message,
                                notification.priority,
                                notification.status,
                                notification.snoozedUntil, notification.dataPayload, notification.actions,
                                notification.correlationId, notification.isSummary, notification.summarizedNotificationIds,
                                notification.createdAt, notification.readAt, notification.sentAt,
                                notification.statusHistory, notification.generatedBy
                            )
                        )
                        record = await cur.fetchone()
                        if record:
                            return Notification(**record)
                raise ValueError("No se pudo guardar/actualizar la notificación y obtener el registro de retorno (psycopg_pool).")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar notificación (psycopg_pool): {e}")
                raise

    async def get_notification_history(self, limit: int = 50) -> List[Notification]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id), limit))
                    records = await cur.fetchall()
                    return [Notification(**dict(record)) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener historial de notificaciones para el usuario {self.fixed_user_id} en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id, limit))
                        records = await cur.fetchall()
                return [Notification(**record) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener historial de notificaciones para el usuario {self.fixed_user_id} (psycopg_pool): {e}")
                raise

    async def mark_notification_as_read(self, notification_id: UUID) -> Optional[Notification]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "UPDATE notifications SET status = 'read', read_at = ? WHERE id = ? AND user_id = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    read_at = datetime.now(timezone.utc).isoformat()
                    await cur.execute(query, (read_at, str(notification_id), str(self.fixed_user_id)))
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    record = await cur.execute("SELECT * FROM notifications WHERE id = ? AND user_id = ?", (str(notification_id), str(self.fixed_user_id)))
                    updated_record = await record.fetchone()
                    if updated_record:
                        return Notification(**dict(updated_record))
                return None
            except Exception as e:
                logger.error(f"Error al marcar notificación {notification_id} como leída para el usuario {self.fixed_user_id} en SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            query = SQL("UPDATE notifications SET status = 'read', read_at = timezone('utc'::text, now()) WHERE id = %s AND user_id = %s RETURNING *;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (notification_id, self.fixed_user_id))
                        record = await cur.fetchone()
                        if record:
                            return Notification(**record)
                return None
            except Exception as e:
                logger.error(f"Error al marcar notificación {notification_id} como leída para el usuario {self.fixed_user_id} (psycopg_pool): {e}")
                raise

    async def upsert_opportunity(self, opportunity_data: Dict[str, Any]) -> Opportunity:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            query_str: str = """
            INSERT INTO opportunities (id, user_id, data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                data = EXCLUDED.data,
                updated_at = EXCLUDED.updated_at;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    now_utc = datetime.now(timezone.utc).isoformat()
                    await cur.execute(query_str, (str(opportunity_data['id']), str(self.fixed_user_id), json.dumps(opportunity_data), now_utc))
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    record = await cur.execute("SELECT * FROM opportunities WHERE id = ? AND user_id = ?", (str(opportunity_data['id']), str(self.fixed_user_id)))
                    returned_record = await record.fetchone()
                    if returned_record:
                        return Opportunity(**json.loads(returned_record['data']))
                raise ValueError("No se pudo guardar/actualizar la oportunidad en SQLite.")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar oportunidad en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            
            query_str: str = """
            INSERT INTO opportunities (id, user_id, data)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                data = EXCLUDED.data,
                updated_at = timezone('utc'::text, now())
            RETURNING *;
            """
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(SQL(query_str), (opportunity_data['id'], self.fixed_user_id, Jsonb(opportunity_data)))
                        record = await cur.fetchone()
                        if record:
                            return Opportunity(**record['data'])
                raise ValueError("No se pudo guardar/actualizar la oportunidad.")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar oportunidad (psycopg_pool): {e}", exc_info=True)
                raise

    async def get_open_paper_trades(self) -> List[Trade]:
        return await self._get_trades_by_status_and_mode('open', 'paper')

    async def get_open_real_trades(self) -> List[Trade]:
        return await self._get_trades_by_status_and_mode('open', 'real')

    async def _get_trades_by_status_and_mode(self, status: str, mode: str) -> List[Trade]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT data FROM trades WHERE user_id = ? AND position_status = ? AND mode = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id), status, mode))
                    records = await cur.fetchall()
                    return [Trade(**json.loads(record['data'])) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener trades para usuario {self.fixed_user_id} con estado {status} y modo {mode} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None

            query = SQL("SELECT data FROM trades WHERE user_id = %s AND position_status = %s AND mode = %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id, status, mode))
                        records = await cur.fetchall()
                        return [Trade(**record['data']) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener trades para usuario {self.fixed_user_id} con estado {status} y modo {mode} (psycopg_pool): {e}", exc_info=True)
                raise

    async def upsert_trade(self, trade_data: Dict[str, Any]):
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            query_str: str = """
            INSERT INTO trades (id, user_id, data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                data = EXCLUDED.data,
                updated_at = EXCLUDED.updated_at;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    now_utc = datetime.now(timezone.utc).isoformat()
                    await cur.execute(query_str, (str(trade_data['id']), str(self.fixed_user_id), json.dumps(trade_data), now_utc))
                    await self.sqlite_conn.commit()
                    logger.info(f"Trade {trade_data['id']} guardado/actualizado exitosamente en SQLite.")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar trade {trade_data['id']} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            
            query: str = """
            INSERT INTO trades (id, user_id, data)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                data = EXCLUDED.data,
                updated_at = timezone('utc'::text, now())
            RETURNING *;
            """
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(SQL(query), (trade_data['id'], self.fixed_user_id, Jsonb(trade_data)))
                logger.info(f"Trade {trade_data['id']} guardado/actualizado exitosamente (psycopg_pool).")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar trade {trade_data['id']} (psycopg_pool): {e}", exc_info=True)
                raise

    async def get_closed_trades_count(self, is_real_trade: bool) -> int:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT COUNT(*) FROM trades WHERE user_id = ? AND position_status = 'closed' AND mode = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id), 'real' if is_real_trade else 'paper'))
                    record = await cur.fetchone()
                    if record:
                        return record[0] # SQLite devuelve el count como el primer elemento de la tupla
                return 0
            except Exception as e:
                logger.error(f"Error al contar trades cerrados para user {self.fixed_user_id}, real_trade={is_real_trade} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None

            query = SQL("SELECT COUNT(*) FROM trades WHERE user_id = %s AND position_status = 'closed' AND mode = %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id, 'real' if is_real_trade else 'paper'))
                        record = await cur.fetchone()
                        if record:
                            return record['count']
                    return 0
            except Exception as e:
                logger.error(f"Error al contar trades cerrados para user {self.fixed_user_id}, real_trade={is_real_trade} (psycopg_pool): {e}", exc_info=True)
                raise

    async def get_opportunities_by_status(self, status: OpportunityStatus) -> List[Opportunity]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query = "SELECT data FROM opportunities WHERE user_id = ? AND status = ?;"
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id), status.value))
                    records = await cur.fetchall()
                    return [Opportunity(**json.loads(record['data'])) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener oportunidades por estado para user {self.fixed_user_id}, status={status.value} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None

            query = SQL("SELECT data FROM opportunities WHERE user_id = %s AND status = %s;")
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id, status.value))
                        records = await cur.fetchall()
                    
                    return [Opportunity(**record['data']) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener oportunidades por estado para user {self.fixed_user_id}, status={status.value} (psycopg_pool): {e}", exc_info=True)
                raise

    async def get_all_trades_for_user(self, user_id: UUID, mode: Optional[str] = None) -> List[Trade]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            query_base = "SELECT data FROM trades WHERE user_id = ?"
            params_list: List[Any] = [str(user_id)]
            
            if mode:
                query_base += " AND mode = ?"
                params_list.append(mode)
                
            final_query = query_base + " ORDER BY created_at DESC;"
            
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(final_query, tuple(params_list))
                    records = await cur.fetchall()
                    return [Trade(**json.loads(record['data'])) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener todos los trades para el usuario {user_id} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None

            query_base = SQL("SELECT data FROM trades WHERE user_id = %s")
            params_list: List[Any] = [user_id]
            
            if mode:
                query_base = Composed([query_base, SQL(" AND mode = %s")])
                params_list.append(mode)
                
            final_query = Composed([query_base, SQL(" ORDER BY created_at DESC;")])
            
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(final_query, tuple(params_list))
                        records = await cur.fetchall()
                    return [Trade(**record['data']) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener todos los trades para el usuario {user_id} (psycopg_pool): {e}", exc_info=True)
                raise

    async def get_closed_trades(self, filters: Dict[str, Any], start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100, offset: int = 0) -> List[Trade]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            params: List[Any] = [str(self.fixed_user_id)]
            query_parts = ["SELECT data FROM trades WHERE user_id = ? AND position_status = 'closed'"]

            if "mode" in filters:
                query_parts.append("AND mode = ?")
                params.append(filters["mode"])
            if "symbol" in filters and filters["symbol"]:
                query_parts.append("AND symbol = ?")
                params.append(filters["symbol"])
            if start_date:
                query_parts.append("AND closed_at >= ?")
                params.append(start_date.isoformat())
            if end_date:
                query_parts.append("AND closed_at <= ?")
                params.append(end_date.isoformat())
                
            query_parts.append("ORDER BY closed_at DESC LIMIT ? OFFSET ?;")
            params.extend([limit, offset])
            
            final_query = " ".join(query_parts)

            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(final_query, tuple(params))
                    records = await cur.fetchall()
                    
                    trades = []
                    for record in records:
                        try:
                            trade_data = json.loads(record['data'])
                            trades.append(Trade(**trade_data))
                        except Exception as transform_e:
                            logger.error(f"Error al transformar registro de trade a modelo Pydantic en SQLite: {transform_e} - Record: {record}", exc_info=True)
                            continue
                    return trades
            except Exception as e:
                logger.error(f"Error al obtener trades cerrados con filtros {filters} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            
            params: List[Any] = [self.fixed_user_id]
            query_parts = [SQL("SELECT data FROM trades WHERE user_id = %s AND position_status = 'closed'")]

            if "mode" in filters:
                query_parts.append(SQL("AND mode = %s"))
                params.append(filters["mode"])
            if "symbol" in filters and filters["symbol"]:
                query_parts.append(SQL("AND symbol = %s"))
                params.append(filters["symbol"])
            if start_date:
                query_parts.append(SQL("AND closed_at >= %s"))
                params.append(start_date)
            if end_date:
                query_parts.append(SQL("AND closed_at <= %s"))
                params.append(end_date)
                
            query_parts.append(SQL("ORDER BY closed_at DESC LIMIT %s OFFSET %s;"))
            params.extend([limit, offset])
            
            final_query = SQL(" ").join(query_parts)

            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(final_query, tuple(params))
                        records = await cur.fetchall()
                    
                    # Transformar los registros a objetos Trade
                    trades = []
                    for record in records:
                        try:
                            # Los datos están en la columna 'data' como JSONB
                            trade_data = record.get('data')
                            if trade_data:
                                trades.append(Trade(**trade_data))
                        except Exception as transform_e:
                            logger.error(f"Error al transformar registro de trade a modelo Pydantic: {transform_e} - Record: {record}", exc_info=True)
                            # Opcional: levantar una excepción o continuar dependiendo de la política de errores
                            continue
                    return trades
            except Exception as e:
                logger.error(f"Error al obtener trades cerrados con filtros {filters} (psycopg_pool): {e}", exc_info=True)
                raise

    async def update_opportunity_analysis(self, opportunity_id: UUID, status: OpportunityStatus, ai_analysis: Optional[str] = None, confidence_score: Optional[float] = None, suggested_action: Optional[str] = None, status_reason: Optional[str] = None) -> Optional[Opportunity]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            query_str: str = """
            UPDATE opportunities
            SET status = ?, 
                ai_analysis = ?, 
                confidence_score = ?, 
                suggested_action = ?,
                status_reason = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
            RETURNING *;
            """
            try:
                async with self.sqlite_conn.cursor() as cur:
                    updated_at = datetime.now(timezone.utc).isoformat()
                    await cur.execute(query_str, (
                        status.value, ai_analysis, confidence_score, suggested_action, status_reason, updated_at, str(opportunity_id), str(self.fixed_user_id)
                    ))
                    await self.sqlite_conn.commit()
                    # SQLite RETURNING * no es estándar, se debe hacer un SELECT después
                    record = await cur.execute("SELECT * FROM opportunities WHERE id = ? AND user_id = ?", (str(opportunity_id), str(self.fixed_user_id)))
                    updated_record = await record.fetchone()
                    if updated_record:
                        return Opportunity(**dict(updated_record))
                return None
            except Exception as e:
                logger.error(f"Error al actualizar análisis de IA para oportunidad {opportunity_id} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None

            query_str: str = """
            UPDATE opportunities
            SET status = %s, 
                ai_analysis = %s, 
                confidence_score = %s, 
                suggested_action = %s,
                status_reason = %s,
                updated_at = timezone('utc'::text, now())
            WHERE id = %s AND user_id = %s
            RETURNING *;
            """
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(SQL(query_str), (
                            status.value, ai_analysis, confidence_score, suggested_action, status_reason, opportunity_id, self.fixed_user_id
                        ))
                        record = await cur.fetchone()
                        if record:
                            return Opportunity(**record)
                return None
            except Exception as e:
                logger.error(f"Error al actualizar análisis de IA para oportunidad {opportunity_id} (psycopg_pool): {e}", exc_info=True)
                raise

    async def upsert_strategy_config(self, strategy_data: Dict[str, Any]) -> None:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            # Convertir UUIDs a string y JSONs a string
            data_to_save = strategy_data.copy()
            data_to_save['id'] = str(data_to_save['id'])
            data_to_save['user_id'] = str(self.fixed_user_id)
            
            json_fields = [
                'parameters', 'applicability_rules', 'risk_parameters_override',
                'performance_metrics', 'market_condition_filters', 'activation_schedule',
                'depends_on_strategies', 'sharing_metadata'
            ]
            for field in json_fields:
                if field in data_to_save and data_to_save[field] is not None:
                    data_to_save[field] = json.dumps(data_to_save[field])

            query = """
            INSERT INTO trading_strategy_configs (
                id, user_id, config_name, base_strategy_type, description,
                is_active_paper_mode, is_active_real_mode, parameters,
                applicability_rules, ai_analysis_profile_id, risk_parameters_override,
                version, parent_config_id, performance_metrics, market_condition_filters,
                activation_schedule, depends_on_strategies, sharing_metadata,
                created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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
                updated_at = ?;
            """
            
            try:
                async with self.sqlite_conn.cursor() as cur:
                    now_utc = datetime.now(timezone.utc).isoformat()
                    await cur.execute(
                        query,
                        (
                            data_to_save['id'], data_to_save['user_id'], data_to_save['config_name'], data_to_save['base_strategy_type'], data_to_save['description'],
                            data_to_save['is_active_paper_mode'], data_to_save['is_active_real_mode'], data_to_save['parameters'],
                            data_to_save['applicability_rules'], data_to_save['ai_analysis_profile_id'], data_to_save['risk_parameters_override'],
                            data_to_save['version'], data_to_save['parent_config_id'], data_to_save['performance_metrics'], data_to_save['market_condition_filters'],
                            data_to_save['activation_schedule'], data_to_save['depends_on_strategies'], data_to_save['sharing_metadata'],
                            data_to_save['created_at'].isoformat() if data_to_save.get('created_at') else now_utc, # created_at
                            now_utc # updated_at
                        )
                    )
                    await self.sqlite_conn.commit()
                    logger.info(f"Configuración de estrategia {data_to_save['id']} guardada/actualizada exitosamente en SQLite.")
            except Exception as e:
                logger.error(f"Error al guardar/actualizar configuración de estrategia en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None
            
            query = """
            INSERT INTO trading_strategy_configs (
                id, user_id, config_name, base_strategy_type, description,
                is_active_paper_mode, is_active_real_mode, parameters,
                applicability_rules, ai_analysis_profile_id, risk_parameters_override,
                version, parent_config_id, performance_metrics, market_condition_filters,
                activation_schedule, depends_on_strategies, sharing_metadata,
                created_at, updated_at
            ) VALUES (
                %(id)s, %(user_id)s, %(config_name)s, %(base_strategy_type)s, %(description)s,
                %(is_active_paper_mode)s, %(is_active_real_mode)s, %(parameters)s,
                %(applicability_rules)s, %(ai_analysis_profile_id)s, %(risk_parameters_override)s,
                %(version)s, %(parent_config_id)s, %(performance_metrics)s, %(market_condition_filters)s,
                %(activation_schedule)s, %(depends_on_strategies)s, %(sharing_metadata)s,
                %(created_at)s, %(updated_at)s
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
                async with self.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        strategy_data['user_id'] = self.fixed_user_id
                        await cur.execute(SQL(query), strategy_data)
            except Exception as e:
                logger.error(f"Database error saving strategy: {e}")
                raise

    async def get_strategy_config_by_id(self, strategy_id: UUID) -> Optional[Dict[str, Any]]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            query = "SELECT * FROM trading_strategy_configs WHERE id = ? AND user_id = ?;"
            
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(strategy_id), str(self.fixed_user_id)))
                    record = await cur.fetchone()
                    if record:
                        config_dict = dict(record)
                        json_fields = [
                            'parameters', 'applicability_rules', 'risk_parameters_override',
                            'performance_metrics', 'market_condition_filters', 'activation_schedule',
                            'depends_on_strategies', 'sharing_metadata'
                        ]
                        for field in json_fields:
                            if field in config_dict and isinstance(config_dict[field], str):
                                try:
                                    config_dict[field] = json.loads(config_dict[field])
                                except json.JSONDecodeError:
                                    logger.warning(f"Error al decodificar JSON para {field} en configuración de estrategia.")
                        return config_dict
                return None
            except Exception as e:
                logger.error(f"Database error getting strategy {strategy_id} in SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            
            query = SQL("SELECT * FROM trading_strategy_configs WHERE id = %s AND user_id = %s;")
            
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (strategy_id, self.fixed_user_id))
                        return await cur.fetchone()
            except Exception as e:
                logger.error(f"Database error getting strategy {strategy_id} (psycopg_pool): {e}")
                raise

    async def list_strategy_configs_by_user(self) -> List[Dict[str, Any]]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            query = "SELECT * FROM trading_strategy_configs WHERE user_id = ? ORDER BY created_at DESC;"
            
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(self.fixed_user_id),))
                    records = await cur.fetchall()
                    
                    result_list = []
                    json_fields = [
                        'parameters', 'applicability_rules', 'risk_parameters_override',
                        'performance_metrics', 'market_condition_filters', 'activation_schedule',
                        'depends_on_strategies', 'sharing_metadata'
                    ]
                    for record in records:
                        config_dict = dict(record)
                        for field in json_fields:
                            if field in config_dict and isinstance(config_dict[field], str):
                                try:
                                    config_dict[field] = json.loads(config_dict[field])
                                except json.JSONDecodeError:
                                    logger.warning(f"Error al decodificar JSON para {field} en configuración de estrategia.")
                        result_list.append(config_dict)
                    return result_list
            except Exception as e:
                logger.error(f"Database error listing strategies for user {self.fixed_user_id} in SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            
            query = SQL("SELECT * FROM trading_strategy_configs WHERE user_id = %s ORDER BY created_at DESC;")
            
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(query, (self.fixed_user_id,))
                        return await cur.fetchall()
            except Exception as e:
                logger.error(f"Database error listing strategies for user {self.fixed_user_id} (psycopg_pool): {e}")
                raise

    async def delete_strategy_config(self, strategy_id: UUID) -> bool:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            query = "DELETE FROM trading_strategy_configs WHERE id = ? AND user_id = ?;"
            
            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(query, (str(strategy_id), str(self.fixed_user_id)))
                    await self.sqlite_conn.commit()
                    return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Database error deleting strategy {strategy_id} in SQLite: {e}")
                raise
        else:
            assert self.pool is not None
            
            query = SQL("DELETE FROM trading_strategy_configs WHERE id = %s AND user_id = %s;")
            
            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute(query, (strategy_id, self.fixed_user_id))
                        return cur.rowcount > 0
            except Exception as e:
                logger.error(f"Database error deleting strategy {strategy_id} (psycopg_pool): {e}")
                raise

    async def get_trades_with_filters(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Trade]:
        await self._check_pool()
        
        if self._is_sqlite:
            if not self.sqlite_conn:
                raise ValueError("Conexión SQLite no establecida.")
            
            sqlite_query_parts: List[str] = ["SELECT data FROM trades"]
            sqlite_where_clauses: List[str] = []
            sqlite_params: List[Any] = []

            # Siempre filtrar por user_id
            sqlite_where_clauses.append("user_id = ?")
            sqlite_params.append(str(self.fixed_user_id))

            for key, value in filters.items():
                if value is not None:
                    if key.endswith("_gte"):
                        sqlite_where_clauses.append(f"{key[:-4]} >= ?")
                        sqlite_params.append(value.isoformat() if isinstance(value, datetime) else value)
                    elif key.endswith("_lte"):
                        sqlite_where_clauses.append(f"{key[:-4]} <= ?")
                        sqlite_params.append(value.isoformat() if isinstance(value, datetime) else value)
                    else:
                        sqlite_where_clauses.append(f"{key} = ?")
                        sqlite_params.append(value)
            
            if sqlite_where_clauses:
                sqlite_query_parts.append("WHERE")
                sqlite_query_parts.append(" AND ".join(sqlite_where_clauses))

            sqlite_query_parts.append("ORDER BY created_at DESC LIMIT ? OFFSET ?")
            sqlite_params.extend([limit, offset])

            final_sqlite_query = " ".join(sqlite_query_parts)

            try:
                async with self.sqlite_conn.cursor() as cur:
                    await cur.execute(final_sqlite_query, tuple(sqlite_params))
                    records = await cur.fetchall()
                    return [Trade(**json.loads(record['data'])) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener trades con filtros {filters} en SQLite: {e}", exc_info=True)
                raise
        else:
            assert self.pool is not None

            psycopg_query_parts: List[Composable] = [SQL("SELECT data FROM trades")]
            psycopg_where_clauses: List[Composable] = []
            psycopg_params: List[Any] = []

            # Siempre filtrar por user_id
            psycopg_where_clauses.append(SQL("user_id = %s"))
            psycopg_params.append(self.fixed_user_id)

            for key, value in filters.items():
                if value is not None:
                    column_name = key
                    operator = SQL("=")
                    if key.endswith("_gte"):
                        column_name = key[:-4]
                        operator = SQL(">=")
                    elif key.endswith("_lte"):
                        column_name = key[:-4]
                        operator = SQL("<=")

                    psycopg_where_clauses.append(
                        SQL("{} {} %s").format(Identifier(column_name), operator)
                    )
                    psycopg_params.append(value)
            
            if psycopg_where_clauses:
                psycopg_query_parts.append(SQL("WHERE"))
                psycopg_query_parts.append(SQL(" AND ").join(psycopg_where_clauses))

            psycopg_query_parts.append(SQL("ORDER BY created_at DESC LIMIT %s OFFSET %s"))
            psycopg_params.extend([limit, offset])

            final_psycopg_query = SQL(" ").join(psycopg_query_parts)

            try:
                async with self.pool.connection() as conn:
                    async with conn.cursor(row_factory=dict_row) as cur:
                        await cur.execute(final_psycopg_query, tuple(psycopg_params))
                        records = await cur.fetchall()
                        return [Trade(**record['data']) for record in records]
            except Exception as e:
                logger.error(f"Error al obtener trades con filtros {filters} (psycopg_pool): {e}", exc_info=True)
                raise
