
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.domain_models.orm_models import (
    Base,
    UserConfigurationORM,
    TradeORM,
    PortfolioSnapshotORM,
    OpportunityORM,
    StrategyConfigORM,
    MarketDataORM,
    NotificationORM,
    GUID
)

# Fixture for in-memory SQLite database session
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

# Tests for UserConfigurationORM
# =================================================================
class TestUserConfigurationORM:

    def test_create_user_configuration(self, db_session):
        user_id = str(uuid4())
        config = UserConfigurationORM(
            id=user_id, # Using user_id as id for simplicity in test
            user_id=user_id,
            telegram_chat_id="12345",
            notification_preferences="{}",
            enable_telegram_notifications=True,
            default_paper_trading_capital=Decimal("50000.0"),
            paper_trading_active=True,
            paper_trading_assets="{}",
            watchlists="[]",
            favorite_pairs="[]",
            risk_profile="moderate",
            risk_profile_settings="{}",
            real_trading_settings="{}",
            ai_strategy_configurations="{}",
            ai_analysis_confidence_thresholds="{}",
            mcp_server_preferences="{}",
            selected_theme="dark",
            dashboard_layout_profiles="{}",
            active_dashboard_layout_profile_id="default",
            dashboard_layout_config="{}",
            cloud_sync_preferences="{}"
        )
        db_session.add(config)
        db_session.commit()

        retrieved_config = db_session.query(UserConfigurationORM).filter_by(user_id=user_id).first()

        assert retrieved_config is not None
        assert retrieved_config.user_id == user_id
        assert retrieved_config.telegram_chat_id == "12345"
        assert retrieved_config.enable_telegram_notifications is True
        assert retrieved_config.default_paper_trading_capital == Decimal("50000.0")
        assert retrieved_config.paper_trading_active is True
        assert isinstance(retrieved_config.created_at, datetime)
        assert isinstance(retrieved_config.updated_at, datetime)

    def test_user_configuration_default_values(self, db_session):
        user_id = str(uuid4())
        config = UserConfigurationORM(
            id=user_id,
            user_id=user_id
        )
        db_session.add(config)
        db_session.commit()

        retrieved_config = db_session.query(UserConfigurationORM).filter_by(user_id=user_id).first()

        assert retrieved_config.enable_telegram_notifications is False
        assert retrieved_config.default_paper_trading_capital == Decimal("10000.0")
        assert retrieved_config.paper_trading_active is False
        assert retrieved_config.telegram_chat_id is None

    def test_user_configuration_repr(self, db_session):
        user_id = str(uuid4())
        config = UserConfigurationORM(id=user_id, user_id=user_id)
        assert repr(config) == f"<UserConfigurationORM(user_id='{user_id}')>"

# Tests for TradeORM
# =================================================================
class TestTradeORM:

    def test_create_trade(self, db_session):
        trade_id = str(uuid4())
        user_id = uuid4()
        trade = TradeORM(
            id=trade_id,
            user_id=user_id,
            mode="paper",
            symbol="BTC/USDT",
            side="buy",
            position_status="open",
            data="{}"
        )
        db_session.add(trade)
        db_session.commit()

        retrieved_trade = db_session.query(TradeORM).filter_by(id=trade_id).first()

        assert retrieved_trade is not None
        assert retrieved_trade.id == trade_id
        assert retrieved_trade.user_id == user_id
        assert retrieved_trade.mode == "paper"
        assert retrieved_trade.symbol == "BTC/USDT"
        assert retrieved_trade.side == "buy"
        assert retrieved_trade.position_status == "open"
        assert retrieved_trade.data == "{}"
        assert isinstance(retrieved_trade.created_at, datetime)
        assert isinstance(retrieved_trade.updated_at, datetime)
        assert retrieved_trade.closed_at is None

    def test_trade_repr(self, db_session):
        trade_id = str(uuid4())
        user_id = uuid4()
        trade = TradeORM(
            id=trade_id,
            user_id=user_id,
            mode="paper",
            symbol="ETH/USDT",
            side="sell",
            position_status="closed",
            data="{}"
        )
        assert repr(trade) == f"<TradeORM(id='{trade_id}', symbol='ETH/USDT', status='closed')>"

