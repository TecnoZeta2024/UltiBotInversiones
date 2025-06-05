import asyncio
import sys
import psycopg
from psycopg_pool import AsyncConnectionPool # Importar AsyncConnectionPool

# Solución para Windows ProactorEventLoop con psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from psycopg.rows import dict_row # Usar dict_row, se aplica al cursor
from psycopg.conninfo import make_conninfo
from src.ultibot_backend.app_config import settings
import logging
import os # Importar os
from urllib.parse import urlparse, unquote
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID
from src.shared.data_types import APICredential, ServiceName, Notification, Opportunity, OpportunityStatus, Trade, TradeOrderDetails # Importar Trade y TradeOrderDetails
from datetime import datetime, timezone
from psycopg.sql import SQL, Identifier, Literal, Composed, Composable # Importar SQL y otros componentes necesarios

logger = logging.getLogger(__name__)

if TYPE_CHECKING: # Bloque para type hints que evitan importaciones circulares en runtime
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
            # Se registrará el error y connect() fallará si self.db_url sigue siendo None.

    async def connect(self):
        if self.pool and not self.pool.closed:
            logger.info("El pool de conexiones ya está activo.")
            return

        if not self.db_url:
            logger.error("DATABASE_URL no está configurada. No se puede inicializar el pool de conexiones.")
            raise ValueError("DATABASE_URL no está configurada en las variables de entorno.")

        try:
            # Usar min_size y max_size de settings si están disponibles, sino valores por defecto.
            min_size = getattr(settings, "DB_POOL_MIN_SIZE", 2)
            max_size = getattr(settings, "DB_POOL_MAX_SIZE", 10)
            
            conninfo = make_conninfo(self.db_url, sslmode='verify-full', sslrootcert='supabase/prod-ca-2021.crt')
            
            self.pool = AsyncConnectionPool(
                conninfo=conninfo,
                min_size=min_size,
                max_size=max_size,
                name="supabase_pool" 
            )
            await self.pool.open() 
            await self.pool.wait()
            logger.info(f"Pool de conexiones a Supabase (psycopg_pool) establecido exitosamente. Min: {min_size}, Max: {max_size}")
        except Exception as e:
            logger.error(f"Error al establecer el pool de conexiones a Supabase (psycopg_pool): {e}")
            if isinstance(e, psycopg.Error) and hasattr(e, 'diag') and e.diag: # type: ignore
                 logger.error(f"Detalles del error de PSQL (diag): {e.diag.message_primary}") # type: ignore
            self.pool = None 
            raise

    async def disconnect(self):
        if self.pool and not self.pool.closed:
            await self.pool.close()
            logger.info("Pool de conexiones a Supabase (psycopg_pool) cerrado.")
            self.pool = None

    async def test_connection(self) -> bool:
        if not self.pool:
            await self.connect()
        
        assert self.pool is not None, "Connection pool must be established"
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL("SELECT 1 AS result;"))
                    result = await cur.fetchone()
                    if result and result.get('result') == 1:
                        logger.info("Conexión de prueba a la base de datos Supabase (psycopg_pool) exitosa.")
                        return True
                    logger.warning(f"Conexión de prueba a Supabase (psycopg_pool) devolvió: {result}")
                    return False
        except Exception as e:
            logger.error(f"Error en la conexión de prueba a la base de datos Supabase (psycopg_pool): {e}")
            return False

    async def save_credential(self, credential: APICredential) -> APICredential:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
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
                            credential.id, credential.user_id, credential.service_name.value, credential.credential_label, # Usar .value para el Enum
                            credential.encrypted_api_key, credential.encrypted_api_secret, credential.encrypted_other_details,
                            credential.status, credential.last_verified_at, credential.permissions, credential.permissions_checked_at,
                            credential.expires_at, credential.rotation_reminder_policy_days, credential.usage_count, credential.last_used_at,
                            credential.purpose_description, credential.tags, credential.notes, credential.created_at, credential.updated_at
                        )
                    )
                    record = await cur.fetchone()
                    # commit es manejado por el pool context manager
                    if record:
                        return APICredential(**record)
            raise ValueError("No se pudo guardar/actualizar la credencial y obtener el registro de retorno (psycopg_pool).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar credencial (psycopg_pool): {e}")
            # rollback es manejado por el pool context manager
            raise

    async def get_credentials_by_service(self, user_id: UUID, service_name: ServiceName) -> List[APICredential]:
        """Recupera todas las credenciales para un usuario y servicio específicos."""
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("SELECT * FROM api_credentials WHERE user_id = %s AND service_name = %s ORDER BY created_at ASC;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (user_id, service_name.value))
                    records = await cur.fetchall()
                    return [APICredential(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener credenciales por servicio para usuario {user_id} y servicio {service_name.value} (psycopg_pool): {e}")
            raise

    async def get_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("SELECT * FROM api_credentials WHERE id = %s;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (credential_id,))
                    record = await cur.fetchone()
                    if record:
                        return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener credencial por ID (psycopg_pool): {e}")
            raise

    async def get_credential_by_service_label(self, user_id: UUID, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("""
        SELECT * FROM api_credentials 
        WHERE user_id = %s AND service_name = %s AND credential_label = %s;
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (user_id, service_name.value, credential_label))
                    record = await cur.fetchone()
                    if record:
                        return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener credencial por servicio y etiqueta (psycopg_pool): {e}")
            raise

    async def update_credential_status(self, credential_id: UUID, new_status: str, last_verified_at: Optional[datetime] = None) -> Optional[APICredential]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("""
        UPDATE api_credentials 
        SET status = %s, last_verified_at = %s, updated_at = timezone('utc'::text, now())
        WHERE id = %s
        RETURNING *;
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (new_status, last_verified_at, credential_id))
                    record = await cur.fetchone()
                    if record:
                        return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar estado de credencial (psycopg_pool): {e}")
            raise

    async def delete_credential(self, credential_id: UUID) -> bool:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("DELETE FROM api_credentials WHERE id = %s;")
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (credential_id,))
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error al eliminar credencial (psycopg_pool): {e}")
            raise

    async def get_user_configuration(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
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

    async def upsert_user_configuration(self, user_id: UUID, config_data: Dict[str, Any]):
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
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
        insert_values_dict['user_id'] = user_id

        json_columns = [
            "notification_preferences", "watchlists", "favorite_pairs", "risk_profile_settings",
            "real_trading_settings", "ai_strategy_configurations", "ai_analysis_confidence_thresholds",
            "mcp_server_preferences", "dashboard_layout_profiles", "dashboard_layout_config", "cloud_sync_preferences"
        ]

        for col in json_columns:
            if col in insert_values_dict and insert_values_dict[col] is not None and not isinstance(insert_values_dict[col], str):
                insert_values_dict[col] = json.dumps(insert_values_dict[col])

        for k, v in insert_values_dict.items():
            logger.debug(f"upsert_user_configuration: {k} type={type(v)} value={v}")

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
            for idx, val in enumerate(values):
                if isinstance(val, (dict, list)):
                    raise TypeError(f"Non-serialized value at position {idx}: {val}")
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, values)
            logger.info(f"Configuración de usuario para {user_id} guardada/actualizada exitosamente (psycopg_pool).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar configuración de usuario para {user_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def update_credential_permissions(self, credential_id: UUID, permissions: List[str], permissions_checked_at: datetime) -> Optional[APICredential]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("""
        UPDATE api_credentials 
        SET permissions = %s, permissions_checked_at = %s, updated_at = timezone('utc'::text, now())
        WHERE id = %s
        RETURNING *;
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (permissions, permissions_checked_at, credential_id))
                    record = await cur.fetchone()
                    if record:
                        return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar permisos de credencial (psycopg_pool): {e}")
            raise

    async def save_notification(self, notification: Notification) -> Notification:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
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
                            notification.id, notification.userId, notification.eventType,
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

    async def get_notification_history(self, user_id: UUID, limit: int = 50) -> List[Notification]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("""
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (user_id, limit))
                    records = await cur.fetchall()
            return [Notification(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener historial de notificaciones para el usuario {user_id} (psycopg_pool): {e}")
            raise

    async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query = SQL("""
        UPDATE notifications
        SET status = 'read', read_at = timezone('utc'::text, now())
        WHERE id = %s AND user_id = %s
        RETURNING *;
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (notification_id, user_id))
                    record = await cur.fetchone()
                    if record:
                        return Notification(**record)
            return None
        except Exception as e:
            logger.error(f"Error al marcar notificación {notification_id} como leída para el usuario {user_id} (psycopg_pool): {e}")
            raise

    async def execute_test_delete(self, user_id_str: str):
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        try:
            user_uuid = UUID(user_id_str)
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL("DELETE FROM user_configurations WHERE user_id = %s;"), (user_uuid,))
            logger.info(f"Datos de prueba para user_id {user_id_str} eliminados (psycopg_pool).")
        except Exception as e:
            logger.error(f"Error al eliminar datos de prueba para user_id {user_id_str} (psycopg_pool): {e}")

    async def execute_test_insert(self, user_id_str: str, theme: str):
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        try:
            user_uuid = UUID(user_id_str)
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        SQL("""
                        INSERT INTO user_configurations (user_id, selected_theme)
                        VALUES (%s, %s);
                        """),
                        (user_uuid, theme)
                    )
            logger.info(f"Inserción de prueba para user_id {user_id_str} exitosa (psycopg_pool).")
        except Exception as e:
            logger.error(f"Error en inserción de prueba para user_id {user_id_str} (psycopg_pool): {e}")
            raise

    async def fetchrow_test_select(self, user_id_str: str) -> Optional[Dict[str, Any]]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        try:
            user_uuid = UUID(user_id_str)
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        SQL("SELECT user_id, selected_theme FROM user_configurations WHERE user_id = %s;"),
                        (user_uuid,)
                    )
                    record = await cur.fetchone()
                    return record
        except Exception as e:
            logger.error(f"Error en lectura de prueba para user_id {user_id_str} (psycopg_pool): {e}")
            raise
            
    async def execute_test_insert_config(self, params: tuple):
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        insert_query = SQL("""
        INSERT INTO user_configurations (user_id, selected_theme, enable_telegram_notifications, default_paper_trading_capital, notification_preferences)
        VALUES (%s, %s, %s, %s, %s::jsonb)
        RETURNING id, user_id, selected_theme;
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(insert_query, params)
                    record = await cur.fetchone()
                    return record
        except Exception as e:
            logger.error(f"Error en execute_test_insert_config (psycopg_pool): {e}")
            raise

    async def fetchrow_test_select_config(self, user_id_str: str) -> Optional[Dict[str, Any]]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        select_query = SQL("SELECT user_id, selected_theme, default_paper_trading_capital FROM user_configurations WHERE user_id = %s;")
        try:
            user_uuid = UUID(user_id_str)
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(select_query, (user_uuid,))
                    record = await cur.fetchone()
                    return record
        except Exception as e:
            logger.error(f"Error en fetchrow_test_select_config (psycopg_pool): {e}")
            raise

    async def execute_raw_sql(self, query: str, params: Optional[tuple] = None):
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    # Para SQL completamente crudo donde 'query' es la cadena SQL completa
                    # y 'params' son los valores para los placeholders en esa cadena.
                    await cur.execute(SQL(query), params) # type: ignore[arg-type]
        except Exception as e:
            logger.error(f"Error ejecutando SQL crudo (psycopg_pool): {query} con params {params} - {e}")
            raise

    async def upsert_opportunity(self, user_id: UUID, opportunity_data: Dict[str, Any]) -> OpportunityTypeHint:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        
        opportunity_data_copy = opportunity_data.copy()
        opportunity_data_copy['id'] = str(opportunity_data_copy['id'])
        opportunity_data_copy['user_id'] = str(opportunity_data_copy['user_id'])

        for key in ['created_at', 'updated_at', 'expires_at', 'executed_at']:
            if key in opportunity_data_copy and isinstance(opportunity_data_copy[key], datetime):
                opportunity_data_copy[key] = opportunity_data_copy[key].isoformat()
        
        db_columns_map = {
            "source_type": "source_type", "source_name": "source_name", "source_data": "source_data",
            "status": "status", "status_reason": "status_reason", "symbol": "symbol",
            "asset_type": "asset_type", "exchange": "exchange", "predicted_direction": "predicted_direction",
            "predicted_price_target": "predicted_price_target", "predicted_stop_loss": "predicted_stop_loss",
            "prediction_timeframe": "prediction_timeframe", "ai_analysis": "ai_analysis",
            "confidence_score": "confidence_score", "suggested_action": "suggested_action",
            "ai_model_used": "ai_model_used", "executed_at": "executed_at",
            "executed_price": "executed_price", "executed_quantity": "executed_quantity",
            "related_order_id": "related_order_id", "created_at": "created_at",
            "updated_at": "updated_at", "expires_at": "expires_at"
        }

        insert_values_dict = {db_columns_map.get(k, k): v for k, v in opportunity_data_copy.items() if k not in ['id', 'user_id']}
        insert_values_dict['id'] = opportunity_data_copy['id']
        insert_values_dict['user_id'] = opportunity_data_copy['user_id']
        
        columns = [Identifier(col) for col in insert_values_dict.keys()]
        
        update_set_parts = [
            SQL("{} = EXCLUDED.{}").format(Identifier(col), Identifier(col))
            for col in insert_values_dict if col not in ['id', 'user_id']
        ]
        update_set_str = SQL(", ").join(update_set_parts)

        query_str: str = """
        INSERT INTO opportunities ({})
        VALUES ({})
        ON CONFLICT (id) DO UPDATE SET
            {},
            updated_at = timezone('utc'::text, now())
        RETURNING *;
        """
        try:
            record = None 
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        SQL(query_str).format(
                            SQL(", ").join(columns),
                            SQL(", ").join(SQL("%s") for _ in insert_values_dict),
                            update_set_str
                        ),
                        tuple(insert_values_dict.values())
                    )
                    record = await cur.fetchone()
                    if record:
                        return Opportunity(**record)
            raise ValueError("No se pudo guardar/actualizar la oportunidad y obtener el registro de retorno (psycopg_pool).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar oportunidad (psycopg_pool): {e}", exc_info=True)
            raise

    async def update_opportunity_status(self, opportunity_id: UUID, new_status: OpportunityStatusTypeHint, status_reason: Optional[str] = None) -> Optional[OpportunityTypeHint]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        query_str: str = """
        UPDATE opportunities
        SET status = %s, status_reason = %s, updated_at = timezone('utc'::text, now())
        WHERE id = %s
        RETURNING *;
        """
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL(query_str), (new_status.value, status_reason, opportunity_id))
                    record = await cur.fetchone()
                    if record:
                        return Opportunity(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar estado de oportunidad {opportunity_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_open_paper_trades(self) -> List['Trade']:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        from src.shared.data_types import Trade 

        query = SQL("""
            SELECT * FROM trades
            WHERE mode = 'paper' AND position_status = 'open';
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query)
                    records = await cur.fetchall()
                
                trades = []
                for record in records:
                    record_copy = record.copy()
                    record_copy['id'] = UUID(record_copy['id'])
                    record_copy['user_id'] = UUID(record_copy['user_id'])
                    if record_copy.get('opportunity_id'):
                        record_copy['opportunity_id'] = UUID(record_copy['opportunity_id'])
                    
                    if 'entry_order' in record_copy and record_copy['entry_order']:
                        entry_order_data = record_copy.pop('entry_order')
                        entry_order_data['orderCategory'] = entry_order_data.get('order_category')
                        entry_order_data['ocoOrderListId'] = entry_order_data.get('oco_order_list_id')
                        record_copy['entryOrder'] = TradeOrderDetails(**entry_order_data)
                    
                    if 'exit_orders' in record_copy and record_copy['exit_orders']:
                        exit_orders_list = []
                        for eo_data in record_copy.pop('exit_orders'):
                            eo_data['orderCategory'] = eo_data.get('order_category')
                            eo_data['ocoOrderListId'] = eo_data.get('oco_order_list_id')
                            exit_orders_list.append(TradeOrderDetails(**eo_data))
                        record_copy['exitOrders'] = exit_orders_list
                    else:
                        record_copy['exitOrders'] = []

                    for key in ['created_at', 'opened_at', 'updated_at', 'closed_at']:
                        if key in record_copy and isinstance(record_copy[key], str):
                            record_copy[key] = datetime.fromisoformat(record_copy[key])
                    
                    pydantic_fields_map = {
                        "position_status": "positionStatus", "opportunity_id": "opportunityId", 
                        "ai_analysis_confidence": "aiAnalysisConfidence", "pnl_usd": "pnl_usd",
                        "pnl_percentage": "pnl_percentage", "closing_reason": "closingReason",
                        "take_profit_price": "takeProfitPrice", "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate", "current_stop_price_tsl": "currentStopPrice_tsl",
                        "risk_reward_adjustments": "riskRewardAdjustments",
                    }
                    for db_col, pydantic_field in pydantic_fields_map.items():
                        if db_col in record_copy:
                            record_copy[pydantic_field] = record_copy.pop(db_col)

                    trades.append(Trade(**record_copy))
                return trades
        except Exception as e:
            logger.error(f"Error al obtener trades abiertos en paper trading (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_open_real_trades(self) -> List['Trade']:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        from src.shared.data_types import Trade 

        query = SQL("""
            SELECT * FROM trades
            WHERE mode = 'real' AND position_status = 'open';
        """)
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query)
                    records = await cur.fetchall()
                
                trades = []
                for record in records:
                    record_copy = record.copy()
                    record_copy['id'] = UUID(record_copy['id'])
                    record_copy['user_id'] = UUID(record_copy['user_id'])
                    if record_copy.get('opportunity_id'):
                        record_copy['opportunity_id'] = UUID(record_copy['opportunity_id'])
                    
                    if 'entry_order' in record_copy and record_copy['entry_order']:
                        entry_order_data = record_copy.pop('entry_order')
                        entry_order_data['orderCategory'] = entry_order_data.get('order_category')
                        entry_order_data['ocoOrderListId'] = entry_order_data.get('oco_order_list_id')
                        record_copy['entryOrder'] = TradeOrderDetails(**entry_order_data)
                    
                    if 'exit_orders' in record_copy and record_copy['exit_orders']:
                        exit_orders_list = []
                        for eo_data in record_copy.pop('exit_orders'):
                            eo_data['orderCategory'] = eo_data.get('order_category')
                            eo_data['ocoOrderListId'] = eo_data.get('oco_order_list_id')
                            exit_orders_list.append(TradeOrderDetails(**eo_data))
                        record_copy['exitOrders'] = exit_orders_list
                    else:
                        record_copy['exitOrders'] = []

                    for key in ['created_at', 'opened_at', 'updated_at', 'closed_at']:
                        if key in record_copy and isinstance(record_copy[key], str):
                            record_copy[key] = datetime.fromisoformat(record_copy[key])
                    
                    pydantic_fields_map = {
                        "position_status": "positionStatus", "opportunity_id": "opportunityId", 
                        "ai_analysis_confidence": "aiAnalysisConfidence", "pnl_usd": "pnl_usd",
                        "pnl_percentage": "pnl_percentage", "closing_reason": "closingReason",
                        "take_profit_price": "takeProfitPrice", "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate", "current_stop_price_tsl": "currentStopPrice_tsl",
                        "risk_reward_adjustments": "riskRewardAdjustments",
                    }
                    for db_col, pydantic_field in pydantic_fields_map.items():
                        if db_col in record_copy:
                            record_copy[pydantic_field] = record_copy.pop(db_col)

                    trades.append(Trade(**record_copy))
                return trades
        except Exception as e:
            logger.error(f"Error al obtener trades abiertos en real trading (psycopg_pool): {e}", exc_info=True)
            raise

    async def upsert_trade(self, user_id: UUID, trade_data: Dict[str, Any]):
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."

        trade_data_copy = trade_data.copy()
        trade_data_copy['id'] = str(trade_data_copy['id'])
        trade_data_copy['user_id'] = str(trade_data_copy['user_id'])
        if trade_data_copy.get('opportunityId'):
            trade_data_copy['opportunityId'] = str(trade_data_copy['opportunityId'])

        for key in ['created_at', 'opened_at', 'updated_at', 'closed_at']:
            if key in trade_data_copy and isinstance(trade_data_copy[key], datetime):
                trade_data_copy[key] = trade_data_copy[key].isoformat()
        
        if 'entryOrder' in trade_data_copy and isinstance(trade_data_copy['entryOrder'], dict):
            if 'timestamp' in trade_data_copy['entryOrder'] and isinstance(trade_data_copy['entryOrder']['timestamp'], datetime):
                trade_data_copy['entryOrder']['timestamp'] = trade_data_copy['entryOrder']['timestamp'].isoformat()
            trade_data_copy['entry_order'] = trade_data_copy.pop('entryOrder') 
        
        if 'exitOrders' in trade_data_copy and isinstance(trade_data_copy['exitOrders'], list):
            processed_exit_orders = []
            for eo in trade_data_copy['exitOrders']:
                if isinstance(eo, dict) and 'timestamp' in eo and isinstance(eo['timestamp'], datetime):
                    eo['timestamp'] = eo['timestamp'].isoformat()
                processed_exit_orders.append(eo)
            trade_data_copy['exit_orders'] = processed_exit_orders 
            trade_data_copy.pop('exitOrders') 

        db_columns_map = {
            "user_id": "user_id", "mode": "mode", "symbol": "symbol", "side": "side",
            "positionStatus": "position_status", "opportunityId": "opportunity_id",
            "aiAnalysisConfidence": "ai_analysis_confidence", "pnl_usd": "pnl_usd",
            "pnl_percentage": "pnl_percentage", "closingReason": "closing_reason",
            "takeProfitPrice": "take_profit_price", "trailingStopActivationPrice": "trailing_stop_activation_price",
            "trailingStopCallbackRate": "trailing_stop_callback_rate", "currentStopPrice_tsl": "current_stop_price_tsl",
            "riskRewardAdjustments": "risk_reward_adjustments",
            "created_at": "created_at", "opened_at": "opened_at", "updated_at": "updated_at", "closed_at": "closed_at"
        }

        insert_values_dict = {db_columns_map.get(k, k): v for k, v in trade_data_copy.items()}
        
        columns = [Identifier(col) for col in insert_values_dict.keys()]
        
        update_set_parts = [
            SQL("{} = EXCLUDED.{}").format(Identifier(col), Identifier(col))
            for col in insert_values_dict if col != 'id'
        ]
        update_set_str = SQL(", ").join(update_set_parts)

        query: str = """
        INSERT INTO trades ({})
        VALUES ({})
        ON CONFLICT (id) DO UPDATE SET
            {},
            updated_at = timezone('utc'::text, now())
        RETURNING *;
        """
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(
                        SQL(query).format(
                            SQL(", ").join(columns),
                            SQL(", ").join(SQL("%s") for _ in insert_values_dict),
                            update_set_str
                        ),
                        tuple(insert_values_dict.values())
                    )
            logger.info(f"Trade {trade_data_copy['id']} guardado/actualizado exitosamente (psycopg_pool).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar trade {trade_data_copy['id']} (psycopg_pool): {e}", exc_info=True)
            raise

    async def update_opportunity_analysis(
        self, 
        opportunity_id: UUID, 
        status: OpportunityStatusTypeHint, 
        ai_analysis: Optional[str] = None, 
        confidence_score: Optional[float] = None,
        suggested_action: Optional[str] = None,
        status_reason: Optional[str] = None
    ) -> Optional[OpportunityTypeHint]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."

        query_str: str = """
        UPDATE opportunities
        SET status = %s, 
            ai_analysis = %s, 
            confidence_score = %s, 
            suggested_action = %s,
            status_reason = %s,
            updated_at = timezone('utc'::text, now())
        WHERE id = %s
        RETURNING *;
        """
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL(query_str), (
                        status.value, ai_analysis, confidence_score, suggested_action, status_reason, opportunity_id
                    ))
                    record = await cur.fetchone()
                    if record:
                        return Opportunity(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar análisis de IA para oportunidad {opportunity_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_closed_trades(
        self, 
        filters: Dict[str, str], 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."
        
        query_parts = [
            SQL("SELECT * FROM trades WHERE user_id = {} AND mode = {} AND position_status = {}").format(
                Literal(str(UUID(filters["user_id"]))), 
                Literal(filters["mode"]),
                Literal(filters["positionStatus"]) 
            )
        ]
        
        if "symbol" in filters and filters["symbol"]:
            query_parts.append(Composed([SQL(" AND symbol = "), Literal(filters["symbol"])]))
            
        if start_date:
            query_parts.append(Composed([SQL(" AND closed_at >= "), Literal(start_date)]))
            
        if end_date:
            query_parts.append(Composed([SQL(" AND closed_at <= "), Literal(end_date)]))
            
        query_parts.append(Composed([SQL(" ORDER BY closed_at DESC LIMIT "), Literal(limit), SQL(" OFFSET "), Literal(offset), SQL(";")]))
        
        final_query = Composed(query_parts)

        # logger.debug(f"Executing query: {final_query.as_string(self.pool.connection())}") # No se puede obtener conexión síncrona para as_string
        logger.debug(f"Query parameters: {filters}, start_date={start_date}, end_date={end_date}, limit={limit}, offset={offset}")

        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(final_query)
                    logger.debug("Query executed successfully.")
                    records = await cur.fetchall()
                
                processed_records = []
                for record in records:
                    record_copy = dict(record)
                    
                    if 'id' in record_copy:
                        record_copy['id'] = UUID(record_copy['id'])
                    if 'user_id' in record_copy:
                        record_copy['user_id'] = UUID(record_copy['user_id'])
                    if 'opportunity_id' in record_copy and record_copy['opportunity_id']:
                        record_copy['opportunity_id'] = UUID(record_copy['opportunity_id'])
                    
                    pydantic_fields_map = {
                        "position_status": "positionStatus", "opportunity_id": "opportunityId", 
                        "ai_analysis_confidence": "aiAnalysisConfidence", "pnl_usd": "pnl_usd",
                        "pnl_percentage": "pnl_percentage", "closing_reason": "closingReason",
                        "take_profit_price": "takeProfitPrice", "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate", "current_stop_price_tsl": "currentStopPrice_tsl",
                        "risk_reward_adjustments": "riskRewardAdjustments",
                    }
                    
                    for db_col, pydantic_field in pydantic_fields_map.items():
                        if db_col in record_copy:
                            record_copy[pydantic_field] = record_copy.pop(db_col)

                    for key in ['created_at', 'opened_at', 'updated_at', 'closed_at']:
                        if key in record_copy and isinstance(record_copy[key], str):
                            record_copy[key] = datetime.fromisoformat(record_copy[key])
                    
                    processed_records.append(record_copy)
                
                logger.info(f"Obtenidos {len(processed_records)} trades cerrados con filtros: {filters}")
                return processed_records
                
        except Exception as e:
            logger.error(f"Error al obtener trades cerrados con filtros {filters} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_closed_trades_count(self, user_id: UUID, is_real_trade: bool) -> int:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."

        query = SQL("""
            SELECT COUNT(*) FROM trades
            WHERE user_id = {} AND position_status = 'closed' AND mode = {};
        """).format(
            Literal(user_id),
            Literal('real' if is_real_trade else 'paper')
        )
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query)
                    record = await cur.fetchone()
                    if record:
                        return record['count']
                return 0
        except Exception as e:
            logger.error(f"Error al contar trades cerrados para user {user_id}, real_trade={is_real_trade} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_all_trades_for_user(self, user_id: UUID, mode: Optional[str] = None) -> List[Trade]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."

        query_base = SQL("SELECT * FROM trades WHERE user_id = %s")
        params_list: List[Any] = [user_id]
        
        query_conditions_parts: List[Composable] = [] 
        if mode:
            query_conditions_parts.append(SQL("mode = %s"))
            params_list.append(mode)
        
        final_query_list: List[Composable] = [query_base] 

        if query_conditions_parts:
            final_query_list.append(SQL(" AND ")) 
            final_query_list.append(SQL(" AND ").join(query_conditions_parts)) 
            
        final_query_list.append(SQL(" ORDER BY created_at DESC;")) 
        
        final_query = SQL("").join(final_query_list) 
        params = tuple(params_list)
        
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(final_query, params) 
                    records = await cur.fetchall()
                
                trades = []
                for record_dict in records:
                    record_copy = record_dict.copy()
                    
                    for key_uuid in ['id', 'user_id', 'strategy_id', 'opportunity_id']:
                        if key_uuid in record_copy and record_copy[key_uuid] is not None:
                            try:
                                record_copy[key_uuid] = UUID(str(record_copy[key_uuid]))
                            except ValueError:
                                logger.warning(f"Invalid UUID format for {key_uuid}: {record_copy[key_uuid]} in trade {record_copy.get('id')}")
                                record_copy[key_uuid] = None

                    if 'entry_order' in record_copy and record_copy['entry_order'] and isinstance(record_copy['entry_order'], dict):
                        entry_order_data = record_copy.pop('entry_order')
                        entry_order_data['orderCategory'] = entry_order_data.pop('order_category', None)
                        entry_order_data['ocoOrderListId'] = entry_order_data.pop('oco_order_list_id', None)
                        if 'timestamp' in entry_order_data and isinstance(entry_order_data['timestamp'], str):
                            entry_order_data['timestamp'] = datetime.fromisoformat(entry_order_data['timestamp'])
                        record_copy['entryOrder'] = TradeOrderDetails(**entry_order_data)
                    else:
                        record_copy['entryOrder'] = None
                    
                    if 'exit_orders' in record_copy and record_copy['exit_orders'] and isinstance(record_copy['exit_orders'], list):
                        exit_orders_list = []
                        for eo_data_dict in record_copy.pop('exit_orders'):
                            if isinstance(eo_data_dict, dict):
                                eo_data_dict['orderCategory'] = eo_data_dict.pop('order_category', None)
                                eo_data_dict['ocoOrderListId'] = eo_data_dict.pop('oco_order_list_id', None)
                                if 'timestamp' in eo_data_dict and isinstance(eo_data_dict['timestamp'], str):
                                     eo_data_dict['timestamp'] = datetime.fromisoformat(eo_data_dict['timestamp'])
                                exit_orders_list.append(TradeOrderDetails(**eo_data_dict))
                        record_copy['exitOrders'] = exit_orders_list
                    else:
                        record_copy['exitOrders'] = []

                    datetime_fields = ['created_at', 'opened_at', 'updated_at', 'closed_at']
                    for field in datetime_fields:
                        if field in record_copy and isinstance(record_copy[field], str):
                            try:
                                record_copy[field] = datetime.fromisoformat(record_copy[field])
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir campo datetime {field}: {record_copy[field]} for trade {record_copy.get('id')}")
                                record_copy[field] = None
                    
                    field_mappings = {
                        "position_status": "positionStatus", "opportunity_id": "opportunityId", 
                        "strategy_id": "strategyId", "ai_analysis_confidence": "aiAnalysisConfidence",
                        "pnl_usd": "pnlUsd", "pnl_percentage": "pnlPercentage",
                        "closing_reason": "closingReason", "take_profit_price": "takeProfitPrice",
                        "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate",
                        "current_stop_price_tsl": "currentStopPriceTsl", 
                        "risk_reward_adjustments": "riskRewardAdjustments",
                        "initial_risk_quote_amount": "initialRiskQuoteAmount",
                        "initial_reward_to_risk_ratio": "initialRewardToRiskRatio",
                        "current_risk_quote_amount": "currentRiskQuoteAmount",
                        "current_reward_to_risk_ratio": "currentRewardToRiskRatio",
                        "market_context_snapshots": "marketContextSnapshots",
                        "external_event_or_analysis_link": "externalEventOrAnalysisLink",
                        "backtest_details": "backtestDetails", "ai_influence_details": "aiInfluenceDetails",
                        "strategy_execution_instance_id": "strategyExecutionInstanceId"
                    }
                    
                    final_record_data = {}
                    for db_key, value in record_copy.items():
                        pydantic_key = field_mappings.get(db_key, db_key)
                        final_record_data[pydantic_key] = value
                    
                    trades.append(Trade(**final_record_data))
                return trades
        except Exception as e:
            logger.error(f"Error al obtener todos los trades para el usuario {user_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[OpportunityTypeHint]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."

        query = SQL("""
            SELECT * FROM opportunities
            WHERE id = {};
        """).format(
            Literal(opportunity_id)
        )
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query)
                    record = await cur.fetchone()
                
                if record:
                    if 'id' in record:
                        record['id'] = UUID(record['id'])
                    if 'user_id' in record:
                        record['user_id'] = UUID(record['user_id'])
                    
                    datetime_fields = ['created_at', 'updated_at', 'expires_at', 'executed_at']
                    for field in datetime_fields:
                        if field in record and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field])
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir campo datetime {field}: {record[field]}")
                                record[field] = None
                    
                    field_mappings = {
                        "source_type": "sourceType", "source_name": "sourceName", "source_data": "sourceData",
                        "status_reason": "statusReason", "asset_type": "assetType",
                        "predicted_direction": "predictedDirection", "predicted_price_target": "predictedPriceTarget",
                        "predicted_stop_loss": "predictedStopLoss", "prediction_timeframe": "predictionTimeframe",
                        "ai_analysis": "aiAnalysis", "confidence_score": "confidenceScore",
                        "suggested_action": "suggestedAction", "ai_model_used": "aiModelUsed",
                        "executed_at": "executedAt", "executed_price": "executedPrice",
                        "executed_quantity": "executedQuantity", "related_order_id": "relatedOrderId",
                    }
                    
                    for db_field, pydantic_field in field_mappings.items():
                        if db_field in record:
                            record[pydantic_field] = record.pop(db_field)
                    
                    return Opportunity(**record)
                return None
        except Exception as e:
            logger.error(f"Error al obtener oportunidad por ID {opportunity_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_opportunities_by_status(self, user_id: UUID, status: OpportunityStatusTypeHint) -> List[OpportunityTypeHint]:
        if not self.pool: await self.connect()
        assert self.pool is not None, "Pool debe estar inicializado."

        query = SQL("""
            SELECT * FROM opportunities
            WHERE user_id = {} AND status = {};
        """).format(
            Literal(user_id),
            Literal(status.value)
        )
        try:
            async with self.pool.connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query)
                    records = await cur.fetchall()
                
                opportunities = []
                for record in records:
                    if 'id' in record:
                        record['id'] = UUID(str(record['id']))
                    if 'user_id' in record:
                        record['user_id'] = UUID(str(record['user_id']))
                    
                    datetime_fields = ['created_at', 'updated_at', 'expires_at', 'executed_at']
                    for field in datetime_fields:
                        if field in record and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field])
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir campo datetime {field}: {record[field]}")
                                record[field] = None
                    
                    field_mappings = {
                        "source_type": "sourceType", "source_name": "sourceName", "source_data": "sourceData",
                        "status_reason": "statusReason", "asset_type": "assetType",
                        "predicted_direction": "predictedDirection", "predicted_price_target": "predictedPriceTarget",
                        "predicted_stop_loss": "predictedStopLoss", "prediction_timeframe": "predictionTimeframe",
                        "ai_analysis": "aiAnalysis", "confidence_score": "confidenceScore",
                        "suggested_action": "suggestedAction", "ai_model_used": "aiModelUsed",
                        "executed_at": "executedAt", "executed_price": "executedPrice",
                        "executed_quantity": "executedQuantity", "related_order_id": "relatedOrderId",
                    }
                    
                    for db_field, pydantic_field in field_mappings.items():
                        if db_field in record:
                            record[pydantic_field] = record.pop(db_field)
                    
                    opportunities.append(Opportunity(**record))
                
                logger.info(f"Obtenidas {len(opportunities)} oportunidades con estado {status.value} para user {user_id}")
                return opportunities
        except Exception as e:
            logger.error(f"Error al obtener oportunidades por estado para user {user_id}, status={status.value} (psycopg_pool): {e}", exc_info=True)
            raise
