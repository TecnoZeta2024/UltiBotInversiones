import sys
import os
import pytest
import subprocess
os.environ["TESTING"] = "True"
import time
import requests
import asyncio
import pathlib
import shutil
from uuid import UUID, uuid4
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone
from decimal import Decimal
import threading
from typing import Tuple, AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# Add the src directory to the Python path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.main import create_app
from src.dependencies import DependencyContainer
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
from src.services.config_service import ConfigurationService
from src.services.credential_service import CredentialService
from src.services.trading_engine_service import TradingEngine
from src.services.unified_order_execution_service import UnifiedOrderExecutionService
from src.services.portfolio_service import PortfolioService
from src.services.performance_service import PerformanceService
from src.services.trading_report_service import TradingReportService
from src.services.notification_service import NotificationService
from src.services.strategy_service import StrategyService
from src.adapters.binance_adapter import BinanceAdapter
from src.adapters.redis_cache import RedisCache

# Define the path to the test database
TEST_DB_PATH = pathlib.Path(__file__).parent.parent / "ultibot_local.db"

def read_stream(stream, buffer):
    for line in iter(stream.readline, ''):
        buffer.append(line)
    stream.close()

@pytest.fixture(scope="function", autouse=True)
def cleanup_test_db():
    """
    Ensures the test database is clean before and after each test function.
    This fixture runs automatically for each test.
    """
    print(f"[{datetime.now()}] Cleaning up test database: {TEST_DB_PATH}")
    if TEST_DB_PATH.exists():
        try:
            os.remove(TEST_DB_PATH)
            print(f"[{datetime.now()}] Successfully removed test database: {TEST_DB_PATH}")
        except OSError as e:
            print(f"[{datetime.now()}] Error removing test database {TEST_DB_PATH}: {e}")
            # Attempt to force delete if possible (Windows specific)
            if os.name == 'nt': # For Windows
                try:
                    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], check=False, capture_output=True)
                    subprocess.run(["taskkill", "/F", "/IM", "node.exe"], check=False, capture_output=True)
                    time.sleep(1) # Give time for processes to terminate
                    if TEST_DB_PATH.exists():
                        os.remove(TEST_DB_PATH)
                        print(f"[{datetime.now()}] Successfully force-removed test database after taskkill: {TEST_DB_PATH}")
                except Exception as force_e:
                    print(f"[{datetime.now()}] Failed to force-remove database: {force_e}")
            pytest.fail(f"Failed to clean up test database: {TEST_DB_PATH}. It might be locked. Error: {e}")
    yield
    print(f"[{datetime.now()}] Final cleanup of test database: {TEST_DB_PATH}")
    if TEST_DB_PATH.exists():
        try:
            os.remove(TEST_DB_PATH)
            print(f"[{datetime.now()}] Successfully removed test database during final cleanup: {TEST_DB_PATH}")
        except OSError as e:
            print(f"[{datetime.now()}] Error during final cleanup of test database {TEST_DB_PATH}: {e}")
            # Attempt to force delete if possible (Windows specific)
            if os.name == 'nt': # For Windows
                try:
                    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], check=False, capture_output=True)
                    subprocess.run(["taskkill", "/F", "/IM", "node.exe"], check=False, capture_output=True)
                    time.sleep(1) # Give time for processes to terminate
                    if TEST_DB_PATH.exists():
                        os.remove(TEST_DB_PATH)
                        print(f"[{datetime.now()}] Successfully force-removed test database during final cleanup after taskkill: {TEST_DB_PATH}")
                except Exception as force_e:
                    print(f"[{datetime.now()}] Failed to force-remove database during final cleanup: {force_e}")
            pytest.fail(f"Failed final cleanup of test database: {TEST_DB_PATH}. It might be locked. Error: {e}")


