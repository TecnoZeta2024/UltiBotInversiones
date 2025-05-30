import asyncio
import platform # Para verificar el sistema operativo
import os

# Configurar la política del bucle de eventos para Windows ANTES de otras importaciones de asyncio o librerías que lo usen.
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from dotenv import load_dotenv
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from psycopg.rows import dict_row # Importar dict_row
from src.ultibot_backend.app_config import settings
import logging
import uuid

# Configurar logging básico para ver la salida
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Cargar variables de entorno desde .env
    load_dotenv()

    # La política del bucle de eventos ya se configuró arriba.

    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL no está configurada en las variables de entorno.")
        return

    service = SupabasePersistenceService()
    try:
        await service.connect()
        if await service.test_connection():
            logger.info("Verificación de conexión exitosa.")
            
            # Generar un user_id fijo para la prueba
            test_user_id = str(uuid.uuid4())
            
            # Intentar insertar una configuración de usuario
            if service.connection and not service.connection.closed: # Asegurarse de que la conexión no es None y está abierta
                try:
                    async with service.connection.cursor(row_factory=dict_row) as cur:
                        # Eliminar cualquier configuración existente para este user_id para evitar conflictos UNIQUE
                        await cur.execute(
                            "DELETE FROM user_configurations WHERE user_id = %s;",
                            (uuid.UUID(test_user_id),) # Los parámetros deben ser una tupla
                        )
                        
                        await cur.execute(
                            """
                            INSERT INTO user_configurations (user_id, selected_theme)
                            VALUES (%s, %s);
                            """,
                            (uuid.UUID(test_user_id), 'dark') # Los parámetros deben ser una tupla
                        )
                        logger.info(f"Inserción de configuración de usuario para {test_user_id} exitosa.")

                        # Intentar leer la configuración de usuario
                        await cur.execute(
                            "SELECT user_id, selected_theme FROM user_configurations WHERE user_id = %s;",
                            (uuid.UUID(test_user_id),) # Los parámetros deben ser una tupla
                        )
                        result = await cur.fetchone()
                    
                    if result and str(result.get('user_id')) == test_user_id and result.get('selected_theme') == 'dark':
                        logger.info(f"Lectura de configuración de usuario para {test_user_id} exitosa: {result}")
                        logger.info("Verificación de inserción y lectura de tablas exitosa.")
                    else:
                        logger.error("La lectura de la configuración de usuario no coincidió con los datos insertados.")
                except Exception as e:
                    logger.error(f"Error durante la prueba de inserción/lectura de user_configurations: {e}")
            else:
                logger.error("La conexión de prueba falló, no se puede realizar la prueba de inserción/lectura.")
    except Exception as e:
        logger.error(f"Error durante la ejecución de la prueba de conexión: {e}")
    finally:
        await service.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
