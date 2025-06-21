import os
import json
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from uuid import UUID
from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from shared.data_types import APICredential, ServiceName
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.adapters.binance_adapter import BinanceAdapter
from ultibot_backend.core.exceptions import BinanceAPIError, CredentialError
from ultibot_backend.app_config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

load_dotenv()

class CredentialService:
    def __init__(self, 
                 session_factory: async_sessionmaker[AsyncSession],
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

        self.session_factory = session_factory
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
            logger.warning("Advertencia: Token de encriptación inválido. La desencriptación falló.")
            return None
        except Exception as e:
            logger.error(f"Error inesperado durante la desencriptación: {e}")
            return None

    async def add_credential(self, service_name: ServiceName, credential_label: str, api_key: str, api_secret: Optional[str] = None, other_details: Optional[Dict[str, Any]] = None) -> APICredential:
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            encrypted_api_key = self.encrypt_data(api_key)
            encrypted_api_secret = self.encrypt_data(api_secret) if api_secret is not None else None # Corrected to handle None explicitly
            encrypted_other_details = self.encrypt_data(json.dumps(other_details)) if other_details is not None else None # Corrected to handle None explicitly

            credential_data = APICredential(
                user_id=self.fixed_user_id,
                service_name=service_name,
                credential_label=credential_label,
                encrypted_api_key=encrypted_api_key,
                encrypted_api_secret=encrypted_api_secret,
                encrypted_other_details=encrypted_other_details
            )
            # Usar upsert en lugar de save_credential
            await persistence_service.upsert(
                table_name="api_credentials",
                data=credential_data.model_dump(mode='json'), # Convertir a dict para upsert
                on_conflict=["user_id", "service_name", "credential_label"] # Asumiendo estas son las claves de conflicto
            )
            # Para devolver el objeto guardado, necesitamos recuperarlo de la BD o construirlo
            # Por simplicidad, devolveremos el objeto que intentamos guardar.
            return credential_data

    async def save_encrypted_credential(self, credential: APICredential) -> APICredential:
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            # Usar upsert en lugar de save_credential
            await persistence_service.upsert(
                table_name="api_credentials",
                data=credential.model_dump(mode='json'),
                on_conflict=["user_id", "service_name", "credential_label"]
            )
            return credential

    async def get_credential(self, service_name: ServiceName, credential_label: str) -> Optional[APICredential]:
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            # Usar get_one en lugar de get_credential_by_service_label
            service_name_value = service_name.value if isinstance(service_name, ServiceName) else service_name
            condition = f"user_id = '{self.fixed_user_id}' AND service_name = '{service_name_value}' AND credential_label = '{credential_label}'"
            encrypted_credential_data = await persistence_service.get_one(table_name="api_credentials", condition=condition)
            
            if encrypted_credential_data:
                encrypted_credential = APICredential.model_validate(encrypted_credential_data) # Reconstruir Pydantic model
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
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            
            condition = f"id = '{credential_id}'"
            existing_credential_data = await persistence_service.get_one(table_name="api_credentials", condition=condition)
            if not existing_credential_data:
                return None
            
            existing_credential = APICredential.model_validate(existing_credential_data)

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
            
            # Usar upsert en lugar de save_credential
            await persistence_service.upsert(
                table_name="api_credentials",
                data=updated_credential_model.model_dump(mode='json'),
                on_conflict=["id"] # Conflicto por ID para actualizar
            )
            return updated_credential_model

    async def delete_credential(self, credential_id: UUID) -> bool:
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            condition = f"id = '{credential_id}'"
            await persistence_service.delete(table_name="api_credentials", condition=condition)
            return True # Asumimos éxito si no hay excepción

    async def get_decrypted_credential_by_id(self, credential_id: UUID) -> Optional[APICredential]:
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            condition = f"id = '{credential_id}'"
            encrypted_credential_data = await persistence_service.get_one(table_name="api_credentials", condition=condition)
            
            if encrypted_credential_data:
                encrypted_credential = APICredential.model_validate(encrypted_credential_data) # Reconstruir Pydantic model
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
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            condition = f"user_id = '{self.fixed_user_id}' AND service_name = '{service_name.value}'"
            encrypted_credentials_data = await persistence_service.get_all(table_name="api_credentials", condition=condition)
            
            if not encrypted_credentials_data:
                logger.info(f"No se encontraron credenciales para el servicio {service_name.value} y usuario {self.fixed_user_id}.")
                return None

            encrypted_credential = APICredential.model_validate(encrypted_credentials_data[0]) # Reconstruir Pydantic model
            
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
        async with self.session_factory() as session:
            persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
            is_valid = False
            
            try:
                if credential.service_name == ServiceName.TELEGRAM_BOT:
                    if notification_service:
                        is_valid = await notification_service.send_test_telegram_notification()
                        if is_valid:
                            logger.info(f"Verificación de Telegram exitosa.")
                            # Usar upsert para actualizar el estado
                            update_data = credential.model_dump(mode='json')
                            update_data['status'] = "active"
                            update_data['updated_at'] = datetime.utcnow().isoformat()
                            await persistence_service.upsert(
                                table_name="api_credentials",
                                data=update_data,
                                on_conflict=["id"]
                            )
                        else:
                            logger.warning(f"Verificación de Telegram fallida.")
                            # Usar upsert para actualizar el estado
                            update_data = credential.model_dump(mode='json')
                            update_data['status'] = "verification_failed"
                            update_data['updated_at'] = datetime.utcnow().isoformat()
                            await persistence_service.upsert(
                                table_name="api_credentials",
                                data=update_data,
                                on_conflict=["id"]
                            )
                    else:
                        logger.warning(f"NotificationService no proporcionado para verificar Telegram. No se puede verificar.")
                        is_valid = False
                        # Usar upsert para actualizar el estado
                        update_data = credential.model_dump(mode='json')
                        update_data['status'] = "verification_failed"
                        update_data['updated_at'] = datetime.utcnow().isoformat()
                        await persistence_service.upsert(
                            table_name="api_credentials",
                            data=update_data,
                            on_conflict=["id"]
                        )
                elif credential.service_name in [ServiceName.BINANCE_SPOT, ServiceName.BINANCE_FUTURES]:
                    decrypted_api_key = self.decrypt_data(credential.encrypted_api_key)
                    decrypted_api_secret = self.decrypt_data(credential.encrypted_api_secret) if credential.encrypted_api_secret else None

                    if decrypted_api_key is None or decrypted_api_secret is None:
                        raise CredentialError(f"API Key o Secret para Binance son nulos o no pudieron ser desencriptados.")
                    
                    try:
                        account_info = await self.binance_adapter.get_account_info(decrypted_api_key, decrypted_api_secret)
                        is_valid = account_info.get("canTrade", False)
                        
                        if is_valid:
                            logger.info(f"Verificación de Binance {credential.service_name} exitosa.")
                            permissions = []
                            if account_info.get("canTrade"): permissions.append("SPOT_TRADING")
                            if account_info.get("canDeposit"): permissions.append("DEPOSIT")
                            if account_info.get("canWithdraw"): permissions.append("WITHDRAWAL")
                            
                            # Usar upsert para actualizar permisos y estado
                            update_data = credential.model_dump(mode='json')
                            update_data['permissions'] = json.dumps(permissions) # Guardar como JSON string
                            update_data['status'] = "active"
                            update_data['updated_at'] = datetime.utcnow().isoformat()
                            await persistence_service.upsert(
                                table_name="api_credentials",
                                data=update_data,
                                on_conflict=["id"]
                            )
                        else:
                            logger.warning(f"Verificación de Binance {credential.service_name} fallida: canTrade es False.")
                            # Usar upsert para actualizar el estado
                            update_data = credential.model_dump(mode='json')
                            update_data['status'] = "verification_failed"
                            update_data['updated_at'] = datetime.utcnow().isoformat()
                            await persistence_service.upsert(
                                table_name="api_credentials",
                                data=update_data,
                                on_conflict=["id"]
                            )

                    except BinanceAPIError as e:
                        logger.error(f"Error de Binance API durante la verificación: {str(e)}")
                        is_valid = False
                        # Usar upsert para actualizar el estado
                        update_data = credential.model_dump(mode='json')
                        update_data['status'] = "verification_failed"
                        update_data['updated_at'] = datetime.utcnow().isoformat()
                        await persistence_service.upsert(
                            table_name="api_credentials",
                            data=update_data,
                            on_conflict=["id"]
                        )
                else:
                    logger.info(f"No hay lógica de verificación implementada para el servicio: {credential.service_name}. Asumiendo válido.")
                    is_valid = True
                    # Usar upsert para actualizar el estado
                    update_data = credential.model_dump(mode='json')
                    update_data['status'] = "active"
                    update_data['updated_at'] = datetime.utcnow().isoformat()
                    await persistence_service.upsert(
                        table_name="api_credentials",
                        data=update_data,
                        on_conflict=["id"]
                    )

            except CredentialError as e:
                # Usar upsert para actualizar el estado
                update_data = credential.model_dump(mode='json')
                update_data['status'] = "verification_failed"
                update_data['updated_at'] = datetime.utcnow().isoformat()
                await persistence_service.upsert(
                    table_name="api_credentials",
                    data=update_data,
                    on_conflict=["id"]
                )
                raise e
            except Exception as e:
                logger.error(f"Error general durante la verificación de {credential.service_name}: {e}", exc_info=True)
                is_valid = False
                # Usar upsert para actualizar el estado
                update_data = credential.model_dump(mode='json')
                update_data['status'] = "verification_failed"
                update_data['updated_at'] = datetime.utcnow().isoformat()
                await persistence_service.upsert(
                    table_name="api_credentials",
                    data=update_data,
                    on_conflict=["id"]
                )
            
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
            
            async with self.session_factory() as session:
                persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
                # Usar upsert para actualizar el estado
                update_data = binance_credential.model_dump(mode='json')
                update_data['status'] = "active"
                update_data['updated_at'] = datetime.utcnow().isoformat()
                await persistence_service.upsert(
                    table_name="api_credentials",
                    data=update_data,
                    on_conflict=["id"]
                )
            
            logger.info(f"API Key de Binance verificada exitosamente para el usuario {self.fixed_user_id}.")
            return True
        except BinanceAPIError as e:
            logger.error(f"Fallo en la verificación de la API Key de Binance para {self.fixed_user_id}: {str(e)}", exc_info=True)
            async with self.session_factory() as session:
                persistence_service = SupabasePersistenceService(session_factory=self.session_factory) # Usar session_factory
                # Usar upsert para actualizar el estado
                update_data = binance_credential.model_dump(mode='json')
                update_data['status'] = "verification_failed"
                update_data['updated_at'] = datetime.utcnow().isoformat()
                await persistence_service.upsert(
                    table_name="api_credentials",
                    data=update_data,
                    on_conflict=["id"]
                )
            return False # Asegurar que siempre retorna un booleano
        except Exception as e:
            logger.error(f"Error inesperado durante la verificación de la API Key de Binance para {self.fixed_user_id}: {str(e)}", exc_info=True)
            async with self.session_factory() as session:
                persistence_service = SupabasePersistenceService(session_factory=self.session_factory)
                
                # Construir update_data de forma defensiva
                update_data: Dict[str, Any] = {
                    'status': "verification_failed",
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                # Intentar añadir id, user_id, service_name, credential_label si binance_credential es válido
                if isinstance(binance_credential, APICredential):
                    update_data['id'] = str(binance_credential.id)
                    update_data['user_id'] = str(binance_credential.user_id)
                    update_data['service_name'] = binance_credential.service_name.value
                    update_data['credential_label'] = binance_credential.credential_label
                else:
                    logger.warning(f"binance_credential no es un objeto APICredential válido en el bloque de excepción. No se puede actualizar con todos los detalles.")

                # Usar upsert para actualizar el estado
                await persistence_service.upsert(
                    table_name="api_credentials",
                    data=update_data,
                    on_conflict=["id"] if 'id' in update_data else ["user_id", "service_name", "credential_label"] # Usar id si está disponible, sino las claves de conflicto
                )
            return False # Asegurar que siempre retorna un booleano
