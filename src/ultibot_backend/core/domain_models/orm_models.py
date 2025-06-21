from sqlalchemy import Column, String, Boolean, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateColumn
from sqlalchemy.orm import relationship
from uuid import UUID as PythonUUID
from datetime import datetime
import json

from .base import Base

# Custom type for UUID to handle both SQLite and PostgreSQL
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR

    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, PythonUUID):
                return str(PythonUUID(value))
            return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, PythonUUID):
                return PythonUUID(value)
            return value

@compiles(CreateColumn, 'sqlite')
def compile_create_column_sqlite(element, compiler, **kw):
    """
    Custom compilation for SQLite to handle UUID columns as TEXT.
    """
    if isinstance(element.element.type, GUID):
        element.element.type = Text()
    return compiler.visit_create_column(element, **kw)

class UserConfigurationORM(Base):
    __tablename__ = 'user_configurations'

    id = Column(String, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    telegram_chat_id = Column(String, nullable=True)
    notification_preferences = Column(Text, nullable=True) # JSON string
    enable_telegram_notifications = Column(Boolean, default=False)
    default_paper_trading_capital = Column(Float, default=10000.0)
    paper_trading_active = Column(Boolean, default=False)
    paper_trading_assets = Column(Text, nullable=True) # JSON string
    watchlists = Column(Text, nullable=True) # JSON string
    favorite_pairs = Column(Text, nullable=True) # JSON string
    risk_profile = Column(Text, nullable=True) # JSON string
    risk_profile_settings = Column(Text, nullable=True) # JSON string
    real_trading_settings = Column(Text, nullable=True) # JSON string
    ai_strategy_configurations = Column(Text, nullable=True) # JSON string
    ai_analysis_confidence_thresholds = Column(Text, nullable=True) # JSON string
    mcp_server_preferences = Column(Text, nullable=True) # JSON string
    selected_theme = Column(String, nullable=True)
    dashboard_layout_profiles = Column(Text, nullable=True) # JSON string
    active_dashboard_layout_profile_id = Column(String, nullable=True)
    dashboard_layout_config = Column(Text, nullable=True) # JSON string
    cloud_sync_preferences = Column(Text, nullable=True) # JSON string
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserConfigurationORM(user_id='{self.user_id}')>"

class TradeORM(Base):
    __tablename__ = 'trades'

    id = Column(GUID(), primary_key=True, default=PythonUUID)
    user_id = Column(GUID(), nullable=False)
    data = Column(Text, nullable=False) # JSON string of Trade Pydantic model
    position_status = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<TradeORM(id='{self.id}', symbol='{self.symbol}', status='{self.position_status}')>"

class PortfolioSnapshotORM(Base):
    __tablename__ = 'portfolio_snapshots'

    id = Column(GUID(), primary_key=True, default=PythonUUID)
    user_id = Column(GUID(), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    data = Column(Text, nullable=False) # JSON string of PortfolioSnapshot Pydantic model

    def __repr__(self):
        return f"<PortfolioSnapshotORM(id='{self.id}', user_id='{self.user_id}', timestamp='{self.timestamp}')>"

class OpportunityORM(Base):
    __tablename__ = 'opportunities'

    id = Column(GUID(), primary_key=True, default=PythonUUID)
    user_id = Column(GUID(), nullable=False)
    symbol = Column(String, nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    source_data = Column(Text, nullable=True) # JSON string
    initial_signal = Column(Text, nullable=True) # JSON string
    system_calculated_priority_score = Column(Float, nullable=True)
    last_priority_calculation_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)
    status_reason_code = Column(String, nullable=True)
    status_reason_text = Column(Text, nullable=True)
    ai_analysis = Column(Text, nullable=True) # JSON string
    investigation_details = Column(Text, nullable=True) # JSON string
    user_feedback = Column(Text, nullable=True) # JSON string
    linked_trade_ids = Column(Text, nullable=True) # JSON string of list of UUIDs
    expires_at = Column(DateTime(timezone=True), nullable=True)
    expiration_logic = Column(Text, nullable=True) # JSON string
    post_trade_feedback = Column(Text, nullable=True) # JSON string
    post_facto_simulation_results = Column(Text, nullable=True) # JSON string
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    strategy_id = Column(GUID(), nullable=True) # Foreign key to strategy config

    def __repr__(self):
        return f"<OpportunityORM(id='{self.id}', symbol='{self.symbol}', status='{self.status}')>"

class StrategyConfigORM(Base):
    __tablename__ = 'strategy_configurations'

    id = Column(GUID(), primary_key=True, default=PythonUUID)
    user_id = Column(GUID(), nullable=False)
    data = Column(Text, nullable=False) # JSON string of TradingStrategyConfig Pydantic model
    config_name = Column(String, nullable=False)
    base_strategy_type = Column(String, nullable=False) # Storing the enum value as string
    is_active_paper_mode = Column(Boolean, default=False)
    is_active_real_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StrategyConfigORM(id='{self.id}', config_name='{self.config_name}', user_id='{self.user_id}')>"
