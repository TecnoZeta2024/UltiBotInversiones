"""Unit tests for User Configuration Domain Models."""

import pytest
from pydantic import ValidationError
from decimal import Decimal

from src.ultibot_backend.core.domain_models.user_configuration_models import (
    ConfidenceThresholds,
    UserConfiguration,
    AIStrategyConfiguration,
    RiskProfile,
    Theme
)

# Test cases for ConfidenceThresholds
def test_confidence_thresholds_valid():
    """Test successful creation of ConfidenceThresholds."""
    thresholds = ConfidenceThresholds(paper_trading=0.5, real_trading=0.7)
    assert thresholds.paper_trading == 0.5
    assert thresholds.real_trading == 0.7

def test_confidence_thresholds_real_lower_than_paper_raises_error():
    """Test that a validation error is raised if real_trading is not higher than paper_trading."""
    with pytest.raises(ValidationError) as excinfo:
        ConfidenceThresholds(paper_trading=0.7, real_trading=0.5)
    assert "Real trading confidence threshold should be higher than paper trading" in str(excinfo.value)

def test_confidence_thresholds_equal_raises_error():
    """Test that a validation error is raised if real_trading is equal to paper_trading."""
    with pytest.raises(ValidationError) as excinfo:
        ConfidenceThresholds(paper_trading=0.7, real_trading=0.7)
    assert "Real trading confidence threshold should be higher than paper trading" in str(excinfo.value)

def test_confidence_thresholds_invalid_range_raises_error():
    """Test that a validation error is raised for values outside the 0-1 range."""
    with pytest.raises(ValidationError):
        ConfidenceThresholds(paper_trading=1.1)
    with pytest.raises(ValidationError):
        ConfidenceThresholds(real_trading=-0.1)

# Test cases for UserConfiguration
def test_user_configuration_minimal_valid():
    """Test successful creation of UserConfiguration with minimal required fields."""
    config = UserConfiguration(user_id="test_user")
    assert config.user_id == "test_user"
    assert config.risk_profile == RiskProfile.MODERATE
    assert config.selected_theme == Theme.DARK
    assert config.model_dump(by_alias=True)['riskProfile'] == 'moderate'

def test_user_configuration_full_valid():
    """Test successful creation of UserConfiguration with all fields."""
    ai_config = AIStrategyConfiguration(
        id="ai_config_1",
        name="Test AI Config",
        total_pnl=Decimal("100.50"),
        number_of_trades=10
    )
    config_data = {
        "user_id": "test_user_full",
        "telegram_chat_id": "12345",
        "default_paper_trading_capital": Decimal("10000"),
        "ai_strategy_configurations": [ai_config],
        "ai_analysis_confidence_thresholds": {
            "paper_trading": 0.6,
            "real_trading": 0.8
        }
    }
    config = UserConfiguration(**config_data)
    assert config.user_id == "test_user_full"
    assert config.telegram_chat_id == "12345"
    assert len(config.ai_strategy_configurations) == 1
    assert config.ai_strategy_configurations[0].id == "ai_config_1"
    assert config.get_effective_confidence_thresholds().real_trading == 0.8

def test_user_configuration_get_ai_config_by_id():
    """Test the get_ai_configuration_by_id method."""
    ai_config1 = AIStrategyConfiguration(id="ai_1", name="Config 1")
    ai_config2 = AIStrategyConfiguration(id="ai_2", name="Config 2")
    config = UserConfiguration(
        user_id="test_user",
        ai_strategy_configurations=[ai_config1, ai_config2]
    )
    
    found_config = config.get_ai_configuration_by_id("ai_2")
    assert found_config is not None
    assert found_config.name == "Config 2"
    
    not_found_config = config.get_ai_configuration_by_id("ai_3")
    assert not_found_config is None

def test_user_configuration_unique_id_validation():
    """Test that unique ID validation for lists works correctly."""
    ai_config1 = AIStrategyConfiguration(id="ai_1", name="Config 1")
    ai_config2 = AIStrategyConfiguration(id="ai_1", name="Config 2") # Duplicate ID
    
    with pytest.raises(ValidationError) as excinfo:
        UserConfiguration(
            user_id="test_user",
            ai_strategy_configurations=[ai_config1, ai_config2]
        )
    assert "aiStrategyConfigurations IDs must be unique" in str(excinfo.value)

def test_user_configuration_favorite_pairs_normalization():
    """Test that favorite_pairs are normalized correctly."""
    pairs = ["BTC/USDT", "ETH-USDT", "SOL,USDT"]
    config = UserConfiguration(user_id="test_user", favorite_pairs=pairs)
    assert config.favorite_pairs == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

def test_user_configuration_json_parsing():
    """Test that stringified JSON fields are parsed correctly."""
    config_data = {
        "user_id": "json_user",
        "watchlists": '[{"id": "wl1", "name": "My Watchlist", "pairs": ["BTCUSDT"]}]'
    }
    config = UserConfiguration(**config_data)
    assert len(config.watchlists) == 1
    assert config.watchlists[0].name == "My Watchlist"

def test_user_configuration_camel_case_alias():
    """Test that camelCase aliases work for serialization."""
    config = UserConfiguration(
        user_id="test_user",
        telegram_chat_id="12345"
    )
    dump = config.model_dump(by_alias=True)
    assert "telegramChatId" in dump
    assert dump["telegramChatId"] == "12345"
