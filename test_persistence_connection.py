import asyncio
import os
from dotenv import load_dotenv
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.app_config import settings
import logging
import uuid

# Configurar logging básico para ver la salida
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Cargar variables de entorno desde .env
    load_dotenv()

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
            if service.connection: # Asegurarse de que la conexión no es None
                try:
                    # Eliminar cualquier configuración existente para este user_id para evitar conflictos UNIQUE
                    await service.connection.execute(
                        "DELETE FROM user_configurations WHERE user_id = $1;",
                        uuid.UUID(test_user_id)
                    )
                    
                    await service.connection.execute(
                        """
                        INSERT INTO user_configurations (user_id, selected_theme)
                        VALUES ($1, $2);
                        """,
                        uuid.UUID(test_user_id), 'dark'
                    )
                    logger.info(f"Inserción de configuración de usuario para {test_user_id} exitosa.")

                    # Intentar leer la configuración de usuario
                    result = await service.connection.fetchrow(
                        "SELECT user_id, selected_theme FROM user_configurations WHERE user_id = $1;",
                        uuid.UUID(test_user_id)
                    )
                    
                    if result and str(result['user_id']) == test_user_id and result['selected_theme'] == 'dark':
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
