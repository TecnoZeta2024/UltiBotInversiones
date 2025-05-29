import httpx
import logging
import asyncio # Importar asyncio
from typing import Optional, Dict, Any
from src.ultibot_backend.core.exceptions import ExternalAPIError # Importar la excepción

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramAdapter:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.client = httpx.AsyncClient(timeout=10) # Timeout de 10 segundos para solicitudes

    async def send_message(self, chat_id: str, message: str, parse_mode: Optional[str] = "HTML") -> Dict[str, Any]:
        """
        Envía un mensaje a un chat de Telegram específico.

        Args:
            chat_id: El ID del chat de Telegram al que enviar el mensaje.
            message: El contenido del mensaje a enviar.
            parse_mode: Modo de parseo para el mensaje (ej. "HTML", "MarkdownV2").

        Returns:
            Un diccionario con la respuesta de la API de Telegram.

        Raises:
            ExternalAPIError: Si ocurre un error al interactuar con la API de Telegram.
            ValueError: Si el token del bot no está configurado.
        """
        if not self.bot_token:
            logger.error("Telegram bot token no está configurado. No se puede enviar el mensaje.")
            raise ValueError("Telegram bot token no configurado.")

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }

        try:
            # Implementación de reintentos básicos
            for attempt in range(3): # Intentar 3 veces
                try:
                    response = await self.client.post(url, json=payload)
                    response.raise_for_status()  # Lanza HTTPStatusError para respuestas 4xx/5xx
                    logger.info(f"Mensaje enviado a Telegram con éxito a chat_id: {chat_id[:4]}... (oculto)")
                    return response.json()
                except httpx.HTTPStatusError as e:
                    if 400 <= e.response.status_code < 500:
                        # Errores del cliente (ej. token inválido, chat_id incorrecto) no se reintentan
                        logger.error(f"Error de la API de Telegram (cliente) al enviar mensaje: {e.response.status_code} - {e.response.text}. Intento {attempt + 1}/3. No se reintentará.")
                        raise
                    else:
                        # Errores del servidor o transitorios se reintentan
                        logger.warning(f"Error de la API de Telegram (servidor/transitorio) al enviar mensaje: {e.response.status_code} - {e.response.text}. Reintentando... ({attempt + 1}/3)")
                        await self._sleep_for_retry(attempt)
                except httpx.RequestError as e:
                    logger.warning(f"Error de red al enviar mensaje a Telegram: {e}. Reintentando... ({attempt + 1}/3)")
                    await self._sleep_for_retry(attempt)
            
            # Si todos los reintentos fallan
            logger.error(f"Fallo al enviar mensaje a Telegram después de múltiples reintentos a chat_id: {chat_id[:4]}... (oculto)")
            raise ExternalAPIError(
                message="Fallo al enviar mensaje a Telegram después de múltiples reintentos.",
                service_name="Telegram",
                original_exception=httpx.RequestError(f"Fallo al enviar mensaje a Telegram después de múltiples reintentos.")
            )

        except httpx.RequestError as e:
            logger.error(f"Error de conexión o timeout al enviar mensaje a Telegram: {e}")
            raise ExternalAPIError(
                message=f"Error de conexión o timeout con la API de Telegram: {e}",
                service_name="Telegram",
                original_exception=e
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"Error de la API de Telegram: {e.response.status_code} - {e.response.text}")
            raise ExternalAPIError(
                message=f"La API de Telegram devolvió un error: {e.response.status_code} - {e.response.text}",
                service_name="Telegram",
                status_code=e.response.status_code,
                response_data=e.response.json() if e.response.text else None,
                original_exception=e
            )
        except Exception as e:
            logger.error(f"Error inesperado al enviar mensaje a Telegram: {e}", exc_info=True)
            raise ExternalAPIError(
                message=f"Error inesperado al interactuar con la API de Telegram: {e}",
                service_name="Telegram",
                original_exception=e
            )

    async def _sleep_for_retry(self, attempt: int):
        """Espera un tiempo antes de reintentar."""
        await asyncio.sleep(2 ** attempt) # Backoff exponencial simple

    async def close(self):
        """Cierra el cliente HTTPX."""
        await self.client.aclose()

# Ejemplo de uso (para pruebas locales, no parte del código de producción)
# async def main():
#     # Asegúrate de que TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID estén configurados en tus variables de entorno
#     # o pásalos directamente para pruebas.
#     bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
#     chat_id = os.getenv("TELEGRAM_CHAT_ID")

#     if not bot_token or not chat_id:
#         print("Por favor, configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en tus variables de entorno.")
#         return

#     adapter = TelegramAdapter(bot_token=bot_token)
#     try:
#         response = await adapter.send_message(chat_id, "¡Hola desde UltiBotInversiones! Este es un mensaje de prueba.")
#         print("Respuesta de Telegram:", response)
#     except Exception as e:
#         print("Error al enviar mensaje:", e)
#     finally:
#         await adapter.close()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
