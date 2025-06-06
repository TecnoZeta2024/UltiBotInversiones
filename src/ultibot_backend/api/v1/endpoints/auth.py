from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
import psycopg # Para capturar UniqueViolation

from src.ultibot_backend.security import schemas as security_schemas
from src.ultibot_backend.security import core as security_core
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.dependencies import get_persistence_service # Importar la dependencia

router = APIRouter()

# Ya no se necesitan los placeholders fake_users_db, get_user_by_email (local), create_db_user (local)

@router.post("/auth/register", response_model=security_schemas.User)
async def register_user(
    user_in: security_schemas.UserCreate,
    db: SupabasePersistenceService = Depends(get_persistence_service)
) -> Any:
    """
    Crea un nuevo usuario.
    """
    db_user = await db.get_user_by_email(email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    
    hashed_password = security_core.get_password_hash(user_in.password)
    try:
        created_user_in_db = await db.create_user(user_in=user_in, hashed_password=hashed_password)
    except psycopg.errors.UniqueViolation: # Captura específica por si acaso la comprobación anterior falla por concurrencia
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system (concurrent creation).",
        )
    except Exception as e: # Captura genérica para otros errores de DB
        # Log the exception e
        # Consider logging 'e' here for better debugging
        print(f"Error creating user: {e}") # Placeholder for actual logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user.",
        )

    # Devolvemos el modelo User, que no incluye el hashed_password
    # UserInDB tiene todos los campos necesarios para construir User
    return security_schemas.User.model_validate(created_user_in_db)


@router.post("/auth/login", response_model=security_schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: SupabasePersistenceService = Depends(get_persistence_service)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # En OAuth2PasswordRequestForm, el "username" es el email.
    user = await db.get_user_by_email(email=form_data.username)

    if not user or not security_core.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token = security_core.create_access_token(
        data={"sub": user.email} # Usamos el email como "subject" del token
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=security_schemas.User)
async def read_users_me(
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
) -> Any:
    """
    Obtiene el usuario actual.
    """
    return current_user
