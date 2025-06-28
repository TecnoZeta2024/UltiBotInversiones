from sqlalchemy import Column, String, Boolean, Float, DateTime, Text, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateColumn
from sqlalchemy.orm import relationship, Mapped, mapped_column
from uuid import UUID as PythonUUID, uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional
import json

from .base import Base
from . import api_credential_models # Importar para asegurar que APICredentialORM se registre

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
        elif dialect and dialect.name == 'postgresql':
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

class UserConfigurationORM(Base):
    __tablename__ = 'user_configurations'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    notification_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enable_telegram_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    default_paper_trading_capital: Mapped[Decimal] = mapped_column(Numeric(18, 8), default=10000.0)
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

    __table_args__ = (
        Index('ix_user_configurations_user_id', 'user_id'),
        Index('ix_user_configurations_created_at', 'created_at'),
        Index('ix_user_configurations_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<UserConfigurationORM(user_id='{self.user_id}')>"

class TradeORM(Base):
    __tablename__ = 'trades'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    mode: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    position_status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  # pylint: disable=not-callable
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())  # pylint: disable=not-callable
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)  # Residual JSON data for complex or less queried fields

    __table_args__ = (
        Index('ix_trades_user_id', 'user_id'),
        Index('ix_trades_symbol', 'symbol'),
        Index('ix_trades_position_status', 'position_status'),
        Index('ix_trades_mode', 'mode'),
        Index('ix_trades_created_at', 'created_at'),
        Index('ix_trades_updated_at', 'updated_at'),
        Index('ix_trades_closed_at', 'closed_at'),
    )

    def __repr__(self):
        return f"<TradeORM(id='{self.id}', symbol='{self.symbol}', status='{self.position_status}')>"

class PortfolioSnapshotORM(Base):
    __tablename__ = 'portfolio_snapshots'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())  # pylint: disable=not-callable
    data: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index('ix_portfolio_snapshots_user_id', 'user_id'),
        Index('ix_portfolio_snapshots_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<PortfolioSnapshotORM(id='{self.id}', user_id='{self.user_id}', timestamp='{self.timestamp}')>"

class OpportunityORM(Base):
    __tablename__ = 'opportunities'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
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

    __table_args__ = (
        Index('ix_opportunities_user_id', 'user_id'),
        Index('ix_opportunities_symbol', 'symbol'),
        Index('ix_opportunities_status', 'status'),
        Index('ix_opportunities_detected_at', 'detected_at'),
        Index('ix_opportunities_created_at', 'created_at'),
        Index('ix_opportunities_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<OpportunityORM(id='{self.id}', symbol='{self.symbol}', status='{self.status}')>"

class StrategyConfigORM(Base):
    __tablename__ = 'strategy_configurations'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    config_name: Mapped[str] = mapped_column(String, nullable=False)
    base_strategy_type: Mapped[str] = mapped_column(String, nullable=False)
    is_active_paper_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active_real_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  # pylint: disable=not-callable
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())  # pylint: disable=not-callable

    __table_args__ = (
        Index('ix_strategy_configurations_user_id', 'user_id'),
        Index('ix_strategy_configurations_config_name', 'config_name'),
        Index('ix_strategy_configurations_base_strategy_type', 'base_strategy_type'),
        Index('ix_strategy_configurations_created_at', 'created_at'),
        Index('ix_strategy_configurations_updated_at', 'updated_at'),
    )

    def __repr__(self):
        return f"<StrategyConfigORM(id='{self.id}', config_name='{self.config_name}', user_id='{self.user_id}')>"

class MarketDataORM(Base):
    __tablename__ = 'market_data'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)

    __table_args__ = (
        Index('ix_market_data_symbol_timestamp', 'symbol', 'timestamp', unique=True),
    )

    def __repr__(self):
        return f"<MarketDataORM(symbol='{self.symbol}', timestamp='{self.timestamp}')>"

class NotificationORM(Base):
    __tablename__ = 'notifications'

    id: Mapped[PythonUUID] = mapped_column(GUID(), primary_key=True, default=uuid4)
    user_id: Mapped[PythonUUID] = mapped_column(GUID(), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())  # pylint: disable=not-callable
    type: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    related_entity_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index('ix_notifications_user_id', 'user_id'),
        Index('ix_notifications_timestamp', 'timestamp'),
        Index('ix_notifications_type', 'type'),
        Index('ix_notifications_is_read', 'is_read'),
    )

    def __repr__(self):
        return f"<NotificationORM(id='{self.id}', type='{self.type}', user_id='{self.user_id}')>"
