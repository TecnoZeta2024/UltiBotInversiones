"""
Adaptador para la API de Telegram.

Este adaptador se encarga de enviar notificaciones y alertas a través de un bot de Telegram.
Implementa la interfaz `INotificationPort`.
"""

import logging
from typing import Dict, Any, Optional
import httpx
import json

from ..core.ports import INotificationPort, ICredentialService, IPersistencePort
from ..core.exceptions import NotificationError, CredentialError
from shared.data_types import ServiceName

logger = logging.getLogger(__name__)

class TelegramAdapter(INotificationPort):
    """
    Adaptador para enviar mensajes a través de la API de Telegram.
    """

    def __init__(self, credential_service: ICredentialService, persistence_port: IPersistencePort):
        """
        Inicializa el adaptador de Telegram.
        """
        self._credential_service = credential_service
        self._persistence_port = persistence_port
        self._api_token: Optional[str] = None
        self._chat_id: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _initialize(self):
        """Carga las credenciales y configura el cliente httpx."""
        if self._client:
            return

        creds = await self._credential_service.get_first_decrypted_credential_by_service(ServiceName.TELEGRAM_BOT)
        if not creds or not creds.encrypted_api_key or not creds.encrypted_other_details:
            raise CredentialError("Credenciales de Telegram (API Token o Chat ID) no configuradas.")

        self._api_token = creds.encrypted_api_key
        
        try:
            other_details = json.loads(creds.encrypted_other_details) # Assuming encrypted_other_details is a JSON string
            self._chat_id = other_details.get("chat_id")
            if not self._chat_id:
                raise CredentialError("Chat ID no encontrado en los detalles de la credencial de Telegram.")
        except (json.JSONDecodeError, KeyError) as e:
            raise CredentialError(f"Error al procesar los detalles de la credencial de Telegram: {e}")

        self.base_url = f"https://api.telegram.org/bot{self._api_token}"
        self._client = httpx.AsyncClient()

    async def send_alert(self, message: str, priority: str) -> None: # MODIFIED: level -> priority, return type bool -> None
        """
        Envía una alerta a un chat de Telegram.

        Args:
            message: El texto del mensaje a enviar.
            priority: El nivel de la alerta (ej. 'info', 'warning', 'error'). No se usa directamente en la lógica de Telegram pero coincide con el puerto.

        Raises:
            NotificationError: Si ocurre un error grave al enviar el mensaje.
        """
        await self._initialize()
        if not self._client or not self._chat_id:
            raise NotificationError("El adaptador de Telegram no está inicializado correctamente.")

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": message,
            "parse_mode": "MarkdownV2", # Consider HTML for more robust formatting if needed
        }

        try:
            response = await self._client.post(url, json=payload, timeout=10.0)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx
            
            response_data = response.json()
            if not response_data.get("ok"):
                # Telegram API specific error, even with 200 OK
                error_description = response_data.get('description', 'Unknown error from Telegram API.')
                logger.error(f"Error de API de Telegram al enviar mensaje (ok=false): {error_description}")
                # Optionally, still raise NotificationError here if "ok=false" is critical
                # For now, just logging as the port doesn't return success/failure
            else:
                logger.info(f"Mensaje enviado exitosamente a Telegram (Chat ID: {self._chat_id})")
            # No return value as per port

        except httpx.HTTPStatusError as e:
            error_message = f"Error de estado HTTP al enviar mensaje a Telegram: {e.response.status_code} - {e.response.text}"
            logger.error(error_message)
            raise NotificationError(error_message) from e
        except httpx.RequestError as e:
            error_message = f"Error de red al conectar con la API de Telegram: {e}"
            logger.error(error_message)
            raise NotificationError(error_message) from e
        except Exception as e:
            error_message = f"Un error inesperado ocurrió al enviar el mensaje de Telegram: {e}"
            logger.error(error_message)
            raise NotificationError(error_message) from e

    async def close(self):
        """Cierra el cliente HTTP si existe."""
        if self._client:
            await self._client.aclose()
            self._client = None
