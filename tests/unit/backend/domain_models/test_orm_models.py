import pytest
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
import json

from src.ultibot_backend.core.domain_models.orm_models import (
    UserConfigurationORM,
    TradeORM,
    PortfolioSnapshotORM,
    OpportunityORM,
    StrategyConfigORM,
    MarketDataORM,
    NotificationORM,
    GUID
)
from src.ultibot_backend.core.domain_models.base import Base

# Mock Dialect for GUID type testing
class MockDialect:
    def __init__(self, name):
        self.name = name
    def type_descriptor(self, type_):
        return type_

# Test UserConfigurationORM Model
def test_user_configuration_orm_creation_and_repr():
    user_config_id = "user_config_123"
    user_id = "test_user_123"
    now = datetime.now()

    user_config = UserConfigurationORM(
        id=user_config_id,
        user_id=user_id,
        telegram_chat_id="123456789",
        notification_preferences=json.dumps({"email": True, "sms": False}),
        enable_telegram_notifications=True,
        default_paper_trading_capital=Decimal("50000.00"),
        paper_trading_active=True,
        paper_trading_assets=json.dumps({"USD": 10000, "BTC": 1}),
        watchlists=json.dumps([{"name": "My Watchlist", "symbols": ["BTC/USDT"]}]),
        favorite_pairs=json.dumps(["ETH/USDT"]),
        risk_profile=json.dumps({"level": "medium"}),
        risk_profile_settings=json.dumps({"max_drawdown": 0.1}),
        real_trading_settings=json.dumps({"enabled": False}),
        ai_strategy_configurations=json.dumps({"strategy_a": {"param": "value"}}),
        ai_analysis_confidence_thresholds=json.dumps({"high": 0.8}),
        mcp_server_preferences=json.dumps({"server_url": "http://mcp.example.com"}),
        selected_theme="dark",
        dashboard_layout_profiles=json.dumps([{"id": "layout1", "name": "Default"}]),
        active_dashboard_layout_profile_id="layout1",
        dashboard_layout_config=json.dumps({"widgets": []}),
        cloud_sync_preferences=json.dumps({"enabled": True}),
        created_at=now,
        updated_at=now,
    )
    assert user_config.id == user_config_id
    assert user_config.user_id == user_id
    assert user_config.enable_telegram_notifications is True
    assert user_config.default_paper_trading_capital == Decimal("50000.00")
    assert user_config.selected_theme == "dark"
    assert user_config.created_at == now
    assert user_config.updated_at == now

    assert repr(user_config) == "<UserConfigurationORM(user_id='test_user_123')>"

# Test TradeORM Model
def test_trade_orm_creation_and_repr():
    trade_id = "trade_123"
    user_id = uuid4()
    now = datetime.now()

    trade = TradeORM(
        id=trade_id,
        user_id=user_id,
        mode="paper",
        symbol="BTC/USDT",
        side="buy",
        position_status="open",
        created_at=now,
        updated_at=now,
        closed_at=None,
        data=json.dumps({"entry_price": 10000, "quantity": 0.001}),
    )
    assert trade.id == trade_id
    assert trade.user_id == user_id
    assert trade.mode == "paper"
    assert trade.symbol == "BTC/USDT"
    assert trade.side == "buy"
    assert trade.position_status == "open"
    assert trade.created_at == now
    assert trade.updated_at == now
    assert trade.closed_at is None
    assert json.loads(trade.data)["entry_price"] == 10000

    assert repr(trade) == "<TradeORM(id='trade_123', symbol='BTC/USDT', status='open')>"

# Test PortfolioSnapshotORM Model
def test_portfolio_snapshot_orm_creation_and_repr():
    snapshot_id = uuid4()
    user_id = uuid4()
    now = datetime.now()

    snapshot = PortfolioSnapshotORM(
        id=snapshot_id,
        user_id=user_id,
        timestamp=now,
        data=json.dumps({"total_value": 100000, "assets": {"BTC": 1}}),
    )
    assert snapshot.id == snapshot_id
    assert snapshot.user_id == user_id
    assert snapshot.timestamp == now
    assert json.loads(snapshot.data)["total_value"] == 100000

    assert repr(snapshot) == f"<PortfolioSnapshotORM(id='{snapshot_id}', user_id='{user_id}', timestamp='{now}')>"

