import pytest
from uuid import UUID, uuid4

@pytest.fixture(scope="session")
def user_id() -> UUID:
    """
    Provides a fixed user ID for the entire test session.
    This ensures consistency across tests that rely on a specific user.
    """
    return uuid4()
