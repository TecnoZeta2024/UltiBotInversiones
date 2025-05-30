import logging
from typing import List, Optional
from uuid import UUID

from src.shared.data_types import AssetBalance, ServiceName, BinanceConnectionStatus
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import BinanceAPIError, CredentialError, UltiBotError
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Servicio para obtener datos de mercado, incluyendo balances de exchanges.
    """
    def __init__(self, credential_service: CredentialService, binance_adapter: BinanceAdapter):
        self.credential_service = credential_service
        self.binance_adapter = binance_adapter

    async def get_binance_connection_status(self, user_id: UUID) -> BinanceConnectionStatus:
        """
        Verifica el estado de la conexión con Binance y devuelve un objeto BinanceConnectionStatus.
        """
        status_message = "Conexión con Binance no verificada."
        is_connected = False
        last_verified_at = None
        status_code = None
        account_permissions = None

        try:
            # Intentar obtener la credencial de Binance Spot
            binance_credential = await self.credential_service.get_credential(
                user_id=user_id,
                service_name=ServiceName.BINANCE_SPOT,
                credential_label="default" # Asumimos una etiqueta por defecto para la credencial principal
            )

            if not binance_credential:
                status_message = "Credenciales de Binance no encontradas. Por favor, configúrelas."
                logger.warning(f"Usuario {user_id}: {status_message}")
                return BinanceConnectionStatus(
                    is_connected=False,
                    status_message=status_message,
                    status_code="CREDENTIALS_NOT_FOUND",
                    last_verified_at=None, # Añadir explícitamente None
                    account_permissions=None # Añadir explícitamente None
                )
            
            # La verificación de la credencial ya actualiza su estado en la BD
            is_connected = await self.credential_service.verify_credential(binance_credential)
            
            # Después de verify_credential, binance_credential.last_verified_at y .permissions ya deberían estar actualizados
            last_verified_at = binance_credential.last_verified_at
            account_permissions = binance_credential.permissions

            if not is_connected:
                status_message = "Fallo en la verificación de conexión con Binance. Revise sus credenciales y permisos."
                status_code = "VERIFICATION_FAILED"
                logger.error(f"Usuario {user_id}: {status_message}")
            else:
                status_message = "Conexión con Binance exitosa."
                logger.info(f"Usuario {user_id}: {status_message}")

        except CredentialError as e:
            status_message = f"Error al acceder a las credenciales de Binance: {e}"
            status_code = "CREDENTIAL_ERROR"
            logger.error(f"Usuario {user_id}: {status_message}", exc_info=True)
        except BinanceAPIError as e:
            status_message = f"Error de la API de Binance: {e}"
            status_code = e.code if e.code else "BINANCE_API_ERROR"
            logger.error(f"Usuario {user_id}: {status_message}", exc_info=True)
        except Exception as e:
            status_message = f"Error inesperado al verificar conexión con Binance: {e}"
            status_code = "UNEXPECTED_ERROR"
            logger.critical(f"Usuario {user_id}: {status_message}", exc_info=True)
        
        return BinanceConnectionStatus(
            is_connected=is_connected,
            last_verified_at=last_verified_at,
            status_message=status_message,
            status_code=status_code,
            account_permissions=account_permissions
        )

    async def get_binance_spot_balances(self, user_id: UUID) -> List[AssetBalance]:
        """
        Obtiene los balances de Spot de Binance para un usuario.
        """
        binance_credential = await self.credential_service.get_credential(
            user_id=user_id,
            service_name=ServiceName.BINANCE_SPOT,
            credential_label="default"
        )

        if not binance_credential:
            raise CredentialError("Credenciales de Binance no encontradas para obtener balances.")

        # Las credenciales ya están desencriptadas en el objeto binance_credential
        # si get_credential no lanzó un error.
        decrypted_api_key = binance_credential.encrypted_api_key
        decrypted_api_secret = binance_credential.encrypted_api_secret

        # Aunque get_credential ya lanza CredentialError si la desencriptación falla,
        # añadimos una comprobación explícita aquí para mayor robustez y claridad.
        if decrypted_api_key is None or decrypted_api_secret is None:
            raise CredentialError("Las credenciales de Binance (API Key o Secret) no están disponibles o no son válidas.")

        try:
            balances = await self.binance_adapter.get_spot_balances(decrypted_api_key, decrypted_api_secret)
            logger.info(f"Balances de Binance obtenidos para el usuario {user_id}.")
            return balances
        except BinanceAPIError as e:
            logger.error(f"Error al obtener balances de Binance para el usuario {user_id}: {e}")
            raise UltiBotError(f"No se pudieron obtener los balances de Binance: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al obtener balances de Binance para el usuario {user_id}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener balances de Binance: {e}")

# Ejemplo de uso (para pruebas locales)
async def main():
    # Configurar un logger básico para el ejemplo
    logging.basicConfig(level=logging.INFO)

    # Necesitarás configurar la variable de entorno CREDENTIAL_ENCRYPTION_KEY
    # y tener una credencial de Binance en tu base de datos Supabase para que esto funcione.
    # Para pruebas, puedes simular el CredentialService y BinanceAdapter.

    # Ejemplo de inicialización de servicios (simplificado para el ejemplo)
    # En una aplicación real, estos serían inyectados por un framework (FastAPI Depends)
    from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
    from src.ultibot_backend.app_config import settings # Asegúrate de que settings esté configurado

    # Configurar una URL de BD de prueba o mockear SupabasePersistenceService
    # settings.DATABASE_URL = "postgresql://..." 

    persistence_service = SupabasePersistenceService()
    # Asegúrate de que la conexión a la BD esté activa para CredentialService
    # await persistence_service.connect() 

    credential_service = CredentialService()
    binance_adapter = BinanceAdapter() # Ya inicializado dentro de CredentialService, pero aquí para claridad

    market_data_service = MarketDataService(credential_service, binance_adapter)

    # ID de usuario de prueba (debe coincidir con el user_id de la credencial en la BD)
    test_user_id = UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef") 

    print("Verificando estado de conexión con Binance...")
    status = await market_data_service.get_binance_connection_status(test_user_id)
    print(f"Estado de conexión: {status.is_connected}, Mensaje: {status.status_message}, Permisos: {status.account_permissions}")

    if status.is_connected:
        print("\nObteniendo balances de Spot de Binance...")
        try:
            balances = await market_data_service.get_binance_spot_balances(test_user_id)
            for balance in balances:
                print(f"  {balance.asset}: Free={balance.free}, Locked={balance.locked}, Total={balance.total}")
        except UltiBotError as e:
            print(f"Error al obtener balances: {e}")
    else:
        print("No se pueden obtener balances sin una conexión exitosa a Binance.")

    # await persistence_service.disconnect() # Desconectar al final

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
