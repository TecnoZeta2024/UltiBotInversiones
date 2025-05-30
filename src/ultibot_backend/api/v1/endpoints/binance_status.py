from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.shared.data_types import BinanceConnectionStatus, AssetBalance, ServiceName # Importar ServiceName
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import CredentialError, UltiBotError, BinanceAPIError

router = APIRouter()

# Dependencias para inyección de servicios
async def get_market_data_service() -> MarketDataService:
    from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
    credential_service = CredentialService()
    binance_adapter = BinanceAdapter()
    return MarketDataService(credential_service, binance_adapter)

@router.get("/binance/status", response_model=BinanceConnectionStatus, summary="Obtener el estado de conexión con Binance")
async def get_binance_status(
    user_id: UUID,
    market_data_service: MarketDataService = Depends(get_market_data_service)
) -> BinanceConnectionStatus:
    """
    Retorna el estado actual de la conexión con la API de Binance para un usuario específico,
    incluyendo si las credenciales son válidas y los permisos de la cuenta.
    """
    try:
        status_result = await market_data_service.get_binance_connection_status(user_id)
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
    user_id: UUID,
    market_data_service: MarketDataService = Depends(get_market_data_service)
) -> List[AssetBalance]:
    """
    Retorna la lista de balances de activos en la cuenta de Spot de Binance para un usuario específico.
    """
    try:
        balances = await market_data_service.get_binance_spot_balances(user_id)
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
    user_id: UUID,
    credential_label: str = "default",
    credential_service: CredentialService = Depends(CredentialService)
):
    """
    Permite al usuario disparar manualmente la verificación de sus credenciales de Binance.
    """
    try:
        credential = await credential_service.get_credential(user_id, ServiceName.BINANCE_SPOT, credential_label)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credencial de Binance con etiqueta '{credential_label}' no encontrada para el usuario {user_id}."
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
