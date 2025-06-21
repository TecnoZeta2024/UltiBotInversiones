from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID as PythonUUID, uuid4
from datetime import datetime
from typing import Optional

from .base import Base

# Custom type for UUID to handle both SQLite and PostgreSQL
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    TEXT for SQLite, storing as stringified UUID values.
    """
    impl = String  # Use String/TEXT as base type
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            # For SQLite and other databases, use TEXT
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            # For SQLite, always convert to string
            if isinstance(value, PythonUUID):
                return str(value)
            elif isinstance(value, str):
                return str(PythonUUID(value))  # Validate it's a valid UUID
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, PythonUUID):
                return value
            else:
                return PythonUUID(str(value))

class APICredentialORM(Base):
    __tablename__ = 'api_credentials'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    service_name: Mapped[str] = mapped_column(String, nullable=False)
    credential_label: Mapped[str] = mapped_column(String, nullable=False)
    encrypted_api_key: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_api_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<APICredentialORM(user_id='{self.user_id}', service_name='{self.service_name}', label='{self.credential_label}')>"
