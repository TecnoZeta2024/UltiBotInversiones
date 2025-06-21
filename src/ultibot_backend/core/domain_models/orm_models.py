from sqlalchemy import Column, String, Boolean, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateColumn
from sqlalchemy.orm import relationship, Mapped, mapped_column
from uuid import UUID as PythonUUID
from datetime import datetime
from typing import Optional
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

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notification_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enable_telegram_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    default_paper_trading_capital: Mapped[float] = mapped_column(Float, default=10000.0)
    paper_trading_active: Mapped[bool] = mapped_column(Boolean, default=False)
    paper_trading_assets: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    watchlists: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    favorite_pairs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_profile: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_profile_settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    real_trading_settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_strategy_configurations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analysis_confidence_thresholds: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mcp_server_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_theme: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dashboard_layout_profiles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active_dashboard_layout_profile_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dashboard_layout_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cloud_sync_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  # pylint: disable=not-callable
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())  # pylint: disable=not-callable

    def __repr__(self):
        return f"<UserConfigurationORM(user_id='{self.user_id}')>"

class TradeORM(Base):
    __tablename__ = 'trades'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=PythonUUID)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    position_status: Mapped[str] = mapped_column(String, nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  # pylint: disable=not-callable
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())  # pylint: disable=not-callable
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<TradeORM(id='{self.id}', symbol='{self.symbol}', status='{self.position_status}')>"

class PortfolioSnapshotORM(Base):
    __tablename__ = 'portfolio_snapshots'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=PythonUUID)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())  # pylint: disable=not-callable
    data: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self):
        return f"<PortfolioSnapshotORM(id='{self.id}', user_id='{self.user_id}', timestamp='{self.timestamp}')>"

class OpportunityORM(Base):
    __tablename__ = 'opportunities'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=PythonUUID)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    initial_signal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    system_calculated_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_priority_calculation_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    status_reason_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status_reason_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    investigation_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linked_trade_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiration_logic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    post_trade_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    post_facto_simulation_results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  # pylint: disable=not-callable
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())  # pylint: disable=not-callable
    strategy_id: Mapped[Optional[PythonUUID]] = mapped_column(GUID(), nullable=True)

    def __repr__(self):
        return f"<OpportunityORM(id='{self.id}', symbol='{self.symbol}', status='{self.status}')>"

class StrategyConfigORM(Base):
    __tablename__ = 'strategy_configurations'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=PythonUUID)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    config_name: Mapped[str] = mapped_column(String, nullable=False)
    base_strategy_type: Mapped[str] = mapped_column(String, nullable=False)
    is_active_paper_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active_real_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  # pylint: disable=not-callable
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())  # pylint: disable=not-callable

    def __repr__(self):
        return f"<StrategyConfigORM(id='{self.id}', config_name='{self.config_name}', user_id='{self.user_id}')>"