# Tests for PortfolioSnapshotORM
# =================================================================
class TestPortfolioSnapshotORM:

    def test_create_portfolio_snapshot(self, db_session):
        snapshot_id = uuid4()
        user_id = uuid4()
        timestamp = datetime.now()
        snapshot = PortfolioSnapshotORM(
            id=snapshot_id,
            user_id=user_id,
            timestamp=timestamp,
            data="{}"
        )
        db_session.add(snapshot)
        db_session.commit()

        retrieved_snapshot = db_session.query(PortfolioSnapshotORM).filter_by(id=snapshot_id).first()

        assert retrieved_snapshot is not None
        assert retrieved_snapshot.id == snapshot_id
        assert retrieved_snapshot.user_id == user_id
        assert retrieved_snapshot.timestamp == timestamp
        assert retrieved_snapshot.data == "{}"

    def test_portfolio_snapshot_repr(self, db_session):
        snapshot_id = uuid4()
        user_id = uuid4()
        timestamp = datetime.now()
        snapshot = PortfolioSnapshotORM(
            id=snapshot_id,
            user_id=user_id,
            timestamp=timestamp,
            data="{}"
        )
        assert repr(snapshot) == f"<PortfolioSnapshotORM(id='{snapshot_id}', user_id='{user_id}', timestamp='{timestamp}')>"

# Tests for OpportunityORM
# =================================================================
class TestOpportunityORM:

    def test_create_opportunity(self, db_session):
        opportunity_id = uuid4()
        user_id = uuid4()
        detected_at = datetime.now()
        opportunity = OpportunityORM(
            id=opportunity_id,
            user_id=user_id,
            symbol="BTC/USDT",
            detected_at=detected_at,
            source_type="mcp_signal",
            source_name="test_source",
            status="new"
        )
        db_session.add(opportunity)
        db_session.commit()

        retrieved_opportunity = db_session.query(OpportunityORM).filter_by(id=opportunity_id).first()

        assert retrieved_opportunity is not None
        assert retrieved_opportunity.id == opportunity_id
        assert retrieved_opportunity.user_id == user_id
        assert retrieved_opportunity.symbol == "BTC/USDT"
        assert retrieved_opportunity.detected_at == detected_at
        assert retrieved_opportunity.source_type == "mcp_signal"
        assert retrieved_opportunity.source_name == "test_source"
        assert retrieved_opportunity.status == "new"
        assert isinstance(retrieved_opportunity.created_at, datetime)
        assert isinstance(retrieved_opportunity.updated_at, datetime)

    def test_opportunity_repr(self, db_session):
        opportunity_id = uuid4()
        user_id = uuid4()
        detected_at = datetime.now()
        opportunity = OpportunityORM(
            id=opportunity_id,
            user_id=user_id,
            symbol="ETH/USDT",
            detected_at=detected_at,
            source_type="manual",
            source_name="user",
            status="analysis_complete"
        )
        assert repr(opportunity) == f"<OpportunityORM(id='{opportunity_id}', symbol='ETH/USDT', status='analysis_complete')>"

# Tests for StrategyConfigORM
# =================================================================
class TestStrategyConfigORM:

    def test_create_strategy_config(self, db_session):
        config_id = uuid4()
        user_id = uuid4()
        config = StrategyConfigORM(
            id=config_id,
            user_id=user_id,
            data="{}",
            config_name="MyStrategy",
            base_strategy_type="RSI",
            is_active_paper_mode=True,
            is_active_real_mode=False
        )
        db_session.add(config)
        db_session.commit()

        retrieved_config = db_session.query(StrategyConfigORM).filter_by(id=config_id).first()

        assert retrieved_config is not None
        assert retrieved_config.id == config_id
        assert retrieved_config.user_id == user_id
        assert retrieved_config.data == "{}"
        assert retrieved_config.config_name == "MyStrategy"
        assert retrieved_config.base_strategy_type == "RSI"
        assert retrieved_config.is_active_paper_mode is True
        assert retrieved_config.is_active_real_mode is False
        assert isinstance(retrieved_config.created_at, datetime)
        assert isinstance(retrieved_config.updated_at, datetime)

    def test_strategy_config_repr(self, db_session):
        config_id = uuid4()
        user_id = uuid4()
        config = StrategyConfigORM(
            id=config_id,
            user_id=user_id,
            data="{}",
            config_name="AnotherStrategy",
            base_strategy_type="MACD"
        )
        assert repr(config) == f"<StrategyConfigORM(id='{config_id}', config_name='AnotherStrategy', user_id='{user_id}')>"

