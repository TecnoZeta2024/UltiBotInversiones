import asyncpg
from src.ultibot_backend.app_config import settings
import logging

logger = logging.getLogger(__name__)

class SupabasePersistenceService:
    def __init__(self):
        self.connection = None
        self.database_url = settings.DATABASE_URL

    async def connect(self):
        try:
            self.connection = await asyncpg.connect(self.database_url)
            logger.info("Conexión a la base de datos Supabase establecida exitosamente.")
        except Exception as e:
            logger.error(f"Error al conectar a la base de datos Supabase: {e}")
            raise

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            logger.info("Conexión a la base de datos Supabase cerrada.")

    async def test_connection(self):
        if not self.connection:
            await self.connect()
        try:
            result = await self.connection.fetchval("SELECT 1;")
            if result == 1:
                logger.info("Conexión de prueba a la base de datos Supabase exitosa.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error en la conexión de prueba a la base de datos Supabase: {e}")
            return False
