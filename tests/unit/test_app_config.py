import pytest
import os
from unittest.mock import patch
from pydantic_core import ValidationError

# Adjust the import path if AppSettings is located elsewhere
from src.ultibot_backend.app_config import AppSettings

def test_load_credential_encryption_key_success():
    """
    Tests that CREDENTIAL_ENCRYPTION_KEY is loaded correctly from environment variables.
    """
    test_key = "test_encryption_key_12345_strong_enough_for_a_test"
    required_env_vars = {
        "CREDENTIAL_ENCRYPTION_KEY": test_key,
        "SUPABASE_URL": "http://fake-supabase.url",
        "SUPABASE_ANON_KEY": "fake_anon_key",
        "SUPABASE_SERVICE_ROLE_KEY": "fake_service_key",
        "DATABASE_URL": "postgresql://fake_user:fake_password@fake_host:5432/fake_db",
        "LOG_LEVEL": "DEBUG" # Optional, but good to include
    }

    # clear=True ensures that only the variables defined in required_env_vars are set during this test.
    # This is important to avoid interference from .env files or pre-existing environment variables.
    with patch.dict(os.environ, required_env_vars, clear=True):
        # Instantiate AppSettings directly to ensure it loads based on the patched environment
        current_settings = AppSettings()
        assert current_settings.CREDENTIAL_ENCRYPTION_KEY == test_key
        assert current_settings.SUPABASE_URL == "http://fake-supabase.url"
        assert current_settings.LOG_LEVEL == "DEBUG"

def test_load_credential_encryption_key_missing_raises_validation_error():
    """
    Tests that a ValidationError is raised if CREDENTIAL_ENCRYPTION_KEY is missing.
    """
    # Environment variables without CREDENTIAL_ENCRYPTION_KEY
    minimal_required_env_vars = {
        "SUPABASE_URL": "http://another-fake-supabase.url",
        "SUPABASE_ANON_KEY": "another_fake_anon_key",
        "SUPABASE_SERVICE_ROLE_KEY": "another_fake_service_key",
        "DATABASE_URL": "postgresql://another_fake_user:another_fake_password@another_fake_host:5432/another_fake_db"
        # LOG_LEVEL has a default, so it's not strictly required here for the test to pass
    }

    # Using clear=True ensures that CREDENTIAL_ENCRYPTION_KEY is indeed missing
    # and not picked up from a potentially existing .env file or environment.
    with patch.dict(os.environ, minimal_required_env_vars, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            AppSettings()  # Attempt to create settings instance

        # Check that the error message clearly indicates the missing field
        error_str = str(exc_info.value).lower()
        assert "credential_encryption_key" in error_str
        # Pydantic v2 typically includes messages like "Field required" or similar.
        # The exact wording can vary, so checking for "field required" or just the field name is robust.
        assert "field required" in error_str # Common in Pydantic v2
        # Example of checking specific error details if needed:
        # found_error = False
        # for error in exc_info.value.errors():
        #     if 'credential_encryption_key' in error['loc'] and error['type'] == 'missing':
        #         found_error = True
        #         break
        # assert found_error, "ValidationError did not report CREDENTIAL_ENCRYPTION_KEY as missing."

# Example of a test for default values, if any were more complex
def test_log_level_default():
    """
    Tests that LOG_LEVEL defaults to "INFO" if not provided.
    """
    # Only provide the absolute minimum required fields, omitting LOG_LEVEL
    minimal_env_vars_for_log_test = {
        "CREDENTIAL_ENCRYPTION_KEY": "a_test_key_for_log_level_test",
        "SUPABASE_URL": "http://logtest-supabase.url",
        "SUPABASE_ANON_KEY": "logtest_anon_key",
        "SUPABASE_SERVICE_ROLE_KEY": "logtest_service_key",
        "DATABASE_URL": "postgresql://logtest:logtest@logtest/logtest"
    }
    with patch.dict(os.environ, minimal_env_vars_for_log_test, clear=True):
        current_settings = AppSettings()
        assert current_settings.LOG_LEVEL == "INFO" # Default value in AppSettings
