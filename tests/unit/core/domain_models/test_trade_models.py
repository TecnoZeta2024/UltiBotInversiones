
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from src.core.domain_models.trade_models import (
    TradeSide,
    TradeMode,
    PositionStatus,
    OrderType,
    OrderStatus,
    OrderCategory,
    Commission,
    TradeOrderDetails,
    RiskRewardAdjustment,
    ExternalEventLink,
    BacktestDetails,
    AIInfluenceDetails,
    Trade
)

# Test Enums
# =================================================================
class TestEnums:
    def test_trade_side_enum(self):
        assert TradeSide.BUY.value == "buy"
        assert TradeSide.SELL.value == "sell"

    def test_trade_mode_enum(self):
        assert TradeMode.PAPER.value == "paper"
        assert TradeMode.REAL.value == "real"
        assert TradeMode.BACKTEST.value == "backtest"

    def test_position_status_enum(self):
        assert PositionStatus.OPEN.value == "open"
        assert PositionStatus.CLOSED.value == "closed"
        assert PositionStatus.PENDING_ENTRY_CONDITIONS.value == "pending_entry_conditions"

    def test_order_type_enum(self):
        assert OrderType.MARKET.value == "market"
        assert OrderType.STOP_LOSS.value == "stop_loss"
        assert OrderType.TAKE_PROFIT.value == "take_profit"

    def test_order_status_enum(self):
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.REJECTED.value == "rejected"
        assert OrderStatus.PENDING_SUBMIT.value == "pending_submit"

    def test_order_category_enum(self):
        assert OrderCategory.ENTRY.value == "entry"
        assert OrderCategory.TAKE_PROFIT.value == "take_profit"
        assert OrderCategory.EXIT.value == "exit"

# Test Pydantic Models (basic instantiation and field types)
# =================================================================
class TestPydanticModels:

    def test_commission_model(self):
        commission = Commission(
            amount=Decimal("0.001"),
            asset="BNB",
            timestamp=datetime.utcnow()
        )
        assert commission.amount == Decimal("0.001")
        assert commission.asset == "BNB"
        assert isinstance(commission.timestamp, datetime)

    def test_trade_order_details_model(self):
        order_details = TradeOrderDetails(
            orderCategory=OrderCategory.ENTRY,
            type="market",
            status="filled",
            requestedQuantity=Decimal("0.001"),
            executedQuantity=Decimal("0.001"),
            executedPrice=Decimal("60000.0"),
            timestamp=datetime.utcnow()
        )
        assert isinstance(order_details.orderId_internal, UUID)
        assert order_details.orderCategory == OrderCategory.ENTRY
        assert order_details.type == "market"
        assert order_details.status == "filled"
        assert order_details.requestedQuantity == Decimal("0.001")
        assert order_details.executedQuantity == Decimal("0.001")
        assert order_details.executedPrice == Decimal("60000.0")
        assert isinstance(order_details.timestamp, datetime)

    def test_trade_order_details_with_optional_fields(self):
        order_details = TradeOrderDetails(
            orderCategory=OrderCategory.TAKE_PROFIT,
            type="limit",
            status="new",
            requestedQuantity=Decimal("0.001"),
            executedQuantity=Decimal("0.0"),
            executedPrice=Decimal("0.0"),
            timestamp=datetime.utcnow(),
            orderId_exchange="exchange123",
            clientOrderId_exchange="client123",
            requestedPrice=Decimal("61000.0"),
            commissions=[{"amount": 0.0001, "asset": "BNB"}],
            price=Decimal("61000.0"),
            timeInForce="GTC"
        )
        assert order_details.orderId_exchange == "exchange123"
        assert order_details.requestedPrice == Decimal("61000.0")
        assert order_details.commissions[0]["amount"] == 0.0001
        assert order_details.price == Decimal("61000.0")
        assert order_details.timeInForce == "GTC"

    def test_risk_reward_adjustment_model(self):
        adjustment = RiskRewardAdjustment(
            timestamp=datetime.utcnow(),
            new_stop_loss_price=Decimal("59000.0"),
            updated_risk_quote_amount=Decimal("100.0")
        )
        assert adjustment.new_stop_loss_price == Decimal("59000.0")
        assert adjustment.updated_risk_quote_amount == Decimal("100.0")

    def test_external_event_link_model(self):
        event_link = ExternalEventLink(
            type="news",
            reference_id="news_id_123",
            description="Major economic announcement"
        )
        assert event_link.type == "news"

    def test_backtest_details_model(self):
        backtest = BacktestDetails(
            backtest_run_id="run_abc",
            parameters_snapshot={"strategy": "RSI", "period": 14}
        )
        assert backtest.backtest_run_id == "run_abc"
        assert backtest.parameters_snapshot["strategy"] == "RSI"

    def test_ai_influence_details_model(self):
        ai_details = AIInfluenceDetails(
            ai_analysis_profile_id="profile_1",
            ai_confidence=Decimal("0.95"),
            ai_suggested_action="buy",
            ai_reasoning_summary="Strong bullish signal",
            ai_analysis_timestamp=datetime.utcnow()
        )
        assert ai_details.ai_confidence == Decimal("0.95")
        assert ai_details.decision_override_by_user is False

