import asyncpg
from src.ultibot_backend.app_config import settings
import logging
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
from uuid import UUID
from src.shared.data_types import APICredential, ServiceName
from datetime import datetime

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
            db_password = "Carlose1411*" # Contraseña original del proyecto
            db_host = parsed_url.hostname
            db_port = parsed_url.port
            db_name = parsed_url.path.lstrip('/')

            if not all([db_user, db_host, db_port, db_name]):
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
                credential.id, credential.user_id, credential.service_name.value, credential.credential_label,
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
            record = await self.connection.fetchrow(query, user_id, service_name.value, credential_label)
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
