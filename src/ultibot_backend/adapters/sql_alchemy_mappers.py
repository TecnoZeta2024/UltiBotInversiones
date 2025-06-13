from sqlalchemy import (
    Column,
    DateTime,
    String,
    ForeignKey,
    Numeric,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

# Base declarativa para todos los modelos ORM de SQLAlchemy.
# Todos los modelos que se mapean a tablas de la base de datos deben heredar de esta Base.
Base = declarative_base()

class TradeORM(Base):
    __tablename__ = 'trades'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), nullable=False)
    symbol = Column(String, nullable=False)
    trade_type = Column(String, nullable=False)
    quantity = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow)
    pnl = Column(Numeric, nullable=True)
    status = Column(String, default='open')
