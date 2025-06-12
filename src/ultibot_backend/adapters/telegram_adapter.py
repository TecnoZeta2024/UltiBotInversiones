"""
Adaptador para la API de Telegram.

Este adaptador se encarga de enviar notificaciones y alertas a través de un bot de Telegram.
Implementa la interfaz `INotificationService` (conceptual).
"""

import logging
from typing import Dict, Any
import httpx

from ..core.exceptions import NotificationError

logger = logging.getLogger(__name__)

class TelegramAdapter:
    """
    Adaptador para enviar mensajes a través de la API de Telegram.
    """

    def __init__(self, api_token: str, chat_id: str):
        """
        Inicializa el adaptador de Telegram.

        Args:
            api_token: El token de la API del bot de Telegram.
            chat_id: El ID del chat al que se enviarán los mensajes.
        """
        if not api_token or not chat_id:
            raise ValueError("El token de la API y el ID del chat de Telegram son obligatorios.")
        
        self.api_token = api_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.api_token}"

    async def send_message(self, message: str, parse_mode: str = "MarkdownV2") -> Dict[str, Any]:
        """
        Envía un mensaje a un chat de Telegram.

        Args:
            message: El texto del mensaje a enviar.
            parse_mode: El modo de formato del mensaje (MarkdownV2, HTML).

        Returns:
            La respuesta de la API de Telegram.

        Raises:
            NotificationError: Si ocurre un error al enviar el mensaje.
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()  # Lanza una excepción para respuestas 4xx/5xx
                
                logger.info(f"Mensaje enviado exitosamente a Telegram (Chat ID: {self.chat_id})")
                return response.json()

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

def create_telegram_adapter(api_token: str, chat_id: str) -> "TelegramAdapter":
    """
    Factory function para crear una instancia de TelegramAdapter.

    Args:
        api_token: El token de la API del bot de Telegram.
        chat_id: El ID del chat de destino.

    Returns:
        Una instancia de TelegramAdapter.
    """
    return TelegramAdapter(api_token=api_token, chat_id=chat_id)