# Test OpportunityORM Model
def test_opportunity_orm_creation_and_repr():
    opportunity_id = uuid4()
    user_id = uuid4()
    strategy_id = uuid4()
    now = datetime.now()

    opportunity = OpportunityORM(
        id=opportunity_id,
        user_id=user_id,
        symbol="ETH/USDT",
        detected_at=now,
        source_type="mcp_signal",
        source_name="MCP_Source_A",
        source_data=json.dumps({"raw_signal": "data"}),
        initial_signal=json.dumps({"direction": "buy"}),
        system_calculated_priority_score=85.5,
        last_priority_calculation_at=now,
        status="new",
        status_reason_code="INITIAL",
        status_reason_text="New opportunity detected",
        ai_analysis=json.dumps({"confidence": 0.9}),
        investigation_details=json.dumps({"notes": "none"}),
        user_feedback=json.dumps({"action": "none"}),
        linked_trade_ids=json.dumps(["trade_abc"]),
        expires_at=now,
        expiration_logic=json.dumps({"type": "time"}),
        post_trade_feedback=json.dumps({"outcome": "profit"}),
        post_facto_simulation_results=json.dumps({"pnl": 100}),
        created_at=now,
        updated_at=now,
        strategy_id=strategy_id,
    )
    assert opportunity.id == opportunity_id
    assert opportunity.user_id == user_id
    assert opportunity.symbol == "ETH/USDT"
    assert opportunity.detected_at == now
    assert opportunity.source_type == "mcp_signal"
    assert opportunity.source_name == "MCP_Source_A"
    assert json.loads(opportunity.source_data)["raw_signal"] == "data"
    assert json.loads(opportunity.initial_signal)["direction"] == "buy"
    assert opportunity.system_calculated_priority_score == 85.5
    assert opportunity.last_priority_calculation_at == now
    assert opportunity.status == "new"
    assert opportunity.status_reason_code == "INITIAL"
    assert opportunity.status_reason_text == "New opportunity detected"
    assert json.loads(opportunity.ai_analysis)["confidence"] == 0.9
    assert json.loads(opportunity.investigation_details)["notes"] == "none"
    assert json.loads(opportunity.user_feedback)["action"] == "none"
    assert json.loads(opportunity.linked_trade_ids) == ["trade_abc"]
    assert opportunity.expires_at == now
    assert json.loads(opportunity.expiration_logic)["type"] == "time"
    assert json.loads(opportunity.post_trade_feedback)["outcome"] == "profit"
    assert json.loads(opportunity.post_facto_simulation_results)["pnl"] == 100
    assert opportunity.created_at == now
    assert opportunity.updated_at == now
    assert opportunity.strategy_id == strategy_id

    assert repr(opportunity) == f"<OpportunityORM(id='{opportunity_id}', symbol='ETH/USDT', status='new')>"

# Test StrategyConfigORM Model
def test_strategy_config_orm_creation_and_repr():
    strategy_id = uuid4()
    user_id = uuid4()
    now = datetime.now()

    strategy_config = StrategyConfigORM(
        id=strategy_id,
        user_id=user_id,
        data=json.dumps({"param1": "value1"}),
        config_name="MyScalpingStrategy",
        base_strategy_type="scalping",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        created_at=now,
        updated_at=now,
    )
    assert strategy_config.id == strategy_id
    assert strategy_config.user_id == user_id
    assert json.loads(strategy_config.data)["param1"] == "value1"
    assert strategy_config.config_name == "MyScalpingStrategy"
    assert strategy_config.base_strategy_type == "scalping"
    assert strategy_config.is_active_paper_mode is True
    assert strategy_config.is_active_real_mode is False
    assert strategy_config.created_at == now
    assert strategy_config.updated_at == now

    assert repr(strategy_config) == f"<StrategyConfigORM(id='{strategy_id}', config_name='MyScalpingStrategy', user_id='{user_id}')>"

# Test MarketDataORM Model (already tested in test_market_data_models.py, but included for completeness)
def test_market_data_orm_creation_from_orm_models():
    market_data_id = uuid4()
    now = datetime.now()

    market_data = MarketDataORM(
        id=market_data_id,
        symbol="XRP/USDT",
        timestamp=now,
        open=Decimal("0.50"),
        high=Decimal("0.55"),
        low=Decimal("0.48"),
        close=Decimal("0.52"),
        volume=Decimal("1000000.00"),
    )
    assert market_data.id == market_data_id
    assert market_data.symbol == "XRP/USDT"
    assert market_data.timestamp == now
    assert market_data.open == Decimal("0.50")
    assert market_data.high == Decimal("0.55")
    assert market_data.low == Decimal("0.48")
    assert market_data.close == Decimal("0.52")
    assert market_data.volume == Decimal("1000000.00")

# Test NotificationORM Model
def test_notification_orm_creation_and_repr():
    notification_id = uuid4()
    user_id = uuid4()
    now = datetime.now()

    notification = NotificationORM(
        id=notification_id,
        user_id=user_id,
        timestamp=now,
        type="alert",
        message="Price alert for BTC/USDT",
        is_read=False,
        related_entity_id="trade_abc",
        related_entity_type="trade",
    )
    assert notification.id == notification_id
    assert notification.user_id == user_id
    assert notification.timestamp == now
    assert notification.type == "alert"
    assert notification.message == "Price alert for BTC/USDT"
    assert notification.is_read is False
    assert notification.related_entity_id == "trade_abc"
    assert notification.related_entity_type == "trade"

    assert repr(notification) == f"<NotificationORM(id='{notification_id}', type='alert', user_id='{user_id}')>"

# Test GUID type (basic instantiation, full testing requires a database)
def test_guid_type_process_result_value_orm():
    guid_type = GUID()
    test_uuid_str = str(uuid4())
    result = guid_type.process_result_value(test_uuid_str, None) # dialect is None for basic test
    assert isinstance(result, UUID)
    assert str(result) == test_uuid_str

def test_guid_type_process_bind_param_orm_with_mock_dialect():
    guid_type = GUID()
    test_uuid = uuid4()

    # Test with postgresql dialect
    pg_dialect = MockDialect('postgresql')
    result_pg = guid_type.process_bind_param(test_uuid, pg_dialect)
    assert isinstance(result_pg, str)
    assert result_pg == str(test_uuid)

    # Test with sqlite dialect
    sqlite_dialect = MockDialect('sqlite')
    result_sqlite = guid_type.process_bind_param(test_uuid, sqlite_dialect)
    assert isinstance(result_sqlite, str)
    assert result_sqlite == str(test_uuid)

    # Test with None dialect (should fall through to else)
    result_none = guid_type.process_bind_param(test_uuid, None)
    assert isinstance(result_none, str)
    assert result_none == str(test_uuid)