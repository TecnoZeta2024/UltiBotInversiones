import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# --- Configuraciones y Imports Arquitectónicos ---
# Se importa directamente desde la raíz del proyecto.
from src.ultibot_backend.app_config import get_app_settings
from src.ultibot_backend.core.ports import ICredentialService, IPersistencePort
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.shared.data_types import ServiceName

# Configurar un logger básico para el script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """
    Script para añadir o verificar la existencia de credenciales de Binance en la base de datos.
    Este script sigue la nueva arquitectura de inyección de dependencias.
    """
    logger.info("Iniciando script para añadir/verificar credenciales de Binance...")

    app_settings = get_app_settings()
    
    if not app_settings.database_url:
        logger.error("Error crítico: DATABASE_URL no está configurada en app_settings.")
        return
    
    logger.info(f"Usando DATABASE_URL: {app_settings.database_url[:20]}...")

    # 1. Inicializar el motor de la base de datos y la sesión
    engine = create_async_engine(app_settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db_session:
        try:
            # 2. Instanciar los servicios siguiendo el grafo de dependencias correcto
            # IPersistencePort -> ICredentialService -> IBinanceAdapter
            
            # Implementación concreta del puerto de persistencia
            persistence_port: IPersistencePort = SupabasePersistenceService(db_session=db_session)
            
            # El servicio de credenciales SOLO depende de la persistencia
            credential_service: ICredentialService = CredentialService(persistence_port=persistence_port)
            
            # El adaptador de Binance AHORA depende del servicio de credenciales y la configuración.
            # Se instancia para validar que la arquitectura es coherente.
            BinanceAdapter(config=app_settings, credential_service=credential_service)
            logger.info(f"Instancia de BinanceAdapter creada correctamente con {type(credential_service).__name__}.")

            # --- Lógica para añadir la credencial ---
            service_name = ServiceName.BINANCE_SPOT
            credential_label = "default"
            
            # Las credenciales se hardcodean aquí para el propósito de este script de setup.
            # NO HACER ESTO EN PRODUCCIÓN.
            binance_api_key = "0B4RChwwMMvHS1rTK0VEonBQIRh2ad3Y4TUBY2oqMwdCB6H1q3gVcKnFzZ23GrB9"
            binance_api_secret = "H1Hq6O89SrAnOQGY1ZsEkTEtK8Q6Plon0CwHDumXlWHDZ3IPBETcw5NYKcRifL2J"

            logger.info(f"Buscando credencial existente para Servicio: {service_name.value}, Etiqueta: {credential_label}")
            
            # El user_id se gestiona internamente en el servicio a través de la configuración.
            existing_credential = await credential_service.get_credential(service_name, credential_label)
            
            if existing_credential:
                logger.info(f"La credencial de Binance para la etiqueta '{credential_label}' ya existe. No se realizarán cambios.")
                # La validación de la clave se hará implícitamente cuando el adaptador la use.
                return

            logger.info(f"Añadiendo nueva credencial de Binance con etiqueta '{credential_label}'...")
            
            await credential_service.add_credential(
                service_name=service_name,
                credential_label=credential_label,
                api_key=binance_api_key,
                api_secret=binance_api_secret
            )
            logger.info("Credencial de Binance añadida exitosamente a la base de datos.")

        except Exception as e:
            logger.error(f"Ocurrió un error durante la gestión de credenciales de Binance: {e}", exc_info=True)
        finally:
            await engine.dispose()
            logger.info("Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    asyncio.run(main())
