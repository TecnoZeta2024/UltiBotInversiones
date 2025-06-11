import asyncio
import sys
import psycopg
from psycopg_pool import AsyncConnectionPool
import logging
import os
from urllib.parse import urlparse, unquote
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier, Literal, Composed, Composable
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
import json

# Solución para Windows ProactorEventLoop con psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.ultibot_backend.app_config import settings
from src.ultibot_backend.core.domain_models.opportunity_models import Opportunity, OpportunityStatus
from src.ultibot_backend.core.domain_models.trade_models import Trade, TradeOrderDetails
from src.ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig
from src.shared.data_types import APICredential, ServiceName, Notification, MarketData
from src.ultibot_backend.core.domain_models.user_configuration_models import ScanPreset, MarketScanConfiguration

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass

# Definir type hints para uso en el módulo
OpportunityTypeHint = Opportunity
OpportunityStatusTypeHint = OpportunityStatus


class SupabasePersistenceService:
    def __init__(self):
        self.pool: Optional[AsyncConnectionPool] = None
        self.db_url: Optional[str] = os.getenv("DATABASE_URL")
        if not self.db_url:
            logger.error("DATABASE_URL no se encontró en las variables de entorno durante la inicialización.")
        self.fixed_user_id = settings.FIXED_USER_ID

    async def connect(self):
        if self.pool and not self.pool.closed:
            logger.info("El pool de conexiones ya está activo.")
            return

        if not self.db_url:
            logger.error("DATABASE_URL no está configurada. No se puede inicializar el pool de conexiones.")
            raise ValueError("DATABASE_URL no está configurada en las variables de entorno.")

        try:
            min_size = getattr(settings, "DB_POOL_MIN_SIZE", 2)
            max_size = getattr(settings, "DB_POOL_MAX_SIZE", 10)
            
            # CORRECTO: Los parámetros de SSL deben ser parte de la cadena de conexión.
            conn_str = f"{self.db_url}?sslmode=verify-full&sslrootcert=supabase/prod-ca-2021.crt"
            
            self.pool = AsyncConnectionPool(
                conninfo=conn_str,
                min_size=min_size,
                max_size=max_size,
                name="supabase_pool"
            )
            await self.pool.open()
            logger.info(f"Pool de conexiones a Supabase (psycopg_pool) establecido exitosamente. Min: {min_size}, Max: {max_size}")
        except Exception as e:
            logger.error(f"Error al establecer el pool de conexiones a Supabase (psycopg_pool): {e}")
            if isinstance(e, psycopg.Error) and hasattr(e, 'diag') and e.diag:
                 logger.error(f"Detalles del error de PSQL (diag): {e.diag.message_primary}")
            self.pool = None
            raise

    async def disconnect(self):
        if self.pool and not self.pool.closed:
            await self.pool.close()
            logger.info("Pool de conexiones a Supabase (psycopg_pool) cerrado.")
            self.pool = None

    async def _check_pool(self):
        """Verifica la salud del pool y lo reconecta si es necesario."""
        if not self.pool or self.pool.closed:
            logger.warning("El pool de conexiones está cerrado o no existe. Intentando reconectar...")
            await self.connect()
        
        assert self.pool is not None, "Fallo crítico al reconectar el pool."
        
        try:
            await self.pool.check()
        except Exception as e:
            logger.error(f"Fallo en la comprobación de salud del pool. Intentando reconectar. Error: {e}")
            await self.disconnect()
            await self.connect()
            assert self.pool is not None, "Fallo crítico al reconectar el pool después de un check fallido."

    async def save_market_data(self, market_data_list: List[MarketData]):
        await self._check_pool()
        assert self.pool is not None

        query = SQL("COPY market_data (symbol, timestamp, open, high, low, close, volume) FROM STDIN")

        async def data_generator():
            for data in market_data_list:
                yield f"{data.symbol}\t{data.timestamp.isoformat()}\t{data.open}\t{data.high}\t{data.low}\t{data.close}\t{data.volume}\n".encode('utf-8')

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    async with cur.copy(query) as copy:
                        async for chunk in data_generator():
                            await copy.write(chunk)
            logger.info(f"Se guardaron {len(market_data_list)} registros de datos de mercado.")
        except Exception as e:
            logger.error(f"Error al guardar datos de mercado con COPY: {e}", exc_info=True)
            raise

    async def get_market_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[MarketData]:
        await self._check_pool()
        assert self.pool is not None

        query = SQL("SELECT * FROM market_data WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s ORDER BY timestamp ASC;")

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (symbol, start_date, end_date))
                    records = await cur.fetchall()
                    return [MarketData(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener datos de mercado para {symbol}: {e}", exc_info=True)
            raise

    async def get_market_data_from_db(self, symbol: str, limit: int) -> List[MarketData]:
        """
        Obtiene los últimos N registros de datos de mercado para un símbolo desde la BD.
        """
        await self._check_pool()
        assert self.pool is not None

        query = SQL("""
            SELECT * FROM market_data 
            WHERE symbol = %s 
            ORDER BY timestamp DESC 
            LIMIT %s;
        """)

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (symbol, limit))
                    records = await cur.fetchall()
                    # Los datos se devuelven en orden descendente, los invertimos para que el más antiguo sea el primero
                    return [MarketData(**record) for record in reversed(records)]
        except Exception as e:
            logger.error(f"Error al obtener datos de mercado desde la BD para {symbol}: {e}", exc_info=True)
            raise

    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[Opportunity]:
        await self._check_pool()
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

    async def get_user_configuration(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        await self._check_pool()
        assert self.pool is not None
        query = SQL("SELECT * FROM user_configurations WHERE user_id = %s;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (user_id,))
                    record = await cur.fetchone()
                    if record:
                        return dict(record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener configuración de usuario para {user_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def upsert_user_configuration(self, config_data: Dict[str, Any]):
        await self._check_pool()
        assert self.pool is not None
        from psycopg import sql
        import json
        
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
        assert self.pool is not None

        query = SQL("SELECT * FROM trades WHERE user_id = %s AND position_status = %s AND mode = %s;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (self.fixed_user_id, status, mode))
                    records = await cur.fetchall()
                    return [Trade(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener trades para usuario {self.fixed_user_id} con estado {status} y modo {mode}: {e}", exc_info=True)
            raise

    async def upsert_trade(self, trade_data: Dict[str, Any]):
        await self._check_pool()
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
            logger.info(f"Trade {trade_data['id']} guardado/actualizado exitosamente.")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar trade {trade_data['id']}: {e}", exc_info=True)
            raise

    async def get_closed_trades_count(self, is_real_trade: bool) -> int:
        await self._check_pool()
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
        assert self.pool is not None

        query = SQL("SELECT * FROM opportunities WHERE user_id = %s AND status = %s;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (self.fixed_user_id, status.value))
                    records = await cur.fetchall()
                
                return [Opportunity(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener oportunidades por estado para user {self.fixed_user_id}, status={status.value} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_all_trades_for_user(self, mode: Optional[str] = None) -> List[Trade]:
        await self._check_pool()
        assert self.pool is not None

        query_base = SQL("SELECT * FROM trades WHERE user_id = %s")
        params_list: List[Any] = [self.fixed_user_id]
        
        if mode:
            query_base = Composed([query_base, SQL(" AND mode = %s")])
            params_list.append(mode)
            
        final_query = Composed([query_base, SQL(" ORDER BY created_at DESC;")])
        
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(final_query, tuple(params_list))
                    records = await cur.fetchall()
                return [Trade(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener todos los trades para el usuario {self.fixed_user_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_closed_trades(self, filters: Dict[str, Any], start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        await self._check_pool()
        assert self.pool is not None
        
        params: List[Any] = [self.fixed_user_id]
        query_parts = [SQL("SELECT * FROM trades WHERE user_id = %s AND position_status = 'closed'")]

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
                return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener trades cerrados con filtros {filters} (psycopg_pool): {e}", exc_info=True)
            raise

    async def update_opportunity_analysis(self, opportunity_id: UUID, status: OpportunityStatus, ai_analysis: Optional[str] = None, confidence_score: Optional[float] = None, suggested_action: Optional[str] = None, status_reason: Optional[str] = None) -> Optional[Opportunity]:
        await self._check_pool()
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
        assert self.pool is not None
        
        query = SQL("SELECT * FROM trading_strategy_configs WHERE id = %s AND user_id = %s;")
        
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (strategy_id, self.fixed_user_id))
                    return await cur.fetchone()
        except Exception as e:
            logger.error(f"Database error getting strategy {strategy_id}: {e}")
            raise

    async def list_strategy_configs_by_user(self) -> List[Dict[str, Any]]:
        await self._check_pool()
        assert self.pool is not None
        
        query = SQL("SELECT * FROM trading_strategy_configs WHERE user_id = %s ORDER BY created_at DESC;")
        
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (self.fixed_user_id,))
                    return await cur.fetchall()
        except Exception as e:
            logger.error(f"Database error listing strategies for user {self.fixed_user_id}: {e}")
            raise

    async def delete_strategy_config(self, strategy_id: UUID) -> bool:
        await self._check_pool()
        assert self.pool is not None
        
        query = SQL("DELETE FROM trading_strategy_configs WHERE id = %s AND user_id = %s;")
        
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, (strategy_id, self.fixed_user_id))
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Database error deleting strategy {strategy_id}: {e}")
            raise

    async def get_trades_with_filters(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Trade]:
        await self._check_pool()
        assert self.pool is not None

        query_parts: List[Composable] = [SQL("SELECT * FROM trades")]
        where_clauses: List[Composable] = []
        params: List[Any] = []

        for key, value in filters.items():
            if value is not None:
                if key.endswith("_gte"):
                    where_clauses.append(SQL("{} >= %s").format(Identifier(key[:-4])))
                    params.append(value)
                elif key.endswith("_lte"):
                    where_clauses.append(SQL("{} <= %s").format(Identifier(key[:-4])))
                    params.append(value)
                else:
                    where_clauses.append(SQL("{} = %s").format(Identifier(key)))
                    params.append(value)
        
        if where_clauses:
            query_parts.append(SQL("WHERE"))
            query_parts.append(SQL(" AND ").join(where_clauses))

        query_parts.append(SQL("ORDER BY created_at DESC LIMIT %s OFFSET %s"))
        params.extend([limit, offset])

        final_query = SQL(" ").join(query_parts)

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(final_query, tuple(params))
                    records = await cur.fetchall()
                    return [Trade(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener trades con filtros {filters}: {e}", exc_info=True)
            raise

    # --- Métodos para Scan Presets ---
    async def list_scan_presets(self, include_system: bool = True) -> List[Dict[str, Any]]:
        await self._check_pool()
        assert self.pool is not None

        query_parts = [SQL("SELECT * FROM scan_presets WHERE user_id = %s")]
        params = [self.fixed_user_id]

        if include_system:
            query_parts.append(SQL("OR is_system_preset = TRUE"))
        
        final_query = SQL(" ").join(query_parts) + SQL(" ORDER BY created_at DESC;")

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(final_query, tuple(params))
                    records = await cur.fetchall()
                    return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error al listar presets de escaneo para usuario {self.fixed_user_id}: {e}", exc_info=True)
            raise

    async def create_scan_preset(self, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        await self._check_pool()
        assert self.pool is not None

        # Asegurarse de que el ID se genere si no está presente
        if 'id' not in preset_data or not preset_data['id']:
            preset_data['id'] = str(UUID(int=0)) # Placeholder, Supabase debería generar uno real

        query = """
        INSERT INTO scan_presets (
            id, user_id, name, description, category, recommended_strategies,
            market_scan_configuration, is_system_preset, is_active,
            usage_count, success_rate, created_at, updated_at
        ) VALUES (
            %(id)s, %(user_id)s, %(name)s, %(description)s, %(category)s, %(recommended_strategies)s,
            %(market_scan_configuration)s, %(is_system_preset)s, %(is_active)s,
            %(usage_count)s, %(success_rate)s, %(created_at)s, %(updated_at)s
        ) RETURNING *;
        """
        
        # Preparar datos para la inserción
        data_to_insert = preset_data.copy()
        data_to_insert['user_id'] = self.fixed_user_id
        data_to_insert['market_scan_configuration'] = Jsonb(data_to_insert.get('market_scan_configuration', {}))
        data_to_insert['recommended_strategies'] = data_to_insert.get('recommended_strategies')
        data_to_insert['created_at'] = datetime.now(timezone.utc)
        data_to_insert['updated_at'] = datetime.now(timezone.utc)
        data_to_insert['usage_count'] = data_to_insert.get('usage_count', 0)
        data_to_insert['success_rate'] = data_to_insert.get('success_rate')

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL(query), data_to_insert)
                    record = await cur.fetchone()
                    if record:
                        return dict(record)
            raise ValueError("No se pudo crear el preset de escaneo.")
        except Exception as e:
            logger.error(f"Error al crear preset de escaneo: {e}", exc_info=True)
            raise

    async def update_scan_preset(self, preset_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
        await self._check_pool()
        assert self.pool is not None

        query = """
        UPDATE scan_presets
        SET
            name = %(name)s,
            description = %(description)s,
            category = %(category)s,
            recommended_strategies = %(recommended_strategies)s,
            market_scan_configuration = %(market_scan_configuration)s,
            is_system_preset = %(is_system_preset)s,
            is_active = %(is_active)s,
            usage_count = %(usage_count)s,
            success_rate = %(success_rate)s,
            updated_at = timezone('utc'::text, now())
        WHERE id = %(id)s AND user_id = %(user_id)s
        RETURNING *;
        """
        
        data_to_update = preset_data.copy()
        data_to_update['id'] = preset_id
        data_to_update['user_id'] = self.fixed_user_id
        data_to_update['market_scan_configuration'] = Jsonb(data_to_update.get('market_scan_configuration', {}))
        data_to_update['recommended_strategies'] = data_to_update.get('recommended_strategies')
        data_to_update['usage_count'] = data_to_update.get('usage_count', 0)
        data_to_update['success_rate'] = data_to_update.get('success_rate')

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL(query), data_to_update)
                    record = await cur.fetchone()
                    if record:
                        return dict(record)
            raise ValueError(f"No se pudo actualizar el preset de escaneo con ID {preset_id}.")
        except Exception as e:
            logger.error(f"Error al actualizar preset de escaneo {preset_id}: {e}", exc_info=True)
            raise

    async def delete_scan_preset(self, preset_id: str) -> bool:
        await self._check_pool()
        assert self.pool is not None

        query = SQL("DELETE FROM scan_presets WHERE id = %s AND user_id = %s AND is_system_preset = FALSE;")
        
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, (preset_id, self.fixed_user_id))
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error al eliminar preset de escaneo {preset_id}: {e}", exc_info=True)
            raise

    async def get_scan_preset_by_id(self, preset_id: str) -> Optional[Dict[str, Any]]:
        await self._check_pool()
        assert self.pool is not None

        query = SQL("SELECT * FROM scan_presets WHERE id = %s AND (user_id = %s OR is_system_preset = TRUE);")
        
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (preset_id, self.fixed_user_id))
                    record = await cur.fetchone()
                    if record:
                        return dict(record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener preset de escaneo por ID {preset_id}: {e}", exc_info=True)
            raise

    # --- Métodos para Market Scan Configurations (no presets) ---
    async def get_market_scan_configuration(self, config_id: UUID) -> Optional[Dict[str, Any]]:
        await self._check_pool()
        assert self.pool is not None
        query = SQL("SELECT * FROM market_scan_configurations WHERE id = %s AND user_id = %s;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (config_id, self.fixed_user_id))
                    record = await cur.fetchone()
                    if record:
                        return dict(record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener configuración de escaneo de mercado por ID {config_id}: {e}", exc_info=True)
            raise

    async def upsert_market_scan_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        await self._check_pool()
        assert self.pool is not None

        config_id = config_data.get('id')
        is_update = bool(config_id)

        if is_update:
            # Lógica de actualización
            query = """
            UPDATE market_scan_configurations SET
                name = %(name)s,
                description = %(description)s,
                min_price_change_24h_percent = %(min_price_change_24h_percent)s,
                max_price_change_24h_percent = %(max_price_change_24h_percent)s,
                volume_filter_type = %(volume_filter_type)s,
                min_volume_24h_usd = %(min_volume_24h_usd)s,
                market_cap_ranges = %(market_cap_ranges)s,
                trend_direction = %(trend_direction)s,
                min_rsi = %(min_rsi)s,
                max_rsi = %(max_rsi)s,
                max_results = %(max_results)s,
                scan_interval_minutes = %(scan_interval_minutes)s,
                allowed_quote_currencies = %(allowed_quote_currencies)s,
                is_active = %(is_active)s,
                updated_at = timezone('utc'::text, now())
            WHERE id = %(id)s AND user_id = %(user_id)s
            RETURNING *;
            """
        else:
            # Lógica de inserción
            config_data['id'] = str(uuid4())
            query = """
            INSERT INTO market_scan_configurations (
                id, user_id, name, description, min_price_change_24h_percent,
                max_price_change_24h_percent, volume_filter_type, min_volume_24h_usd,
                market_cap_ranges, trend_direction, min_rsi, max_rsi,
                max_results, scan_interval_minutes, allowed_quote_currencies,
                is_active, created_at, updated_at
            ) VALUES (
                %(id)s, %(user_id)s, %(name)s, %(description)s, %(min_price_change_24h_percent)s,
                %(max_price_change_24h_percent)s, %(volume_filter_type)s, %(min_volume_24h_usd)s,
                %(market_cap_ranges)s, %(trend_direction)s, %(min_rsi)s, %(max_rsi)s,
                %(max_results)s, %(scan_interval_minutes)s, %(allowed_quote_currencies)s,
                %(is_active)s, %(created_at)s, %(updated_at)s
            ) RETURNING *;
            """
            config_data['created_at'] = datetime.now(timezone.utc)

        data_to_process = config_data.copy()
        data_to_process['user_id'] = self.fixed_user_id
        data_to_process['updated_at'] = datetime.now(timezone.utc)
        
        # Convertir listas a JSONB si es necesario
        for key in ['market_cap_ranges', 'allowed_quote_currencies']:
            if key in data_to_process and isinstance(data_to_process[key], list):
                data_to_process[key] = json.dumps(data_to_process[key])

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL(query), data_to_process)
                    record = await cur.fetchone()
                    if record:
                        return dict(record)
            raise ValueError("No se pudo guardar/actualizar la configuración de escaneo de mercado.")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar configuración de escaneo de mercado: {e}", exc_info=True)
            raise

    async def delete_market_scan_configuration(self, config_id: UUID) -> bool:
        await self._check_pool()
        assert self.pool is not None
        query = SQL("DELETE FROM market_scan_configurations WHERE id = %s AND user_id = %s;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, (config_id, self.fixed_user_id))
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error al eliminar configuración de escaneo de mercado {config_id}: {e}", exc_info=True)
            raise

    async def list_market_scan_configurations(self) -> List[Dict[str, Any]]:
        await self._check_pool()
        assert self.pool is not None
        query = SQL("SELECT * FROM market_scan_configurations WHERE user_id = %s ORDER BY created_at DESC;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (self.fixed_user_id,))
                    records = await cur.fetchall()
                    return [dict(record) for record in records]
        except Exception as e:
            logger.error(f"Error al listar configuraciones de escaneo de mercado para usuario {self.fixed_user_id}: {e}", exc_info=True)
            raise
