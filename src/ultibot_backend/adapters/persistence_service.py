import psycopg
from psycopg.rows import dict_row # Usar dict_row, se aplica al cursor
from psycopg.conninfo import make_conninfo
from src.ultibot_backend.app_config import settings
import logging
import os # Importar os
from urllib.parse import urlparse, unquote
from typing import Optional, List, Dict, Any
from uuid import UUID
from src.shared.data_types import APICredential, ServiceName, Notification
from datetime import datetime, timezone
from psycopg.sql import SQL, Identifier, Literal, Composed # Importar SQL y otros componentes necesarios

logger = logging.getLogger(__name__)

class SupabasePersistenceService:
    def __init__(self):
        self.connection: Optional[psycopg.AsyncConnection] = None
        # self.database_url ya no se establece desde settings aquí para asegurar que se lee la más fresca en connect()
        # if not settings.DATABASE_URL: # Esta verificación se hará en connect()
        #     raise ValueError("DATABASE_URL no está configurada.")
        
        # self.database_url se leerá directamente de os.getenv() en el método connect
        # para asegurar que se usa el valor más fresco, especialmente después de cambios en .env
        # Sin embargo, la lógica de parseo que estaba aquí para el logging de conninfo
        # puede eliminarse o ajustarse si ya no es necesaria en __init__.
        # Por ahora, la eliminaremos de __init__ para simplificar, ya que connect() usa el DSN directamente.

        # Parsear la URL una vez para obtener los componentes
        # y construir el conninfo para psycopg
        # Ejemplo DSN: postgresql://user:pass@host:port/dbname?sslmode=verify-full&sslrootcert=path/to/cert.crt
        
        # No es necesario parsear manualmente si pasamos el DSN directamente a connect,
        # pero para añadir sslrootcert de forma programática, construir conninfo es más limpio.
        
        # parsed = urlparse(self.database_url) # self.database_url no está definido aquí ahora
        # Dejar que psycopg maneje la decodificación de la contraseña del DSN.
        # make_conninfo espera la contraseña tal como estaría en un DSN.
        # Si la DATABASE_URL tiene la contraseña codificada (%2A), make_conninfo la pasará así.
        # psycopg.Connection.connect luego la decodificará.
        # No es necesario construir conninfo explícitamente si pasamos el DSN y los parámetros SSL directamente.
        pass # __init__ ya no necesita construir self.conninfo de esta manera


    async def connect(self):
        try:
            if self.connection and not self.connection.closed:
                logger.info("Ya existe una conexión activa.")
                return

            # Leer DATABASE_URL directamente de las variables de entorno aquí
            # para asegurar que se usa el valor más reciente, especialmente después de cambios en .env
            current_database_url = os.getenv("DATABASE_URL")
            if not current_database_url:
                logger.error("DATABASE_URL no se encontró en las variables de entorno al intentar conectar.")
                raise ValueError("DATABASE_URL no está configurada en las variables de entorno.")

            # Pasar el DSN directamente y los parámetros SSL por separado.
            # psycopg decodificará la contraseña del DSN.
            self.connection = await psycopg.AsyncConnection.connect(
                current_database_url, # Usar la URL leída directamente
                sslmode='verify-full',
                sslrootcert='supabase/prod-ca-2021.crt'
                # row_factory se aplicará al cursor
            )
            logger.info("Conexión a la base de datos Supabase (psycopg) establecida exitosamente usando DSN directo.")
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos Supabase (psycopg): {e}")
            if isinstance(e, psycopg.Error) and e.diag: # Comprobación más segura para diag
                 logger.error(f"Detalles del error de PSQL (diag): {e.diag.message_primary}")
            raise

    async def disconnect(self):
        if self.connection and not self.connection.closed:
            await self.connection.close()
            logger.info("Conexión a la base de datos Supabase (psycopg) cerrada.")

    async def _ensure_connection(self):
        if not self.connection or self.connection.closed:
            await self.connect()
        # No es necesario el segundo if not self.connection, connect() ya lanzaría una excepción si falla.
        # Si connect() no lanza excepción, self.connection debería estar establecido.

    async def test_connection(self) -> bool:
        await self._ensure_connection()
        assert self.connection is not None, "Connection must be established by _ensure_connection"
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(SQL("SELECT 1 AS result;")) # Envolver en SQL()
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
        query = SQL("""
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
        """)
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    query,
                    (
                        credential.id, credential.user_id, credential.service_name, credential.credential_label,
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
            if self.connection and not self.connection.closed: # Asegurar que hay conexión para rollback
                await self.connection.rollback() # Rollback en caso de error
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
                await cur.execute(query, (user_id, service_name, credential_label))
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

        query = SQL("""
        INSERT INTO user_configurations ({})
        VALUES ({})
        ON CONFLICT (user_id) DO UPDATE SET
            {},
            updated_at = timezone('utc'::text, now())
        RETURNING *;
        """).format(
            SQL(", ").join(columns),
            SQL(", ").join(SQL("%s") for _ in insert_values_dict),
            update_set_str
        )
        
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(query, tuple(insert_values_dict.values()))
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
        query = SQL("""
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
        """)
        # Nota: El ON CONFLICT para created_at = EXCLUDED.created_at puede no ser lo deseado si created_at
        # solo debe establecerse en la inserción inicial. Ajustar si es necesario.
        try:
            async with self.connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    query,
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
            # No relanzar si es para limpieza, pero sí loggear.
            # Si no es para limpieza, el que llama debería manejar el error.
            # Para los tests, si la limpieza falla, es informativo pero no debe detener otros tests.
            # raise # Descomentar si se necesita que el error se propague
