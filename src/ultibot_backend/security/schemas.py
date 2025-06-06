from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: Optional[int] = None # Supabase asignará el ID como UUID, pero Pydantic puede manejarlo como str o int si se mapea.
                             # Por ahora, lo mantendremos opcional y consideraremos el tipo exacto más adelante.
    hashed_password: str

    class Config:
        orm_mode = True # Pydantic V2 usa `model_config = {"from_attributes": True}`
                        # Mantendré orm_mode por ahora, se ajustará si es necesario para Pydantic V2.
                        # Actualización: Pydantic V2 usa from_attributes.
        # Pydantic V2:
        model_config = {
            "from_attributes": True
        }


class User(UserInDBBase): # Para devolver al cliente, sin el hashed_password
    pass


class UserInDB(UserInDBBase): # Para uso interno, con el hashed_password
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    # En lugar de username, usaremos email como identificador principal,
    # o podríamos añadir un campo user_id si es preferible después de la creación del usuario.
    # Por ahora, el email será el "subject" del token.
