"""Unit tests for User Configuration Domain Models."""

import pytest
from pydantic import ValidationError
from decimal import Decimal
import uuid

from src.core.domain_models.user_configuration_models import (
    ConfidenceThresholds,
    UserConfiguration,
    AIStrategyConfiguration,
    RiskProfile,
    Theme,
    Watchlist,
)

# Helper to create a valid AIStrategyConfiguration for tests
def create_test_ai_config(config_id: str, name: str) -> AIStrategyConfiguration:
    """Creates a valid AIStrategyConfiguration instance for testing."""
    return AIStrategyConfiguration(
        id=config_id,
        name=name,
        is_active_paper_mode=False,
        is_active_real_mode=False,
        total_pnl=Decimal("0.0"),
        number_of_trades=0,
        applies_to_strategies=[],
        applies_to_pairs=[],
        gemini_prompt_template="Test prompt",
        tools_available_to_gemini=[],
        output_parser_config={},
        indicator_weights={},
        confidence_thresholds=ConfidenceThresholds(paper_trading=0.7, real_trading=0.85), # Instantiated as object
        max_context_window_tokens=1000
    )

# Test cases for ConfidenceThresholds
def test_confidence_thresholds_valid():
    """Test successful creation of ConfidenceThresholds."""
    thresholds = ConfidenceThresholds(paper_trading=0.5, real_trading=0.7)
    assert thresholds.paper_trading == 0.5
    assert thresholds.real_trading == 0.7

def test_confidence_thresholds_real_lower_than_paper_raises_error():
    """Test that a validation error is raised if real_trading is not higher than paper_trading."""
    with pytest.raises(ValidationError, match="Real trading confidence threshold should be higher than paper trading"):
        ConfidenceThresholds(paper_trading=0.7, real_trading=0.5)

def test_confidence_thresholds_equal_raises_error():
    """Test that a validation error is raised if real_trading is equal to paper_trading."""
    with pytest.raises(ValidationError, match="Real trading confidence threshold should be higher than paper trading"):
        ConfidenceThresholds(paper_trading=0.7, real_trading=0.7)

def test_confidence_thresholds_invalid_range_raises_error():
    """Test that a validation error is raised for values outside the 0-1 range."""
    with pytest.raises(ValidationError):
        ConfidenceThresholds(paper_trading=1.1, real_trading=1.2)
    with pytest.raises(ValidationError):
        ConfidenceThresholds(paper_trading=0.1, real_trading=-0.1)

# Test cases for UserConfiguration
def test_user_configuration_minimal_valid():
    """Test successful creation of UserConfiguration with minimal required fields."""
    config = UserConfiguration(
        user_id=str(uuid.uuid4()),
        telegram_chat_id=None,
        notification_preferences=None,
        enable_telegram_notifications=True,
        default_paper_trading_capital=None,
        paper_trading_active=False,
        paper_trading_assets=None,
        watchlists=None,
        favorite_pairs=None,
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=None,
        real_trading_settings=None,
        ai_strategy_configurations=None,
        ai_analysis_confidence_thresholds=None,
        mcp_server_preferences=None,
        selected_theme=Theme.DARK,
        dashboard_layout_profiles=None,
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None,
        cloud_sync_preferences=None,
        created_at=None,
        updated_at=None
    )
    assert config.risk_profile == RiskProfile.MODERATE
    assert config.selected_theme == Theme.DARK
    assert config.model_dump(by_alias=True)['riskProfile'] == 'moderate'

def test_user_configuration_full_valid():
    """Test successful creation of UserConfiguration with all fields."""
    ai_config = create_test_ai_config("ai_config_1", "Test AI Config")
    ai_config.total_pnl = Decimal("100.50")
    ai_config.number_of_trades = 10
    
    config_data = {
        "user_id": str(uuid.uuid4()),
        "telegram_chat_id": "12345",
        "notification_preferences": None,
        "enable_telegram_notifications": True,
        "default_paper_trading_capital": Decimal("10000"),
        "paper_trading_active": False,
        "paper_trading_assets": None,
        "watchlists": None,
        "favorite_pairs": None,
        "risk_profile": RiskProfile.MODERATE,
        "risk_profile_settings": None,
        "real_trading_settings": None,
        "ai_strategy_configurations": [ai_config],
        "ai_analysis_confidence_thresholds": ConfidenceThresholds(paper_trading=0.6, real_trading=0.8),
        "mcp_server_preferences": None,
        "selected_theme": Theme.DARK,
        "dashboard_layout_profiles": None,
        "active_dashboard_layout_profile_id": None,
        "dashboard_layout_config": None,
        "cloud_sync_preferences": None,
        "created_at": None,
        "updated_at": None
    }
    config = UserConfiguration(**config_data)
    assert config.telegram_chat_id == "12345"
    assert len(config.ai_strategy_configurations) == 1
    assert config.ai_strategy_configurations[0].id == "ai_config_1"
    assert config.get_effective_confidence_thresholds().real_trading == 0.8

