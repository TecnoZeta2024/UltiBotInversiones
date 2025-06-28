import pytest
import requests
import os
import pathlib
import time

# Define the path to the test database (should match conftest.py)
TEST_DB_PATH = pathlib.Path(__file__).parent.parent.parent / "ultibot_local.db"

@pytest.mark.asyncio
async def test_e2e_servers_start_and_stop(e2e_setup):
    """
    Verifies that the backend and frontend servers start and are accessible.
    """
    backend_url = "http://127.0.0.1:8000"
    frontend_url = "http://localhost:5173"

    # Verify backend is running
    try:
        response = requests.get(f"{backend_url}/docs")
        assert response.status_code == 200, f"Backend not accessible at {backend_url}/docs"
    except requests.ConnectionError:
        pytest.fail(f"Backend server is not running or not accessible at {backend_url}")

    # Verify frontend is running
    try:
        response = requests.get(frontend_url)
        assert response.status_code == 200, f"Frontend not accessible at {frontend_url}"
    except requests.ConnectionError:
        pytest.fail(f"Frontend server is not running or not accessible at {frontend_url}")

    # Verify database cleanup (should not exist at this point if cleanup_test_db is working)
    assert not TEST_DB_PATH.exists(), f"Test database file {TEST_DB_PATH} should not exist at the start of the test."

    print(f"Backend accessible at {backend_url}")
    print(f"Frontend accessible at {frontend_url}")
