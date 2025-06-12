"""
Endpoints para verificar el estado y la conectividad con Binance.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ....shared.data_types import BinanceConnectionStatus, AssetBalance
from ...core.ports import IMarketDataProvider
from ...core.exceptions import CredentialError, UltiBotError, BinanceAPIError
from ...dependencies import get_binance_adapter

router = APIRouter()

@router.get("/binance/status", response_model=BinanceConnectionStatus, summary="Obtener el estado de conexión con Binance")
async def get_binance_status(
    market_provider: IMarketDataProvider = Depends(get_binance_adapter)
) -> BinanceConnectionStatus:
    """
    Retorna el estado actual de la conexión con la API de Binance,
    incluyendo si las credenciales son válidas y los permisos de la cuenta.
    """
    try:
        # Se asume que el proveedor de mercado tiene un método para obtener el estado.
        status_result = await market_provider.get_connection_status()
        return status_result
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de credenciales: {e}"
        )
    except BinanceAPIError as e:
        raise HTTPException(
            status_code=e.status_code if e.status_code else status.HTTP_502_BAD_GATEWAY,
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
    market_provider: IMarketDataProvider = Depends(get_binance_adapter)
) -> List[AssetBalance]:
    """
    Retorna la lista de balances de activos en la cuenta de Spot de Binance.
    """
    try:
        # Se asume que el proveedor de mercado tiene un método para obtener los balances.
        balances = await market_provider.get_spot_balances()
        return balances
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de credenciales: {e}"
        )
    except BinanceAPIError as e:
        raise HTTPException(
            status_code=e.status_code if e.status_code else status.HTTP_502_BAD_GATEWAY,
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
    market_provider: IMarketDataProvider = Depends(get_binance_adapter)
):
    """
    Permite disparar manualmente la verificación de las credenciales de Binance.
    """
    try:
        # Se asume que el proveedor de mercado tiene un método para verificar las credenciales.
        is_verified = await market_provider.verify_credentials()
        if is_verified:
            return {"message": "Verificación de credenciales de Binance exitosa.", "status": "active"}
        else:
            # Este caso es poco probable si verify_credentials levanta una excepción en caso de fallo.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La verificación de credenciales de Binance falló. Revise los logs para más detalles."
            )
    except CredentialError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error de credenciales durante la verificación manual: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado durante la verificación manual: {e}"
        )