@pytest.fixture(scope="session")
def live_server():
    """
    Fixture to run the FastAPI application in a separate process for e2e tests.
    """
    env = os.environ.copy()
    env["TESTING"] = "True"
    # Ensure the backend uses the test database
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

    print(f"[{datetime.now()}] Starting backend server...")
    process = subprocess.Popen(
        ["poetry", "run", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--app-dir", "src/"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    stdout_buffer = []
    stderr_buffer = []
    stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, stdout_buffer))
    stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, stderr_buffer))
    stdout_thread.start()
    stderr_thread.start()

    timeout = time.time() + 30
    base_url = "http://127.0.0.1:8000"
    while True:
        try:
            response = requests.get(f"{base_url}/docs")
            if response.status_code == 200:
                print(f"[{datetime.now()}] Backend server started successfully at {base_url}")
                break
        except requests.ConnectionError:
            if time.time() > timeout:
                print(f"[{datetime.now()}] Backend stdout: {''.join(stdout_buffer)}")
                print(f"[{datetime.now()}] Backend stderr: {''.join(stderr_buffer)}")
                pytest.fail(f"Server failed to start within 30 seconds.")
            time.sleep(0.5)

    yield base_url
    print(f"[{datetime.now()}] Backend server yielded: {base_url}")
    
    process.terminate()
    time.sleep(1) # Give time for process to terminate
    process.wait()
    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)
    print(f"[{datetime.now()}] Backend server terminated.")
    print(f"[{datetime.now()}] Backend stdout on exit: {''.join(stdout_buffer)}")
    print(f"[{datetime.now()}] Backend stderr on exit: {''.join(stderr_buffer)}")


@pytest.fixture(scope="session")
def frontend_server():
    """
    Fixture to run the frontend development server in a separate process for e2e tests.
    """
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/ultibot_frontend'))
    
    print(f"[{datetime.now()}] Starting frontend server from {frontend_path}...")
    process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True
    )

    stdout_buffer = []
    stderr_buffer = []
    stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, stdout_buffer))
    stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, stderr_buffer))
    stdout_thread.start()
    stderr_thread.start()

    timeout = time.time() + 60
    frontend_url = "http://localhost:5173"
    while True:
        try:
            response = requests.get(frontend_url)
            if response.status_code == 200:
                print(f"[{datetime.now()}] Frontend server started successfully at {frontend_url}")
                break
        except requests.ConnectionError:
            if time.time() > timeout:
                print(f"[{datetime.now()}] Frontend stdout: {''.join(stdout_buffer)}")
                print(f"[{datetime.now()}] Frontend stderr: {''.join(stderr_buffer)}")
                pytest.fail(f"Frontend server failed to start within 60 seconds.")
            time.sleep(1)

    yield frontend_url
    print(f"[{datetime.now()}] Frontend server yielded: {frontend_url}")
    
    process.terminate()
    time.sleep(1) # Give time for process to terminate
    process.wait()
    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)
    print(f"[{datetime.now()}] Frontend server terminated.")
    print(f"[{datetime.now()}] Frontend stdout on exit: {''.join(stdout_buffer)}")
    print(f"[{datetime.now()}] Frontend stderr on exit: {''.join(stderr_buffer)}")

@pytest.fixture(scope="session")
async def e2e_setup(live_server, frontend_server):
    """
    Combines backend and frontend server fixtures for E2E test setup.
    """
    print(f"[{datetime.now()}] E2E setup complete. Both servers are running.")
    yield
    print(f"[{datetime.now()}] E2E teardown complete.")

@pytest.fixture(scope="session")
def app_settings_fixture() -> AppSettings:
    """
    Provides application settings. It now correctly uses the get_app_settings
    function which handles loading from the correct .env file and caching.
    """
    return get_app_settings()

@pytest.fixture(scope="session")
def user_id(app_settings_fixture: AppSettings) -> UUID:
    """
    Provides a fixed user ID for the entire test session from settings.
    """
    return app_settings_fixture.FIXED_USER_ID

