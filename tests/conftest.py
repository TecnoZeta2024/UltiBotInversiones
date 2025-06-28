import sys
import os
import pytest
from uuid import UUID, uuid4
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone
from decimal import Decimal

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app_config import AppSettings, get_app_settings
from src.core.domain_models.opportunity_models import (
    Opportunity, 
    OpportunityStatus, 
    SourceType, 
    InitialSignal,
    Direction
)
from src.core.domain_models.user_configuration_models import AIStrategyConfiguration, ConfidenceThresholds
from src.services.ai_orchestrator_service import AIOrchestrator
from src.adapters.persistence_service import SupabasePersistenceService
from src.services.market_data_service import MarketDataService

@pytest.fixture(scope="session")
def app_settings_fixture() -> AppSettings:
    """
    Provides application settings. It now correctly uses the get_app_settings
    function which handles loading from the correct .env file and caching.
    """
    import os
    os.environ["TESTING"] = "True"
    return get_app_settings()

@pytest.fixture(scope="session")
def user_id(app_settings_fixture: AppSettings) -> UUID:
    """
    Provides a fixed user ID for the entire test session from settings.
    """
    return app_settings_fixture.FIXED_USER_ID

@pytest.fixture
def mock_persistence_service() -> MagicMock:
    """
    Provides a more robust mock for SupabasePersistenceService, simulating
    the async session and SQLAlchemy's Result object structure to prevent
    'coroutine' object has no attribute '_mapping' errors.
    """
    mock = AsyncMock(spec=SupabasePersistenceService)
    
    # Mock the async context manager for sessions
    mock_session = AsyncMock()
    
    # Mock the result of session.execute()
    # This should be a MagicMock, not AsyncMock, because the result object
    # itself is not awaitable, but is the result of an awaited call.
    mock_result = MagicMock()
    
    # Configure the chain of calls: result.scalars().first()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None # Default to finding nothing
    mock_result.scalars.return_value = mock_scalars
    
    # Configure the chain for fetchone()._mapping
    mock_record = MagicMock()
    mock_record._mapping = {} # Default to an empty dict
    mock_result.fetchone.return_value = mock_record
    
    # Configure the chain for fetchall()
    mock_result.fetchall.return_value = [] # Default to an empty list
    
    # Configure the chain for scalars().all()
    mock_scalars.all.return_value = [] # Default to an empty list

    # Set the return value for session.execute
    mock_session.execute.return_value = mock_result
    
    # The service's _get_session() should return our mock session
    mock_async_session_manager = AsyncMock()
    mock_async_session_manager.__aenter__.return_value = mock_session
    mock._get_session.return_value = mock_async_session_manager
    
    # Also mock the direct method calls for tests that patch them directly
    mock.get_user_configuration = AsyncMock(return_value=None)
    mock.upsert_user_configuration = AsyncMock()

    return mock

@pytest.fixture
def mock_market_data_service() -> MagicMock:
    """Mock for MarketDataService."""
    return AsyncMock(spec=MarketDataService)

@pytest.fixture
def ai_orchestrator_fixture(mock_market_data_service: MagicMock) -> AIOrchestrator:
    """Provides an instance of the AIOrchestrator with a mocked market data service."""
    return AIOrchestrator(market_data_service=mock_market_data_service)

@pytest.fixture
def sample_opportunity_data() -> Opportunity:
    """Provides a complete and valid sample Opportunity for testing."""
    current_time = datetime.now(timezone.utc) # Defined current_time

    return Opportunity(
        id=str(uuid4()),
        user_id=str(uuid4()),
        strategy_id=uuid4(),
        symbol="BTC/USDT",
        exchange="binance",
        detected_at=current_time, # Using defined current_time
        source_type=SourceType.MANUAL_ENTRY,
        source_name="Test Source",
        source_data={},
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=Decimal("50000"),
            stop_loss_target=Decimal("49000"),
            take_profit_target=[Decimal("51000"), Decimal("52000")],
            timeframe="1h",
            reasoning_source_structured={},
            reasoning_source_text="Test reasoning",
            confidence_source=0.9
        ),
        system_calculated_priority_score=50, # Added default
        last_priority_calculation_at=current_time, # Added default
        status=OpportunityStatus.NEW,
        status_reason_code=None, # Added default
        status_reason_text=None, # Added default
        ai_analysis=None, # Added default
        investigation_details=None, # Added default
        user_feedback=None, # Added default
        linked_trade_ids=[], # Added default
        expires_at=None, # Added default
        expiration_logic=None, # Added default
        post_trade_feedback=None, # Added default
        post_facto_simulation_results=None, # Added default
        created_at=current_time, # Using defined current_time
        updated_at=current_time # Using defined current_time
    )

@pytest.fixture
def sample_ai_config() -> AIStrategyConfiguration:
    """Provides a sample AI strategy configuration."""
    return AIStrategyConfiguration(
        id="ai-config-001",
        name="Test AI Config",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        total_pnl=Decimal("0.0"),
        number_of_trades=0,
        applies_to_strategies=None,
        applies_to_pairs=None,
        gemini_prompt_template=None,
        tools_available_to_gemini=None,
        output_parser_config=None,
        indicator_weights=None,
        confidence_thresholds=ConfidenceThresholds(paper_trading=0.7, real_trading=0.85),
        max_context_window_tokens=None
    )
