import asyncio
import sys
import psycopg

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
from psycopg.sql import SQL, Identifier, Literal, Composed # Importar SQL y otros componentes necesarios

logger = logging.getLogger(__name__)

if TYPE_CHECKING: # Bloque para type hints que evitan importaciones circulares en runtime
    pass
    
# Definir type hints para uso en el módulo
OpportunityTypeHint = Opportunity
OpportunityStatusTypeHint = OpportunityStatus

class SupabasePersistenceService:
    def __init__(self):
        self.connection: Optional[psycopg.AsyncConnection] = None
        pass


    async def connect(self):
        try:
            if self.connection and not self.connection.closed:
                logger.info("Ya existe una conexión activa.")
                return

            current_database_url = os.getenv("DATABASE_URL")
            if not current_database_url:
                logger.error("DATABASE_URL no se encontró en las variables de entorno al intentar conectar.")
                raise ValueError("DATABASE_URL no está configurada en las variables de entorno.")

            self.connection = await psycopg.AsyncConnection.connect(
                current_database_url,
                sslmode='verify-full',
                sslrootcert='supabase/prod-ca-2021.crt'
            )
            logger.info("Conexión a la base de datos Supabase (psycopg) establecida exitosamente usando DSN directo.")
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos Supabase (psycopg): {e}")
            if isinstance(e, psycopg.Error) and e.diag:
                 logger.error(f"Detalles del error de PSQL (diag): {e.diag.message_primary}")
            raise

    async def disconnect(self):
        if self.connection and not self.connection.closed:
            await self.connection.close()
            logger.info("Conexión a la base de datos Supabase (psycopg) cerrada.")

    async def _ensure_connection(self):
        if not self.connection or self.connection.closed:
            await self.connect()

    async def test_connection(self) -> bool:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL("SELECT 1 AS result;"))
                result = await cur.fetchone()
                if result and result.get('result') == 1:
                    logger.info("Conexión de prueba a la base de datos Supabase (psycopg) exitosa.")
                    return True
                logger.warning(f"Conexión de prueba a Supabase (psycopg) devolvió: {result}")
                return False
        except Exception as e:
            logger.error(f"Error en la conexión de prueba a la base de datos Supabase (psycopg): {e}")
            return False

    async def save_credential(self, credential: APICredential) -> APICredential:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
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
            async with self.connection.cursor(row_factory=dict_row) as cur:
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
                await self.connection.commit()
                if record:
                    return APICredential(**record)
            raise ValueError("No se pudo guardar/actualizar la credencial y obtener el registro de retorno (psycopg).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar credencial (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def get_credentials_by_service(self, user_id: UUID, service_name: ServiceName) -> List[APICredential]:
        """Recupera todas las credenciales para un usuario y servicio específicos."""
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("SELECT * FROM api_credentials WHERE user_id = %s AND service_name = %s ORDER BY created_at ASC;")
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (user_id, service_name.value))
                records = await cur.fetchall()
                return [APICredential(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener credenciales por servicio para usuario {user_id} y servicio {service_name.value} (psycopg): {e}")
            raise

    async def get_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("SELECT * FROM api_credentials WHERE id = %s;")
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (credential_id,))
                record = await cur.fetchone()
                if record:
                    return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener credencial por ID (psycopg): {e}")
            raise

    async def get_credential_by_service_label(self, user_id: UUID, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("""
        SELECT * FROM api_credentials 
        WHERE user_id = %s AND service_name = %s AND credential_label = %s;
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (user_id, service_name.value, credential_label))
                record = await cur.fetchone()
                if record:
                    return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener credencial por servicio y etiqueta (psycopg): {e}")
            raise

    async def update_credential_status(self, credential_id: UUID, new_status: str, last_verified_at: Optional[datetime] = None) -> Optional[APICredential]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("""
        UPDATE api_credentials 
        SET status = %s, last_verified_at = %s, updated_at = timezone('utc'::text, now())
        WHERE id = %s
        RETURNING *;
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (new_status, last_verified_at, credential_id))
                record = await cur.fetchone()
                await self.connection.commit()
                if record:
                    return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar estado de credencial (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def delete_credential(self, credential_id: UUID) -> bool:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("DELETE FROM api_credentials WHERE id = %s;")
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (credential_id,))
                await self.connection.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error al eliminar credencial (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def get_user_configuration(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("SELECT * FROM user_configurations WHERE user_id = %s;")
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (user_id,))
                record = await cur.fetchone()
                if record:
                    return dict(record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener configuración de usuario para {user_id} (psycopg): {e}", exc_info=True)
            raise

    async def upsert_user_configuration(self, user_id: UUID, config_data: Dict[str, Any]):
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        
        config_to_save = config_data.copy()
        config_to_save.pop('id', None)
        config_to_save.pop('createdAt', None)
        config_to_save.pop('updatedAt', None)

        db_columns_map = {
            "telegramChatId": "telegram_chat_id", "notificationPreferences": "notification_preferences",
            "enableTelegramNotifications": "enable_telegram_notifications", "defaultPaperTradingCapital": "default_paper_trading_capital",
            "paperTradingActive": "paper_trading_active", # Nuevo campo
            "watchlists": "watchlists", "favoritePairs": "favorite_pairs", "riskProfile": "risk_profile",
            "riskProfileSettings": "risk_profile_settings", "realTradingSettings": "real_trading_settings",
            "aiStrategyConfigurations": "ai_strategy_configurations", "aiAnalysisConfidenceThresholds": "ai_analysis_confidence_thresholds",
            "mcpServerPreferences": "mcp_server_preferences", "selectedTheme": "selected_theme",
            "dashboardLayoutProfiles": "dashboard_layout_profiles", "activeDashboardLayoutProfileId": "active_dashboard_layout_profile_id",
            "dashboardLayoutConfig": "dashboard_layout_config", "cloudSyncPreferences": "cloud_sync_preferences",
        }
        
        insert_values_dict = {db_columns_map.get(k, k): v for k, v in config_to_save.items()}
        insert_values_dict['user_id'] = user_id

        columns = [Identifier(col) for col in insert_values_dict.keys()]
        
        update_set_parts = [
            SQL("{} = EXCLUDED.{}").format(Identifier(col), Identifier(col))
            for col in insert_values_dict if col != 'user_id'
        ]
        update_set_str = SQL(", ").join(update_set_parts)

        query: str = """
        INSERT INTO user_configurations ({})
        VALUES ({})
        ON CONFLICT (user_id) DO UPDATE SET
            {},
            updated_at = timezone('utc'::text, now())
        RETURNING *;
        """
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    SQL(query).format(
                        SQL(", ").join(columns),
                        SQL(", ").join(SQL("%s") for _ in insert_values_dict),
                        update_set_str
                    ),
                    tuple(insert_values_dict.values())
                )
                await self.connection.commit()
            logger.info(f"Configuración de usuario para {user_id} guardada/actualizada exitosamente (psycopg).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar configuración de usuario para {user_id} (psycopg): {e}", exc_info=True)
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def update_credential_permissions(self, credential_id: UUID, permissions: List[str], permissions_checked_at: datetime) -> Optional[APICredential]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("""
        UPDATE api_credentials 
        SET permissions = %s, permissions_checked_at = %s, updated_at = timezone('utc'::text, now())
        WHERE id = %s
        RETURNING *;
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (permissions, permissions_checked_at, credential_id))
                record = await cur.fetchone()
                await self.connection.commit()
                if record:
                    return APICredential(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar permisos de credencial (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def save_notification(self, notification: Notification) -> Notification:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
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
            created_at = EXCLUDED.created_at -- Asegurarse de que created_at se actualice si es parte del EXCLUDED
        RETURNING *;
        """
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
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
                await self.connection.commit()
                if record:
                    return Notification(**record)
            raise ValueError("No se pudo guardar/actualizar la notificación y obtener el registro de retorno (psycopg).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar notificación (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def get_notification_history(self, user_id: UUID, limit: int = 50) -> List[Notification]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("""
        SELECT * FROM notifications
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (user_id, limit))
                records = await cur.fetchall()
            return [Notification(**record) for record in records]
        except Exception as e:
            logger.error(f"Error al obtener historial de notificaciones para el usuario {user_id} (psycopg): {e}")
            raise

    async def mark_notification_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        query = SQL("""
        UPDATE notifications
        SET status = 'read', read_at = timezone('utc'::text, now())
        WHERE id = %s AND user_id = %s
        RETURNING *;
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, (notification_id, user_id))
                record = await cur.fetchone()
                await self.connection.commit()
                if record:
                    return Notification(**record)
            return None
        except Exception as e:
            logger.error(f"Error al marcar notificación {notification_id} como leída para el usuario {user_id} (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    # Métodos específicos de los tests que necesitan ser adaptados
    async def execute_test_delete(self, user_id_str: str):
        """Método de ayuda para eliminar datos de prueba, usado en test_persistence_connection.py"""
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        try:
            user_uuid = UUID(user_id_str)
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL("DELETE FROM user_configurations WHERE user_id = %s;"), (user_uuid,))
                await self.connection.commit()
            logger.info(f"Datos de prueba para user_id {user_id_str} eliminados (psycopg).")
        except Exception as e:
            logger.error(f"Error al eliminar datos de prueba para user_id {user_id_str} (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback() # Asegurar rollback en caso de error
            # No relanzar para no interrumpir la limpieza en finally, pero loggear es importante.

    async def execute_test_insert(self, user_id_str: str, theme: str):
        """Método de ayuda para insertar datos de prueba, usado en test_persistence_connection.py"""
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        try:
            user_uuid = UUID(user_id_str)
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    SQL("""
                    INSERT INTO user_configurations (user_id, selected_theme)
                    VALUES (%s, %s);
                    """),
                    (user_uuid, theme)
                )
                await self.connection.commit()
            logger.info(f"Inserción de prueba para user_id {user_id_str} exitosa (psycopg).")
        except Exception as e:
            logger.error(f"Error en inserción de prueba para user_id {user_id_str} (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise # Relanzar para que el test falle si la inserción falla

    async def fetchrow_test_select(self, user_id_str: str) -> Optional[Dict[str, Any]]:
        """Método de ayuda para leer datos de prueba, usado en test_persistence_connection.py"""
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        try:
            user_uuid = UUID(user_id_str)
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    SQL("SELECT user_id, selected_theme FROM user_configurations WHERE user_id = %s;"),
                    (user_uuid,)
                )
                record = await cur.fetchone()
                return record
        except Exception as e:
            logger.error(f"Error en lectura de prueba para user_id {user_id_str} (psycopg): {e}")
            raise
            
    # Adaptación de los métodos de test_persistence.py
    async def execute_test_insert_config(self, params: tuple):
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        insert_query = SQL("""
        INSERT INTO user_configurations (user_id, selected_theme, enable_telegram_notifications, default_paper_trading_capital, notification_preferences)
        VALUES (%s, %s, %s, %s, %s::jsonb)
        RETURNING id, user_id, selected_theme;
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(insert_query, params)
                record = await cur.fetchone()
                await self.connection.commit()
                return record
        except Exception as e:
            logger.error(f"Error en execute_test_insert_config (psycopg): {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def fetchrow_test_select_config(self, user_id_str: str) -> Optional[Dict[str, Any]]:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        select_query = SQL("SELECT user_id, selected_theme, default_paper_trading_capital FROM user_configurations WHERE user_id = %s;")
        try:
            user_uuid = UUID(user_id_str)
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(select_query, (user_uuid,))
                record = await cur.fetchone()
                return record
        except Exception as e:
            logger.error(f"Error en fetchrow_test_select_config (psycopg): {e}")
            raise

    async def execute_raw_sql(self, query: str, params: Optional[tuple] = None):
        """ Ejecuta una consulta SQL cruda. Usado para limpieza en tests. """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query), params)
                await self.connection.commit()
        except Exception as e:
            logger.error(f"Error ejecutando SQL crudo (psycopg): {query} con params {params} - {e}")
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def upsert_opportunity(self, user_id: UUID, opportunity_data: Dict[str, Any]) -> OpportunityTypeHint:
        """Guarda una nueva oportunidad o actualiza una existente."""
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        
        # Asegurarse de que los campos de fecha y UUID estén en el formato correcto para la BD
        opportunity_data_copy = opportunity_data.copy()
        opportunity_data_copy['id'] = str(opportunity_data_copy['id'])
        opportunity_data_copy['user_id'] = str(opportunity_data_copy['user_id'])

        # Convertir objetos datetime a strings ISO 8601 si no lo están ya
        for key in ['created_at', 'updated_at', 'expires_at', 'executed_at']:
            if key in opportunity_data_copy and isinstance(opportunity_data_copy[key], datetime):
                opportunity_data_copy[key] = opportunity_data_copy[key].isoformat()
        
        # Mapeo de nombres de campos de Pydantic a nombres de columnas de BD (snake_case)
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
            for col in insert_values_dict if col not in ['id', 'user_id'] # No actualizar el ID ni user_id en el UPDATE
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
            record = None # Inicializar record
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    SQL(query_str).format(
                        SQL(", ").join(columns),
                        SQL(", ").join(SQL("%s") for _ in insert_values_dict),
                        update_set_str
                    ),
                    tuple(insert_values_dict.values())
                )
                record = await cur.fetchone()
                await self.connection.commit()
                if record:
                    return Opportunity(**record)
            raise ValueError("No se pudo guardar/actualizar la oportunidad y obtener el registro de retorno.")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar oportunidad: {e}", exc_info=True)
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def update_opportunity_status(self, opportunity_id: UUID, new_status: OpportunityStatusTypeHint, status_reason: Optional[str] = None) -> Optional[OpportunityTypeHint]:
        """Actualiza el estado y la razón del estado de una oportunidad."""
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        # Opportunity y OpportunityStatus ya están importados a nivel de módulo para type hints

        query_str: str = """
        UPDATE opportunities
        SET status = %s, status_reason = %s, updated_at = timezone('utc'::text, now())
        WHERE id = %s
        RETURNING *;
        """
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query_str), (new_status.value, status_reason, opportunity_id))
                record = await cur.fetchone()
                await self.connection.commit()
                if record:
                    return Opportunity(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar estado de oportunidad {opportunity_id}: {e}", exc_info=True)
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def get_open_paper_trades(self) -> List['Trade']:
        """
        Recupera todos los trades abiertos en modo 'paper'.
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        
        # Importar Trade aquí para evitar importación circular a nivel de módulo
        from src.shared.data_types import Trade 

        query = SQL("""
            SELECT * FROM trades
            WHERE mode = 'paper' AND position_status = 'open';
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query)
                records = await cur.fetchall()
                
                trades = []
                for record in records:
                    # Convertir los campos JSONB de la BD a objetos Python
                    # Asegurarse de que los UUIDs y datetimes se manejen correctamente
                    record_copy = record.copy()
                    record_copy['id'] = UUID(record_copy['id'])
                    record_copy['user_id'] = UUID(record_copy['user_id'])
                    if record_copy.get('opportunity_id'):
                        record_copy['opportunity_id'] = UUID(record_copy['opportunity_id'])
                    
                    # Convertir entry_order y exit_orders de dict a TradeOrderDetails
                    if 'entry_order' in record_copy and record_copy['entry_order']:
                        record_copy['entryOrder'] = TradeOrderDetails(**record_copy.pop('entry_order'))
                    if 'exit_orders' in record_copy and record_copy['exit_orders']:
                        record_copy['exitOrders'] = [TradeOrderDetails(**eo) for eo in record_copy.pop('exit_orders')]
                    else:
                        record_copy['exitOrders'] = [] # Asegurar que sea una lista vacía si no hay

                    # Convertir timestamps de string ISO a datetime
                    for key in ['created_at', 'opened_at', 'updated_at', 'closed_at']:
                        if key in record_copy and isinstance(record_copy[key], str):
                            record_copy[key] = datetime.fromisoformat(record_copy[key])
                    
                    # Mapear nombres de columnas de BD (snake_case) a nombres de campos de Pydantic (camelCase/PascalCase)
                    # Esto es crucial para que Pydantic pueda instanciar el modelo correctamente
                    pydantic_fields_map = {
                        "position_status": "positionStatus",
                        "opportunity_id": "opportunityId", 
                        "ai_analysis_confidence": "aiAnalysisConfidence",
                        "pnl_usd": "pnl_usd",
                        "pnl_percentage": "pnl_percentage",
                        "closing_reason": "closingReason",
                        "take_profit_price": "takeProfitPrice",
                        "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate",
                        "current_stop_price_tsl": "currentStopPrice_tsl",
                        "risk_reward_adjustments": "riskRewardAdjustments",
                    }
                    
                    # Mapear campos específicos de TradeOrderDetails dentro de entryOrder y exitOrders
                    if 'entry_order' in record_copy and record_copy['entry_order']:
                        entry_order_data = record_copy.pop('entry_order')
                        # Asegurarse de que los campos de TradeOrderDetails se mapeen correctamente
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
                        record_copy['exitOrders'] = [] # Asegurar que sea una lista vacía si no hay

                    for db_col, pydantic_field in pydantic_fields_map.items():
                        if db_col in record_copy:
                            record_copy[pydantic_field] = record_copy.pop(db_col)

                    trades.append(Trade(**record_copy))
                return trades
        except Exception as e:
            logger.error(f"Error al obtener trades abiertos en paper trading (psycopg): {e}", exc_info=True)
            raise

    async def get_open_real_trades(self) -> List['Trade']:
        """
        Recupera todos los trades abiertos en modo 'real'.
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        
        # Importar Trade aquí para evitar importación circular a nivel de módulo
        from src.shared.data_types import Trade 

        query = SQL("""
            SELECT * FROM trades
            WHERE mode = 'real' AND position_status = 'open';
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query)
                records = await cur.fetchall()
                
                trades = []
                for record in records:
                    # Convertir los campos JSONB de la BD a objetos Python
                    # Asegurarse de que los UUIDs y datetimes se manejen correctamente
                    record_copy = record.copy()
                    record_copy['id'] = UUID(record_copy['id'])
                    record_copy['user_id'] = UUID(record_copy['user_id'])
                    if record_copy.get('opportunity_id'):
                        record_copy['opportunity_id'] = UUID(record_copy['opportunity_id'])
                    
                    # Convertir entry_order y exit_orders de dict a TradeOrderDetails
                    if 'entry_order' in record_copy and record_copy['entry_order']:
                        entry_order_data = record_copy.pop('entry_order')
                        # Asegurarse de que los campos de TradeOrderDetails se mapeen correctamente
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
                        record_copy['exitOrders'] = [] # Asegurar que sea una lista vacía si no hay

                    # Convertir timestamps de string ISO a datetime
                    for key in ['created_at', 'opened_at', 'updated_at', 'closed_at']:
                        if key in record_copy and isinstance(record_copy[key], str):
                            record_copy[key] = datetime.fromisoformat(record_copy[key])
                    
                    # Mapear nombres de columnas de BD (snake_case) a nombres de campos de Pydantic (camelCase/PascalCase)
                    # Esto es crucial para que Pydantic pueda instanciar el modelo correctamente
                    pydantic_fields_map = {
                        "position_status": "positionStatus",
                        "opportunity_id": "opportunityId", 
                        "ai_analysis_confidence": "aiAnalysisConfidence",
                        "pnl_usd": "pnl_usd",
                        "pnl_percentage": "pnl_percentage",
                        "closing_reason": "closingReason",
                        "take_profit_price": "takeProfitPrice",
                        "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate",
                        "current_stop_price_tsl": "currentStopPrice_tsl",
                        "risk_reward_adjustments": "riskRewardAdjustments",
                    }
                    for db_col, pydantic_field in pydantic_fields_map.items():
                        if db_col in record_copy:
                            record_copy[pydantic_field] = record_copy.pop(db_col)

                    trades.append(Trade(**record_copy))
                return trades
        except Exception as e:
            logger.error(f"Error al obtener trades abiertos en real trading (psycopg): {e}", exc_info=True)
            raise

    async def upsert_trade(self, user_id: UUID, trade_data: Dict[str, Any]):
        """
        Inserta un nuevo trade o actualiza uno existente.
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"

        # Asegurarse de que los campos de fecha y UUID estén en el formato correcto para la BD
        trade_data_copy = trade_data.copy()
        trade_data_copy['id'] = str(trade_data_copy['id'])
        trade_data_copy['user_id'] = str(trade_data_copy['user_id'])
        if trade_data_copy.get('opportunityId'):
            trade_data_copy['opportunityId'] = str(trade_data_copy['opportunityId'])

        # Convertir objetos datetime a strings ISO 8601 si no lo están ya
        for key in ['created_at', 'opened_at', 'updated_at', 'closed_at']:
            if key in trade_data_copy and isinstance(trade_data_copy[key], datetime):
                trade_data_copy[key] = trade_data_copy[key].isoformat()
        
        # Manejar entryOrder y exitOrders
        if 'entryOrder' in trade_data_copy and isinstance(trade_data_copy['entryOrder'], dict):
            if 'timestamp' in trade_data_copy['entryOrder'] and isinstance(trade_data_copy['entryOrder']['timestamp'], datetime):
                trade_data_copy['entryOrder']['timestamp'] = trade_data_copy['entryOrder']['timestamp'].isoformat()
            trade_data_copy['entry_order'] = trade_data_copy.pop('entryOrder') # Mapear a snake_case para BD
        
        if 'exitOrders' in trade_data_copy and isinstance(trade_data_copy['exitOrders'], list):
            processed_exit_orders = []
            for eo in trade_data_copy['exitOrders']:
                if isinstance(eo, dict) and 'timestamp' in eo and isinstance(eo['timestamp'], datetime):
                    eo['timestamp'] = eo['timestamp'].isoformat()
                processed_exit_orders.append(eo)
            trade_data_copy['exit_orders'] = processed_exit_orders # Mapear a snake_case para BD
            trade_data_copy.pop('exitOrders') # Eliminar el campo original

        # Mapeo de nombres de campos de Pydantic a nombres de columnas de BD (snake_case)
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
            for col in insert_values_dict if col != 'id' # No actualizar el ID en el UPDATE
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
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    SQL(query).format(
                        SQL(", ").join(columns),
                        SQL(", ").join(SQL("%s") for _ in insert_values_dict),
                        update_set_str
                    ),
                    tuple(insert_values_dict.values())
                )
                await self.connection.commit()
            logger.info(f"Trade {trade_data_copy['id']} guardado/actualizado exitosamente (psycopg).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar trade {trade_data_copy['id']} (psycopg): {e}", exc_info=True)
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def update_opportunity_analysis(
        self, 
        opportunity_id: UUID, 
        status: OpportunityStatusTypeHint, 
        ai_analysis: Optional[str] = None, # JSON string
        confidence_score: Optional[float] = None,
        suggested_action: Optional[str] = None,
        status_reason: Optional[str] = None
    ) -> Optional[OpportunityTypeHint]:
        """Actualiza los campos relacionados con el análisis de IA de una oportunidad."""
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        # Opportunity y OpportunityStatus ya están importados a nivel de módulo para type hints

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
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL(query_str), (
                    status.value, ai_analysis, confidence_score, suggested_action, status_reason, opportunity_id
                ))
                record = await cur.fetchone()
                await self.connection.commit()
                if record:
                    return Opportunity(**record)
            return None
        except Exception as e:
            logger.error(f"Error al actualizar análisis de IA para oportunidad {opportunity_id}: {e}", exc_info=True)
            if self.connection and not self.connection.closed:
                await self.connection.rollback()
            raise

    async def get_closed_trades(
        self, 
        filters: Dict[str, str], 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene una lista de trades cerrados con capacidad de filtrado.
        
        Args:
            filters: Diccionario con filtros básicos (user_id, mode, positionStatus, symbol)
            start_date: Fecha de inicio para filtrar por closed_at (opcional)
            end_date: Fecha de fin para filtrar por closed_at (opcional)
            limit: Número máximo de trades a devolver
            offset: Número de trades a saltar (para paginación)
            
        Returns:
            Lista de diccionarios con datos de trades que cumplen los filtros
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        
        # Construir la query SQL base
        # Construir la query SQL base usando psycopg.sql componentes
        query_parts = [
            SQL("SELECT * FROM trades WHERE user_id = {} AND mode = {} AND position_status = {}").format(
                Literal(str(UUID(filters["user_id"]))), # Convertir UUID a string
                Literal(filters["mode"]),
                Literal(filters["positionStatus"])  # type: ignore[arg-type]
            )
        ]
        
        # Añadir filtro por símbolo si está presente
        if "symbol" in filters and filters["symbol"]:
            query_parts.append(Composed([SQL(" AND symbol = "), Literal(filters["symbol"])]))
            
        # Añadir filtro por fechas si están presentes
        if start_date:
            query_parts.append(Composed([SQL(" AND closed_at >= "), Literal(start_date)]))
            
        if end_date:
            query_parts.append(Composed([SQL(" AND closed_at <= "), Literal(end_date)]))
            
        # Añadir ordenamiento, límite y offset
        query_parts.append(Composed([SQL(" ORDER BY closed_at DESC LIMIT "), Literal(limit), SQL(" OFFSET "), Literal(offset), SQL(";")]))
        
        final_query = Composed(query_parts)

        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(final_query)
                records = await cur.fetchall()
                
                # Convertir a lista de diccionarios con el formato esperado por TradingReportService
                processed_records = []
                for record in records:
                    record_copy = dict(record)
                    
                    # Convertir UUIDs de string a UUID objects
                    if 'id' in record_copy:
                        record_copy['id'] = UUID(record_copy['id'])
                    if 'user_id' in record_copy:
                        record_copy['user_id'] = UUID(record_copy['user_id'])
                    if 'opportunity_id' in record_copy and record_copy['opportunity_id']:
                        record_copy['opportunity_id'] = UUID(record_copy['opportunity_id'])
                    
                    # Mapear nombres de columnas de BD (snake_case) a nombres de campos de Pydantic
                    field_mappings = {
                        "position_status": "positionStatus",
                        "opportunity_id": "opportunityId", 
                        "ai_analysis_confidence": "aiAnalysisConfidence",
                        "pnl_usd": "pnl_usd",
                        "pnl_percentage": "pnl_percentage",
                        "closing_reason": "closingReason",
                        "entry_order": "entryOrder",
                        "exit_orders": "exitOrders",
                        "take_profit_price": "takeProfitPrice",
                        "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate",
                        "current_stop_price_tsl": "currentStopPrice_tsl",
                        "risk_reward_adjustments": "riskRewardAdjustments",
                    }
                    
                    for db_field, pydantic_field in field_mappings.items():
                        if db_field in record_copy:
                            record_copy[pydantic_field] = record_copy.pop(db_field)
                    
                    # Convertir timestamps ISO a datetime si son strings
                    datetime_fields = ['created_at', 'opened_at', 'updated_at', 'closed_at']
                    for field in datetime_fields:
                        if field in record_copy and isinstance(record_copy[field], str):
                            try:
                                record_copy[field] = datetime.fromisoformat(record[field])
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir campo datetime {field}: {record_copy[field]}")
                                record_copy[field] = None
                    
                    processed_records.append(record_copy)
                
                logger.info(f"Obtenidos {len(processed_records)} trades cerrados con filtros: {filters}")
                return processed_records
                
        except Exception as e:
            logger.error(f"Error al obtener trades cerrados con filtros {filters}: {e}", exc_info=True)
            raise

    async def get_closed_trades_count(self, user_id: UUID, is_real_trade: bool) -> int:
        """
        Cuenta el número de trades cerrados para un usuario, filtrando por si es una operación real o no.
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"

        query = SQL("""
            SELECT COUNT(*) FROM trades
            WHERE user_id = {} AND position_status = 'closed' AND mode = {};
        """).format(
            Literal(user_id),
            Literal('real' if is_real_trade else 'paper')
        )
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query)
                record = await cur.fetchone()
                if record:
                    return record['count']
                return 0
        except Exception as e:
            logger.error(f"Error al contar trades cerrados para user {user_id}, real_trade={is_real_trade}: {e}", exc_info=True)
            raise # Re-lanzar la excepción para que el llamador pueda manejarla

    async def get_all_trades_for_user(self, user_id: UUID, mode: Optional[str] = None) -> List[Trade]:
        """
        Recupera todos los trades para un usuario específico, opcionalmente filtrados por modo.
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"

        query_parts = [SQL("SELECT * FROM trades WHERE user_id = %s")]
        params: List[Any] = [user_id]

        if mode:
            query_parts.append(SQL("AND mode = %s"))
            params.append(mode)
        
        query_parts.append(SQL("ORDER BY created_at DESC;"))
        final_query = Composed(query_parts)
        
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(final_query, tuple(params))
                records = await cur.fetchall()
                
                trades = []
                for record_dict in records:
                    record_copy = record_dict.copy() # Usar el dict directamente
                    
                    # Convertir UUIDs de string a UUID objects
                    for key_uuid in ['id', 'user_id', 'strategy_id', 'opportunity_id']:
                        if key_uuid in record_copy and record_copy[key_uuid] is not None:
                            try:
                                record_copy[key_uuid] = UUID(str(record_copy[key_uuid]))
                            except ValueError:
                                logger.warning(f"Invalid UUID format for {key_uuid}: {record_copy[key_uuid]} in trade {record_copy.get('id')}")
                                record_copy[key_uuid] = None


                    # Convertir entry_order y exit_orders de dict a TradeOrderDetails
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

                    # Convertir timestamps de string ISO a datetime
                    datetime_fields = ['created_at', 'opened_at', 'updated_at', 'closed_at']
                    for field in datetime_fields:
                        if field in record_copy and isinstance(record_copy[field], str):
                            try:
                                record_copy[field] = datetime.fromisoformat(record_copy[field])
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir campo datetime {field}: {record_copy[field]} for trade {record_copy.get('id')}")
                                record_copy[field] = None
                    
                    # Mapear nombres de columnas de BD (snake_case) a nombres de campos de Pydantic
                    field_mappings = {
                        "position_status": "positionStatus",
                        "opportunity_id": "opportunityId", 
                        "strategy_id": "strategyId",
                        "ai_analysis_confidence": "aiAnalysisConfidence",
                        "pnl_usd": "pnlUsd", # Corregido a camelCase
                        "pnl_percentage": "pnlPercentage",
                        "closing_reason": "closingReason",
                        "take_profit_price": "takeProfitPrice",
                        "trailing_stop_activation_price": "trailingStopActivationPrice",
                        "trailing_stop_callback_rate": "trailingStopCallbackRate",
                        "current_stop_price_tsl": "currentStopPriceTsl", # Corregido a camelCase
                        "risk_reward_adjustments": "riskRewardAdjustments",
                        "initial_risk_quote_amount": "initialRiskQuoteAmount",
                        "initial_reward_to_risk_ratio": "initialRewardToRiskRatio",
                        "current_risk_quote_amount": "currentRiskQuoteAmount",
                        "current_reward_to_risk_ratio": "currentRewardToRiskRatio",
                        "market_context_snapshots": "marketContextSnapshots",
                        "external_event_or_analysis_link": "externalEventOrAnalysisLink",
                        "backtest_details": "backtestDetails",
                        "ai_influence_details": "aiInfluenceDetails",
                        "strategy_execution_instance_id": "strategyExecutionInstanceId"
                    }
                    
                    final_record_data = {}
                    for db_key, value in record_copy.items():
                        pydantic_key = field_mappings.get(db_key, db_key)
                        final_record_data[pydantic_key] = value
                    
                    # Asegurar que los campos requeridos por Trade estén presentes o tengan un default
                    # Esto es importante si la tabla de BD tiene columnas nullable que Pydantic espera.
                    # Trade.__fields__ puede dar los campos requeridos.
                    # Por simplicidad, asumimos que los datos de la BD son suficientes.

                    trades.append(Trade(**final_record_data))
                return trades
        except Exception as e:
            logger.error(f"Error al obtener todos los trades para el usuario {user_id} (psycopg): {e}", exc_info=True)
            raise

    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[OpportunityTypeHint]:
        """
        Recupera una oportunidad por su ID.
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"

        query = SQL("""
            SELECT * FROM opportunities
            WHERE id = {};
        """).format(
            Literal(opportunity_id)
        )
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query)
                record = await cur.fetchone()
                
                if record:
                    # Convertir UUIDs de string a UUID objects
                    if 'id' in record:
                        record['id'] = UUID(record['id'])
                    if 'user_id' in record:
                        record['user_id'] = UUID(record['user_id'])
                    
                    # Convertir timestamps ISO a datetime si son strings
                    datetime_fields = ['created_at', 'updated_at', 'expires_at', 'executed_at']
                    for field in datetime_fields:
                        if field in record and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field])
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir campo datetime {field}: {record[field]}")
                                record[field] = None
                    
                    # Mapear nombres de columnas de BD (snake_case) a nombres de campos de Pydantic
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
            logger.error(f"Error al obtener oportunidad por ID {opportunity_id}: {e}", exc_info=True)
            raise # Re-lanzar la excepción para que el llamador pueda manejarla

    async def get_opportunities_by_status(self, user_id: UUID, status: OpportunityStatusTypeHint) -> List[OpportunityTypeHint]:
        """
        Recupera oportunidades para un usuario con un estado específico.
        """
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"

        query = SQL("""
            SELECT * FROM opportunities
            WHERE user_id = {} AND status = {};
        """).format(
            Literal(user_id),
            Literal(status.value)
        )
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query)
                records = await cur.fetchall()
                
                opportunities = []
                for record in records:
                    # Convertir UUIDs de string a UUID objects
                    if 'id' in record:
                        record['id'] = UUID(str(record['id']))
                    if 'user_id' in record:
                        record['user_id'] = UUID(str(record['user_id']))
                    
                    # Convertir timestamps ISO a datetime si son strings
                    datetime_fields = ['created_at', 'updated_at', 'expires_at', 'executed_at']
                    for field in datetime_fields:
                        if field in record and isinstance(record[field], str):
                            try:
                                record[field] = datetime.fromisoformat(record[field])
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir campo datetime {field}: {record[field]}")
                                record[field] = None
                    
                    # Mapear nombres de columnas de BD (snake_case) a nombres de campos de Pydantic
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
            logger.error(f"Error al obtener oportunidades por estado para user {user_id}, status={status.value}: {e}", exc_info=True)
            raise # Re-lanzar la excepción para que el llamador pueda manejarla
