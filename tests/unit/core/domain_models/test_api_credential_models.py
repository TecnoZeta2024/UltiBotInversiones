
import pytest
from uuid import UUID, uuid4
from datetime import datetime
import unittest.mock as mock

from src.core.domain_models.api_credential_models import GUID, APICredentialORM

# Tests for the GUID TypeDecorator
# =================================================================
class TestGUIDTypeDecorator:

    @pytest.fixture
    def guid_type(self):
        """Fixture to provide an instance of the GUID type decorator."""
        return GUID()

    @pytest.fixture
    def postgres_dialect(self):
        """Mock PostgreSQL dialect."""
        dialect = mock.Mock()
        dialect.name = 'postgresql'
        dialect.type_descriptor.return_value = mock.Mock()
        return dialect

    @pytest.fixture
    def sqlite_dialect(self):
        """Mock SQLite dialect."""
        dialect = mock.Mock()
        dialect.name = 'sqlite'
        dialect.type_descriptor.return_value = mock.Mock()
        return dialect

    def test_load_dialect_impl_postgresql(self, guid_type, postgres_dialect):
        """Test that GUID uses PG_UUID for PostgreSQL."""
        guid_type.load_dialect_impl(postgres_dialect)
        postgres_dialect.type_descriptor.assert_called_once()
        # Check if it was called with something that looks like PG_UUID
        # We can't directly import PG_UUID here without circular dependency or complex mocking
        # So we check the type of the object passed to type_descriptor
        assert "UUID" in str(postgres_dialect.type_descriptor.call_args[0][0].__class__)

    def test_load_dialect_impl_sqlite(self, guid_type, sqlite_dialect):
        """Test that GUID uses Text for SQLite."""
        guid_type.load_dialect_impl(sqlite_dialect)
        sqlite_dialect.type_descriptor.assert_called_once()
        # Check if it was called with Text
        assert "Text" in str(sqlite_dialect.type_descriptor.call_args[0][0].__class__)

    def test_process_bind_param_none(self, guid_type, postgres_dialect, sqlite_dialect):
        """Test that None is handled correctly."""
        assert guid_type.process_bind_param(None, postgres_dialect) is None
        assert guid_type.process_bind_param(None, sqlite_dialect) is None

    def test_process_bind_param_uuid_to_str_for_dialects(self, guid_type, postgres_dialect, sqlite_dialect):
        """Test that UUID objects are converted to strings for all dialects."""
        test_uuid = uuid4()
        assert guid_type.process_bind_param(test_uuid, postgres_dialect) == str(test_uuid)
        assert guid_type.process_bind_param(test_uuid, sqlite_dialect) == str(test_uuid)

    def test_process_bind_param_str_uuid_for_sqlite(self, guid_type, sqlite_dialect):
        """Test that string UUIDs are validated and passed through for SQLite."""
        test_uuid_str = str(uuid4())
        assert guid_type.process_bind_param(test_uuid_str, sqlite_dialect) == test_uuid_str

    def test_process_bind_param_invalid_uuid_str_for_sqlite(self, guid_type, sqlite_dialect):
        """Test that an invalid UUID string raises ValueError for SQLite."""
        with pytest.raises(ValueError):
            guid_type.process_bind_param("not-a-uuid", sqlite_dialect)

    def test_process_result_value_none(self, guid_type, postgres_dialect):
        """Test that None is returned as None."""
        assert guid_type.process_result_value(None, postgres_dialect) is None

    def test_process_result_value_from_uuid(self, guid_type, postgres_dialect):
        """Test that a UUID object is returned as is."""
        test_uuid = uuid4()
        assert guid_type.process_result_value(test_uuid, postgres_dialect) == test_uuid

    def test_process_result_value_from_str(self, guid_type, postgres_dialect):
        """Test that a string is converted to a UUID object."""
        test_uuid = uuid4()
        assert guid_type.process_result_value(str(test_uuid), postgres_dialect) == test_uuid

# Tests for the APICredentialORM Model
# =================================================================
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.domain_models.base import Base

class TestAPICredentialORM:

    @pytest.fixture(scope="function")
    def db_session(self):
        """Provides a SQLAlchemy session for testing, with a clean database for each test."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(engine)

    def test_creation_with_required_fields(self, db_session):
        """Test that an instance can be created with all required fields and persisted."""
        user_id = uuid4()
        credential = APICredentialORM(
            user_id=user_id,
            service_name="binance",
            credential_label="my_key",
            encrypted_api_key="encrypted_key"
        )
        db_session.add(credential)
        db_session.commit()
        assert isinstance(credential.id, UUID)
        assert credential.user_id == user_id
        assert credential.service_name == "binance"
        assert credential.credential_label == "my_key"
        assert credential.encrypted_api_key == "encrypted_key"
        assert credential.encrypted_api_secret is None
        assert credential.is_active is True
        assert isinstance(credential.created_at, datetime)
        assert isinstance(credential.updated_at, datetime)

    def test_creation_with_all_fields(self, db_session):
        """Test that an instance can be created with all fields, including optional ones, and persisted."""
        user_id = uuid4()
        credential = APICredentialORM(
            user_id=user_id,
            service_name="binance_futures",
            credential_label="another_key",
            encrypted_api_key="key123",
            encrypted_api_secret="secret123",
            is_active=False
        )
        db_session.add(credential)
        db_session.commit()
        assert credential.encrypted_api_secret == "secret123"
        assert credential.is_active is False

    def test_repr_method(self, db_session):
        """Test the __repr__ method for a clear representation."""
        user_id = uuid4()
        credential = APICredentialORM(
            user_id=user_id,
            service_name="kucoin",
            credential_label="main_account",
            encrypted_api_key="key"
        )
        # No need to add to session for __repr__ test, but keeping db_session fixture for consistency
        expected_repr = f"<APICredentialORM(user_id='{user_id}', service_name='kucoin', label='main_account')>"
        assert repr(credential) == expected_repr