@pytest.fixture
def mock_persistence_service() -> AsyncMock:
    """
    Provides a fully asynchronous mock for SupabasePersistenceService.
    This ensures all methods are awaitable by default.
    """
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default event loop for the entire test session.
    Prevents 'Event loop is closed' errors with pytest-asyncio.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_dependency_container() -> MagicMock:
    """
    Provides a fully mocked DependencyContainer with all service attributes.
    Using MagicMock as the base allows for flexible attribute assignment,
    while spec ensures it conforms to the DependencyContainer's interface.
    """
    container_mock = MagicMock(spec=DependencyContainer)

    # Mock all service attributes to prevent AttributeError in integration tests
    container_mock.persistence_service = AsyncMock(spec=SupabasePersistenceService)
    container_mock.config_service = AsyncMock(spec=ConfigurationService)
    container_mock.credential_service = AsyncMock(spec=CredentialService)
    container_mock.trading_engine_service = AsyncMock(spec=TradingEngine)
    container_mock.unified_order_execution_service = AsyncMock(spec=UnifiedOrderExecutionService)
    container_mock.market_data_service = AsyncMock(spec=MarketDataService)
    container_mock.ai_orchestrator = AsyncMock(spec=AIOrchestrator)
    container_mock.portfolio_service = AsyncMock(spec=PortfolioService)
    container_mock.performance_service = AsyncMock(spec=PerformanceService)
    container_mock.report_service = AsyncMock(spec=TradingReportService)
    container_mock.notification_service = AsyncMock(spec=NotificationService)
    container_mock.strategy_service = AsyncMock(spec=StrategyService)
    container_mock.binance_adapter = AsyncMock(spec=BinanceAdapter)
    container_mock.cache = AsyncMock(spec=RedisCache)
    
    return container_mock

@pytest_asyncio.fixture
async def client(mock_dependency_container: AsyncMock) -> AsyncGenerator[Tuple[AsyncClient, FastAPI], None]:
    """
    Test client fixture that injects a mocked dependency container for each test.
    This ensures complete isolation from real services during integration tests.
    """
    app = create_app()

    async with app.router.lifespan_context(app):
        # In testing, we inject the mocked container directly into the app's state.
        # This bypasses the real service initialization in the lifespan event.
        app.state.dependency_container = mock_dependency_container
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, app


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

@pytest.fixture
def trading_engine_fixture() -> TradingEngine:
    """
    Provides a REAL TradingEngine instance with mocked dependencies for integration tests.
    This allows testing the internal logic of TradingEngine while controlling its external interactions.
    """
    # Mock all service dependencies with AsyncMocks
    persistence_service = AsyncMock(spec=SupabasePersistenceService)
    market_data_service = AsyncMock(spec=MarketDataService)
    unified_order_execution_service = AsyncMock(spec=UnifiedOrderExecutionService)
    credential_service = AsyncMock(spec=CredentialService)
    notification_service = AsyncMock(spec=NotificationService)
    strategy_service = AsyncMock(spec=StrategyService)
    configuration_service = AsyncMock(spec=ConfigurationService)
    portfolio_service = AsyncMock(spec=PortfolioService)
    ai_orchestrator = AsyncMock(spec=AIOrchestrator)

    # Create a real instance of the TradingEngine with mocked dependencies
    engine = TradingEngine(
        persistence_service=persistence_service,
        market_data_service=market_data_service,
        unified_order_execution_service=unified_order_execution_service,
        credential_service=credential_service,
        notification_service=notification_service,
        strategy_service=strategy_service,
        configuration_service=configuration_service,
        portfolio_service=portfolio_service,
        ai_orchestrator=ai_orchestrator,
    )

    # Spy on methods that we might want to assert calls to, without replacing their logic.
    # We use patch.object on the *instance* to spy on them.
    # Note: This is better done inside the test itself using `with patch.object(...)`
    # to avoid test-to-test contamination. We leave this fixture clean.

    return engine
