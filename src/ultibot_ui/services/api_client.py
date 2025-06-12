"""
Módulo que define el cliente API para la comunicación entre la UI y el backend.
Utiliza httpx para realizar solicitudes HTTP asíncronas.
"""

import httpx
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from src.ultibot_backend.core.domain_models.trading import CommandResult

class APIError(Exception):
    """Excepción personalizada para errores del cliente API."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

class UltiBotAPIClient:
    """
    Cliente API para interactuar con el backend de UltiBotInversiones.
    Abstrae las llamadas HTTP a los endpoints de comandos y consultas.
    """
    def __init__(self, base_url: str):
        """
        Inicializa el UltiBotAPIClient.

        Args:
            base_url (str): La URL base del backend de la API (ej. "http://localhost:8000/api/v1").
        """
        self._base_url = base_url
        self._client = httpx.AsyncClient()

    async def send_command(self, command_name: str, payload: Dict[str, Any]) -> CommandResult:
        """
        Envía un comando al backend.

        Args:
            command_name (str): El nombre del comando (ej. "place_order").
            payload (Dict[str, Any]): Los datos del comando.

        Returns:
            CommandResult: El resultado de la ejecución del comando.

        Raises:
            APIError: Si la solicitud HTTP falla de forma inesperada.
        """
        url = f"{self._base_url}/commands/{command_name}"
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()  # Lanza una excepción para códigos de estado HTTP 4xx/5xx
            return CommandResult.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            error_message = f"Error HTTP: {e.response.status_code}"
            try:
                # Intenta parsear el detalle del error del backend
                error_details = e.response.json().get("detail", e.response.text)
                error_message += f" - {error_details}"
            except Exception:
                error_message += f" - {e.response.text}"
            
            print(f"Error HTTP al enviar comando {command_name}: {error_message}")
            raise APIError(error_message, status_code=e.response.status_code, response_text=e.response.text) from e
        except httpx.RequestError as e:
            error_message = f"Error de red al enviar comando {command_name}: {e}"
            print(error_message)
            raise APIError(error_message) from e
        except Exception as e:
            error_message = f"Error inesperado al enviar comando {command_name}: {e}"
            print(error_message)
            raise APIError(error_message) from e

    async def fetch_query(self, query_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Realiza una consulta al backend.

        Args:
            query_name (str): El nombre de la consulta (ej. "get_portfolio").
            params (Optional[Dict[str, Any]]): Parámetros de la consulta.

        Returns:
            Dict[str, Any]: Los datos resultantes de la consulta.

        Raises:
            APIError: Si la solicitud HTTP falla.
        """
        url = f"{self._base_url}/queries/{query_name}"
        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_message = f"Error HTTP al realizar consulta {query_name}: {e.response.status_code} - {e.response.text}"
            print(error_message)
            raise APIError(error_message, status_code=e.response.status_code, response_text=e.response.text) from e
        except httpx.RequestError as e:
            error_message = f"Error de red al realizar consulta {query_name}: {e}"
            print(error_message)
            raise APIError(error_message) from e
        except Exception as e:
            error_message = f"Error inesperado al realizar consulta {query_name}: {e}"
            print(error_message)
            raise APIError(error_message) from e

    async def close(self) -> None:
        """Cierra la sesión HTTP del cliente."""
        await self._client.aclose()