def test_user_configuration_get_ai_config_by_id():
    """Test the get_ai_configuration_by_id method."""
    ai_config1 = create_test_ai_config("ai_1", "Config 1")
    ai_config2 = create_test_ai_config("ai_2", "Config 2")
    config = UserConfiguration(
        user_id=str(uuid.uuid4()),
        telegram_chat_id=None,
        notification_preferences=None,
        enable_telegram_notifications=True,
        default_paper_trading_capital=None,
        paper_trading_active=False,
        paper_trading_assets=None,
        watchlists=None,
        favorite_pairs=None,
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=None,
        real_trading_settings=None,
        ai_strategy_configurations=[ai_config1, ai_config2],
        ai_analysis_confidence_thresholds=None,
        mcp_server_preferences=None,
        selected_theme=Theme.DARK,
        dashboard_layout_profiles=None,
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None,
        cloud_sync_preferences=None,
        created_at=None,
        updated_at=None
    )
    
    found_config = config.get_ai_configuration_by_id("ai_2")
    assert found_config is not None
    assert found_config.name == "Config 2"
    
    not_found_config = config.get_ai_configuration_by_id("ai_3")
    assert not_found_config is None

def test_user_configuration_unique_id_validation():
    """Test that unique ID validation for lists works correctly."""
    ai_config1 = create_test_ai_config("ai_1", "Config 1")
    ai_config2 = create_test_ai_config("ai_1", "Config 2") # Duplicate ID
    
    with pytest.raises(ValidationError, match="ai_strategy_configurations IDs must be unique"):
        UserConfiguration(
            user_id=str(uuid.uuid4()),
            ai_strategy_configurations=[ai_config1, ai_config2]
        )

def test_user_configuration_favorite_pairs_normalization():
    """Test that favorite_pairs are normalized correctly."""
    pairs = ["BTC/USDT", "ETH-USDT", "SOL,USDT"]
    config = UserConfiguration(
        user_id=str(uuid.uuid4()),
        telegram_chat_id=None,
        notification_preferences=None,
        enable_telegram_notifications=True,
        default_paper_trading_capital=None,
        paper_trading_active=False,
        paper_trading_assets=None,
        watchlists=None,
        favorite_pairs=pairs,
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=None,
        real_trading_settings=None,
        ai_strategy_configurations=None,
        ai_analysis_confidence_thresholds=None,
        mcp_server_preferences=None,
        selected_theme=Theme.DARK,
        dashboard_layout_profiles=None,
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None,
        cloud_sync_preferences=None,
        created_at=None,
        updated_at=None
    )
    assert config.favorite_pairs == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def test_user_configuration_json_parsing():
    """Test that stringified JSON fields are parsed correctly."""
    config_data = {
        "user_id": str(uuid.uuid4()),
        "telegram_chat_id": None,
        "notification_preferences": None,
        "enable_telegram_notifications": True,
        "default_paper_trading_capital": None,
        "paper_trading_active": False,
        "paper_trading_assets": None,
        "watchlists": '[{"id": "wl1", "name": "My Watchlist", "pairs": ["BTCUSDT"]}]',
        "favorite_pairs": None,
        "risk_profile": RiskProfile.MODERATE,
        "risk_profile_settings": None,
        "real_trading_settings": None,
        "ai_strategy_configurations": None,
        "ai_analysis_confidence_thresholds": None,
        "mcp_server_preferences": None,
        "selected_theme": Theme.DARK,
        "dashboard_layout_profiles": None,
        "active_dashboard_layout_profile_id": None,
        "dashboard_layout_config": None,
        "cloud_sync_preferences": None,
        "created_at": None,
        "updated_at": None
    }
    config = UserConfiguration(**config_data)
    assert isinstance(config.watchlists, list)
    assert len(config.watchlists) == 1
    assert isinstance(config.watchlists[0], Watchlist)
    assert config.watchlists[0].name == "My Watchlist"

def test_user_configuration_camel_case_alias():
    """Test that camelCase aliases work for serialization."""
    config = UserConfiguration(
        user_id=str(uuid.uuid4()),
        telegram_chat_id="12345",
        notification_preferences=None,
        enable_telegram_notifications=True,
        default_paper_trading_capital=None,
        paper_trading_active=False,
        paper_trading_assets=None,
        watchlists=None,
        favorite_pairs=None,
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=None,
        real_trading_settings=None,
        ai_strategy_configurations=None,
        ai_analysis_confidence_thresholds=None,
        mcp_server_preferences=None,
        selected_theme=Theme.DARK,
        dashboard_layout_profiles=None,
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None,
        cloud_sync_preferences=None,
        created_at=None,
        updated_at=None
    )
    dump = config.model_dump(by_alias=True)
    assert "telegramChatId" in dump
    assert dump["telegramChatId"] == "12345"