# Test Trade Model
# =================================================================
class TestTradeModel:

    @pytest.fixture
    def sample_trade_order_details(self):
        return TradeOrderDetails(
            orderCategory=OrderCategory.ENTRY,
            type="market",
            status="filled",
            requestedQuantity=Decimal("0.001"),
            executedQuantity=Decimal("0.001"),
            executedPrice=Decimal("60000.0"),
            timestamp=datetime.utcnow()
        )

    def test_trade_creation(self, sample_trade_order_details):
        user_id = uuid4()
        trade = Trade(
            user_id=user_id,
            mode=TradeMode.PAPER,
            symbol="BTC/USDT",
            side=TradeSide.BUY,
            entryOrder=sample_trade_order_details,
            positionStatus=PositionStatus.OPEN
        )
        assert isinstance(trade.id, UUID)
        assert trade.user_id == user_id
        assert trade.mode == TradeMode.PAPER
        assert trade.symbol == "BTC/USDT"
        assert trade.side == TradeSide.BUY
        assert trade.entryOrder == sample_trade_order_details
        assert trade.positionStatus == PositionStatus.OPEN
        assert isinstance(trade.created_at, datetime)
        assert isinstance(trade.opened_at, datetime)
        assert isinstance(trade.updated_at, datetime)
        assert trade.closed_at is None
        assert len(trade.exitOrders) == 0
        assert len(trade.riskRewardAdjustments) == 0

    def test_trade_with_optional_fields(self, sample_trade_order_details):
        user_id = uuid4()
        trade = Trade(
            user_id=user_id,
            mode=TradeMode.REAL,
            symbol="ETH/USDT",
            side=TradeSide.SELL,
            entryOrder=sample_trade_order_details,
            positionStatus=PositionStatus.CLOSED,
            exitOrders=[
                TradeOrderDetails(
                    orderCategory=OrderCategory.EXIT,
                    type="market",
                    status="filled",
                    requestedQuantity=Decimal("0.001"),
                    executedQuantity=Decimal("0.001"),
                    executedPrice=Decimal("59000.0"),
                    timestamp=datetime.utcnow()
                )
            ],
            strategyId=uuid4(),
            opportunityId=uuid4(),
            aiAnalysisConfidence=Decimal("0.85"),
            pnl_usd=Decimal("100.0"),
            pnl_percentage=Decimal("0.05"),
            closingReason="SL_HIT",
            ocoOrderListId="oco123",
            takeProfitPrice=Decimal("62000.0"),
            trailingStopActivationPrice=Decimal("60500.0"),
            trailingStopCallbackRate=Decimal("0.005"),
            currentStopPrice_tsl=Decimal("60000.0"),
            riskRewardAdjustments=[
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "new_stop_loss_price": "59500.0",
                    "reason": "Trailing stop moved"
                }
            ],
            closed_at=datetime.utcnow()
        )

        assert trade.mode == TradeMode.REAL
        assert len(trade.exitOrders) == 1
        assert isinstance(trade.strategyId, UUID)
        assert isinstance(trade.opportunityId, UUID)
        assert trade.aiAnalysisConfidence == Decimal("0.85")
        assert trade.pnl_usd == Decimal("100.0")
        assert trade.closingReason == "SL_HIT"
        assert trade.takeProfitPrice == Decimal("62000.0")
        assert trade.trailingStopActivationPrice == Decimal("60500.0")
        assert trade.trailingStopCallbackRate == Decimal("0.005")
        assert trade.currentStopPrice_tsl == Decimal("60000.0")
        assert len(trade.riskRewardAdjustments) == 1
        assert isinstance(trade.closed_at, datetime)
