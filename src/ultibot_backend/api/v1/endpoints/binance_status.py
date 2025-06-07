from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
from uuid import UUID

from src.shared.data_types import BinanceConnectionStatus, AssetBalance, ServiceName
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import CredentialError, UltiBotError, BinanceAPIError
from src.ultibot_backend.dependencies import DependencyContainer

router = APIRouter()

def get_container(request: Request) -> DependencyContainer:
    return request.app.state.container

@router.get("/binance/status", response_model=BinanceConnectionStatus, summary="Obtener el estado de conexión con Binance")
async def get_binance_status(
    container: DependencyContainer = Depends(get_container)
) -> BinanceConnectionStatus:
    """
    Retorna el estado actual de la conexión con la API de Binance,
    incluyendo si las credenciales son válidas y los permisos de la cuenta.
    """
    market_data_service = container.market_data_service
    assert market_data_service is not None, "MarketDataService no inicializado"
    try:
        status_result = await market_data_service.get_binance_connection_status()
        return status_result
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error de credenciales: {e}"
        )
    except BinanceAPIError as e:
        raise HTTPException(
            status_code=e.status_code if e.status_code else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de la API de Binance: {str(e)}"
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
    container: DependencyContainer = Depends(get_container)
) -> List[AssetBalance]:
    """
    Retorna la lista de balances de activos en la cuenta de Spot de Binance.
    """
    market_data_service = container.market_data_service
    assert market_data_service is not None, "MarketDataService no inicializado"
    try:
        balances = await market_data_service.get_binance_spot_balances()
        return balances
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error de credenciales: {e}"
        )
    except BinanceAPIError as e:
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
    request: Request,
    credential_label: str = "default"
):
    """
    Permite disparar manualmente la verificación de las credenciales de Binance.
    """
    try:
        container: DependencyContainer = get_container(request)
        credential_service = container.credential_service
        assert credential_service is not None, "CredentialService no inicializado"
        credential = await credential_service.get_credential(service_name=ServiceName.BINANCE_SPOT, credential_label=credential_label)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credencial de Binance con etiqueta '{credential_label}' no encontrada."
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
