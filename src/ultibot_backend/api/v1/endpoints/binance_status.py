from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.ultibot_backend.security import core as security_core
from src.ultibot_backend.security import schemas as security_schemas
# Importar el módulo de dependencias
from src.ultibot_backend import dependencies as deps

from src.shared.data_types import BinanceConnectionStatus, AssetBalance, ServiceName # Importar ServiceName
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import CredentialError, UltiBotError, BinanceAPIError

router = APIRouter()

# Ya no se necesita la función local get_market_data_service
# async def get_market_data_service() -> MarketDataService:
#     from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
#     # Esto crearía instancias nuevas y no configuradas, lo cual es incorrecto.
#     # credential_service = CredentialService() # Incorrecto
#     # binance_adapter = BinanceAdapter() # Incorrecto
#     # return MarketDataService(credential_service, binance_adapter) # Incorrecto
#     # En su lugar, usaremos deps.get_market_data_service()

@router.get("/binance/status", response_model=BinanceConnectionStatus, summary="Obtener el estado de conexión con Binance")
async def get_binance_status(
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    market_data_service: MarketDataService = Depends(deps.get_market_data_service)
) -> BinanceConnectionStatus:
    """
    Retorna el estado actual de la conexión con la API de Binance para el usuario autenticado,
    incluyendo si las credenciales son válidas y los permisos de la cuenta.
    """
    try:
        if not isinstance(current_user.id, UUID):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")
        status_result = await market_data_service.get_binance_connection_status(current_user.id)
        return status_result
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error de credenciales: {e}"
        )
    except BinanceAPIError as e: # Mover BinanceAPIError antes de UltiBotError
        raise HTTPException(
            status_code=e.status_code if e.status_code else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de la API de Binance: {str(e)}" # Usar str(e) para el mensaje
        )
    except UltiBotError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al verificar el estado de Binance: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {e}"
        )

@router.get("/binance/balances", response_model=List[AssetBalance], summary="Obtener los balances de Spot de Binance")
async def get_binance_balances(
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    market_data_service: MarketDataService = Depends(deps.get_market_data_service)
) -> List[AssetBalance]:
    """
    Retorna la lista de balances de activos en la cuenta de Spot de Binance para el usuario autenticado.
    """
    try:
        if not isinstance(current_user.id, UUID):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")
        balances = await market_data_service.get_binance_spot_balances(current_user.id)
        return balances
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error de credenciales: {e}"
        )
    except BinanceAPIError as e: # Mover BinanceAPIError antes de UltiBotError
        raise HTTPException(
            status_code=e.status_code if e.status_code else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de la API de Binance: {str(e)}"
        )
    except UltiBotError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al obtener balances de Binance: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {e}"
        )

@router.post("/binance/verify", summary="Disparar la verificación manual de credenciales de Binance")
async def verify_binance_credentials_manual(
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    credential_label: str = "default",
    credential_service: CredentialService = Depends(deps.get_credential_service)
):
    """
    Permite al usuario autenticado disparar manualmente la verificación de sus credenciales de Binance.
    """
    try:
        if not isinstance(current_user.id, UUID):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")
            
        credential = await credential_service.get_credential(current_user.id, ServiceName.BINANCE_SPOT, credential_label)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credencial de Binance con etiqueta '{credential_label}' no encontrada para el usuario {current_user.id}."
            )
        
        is_verified = await credential_service.verify_credential(credential)
        if is_verified:
            return {"message": "Verificación de credenciales de Binance iniciada y exitosa.", "status": "active"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La verificación de credenciales de Binance falló. Revise los logs para más detalles."
            )
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de credenciales durante la verificación manual: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante la verificación manual: {e}"
        )
