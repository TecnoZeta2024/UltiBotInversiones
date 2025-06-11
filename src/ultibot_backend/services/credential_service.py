import os
import json
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from uuid import UUID
from dotenv import load_dotenv
from fastapi import Depends

from src.shared.data_types import APICredential, ServiceName
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.core.exceptions import BinanceAPIError, CredentialError
from src.ultibot_backend.app_config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class CredentialService:
    def __init__(self, 
                 persistence_service: SupabasePersistenceService,
                 binance_adapter: BinanceAdapter
                 ):
        encryption_key_str = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        logger.info(f"CredentialService __init__ intentando obtener encryption_key de ENV: {'Presente' if encryption_key_str else 'Ausente'}")

        if not encryption_key_str:
            logger.critical("CREDENTIAL_ENCRYPTION_KEY no está configurada en las variables de entorno o está vacía.")
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY es requerida y no está configurada o está vacía.")
        
        logger.info(f"Pasando la siguiente clave (str) a Fernet: {encryption_key_str[:5]}... (truncada por seguridad)")
        try:
            self.fernet = Fernet(encryption_key_str.encode('utf-8'))
        except Exception as e:
            logger.critical(f"Error al inicializar Fernet con la clave de encriptación: {e}", exc_info=True)
            raise ValueError(f"Error al inicializar Fernet: {e}")

        self.persistence_service = persistence_service
        self.binance_adapter = binance_adapter
        self.fixed_user_id = settings.FIXED_USER_ID

    def encrypt_data(self, data: str) -> str:
        encoded_data = data.encode('utf-8')
        encrypted_data = self.fernet.encrypt(encoded_data)
        return encrypted_data.decode('utf-8')

    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except InvalidToken:
            print("Advertencia: Token de encriptación inválido. La desencriptación falló.")
            return None
        except Exception as e:
            print(f"Error inesperado durante la desencriptación: {e}")
            return None

    async def add_credential(self, service_name: ServiceName, credential_label: str, api_key: str, api_secret: Optional[str] = None, other_details: Optional[Dict[str, Any]] = None) -> APICredential:
        encrypted_api_key = self.encrypt_data(api_key)
        encrypted_api_secret = self.encrypt_data(api_secret) if api_secret else None
        encrypted_other_details = self.encrypt_data(json.dumps(other_details)) if other_details else None

        credential_data = APICredential(
            user_id=self.fixed_user_id,
            service_name=service_name,
            credential_label=credential_label,
            encrypted_api_key=encrypted_api_key,
            encrypted_api_secret=encrypted_api_secret,
            encrypted_other_details=encrypted_other_details
        )
        saved_credential = await self.persistence_service.save_credential(credential_data)
        return saved_credential

    async def save_encrypted_credential(self, credential: APICredential) -> APICredential:
        saved_credential = await self.persistence_service.save_credential(credential)
        return saved_credential

    async def get_credential(self, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        encrypted_credential = await self.persistence_service.get_credential_by_service_label(service_name, credential_label)
        if encrypted_credential:
            decrypted_api_key = self.decrypt_data(encrypted_credential.encrypted_api_key)
            if decrypted_api_key is None:
                raise CredentialError(f"API Key para {encrypted_credential.service_name} no pudo ser desencriptada.")

            decrypted_api_secret = self.decrypt_data(encrypted_credential.encrypted_api_secret) if encrypted_credential.encrypted_api_secret else None
            if encrypted_credential.encrypted_api_secret and decrypted_api_secret is None:
                raise CredentialError(f"API Secret para {encrypted_credential.service_name} no pudo ser desencriptado.")
            
            decrypted_other_details_str = self.decrypt_data(encrypted_credential.encrypted_other_details) if encrypted_credential.encrypted_other_details else None
            decrypted_other_details = json.loads(decrypted_other_details_str) if decrypted_other_details_str else None
            
            # Reconstruimos el objeto con los datos desencriptados para el retorno
            decrypted_credential = encrypted_credential.model_copy(deep=True)
            decrypted_credential.encrypted_api_key = decrypted_api_key
            decrypted_credential.encrypted_api_secret = decrypted_api_secret
            decrypted_credential.encrypted_other_details = json.dumps(decrypted_other_details) if decrypted_other_details else None
            
            return decrypted_credential
        return None

    async def update_credential(self, credential_id: UUID, api_key: Optional[str] = None, api_secret: Optional[str] = None, other_details: Optional[Dict[str, Any]] = None, status: Optional[str] = None) -> Optional[APICredential]:
        existing_credential = await self.persistence_service.get_credential_by_id(credential_id)
        if not existing_credential:
            return None

        update_data = existing_credential.model_dump()

        if api_key is not None:
            update_data['encrypted_api_key'] = self.encrypt_data(api_key)
        if api_secret is not None:
            update_data['encrypted_api_secret'] = self.encrypt_data(api_secret)
        if other_details is not None:
            update_data['encrypted_other_details'] = self.encrypt_data(json.dumps(other_details))
        if status is not None:
            update_data['status'] = status
        
        update_data['updated_at'] = datetime.utcnow()

        updated_credential_model = APICredential(**update_data)
        
        saved_credential = await self.persistence_service.save_credential(updated_credential_model)
        return saved_credential

    async def delete_credential(self, credential_id: UUID) -> bool:
        return await self.persistence_service.delete_credential(credential_id)

    async def get_decrypted_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]:
        encrypted_credential = await self.persistence_service.get_credential_by_id(credential_id)
        if encrypted_credential:
            decrypted_api_key = self.decrypt_data(encrypted_credential.encrypted_api_key)
            if decrypted_api_key is None:
                logger.error(f"API Key para la credencial ID {credential_id} no pudo ser desencriptada.")
                raise CredentialError(f"API Key para la credencial ID {credential_id} ({encrypted_credential.service_name}) no pudo ser desencriptada.")

            decrypted_api_secret = self.decrypt_data(encrypted_credential.encrypted_api_secret) if encrypted_credential.encrypted_api_secret else None
            if encrypted_credential.encrypted_api_secret and decrypted_api_secret is None:
                logger.error(f"API Secret para la credencial ID {credential_id} ({encrypted_credential.service_name}) no pudo ser desencriptado.")
                raise CredentialError(f"API Secret para la credencial ID {credential_id} ({encrypted_credential.service_name}) no pudo ser desencriptado.")
            
            decrypted_other_details_str = self.decrypt_data(encrypted_credential.encrypted_other_details) if encrypted_credential.encrypted_other_details else None
            decrypted_other_details = json.loads(decrypted_other_details_str) if decrypted_other_details_str else None
            
            decrypted_credential = encrypted_credential.model_copy(deep=True)
            decrypted_credential.encrypted_api_key = decrypted_api_key
            decrypted_credential.encrypted_api_secret = decrypted_api_secret
            decrypted_credential.encrypted_other_details = json.dumps(decrypted_other_details) if decrypted_other_details else None

            return decrypted_credential
        return None

    async def get_first_decrypted_credential_by_service(self, service_name: ServiceName) -> Optional[APICredential]:
        encrypted_credentials = await self.persistence_service.get_credentials_by_service(service_name)
        if not encrypted_credentials:
            logger.info(f"No se encontraron credenciales para el servicio {service_name.value} y usuario {self.fixed_user_id}.")
            return None

        encrypted_credential = encrypted_credentials[0]
        
        decrypted_api_key = self.decrypt_data(encrypted_credential.encrypted_api_key)
        if decrypted_api_key is None:
            logger.error(f"API Key para la credencial ID {encrypted_credential.id} ({service_name.value}) no pudo ser desencriptada.")
            raise CredentialError(f"API Key para la credencial ID {encrypted_credential.id} ({service_name.value}) no pudo ser desencriptada.")

        decrypted_api_secret = self.decrypt_data(encrypted_credential.encrypted_api_secret) if encrypted_credential.encrypted_api_secret else None
        if encrypted_credential.encrypted_api_secret and decrypted_api_secret is None:
            logger.error(f"API Secret para la credencial ID {encrypted_credential.id} ({service_name.value}) no pudo ser desencriptado.")
            raise CredentialError(f"API Secret para la credencial ID {encrypted_credential.id} ({service_name.value}) no pudo ser desencriptado.")
        
        decrypted_other_details_str = self.decrypt_data(encrypted_credential.encrypted_other_details) if encrypted_credential.encrypted_other_details else None
        decrypted_other_details = json.loads(decrypted_other_details_str) if decrypted_other_details_str else None
        
        decrypted_credential = encrypted_credential.model_copy(deep=True)
        decrypted_credential.encrypted_api_key = decrypted_api_key
        decrypted_credential.encrypted_api_secret = decrypted_api_secret
        decrypted_credential.encrypted_other_details = json.dumps(decrypted_other_details) if decrypted_other_details else None
        
        return decrypted_credential

    async def verify_credential(self, credential: APICredential, notification_service: Optional[Any] = None) -> bool:
        is_valid = False
        
        # Usamos los datos ya desencriptados del objeto que recibimos
        decrypted_api_key = credential.encrypted_api_key
        decrypted_api_secret = credential.encrypted_api_secret

        try:
            if credential.service_name == ServiceName.TELEGRAM_BOT:
                if notification_service:
                    is_valid = await notification_service.send_test_telegram_notification()
                    if is_valid:
                        logger.info(f"Verificación de Telegram exitosa.")
                    else:
                        logger.warning(f"Verificación de Telegram fallida.")
                else:
                    logger.warning(f"NotificationService no proporcionado para verificar Telegram. No se puede verificar.")
                    is_valid = False
            elif credential.service_name in [ServiceName.BINANCE_SPOT, ServiceName.BINANCE_FUTURES]:
                if decrypted_api_key is None or decrypted_api_secret is None:
                    raise CredentialError(f"API Key o Secret para Binance son nulos.")
                
                try:
                    account_info = await self.binance_adapter.get_account_info(decrypted_api_key, decrypted_api_secret)
                    is_valid = account_info.get("canTrade", False)
                    
                    if is_valid:
                        logger.info(f"Verificación de Binance {credential.service_name} exitosa.")
                        permissions = []
                        if account_info.get("canTrade"): permissions.append("SPOT_TRADING")
                        if account_info.get("canDeposit"): permissions.append("DEPOSIT")
                        if account_info.get("canWithdraw"): permissions.append("WITHDRAWAL")
                        await self.persistence_service.update_credential_permissions(credential.id, permissions, datetime.utcnow())
                    else:
                        logger.warning(f"Verificación de Binance {credential.service_name} fallida: canTrade es False.")

                except BinanceAPIError as e:
                    logger.error(f"Error de Binance API durante la verificación: {str(e)}")
                    is_valid = False
            else:
                logger.info(f"No hay lógica de verificación implementada para el servicio: {credential.service_name}. Asumiendo válido.")
                is_valid = True

        except CredentialError:
            raise
        except Exception as e:
            logger.error(f"Error general durante la verificación de {credential.service_name}: {e}", exc_info=True)
            is_valid = False
        
        new_status = "active" if is_valid else "verification_failed"
        await self.persistence_service.update_credential_status(credential.id, new_status, datetime.utcnow())
        
        return is_valid

    async def verify_binance_api_key(self) -> bool:
        binance_credential = await self.get_first_decrypted_credential_by_service(service_name=ServiceName.BINANCE_SPOT)
        
        if not binance_credential:
            logger.error(f"No se encontró credencial de Binance para el usuario {self.fixed_user_id}.")
            raise CredentialError(f"No se encontró credencial de Binance para el usuario {self.fixed_user_id}.")

        try:
            if binance_credential.encrypted_api_key is None or binance_credential.encrypted_api_secret is None:
                raise CredentialError("El API Key o Secret de Binance es requerido pero no se encontró en la credencial.")

            account_info = await self.binance_adapter.get_account_info(
                api_key=binance_credential.encrypted_api_key,
                api_secret=binance_credential.encrypted_api_secret
            )
            
            if not account_info.get("canTrade", False):
                raise BinanceAPIError(
                    message="La API Key de Binance no tiene permisos de trading.",
                    response_data=account_info
                )
            
            await self.persistence_service.update_credential_status(binance_credential.id, "active", datetime.utcnow())
            logger.info(f"API Key de Binance verificada exitosamente para el usuario {self.fixed_user_id}.")
            return True
        except BinanceAPIError as e:
            logger.error(f"Fallo en la verificación de la API Key de Binance para {self.fixed_user_id}: {str(e)}", exc_info=True)
            await self.persistence_service.update_credential_status(binance_credential.id, "verification_failed", datetime.utcnow())
            raise e
        except Exception as e:
            logger.error(f"Error inesperado durante la verificación de la API Key de Binance para {self.fixed_user_id}: {str(e)}", exc_info=True)
            await self.persistence_service.update_credential_status(binance_credential.id, "verification_failed", datetime.utcnow())
            raise BinanceAPIError(message="Error inesperado al verificar la API Key de Binance.", original_exception=e)
