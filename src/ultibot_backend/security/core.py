from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError, EmailStr

from src.ultibot_backend.app_config import settings
from src.ultibot_backend.security import schemas
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Importar servicio
from src.ultibot_backend.dependencies import get_persistence_service # Importar dependencia

# Configuración de Passlib para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración de OAuth2 (para la dependencia de FastAPI)
# La URL tokenUrl apuntará al endpoint de login que crearemos más adelante.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login") # Ajustar tokenUrl según la ruta final del endpoint de login

# --- Funciones de Hashing de Contraseñas ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- Funciones de Token JWT ---

# Las configuraciones (settings.SECRET_KEY, settings.ALGORITHM, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
# se acceden directamente desde el objeto 'settings' importado.

# Estas variables se cargarán desde AppConfig más adelante
# Por ahora, las definimos aquí temporalmente para desarrollo y se moverán/referenciarán correctamente.
# Se accederá a ellas a través de `settings.SECRET_KEY`, `settings.ALGORITHM`, etc.
# SECRET_KEY = "a_very_secret_key_that_should_be_in_env" # Ejemplo, se reemplazará
# ALGORITHM = "HS256" # Ejemplo, se reemplazará
# ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Ejemplo, se reemplazará


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) # Acceder a través de settings
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM) # Usar los nombres correctos de AppSettings
    return encoded_jwt

# --- Dependencia para Obtener Usuario Actual ---

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: SupabasePersistenceService = Depends(get_persistence_service)
) -> schemas.User: # Devuelve User, no UserInDB, para no exponer hashed_password
    """
    Decodifica el token JWT para obtener el email del usuario y luego recupera
    al usuario de la base de datos.
    Esta función será una dependencia de FastAPI para proteger endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email_str: Optional[str] = payload.get("sub")
        if email_str is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email_str)
    except (JWTError, ValidationError):
        raise credentials_exception

    if token_data.email is None: # Aunque ya se valida arriba, una comprobación extra.
        raise credentials_exception

    user_in_db = await db.get_user_by_email(email=token_data.email)
    if user_in_db is None:
        raise credentials_exception
    
    # Convertir UserInDB a User para no exponer la contraseña hasheada, etc.
    # UserInDB tiene todos los campos para validar User.
    return schemas.User.model_validate(user_in_db)


async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)) -> schemas.User:
    if not current_user.is_active: # Suponiendo que el schema User tiene un campo is_active
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(current_user: schemas.User = Depends(get_current_active_user)) -> schemas.User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
