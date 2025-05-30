import asyncpg
from src.ultibot_backend.app_config import settings
import logging
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
from uuid import UUID
from src.shared.data_types import APICredential, ServiceName
from datetime import datetime, timezone # Importar timezone

logger = logging.getLogger(__name__)

class SupabasePersistenceService:
    def __init__(self):
        self.connection: Optional[asyncpg.Connection] = None
        self.database_url = settings.DATABASE_URL

    async def connect(self):
        try:
            if not self.database_url:
                logger.error("DATABASE_URL no está configurada.")
                raise ValueError("DATABASE_URL no está configurada.")

            parsed_url = urlparse(self.database_url)
            
            # Usar la contraseña original directamente, asyncpg debería manejarla.
            # La contraseña en .env es Carlose1411* (según API_Keys.txt y la lógica previa)
            # El usuario es postgres.ryfkuilvlbuzaxniqxwx
            # El host es aws-0-sa-east-1.pooler.supabase.com
            # El puerto es 5432
            # La base de datos es postgres
            
            # Extraer componentes de la URL. El DSN del .env es:
            # postgresql://postgres.ryfkuilvlbuzaxniqxwx:Carlose1411%2A@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
            # El usuario es 'postgres.ryfkuilvlbuzaxniqxwx'
            # La contraseña original es 'Carlose1411*'
            
            db_user = parsed_url.username
            # La contraseña del parsed_url podría estar codificada, usamos la original.
            # En este caso, el pooler usa el formato 'postgres.PROJECT_REF' como usuario
            # y la contraseña del proyecto como contraseña.
            db_password = parsed_url.password # Contraseña original del proyecto
            if not db_password:
                logger.error("La contraseña no se encontró en DATABASE_URL.")
                raise ValueError("La contraseña no se encontró en DATABASE_URL.")
            db_host = parsed_url.hostname
            db_port = parsed_url.port
            db_name = parsed_url.path.lstrip('/')

            if not all([db_user, db_password, db_host, db_port, db_name]):
                logger.error(f"No se pudieron parsear todos los componentes de DATABASE_URL: {self.database_url}")
                raise ValueError(f"DATABASE_URL mal formada: {self.database_url}")

            self.connection = await asyncpg.connect(
                user=db_user,
                password=db_password,
                database=db_name,
                host=db_host,
                port=db_port
            )
            logger.info("Conexión a la base de datos Supabase establecida exitosamente usando parámetros individuales.")
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos Supabase con parámetros individuales: {e}")
            raise

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            logger.info("Conexión a la base de datos Supabase cerrada.")

    async def test_connection(self):
        if not self.connection:
            await self.connect()
        if self.connection: # Asegurar que la conexión no es None
            try:
                result = await self.connection.fetchval("SELECT 1;")
                if result == 1:
                    logger.info("Conexión de prueba a la base de datos Supabase exitosa.")
                    return True
                return False
            except Exception as e:
                logger.error(f"Error en la conexión de prueba a la base de datos Supabase: {e}")
                return False
        return False # Si la conexión es None después de intentar conectar

    async def save_credential(self, credential: APICredential) -> APICredential:
        """
        Guarda una nueva credencial o actualiza una existente en la tabla api_credentials.
        """
        if not self.connection:
            await self.connect()
        if not self.connection: # Asegurar que la conexión no es None
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        query = """
        INSERT INTO api_credentials (
            id, user_id, service_name, credential_label, 
            encrypted_api_key, encrypted_api_secret, encrypted_other_details, 
            status, last_verified_at, permissions, permissions_checked_at, 
            expires_at, rotation_reminder_policy_days, usage_count, last_used_at, 
            purpose_description, tags, notes, created_at, updated_at
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
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
            record = await self.connection.fetchrow(
                query,
                credential.id, credential.user_id, credential.service_name, credential.credential_label, # Eliminar .value
                credential.encrypted_api_key, credential.encrypted_api_secret, credential.encrypted_other_details,
                credential.status, credential.last_verified_at, credential.permissions, credential.permissions_checked_at,
                credential.expires_at, credential.rotation_reminder_policy_days, credential.usage_count, credential.last_used_at,
                credential.purpose_description, credential.tags, credential.notes, credential.created_at, credential.updated_at
            )
            if record:
                return APICredential(**dict(record)) # Convertir a dict
            raise ValueError("No se pudo guardar/actualizar la credencial y obtener el registro de retorno.")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar credencial: {e}")
            raise

    async def get_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]:
        """
        Recupera una credencial por su ID.
        """
        if not self.connection:
            await self.connect()
        if not self.connection: # Asegurar que la conexión no es None
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        query = "SELECT * FROM api_credentials WHERE id = $1;"
        try:
            record = await self.connection.fetchrow(query, credential_id)
            if record:
                return APICredential(**dict(record)) # Convertir a dict
            return None
        except Exception as e:
            logger.error(f"Error al obtener credencial por ID: {e}")
            raise

    async def get_credential_by_service_label(self, user_id: UUID, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        """
        Recupera una credencial por user_id, service_name y credential_label.
        """
        if not self.connection:
            await self.connect()
        if not self.connection: # Asegurar que la conexión no es None
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        query = """
        SELECT * FROM api_credentials 
        WHERE user_id = $1 AND service_name = $2 AND credential_label = $3;
        """
        try:
            record = await self.connection.fetchrow(query, user_id, service_name, credential_label) # Eliminar .value
            if record:
                return APICredential(**dict(record)) # Convertir a dict
            return None
        except Exception as e:
            logger.error(f"Error al obtener credencial por servicio y etiqueta: {e}")
            raise

    async def update_credential_status(self, credential_id: UUID, new_status: str, last_verified_at: Optional[datetime] = None) -> Optional[APICredential]:
        """
        Actualiza el estado de una credencial y opcionalmente la fecha de última verificación.
        """
        if not self.connection:
            await self.connect()
        if not self.connection: # Asegurar que la conexión no es None
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        query = """
        UPDATE api_credentials 
        SET status = $2, last_verified_at = $3, updated_at = timezone('utc'::text, now())
        WHERE id = $1
        RETURNING *;
        """
        try:
            record = await self.connection.fetchrow(query, credential_id, new_status, last_verified_at)
            if record:
                return APICredential(**dict(record)) # Convertir a dict
            return None
        except Exception as e:
            logger.error(f"Error al actualizar estado de credencial: {e}")
            raise

    async def delete_credential(self, credential_id: UUID) -> bool:
        """
        Elimina una credencial por su ID.
        """
        if not self.connection:
            await self.connect()
        if not self.connection: # Asegurar que la conexión no es None
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        query = "DELETE FROM api_credentials WHERE id = $1;"
        try:
            result = await self.connection.execute(query, credential_id)
            return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Error al eliminar credencial: {e}")
            raise

    async def get_user_configuration(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Recupera la configuración de un usuario por su ID.
        """
        if not self.connection:
            await self.connect()
        if not self.connection:
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        query = "SELECT * FROM user_configurations WHERE user_id = $1;"
        try:
            record = await self.connection.fetchrow(query, user_id)
            if record:
                # Convertir el record a un diccionario para que Pydantic lo pueda procesar
                # Los campos JSONB ya deberían ser dicts/lists de Python
                return dict(record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener configuración de usuario para {user_id}: {e}", exc_info=True)
            raise

    async def upsert_user_configuration(self, user_id: UUID, config_data: Dict[str, Any]):
        """
        Inserta o actualiza la configuración de un usuario.
        """
        if not self.connection:
            await self.connect()
        if not self.connection:
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        # Eliminar 'id' y 'createdAt' si están presentes y son generados por la DB
        # Pydantic model_dump con exclude_none=True ya debería manejar esto,
        # pero es una salvaguarda si el dict viene de otra fuente.
        config_to_save = config_data.copy()
        config_id = config_to_save.pop('id', None) # El ID de la configuración, no el user_id
        config_to_save.pop('createdAt', None)
        config_to_save.pop('updatedAt', None) # updated_at se maneja por trigger

        # Convertir nombres de campos de camelCase a snake_case para la DB
        db_columns = {
            "telegramChatId": "telegram_chat_id",
            "notificationPreferences": "notification_preferences",
            "enableTelegramNotifications": "enable_telegram_notifications",
            "defaultPaperTradingCapital": "default_paper_trading_capital",
            "watchlists": "watchlists",
            "favoritePairs": "favorite_pairs",
            "riskProfile": "risk_profile",
            "riskProfileSettings": "risk_profile_settings",
            "realTradingSettings": "real_trading_settings",
            "aiStrategyConfigurations": "ai_strategy_configurations",
            "aiAnalysisConfidenceThresholds": "ai_analysis_confidence_thresholds",
            "mcpServerPreferences": "mcp_server_preferences",
            "selectedTheme": "selected_theme",
            "dashboardLayoutProfiles": "dashboard_layout_profiles",
            "activeDashboardLayoutProfileId": "active_dashboard_layout_profile_id",
            "dashboardLayoutConfig": "dashboard_layout_config",
            "cloudSyncPreferences": "cloud_sync_preferences",
        }
        
        # Construir el diccionario para la inserción/actualización
        insert_values = {db_columns.get(k, k): v for k, v in config_to_save.items()}
        
        # Asegurar que user_id esté presente para la inserción/conflicto
        insert_values['user_id'] = user_id

        # Construir la consulta dinámicamente
        columns = ', '.join(insert_values.keys())
        placeholders = ', '.join(f"${i+1}" for i in range(len(insert_values)))
        update_set = ', '.join(f"{col} = EXCLUDED.{col}" for col in insert_values.keys() if col != 'user_id') # No actualizar user_id en ON CONFLICT

        query = f"""
        INSERT INTO user_configurations ({columns})
        VALUES ({placeholders})
        ON CONFLICT (user_id) DO UPDATE SET
            {update_set},
            updated_at = timezone('utc'::text, now())
        RETURNING *;
        """
        
        try:
            # Ejecutar la consulta con los valores en el orden correcto
            await self.connection.fetchrow(query, *insert_values.values())
            logger.info(f"Configuración de usuario para {user_id} guardada/actualizada exitosamente.")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar configuración de usuario para {user_id}: {e}", exc_info=True)
            raise

    async def update_credential_permissions(self, credential_id: UUID, permissions: List[str], permissions_checked_at: datetime) -> Optional[APICredential]:
        """
        Actualiza los permisos y la fecha de verificación de permisos de una credencial.
        """
        if not self.connection:
            await self.connect()
        if not self.connection:
            raise ConnectionError("No se pudo establecer conexión con la base de datos.")
        
        query = """
        UPDATE api_credentials 
        SET permissions = $2, permissions_checked_at = $3, updated_at = timezone('utc'::text, now())
        WHERE id = $1
        RETURNING *;
        """
        try:
            record = await self.connection.fetchrow(query, credential_id, permissions, permissions_checked_at)
            if record:
                return APICredential(**dict(record))
            return None
        except Exception as e:
            logger.error(f"Error al actualizar permisos de credencial: {e}")
            raise
