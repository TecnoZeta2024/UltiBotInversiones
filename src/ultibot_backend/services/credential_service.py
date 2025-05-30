import os
import json
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from uuid import UUID

from src.shared.data_types import APICredential, ServiceName, BinanceConnectionStatus, AssetBalance
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter # Importar BinanceAdapter
from src.ultibot_backend.core.exceptions import BinanceAPIError, CredentialError, ExternalAPIError # Importar excepciones relevantes
from datetime import datetime
import logging # Importar logging

logger = logging.getLogger(__name__) # Configurar logger

class CredentialService:
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Inicializa CredentialService.
        :param encryption_key: Clave de encriptación Fernet URL-safe base64-encoded.
                               Si es None o inválida, se generará una clave de prueba.
        """
        logger.info(f"CredentialService __init__ recibió encryption_key (str): {encryption_key}")
        # encryption_key aquí es la cadena base64url. Fernet() la manejará.
        # Solo necesitamos asegurarnos de que sea una cadena y no None.
        if not isinstance(encryption_key, str) or not encryption_key:
            logger.error("CREDENTIAL_ENCRYPTION_KEY debe ser una cadena no vacía.")
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY inválida en __init__.")
        
        # Pasamos la clave (string) directamente a Fernet, que espera bytes o string.
        # Si es string, Fernet la codificará a ascii y luego la decodificará de base64.
        logger.info(f"Pasando la siguiente clave (str) a Fernet: {encryption_key}")
        self.fernet = Fernet(encryption_key.encode('utf-8')) # Fernet espera bytes
        self.persistence_service = SupabasePersistenceService()
        self.binance_adapter = BinanceAdapter()
        # self.telegram_adapter = TelegramAdapter()
        # self.gemini_adapter = GeminiAdapter()
        # self.mobula_adapter = MobulaAdapter()

    def _get_encryption_key(self, provided_key: Optional[str]) -> bytes:
        """
        Valida la clave de encriptación proporcionada o genera una si es necesario.
        """
        if provided_key:
            try:
                # Asegurarse de que la clave proporcionada (string) se codifique a bytes antes de decodificarla con base64
                key_bytes = provided_key.encode('utf-8')
                decoded_key = base64.urlsafe_b64decode(key_bytes)
                if len(decoded_key) == 32:
                    logger.info("Usando clave de encriptación proporcionada.")
                    return decoded_key
                else:
                    # Si la longitud no es 32 después de la decodificación, es un error.
                    logger.error(f"La clave de encriptación decodificada no tiene 32 bytes de longitud: {len(decoded_key)} bytes. Clave original: {provided_key}")
                    raise ValueError("La clave de encriptación Fernet debe ser de 32 bytes después de la decodificación base64.")
            except Exception as e:
                logger.error(f"Error al procesar la clave de encriptación proporcionada '{provided_key}': {e}. Esto es un error crítico.")
                # Levantar una excepción para detener la inicialización si la clave es mala.
                raise ValueError(f"La clave de encriptación proporcionada no es válida: {e}")
        else:
            # Si no se proporciona ninguna clave, esto es un error de configuración.
            logger.error("No se proporcionó CREDENTIAL_ENCRYPTION_KEY. Este es un valor requerido.")
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY no puede ser None.")

    def encrypt_data(self, data: str) -> str:
        """
        Encripta una cadena de texto usando Fernet.
        """
        encoded_data = data.encode('utf-8')
        encrypted_data = self.fernet.encrypt(encoded_data)
        return encrypted_data.decode('utf-8')

    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """
        Desencripta una cadena de texto usando Fernet.
        Retorna None si la desencriptación falla (ej. token inválido).
        """
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except InvalidToken:
            print("Advertencia: Token de encriptación inválido. La desencriptación falló.")
            return None
        except Exception as e:
            print(f"Error inesperado durante la desencriptación: {e}")
            return None

    async def add_credential(self, user_id: UUID, service_name: ServiceName, credential_label: str, api_key: str, api_secret: Optional[str] = None, other_details: Optional[Dict[str, Any]] = None) -> APICredential:
        """
        Añade una nueva credencial encriptada a la base de datos.
        """
        encrypted_api_key = self.encrypt_data(api_key)
        encrypted_api_secret = self.encrypt_data(api_secret) if api_secret else None
        encrypted_other_details = self.encrypt_data(json.dumps(other_details)) if other_details else None

        credential_data = APICredential(
            user_id=user_id,
            service_name=service_name,
            credential_label=credential_label,
            encrypted_api_key=encrypted_api_key,
            encrypted_api_secret=encrypted_api_secret,
            encrypted_other_details=encrypted_other_details
        )
        saved_credential = await self.persistence_service.save_credential(credential_data)
        return saved_credential

    async def get_credential(self, user_id: UUID, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        """
        Recupera y desencripta una credencial de la base de datos.
        """
        encrypted_credential = await self.persistence_service.get_credential_by_service_label(user_id, service_name, credential_label)
        if encrypted_credential:
            decrypted_api_key = self.decrypt_data(encrypted_credential.encrypted_api_key)
            if decrypted_api_key is None:
                raise CredentialError(f"API Key para {encrypted_credential.service_name} no pudo ser desencriptada.")

            decrypted_api_secret = self.decrypt_data(encrypted_credential.encrypted_api_secret) if encrypted_credential.encrypted_api_secret else None
            if encrypted_credential.encrypted_api_secret and decrypted_api_secret is None:
                raise CredentialError(f"API Secret para {encrypted_credential.service_name} no pudo ser desencriptado.")
            
            decrypted_other_details_str = self.decrypt_data(encrypted_credential.encrypted_other_details) if encrypted_credential.encrypted_other_details else None
            decrypted_other_details = json.loads(decrypted_other_details_str) if decrypted_other_details_str else None
            
            # Retornar una copia con los datos desencriptados (o un objeto temporal)
            # Asegurarse de que los datos desencriptados no persistan más de lo necesario.
            return APICredential(
                id=encrypted_credential.id,
                user_id=encrypted_credential.user_id,
                service_name=encrypted_credential.service_name,
                credential_label=encrypted_credential.credential_label,
                encrypted_api_key=decrypted_api_key,
                encrypted_api_secret=decrypted_api_secret,
                encrypted_other_details=json.dumps(decrypted_other_details) if decrypted_other_details else None,
                status=encrypted_credential.status,
                last_verified_at=encrypted_credential.last_verified_at,
                permissions=encrypted_credential.permissions,
                permissions_checked_at=encrypted_credential.permissions_checked_at,
                expires_at=encrypted_credential.expires_at,
                rotation_reminder_policy_days=encrypted_credential.rotation_reminder_policy_days,
                usage_count=encrypted_credential.usage_count,
                last_used_at=encrypted_credential.last_used_at,
                purpose_description=encrypted_credential.purpose_description,
                tags=encrypted_credential.tags,
                notes=encrypted_credential.notes,
                created_at=encrypted_credential.created_at,
                updated_at=encrypted_credential.updated_at
            )
        return None

    async def update_credential(self, credential_id: UUID, api_key: Optional[str] = None, api_secret: Optional[str] = None, other_details: Optional[Dict[str, Any]] = None, status: Optional[str] = None) -> Optional[APICredential]:
        """
        Actualiza una credencial existente.
        """
        existing_credential = await self.persistence_service.get_credential_by_id(credential_id)
        if not existing_credential:
            return None

        # Encriptar solo los campos que se van a actualizar si se proporcionan nuevos valores
        updated_encrypted_api_key = existing_credential.encrypted_api_key
        if api_key is not None:
            updated_encrypted_api_key = self.encrypt_data(api_key)

        updated_encrypted_api_secret = existing_credential.encrypted_api_secret
        if api_secret is not None:
            updated_encrypted_api_secret = self.encrypt_data(api_secret)

        updated_encrypted_other_details = existing_credential.encrypted_other_details
        if other_details is not None:
            updated_encrypted_other_details = self.encrypt_data(json.dumps(other_details))

        # Crear un nuevo objeto APICredential con los datos actualizados
        updated_credential_data = APICredential(
            id=credential_id,
            user_id=existing_credential.user_id,
            service_name=existing_credential.service_name,
            credential_label=existing_credential.credential_label,
            encrypted_api_key=updated_encrypted_api_key,
            encrypted_api_secret=updated_encrypted_api_secret,
            encrypted_other_details=updated_encrypted_other_details,
            status=status if status else existing_credential.status,
            last_verified_at=existing_credential.last_verified_at,
            permissions=existing_credential.permissions,
            permissions_checked_at=existing_credential.permissions_checked_at,
            expires_at=existing_credential.expires_at,
            rotation_reminder_policy_days=existing_credential.rotation_reminder_policy_days,
            usage_count=existing_credential.usage_count,
            last_used_at=existing_credential.last_used_at,
            purpose_description=existing_credential.purpose_description,
            tags=existing_credential.tags,
            notes=existing_credential.notes,
            created_at=existing_credential.created_at,
            updated_at=datetime.utcnow() # Actualizar timestamp
        )
        
        saved_credential = await self.persistence_service.save_credential(updated_credential_data)
        return saved_credential

    async def delete_credential(self, credential_id: UUID) -> bool:
        """
        Elimina una credencial de la base de datos.
        """
        return await self.persistence_service.delete_credential(credential_id)

    async def verify_credential(self, credential: APICredential, notification_service: Optional[Any] = None) -> bool:
        """
        Verifica la validez de una credencial realizando una llamada de prueba no transaccional.
        Actualiza el estado de la credencial en la base de datos.
        Si es una credencial de Telegram, usa NotificationService para enviar un mensaje de prueba.
        """
        is_valid = False
        decrypted_api_key = self.decrypt_data(credential.encrypted_api_key)
        if decrypted_api_key is None:
            logger.error(f"Error de verificación para {credential.service_name}: API Key no pudo ser desencriptada.")
            await self.persistence_service.update_credential_status(credential.id, "verification_failed", datetime.utcnow())
            raise CredentialError(f"API Key para {credential.service_name} no pudo ser desencriptada.")

        decrypted_api_secret = None
        if credential.encrypted_api_secret:
            decrypted_api_secret = self.decrypt_data(credential.encrypted_api_secret)
            if decrypted_api_secret is None:
                logger.error(f"Error de verificación para {credential.service_name}: API Secret no pudo ser desencriptado.")
                await self.persistence_service.update_credential_status(credential.id, "verification_failed", datetime.utcnow())
                raise CredentialError(f"API Secret para {credential.service_name} no pudo ser desencriptado.")

        decrypted_other_details_str = self.decrypt_data(credential.encrypted_other_details) if credential.encrypted_other_details else None
        decrypted_other_details = json.loads(decrypted_other_details_str) if decrypted_other_details_str else {}

        try:
            if credential.service_name == ServiceName.TELEGRAM_BOT:
                if notification_service:
                    is_valid = await notification_service.send_test_telegram_notification(credential.user_id)
                    if is_valid:
                        logger.info(f"Verificación de Telegram exitosa para el usuario {credential.user_id}.")
                    else:
                        logger.warning(f"Verificación de Telegram fallida para el usuario {credential.user_id}.")
                else:
                    logger.warning(f"NotificationService no proporcionado para verificar Telegram. No se puede verificar.")
                    is_valid = False # No se puede verificar sin NotificationService
            elif credential.service_name in [ServiceName.BINANCE_SPOT, ServiceName.BINANCE_FUTURES]:
                if decrypted_api_secret is None:
                    logger.error(f"Error de verificación para Binance: API Secret no pudo ser desencriptado o es nulo.")
                    await self.persistence_service.update_credential_status(credential.id, "verification_failed", datetime.utcnow())
                    raise CredentialError(f"API Secret para Binance no pudo ser desencriptado o es nulo.")
                
                try:
                    # Intentar obtener información de la cuenta para verificar la validez de las credenciales
                    account_info = await self.binance_adapter.get_account_info(decrypted_api_key, decrypted_api_secret)
                    # Verificar si la cuenta tiene permisos de trading si es necesario (AC5)
                    can_trade = account_info.get("canTrade", False)
                    # Aquí se podría añadir lógica para verificar permisos específicos si la AC lo requiere
                    
                    is_valid = True
                    logger.info(f"Verificación de Binance {credential.service_name} exitosa para el usuario {credential.user_id}.")
                    # Actualizar permisos si se obtienen de la API
                    permissions = []
                    if account_info.get("canTrade"): permissions.append("SPOT_TRADING")
                    if account_info.get("canDeposit"): permissions.append("DEPOSIT")
                    if account_info.get("canWithdraw"): permissions.append("WITHDRAWAL")
                    # Otros permisos relevantes de Binance
                    await self.persistence_service.update_credential_permissions(credential.id, permissions, datetime.utcnow())

                except BinanceAPIError as e:
                    logger.error(f"Error de Binance API durante la verificación: {e}")
                    is_valid = False
                    # El estado ya se actualiza en el bloque finally
                except Exception as e:
                    logger.error(f"Error inesperado durante la verificación de Binance: {e}")
                    is_valid = False
            elif credential.service_name == ServiceName.GEMINI_API:
                logger.info(f"Simulando verificación para Gemini {credential.service_name}...")
                is_valid = True # Simulación
            elif credential.service_name == ServiceName.MOBULA_API:
                logger.info(f"Simulando verificación para Mobula {credential.service_name}...")
                is_valid = True # Simulación
            else:
                logger.info(f"No hay lógica de verificación implementada para el servicio: {credential.service_name}. Asumiendo válido.")
                is_valid = True # Asumir válido si no hay lógica específica

        except CredentialError: # Propagar errores de desencriptación
            raise
        except Exception as e:
            logger.error(f"Error general durante la verificación de {credential.service_name}: {e}", exc_info=True)
            is_valid = False
        
        # Actualizar el estado de la credencial en la base de datos
        new_status = "active" if is_valid else "verification_failed"
        await self.persistence_service.update_credential_status(credential.id, new_status, datetime.utcnow())
        
        return is_valid