# Tests for MarketDataORM
# =================================================================
class TestMarketDataORM:

    def test_create_market_data(self, db_session):
        market_data_id = uuid4()
        timestamp = datetime.now()
        market_data = MarketDataORM(
            id=market_data_id,
            symbol="BTC/USDT",
            timestamp=timestamp,
            open=Decimal("100.0"),
            high=Decimal("110.0"),
            low=Decimal("90.0"),
            close=Decimal("105.0"),
            volume=Decimal("1000.0")
        )
        db_session.add(market_data)
        db_session.commit()

        retrieved_market_data = db_session.query(MarketDataORM).filter_by(id=market_data_id).first()

        assert retrieved_market_data is not None
        assert retrieved_market_data.id == market_data_id
        assert retrieved_market_data.symbol == "BTC/USDT"
        assert retrieved_market_data.timestamp == timestamp
        assert retrieved_market_data.open == Decimal("100.0")
        assert retrieved_market_data.high == Decimal("110.0")
        assert retrieved_market_data.low == Decimal("90.0")
        assert retrieved_market_data.close == Decimal("105.0")
        assert retrieved_market_data.volume == Decimal("1000.0")

    def test_market_data_repr(self, db_session):
        market_data_id = uuid4()
        timestamp = datetime.now()
        market_data = MarketDataORM(
            id=market_data_id,
            symbol="ETH/USDT",
            timestamp=timestamp,
            open=Decimal("200.0"),
            high=Decimal("210.0"),
            low=Decimal("190.0"),
            close=Decimal("205.0"),
            volume=Decimal("500.0")
        )
        assert repr(market_data) == f"<MarketDataORM(symbol='ETH/USDT', timestamp='{timestamp}')>"

# Tests for NotificationORM
# =================================================================
class TestNotificationORM:

    def test_create_notification(self, db_session):
        notification_id = uuid4()
        user_id = uuid4()
        timestamp = datetime.now()
        notification = NotificationORM(
            id=notification_id,
            user_id=user_id,
            timestamp=timestamp,
            type="alert",
            message="Test notification",
            is_read=False,
            related_entity_id=str(uuid4()),
            related_entity_type="trade"
        )
        db_session.add(notification)
        db_session.commit()

        retrieved_notification = db_session.query(NotificationORM).filter_by(id=notification_id).first()

        assert retrieved_notification is not None
        assert retrieved_notification.id == notification_id
        assert retrieved_notification.user_id == user_id
        assert retrieved_notification.timestamp == timestamp
        assert retrieved_notification.type == "alert"
        assert retrieved_notification.message == "Test notification"
        assert retrieved_notification.is_read is False
        assert isinstance(retrieved_notification.related_entity_id, str)
        assert retrieved_notification.related_entity_type == "trade"

    def test_notification_default_is_read(self, db_session):
        notification_id = uuid4()
        user_id = uuid4()
        timestamp = datetime.now()
        notification = NotificationORM(
            id=notification_id,
            user_id=user_id,
            timestamp=timestamp,
            type="info",
            message="Another notification"
        )
        db_session.add(notification)
        db_session.commit()

        retrieved_notification = db_session.query(NotificationORM).filter_by(id=notification_id).first()
        assert retrieved_notification.is_read is False

    def test_notification_repr(self, db_session):
        notification_id = uuid4()
        user_id = uuid4()
        timestamp = datetime.now()
        notification = NotificationORM(
            id=notification_id,
            user_id=user_id,
            timestamp=timestamp,
            type="warning",
            message="Warning message"
        )
        assert repr(notification) == f"<NotificationORM(id='{notification_id}', type='warning', user_id='{user_id}')>"
