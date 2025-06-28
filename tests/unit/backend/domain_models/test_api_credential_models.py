
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.ultibot_backend.core.domain_models.api_credential_models import APICredentialORM, GUID
from src.ultibot_backend.core.domain_models.base import Base

# Test APICredentialORM Model
def test_api_credential_orm_creation_and_repr():
    user_id = uuid4()
    credential_id = uuid4()
    now = datetime.now()

    credential = APICredentialORM(
        id=credential_id,
        user_id=user_id,
        service_name="Binance",
        credential_label="My Binance API",
        encrypted_api_key="encrypted_key",
        encrypted_api_secret="encrypted_secret",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    assert credential.id == credential_id
    assert credential.user_id == user_id
    assert credential.service_name == "Binance"
    assert credential.credential_label == "My Binance API"
    assert credential.encrypted_api_key == "encrypted_key"
    assert credential.encrypted_api_secret == "encrypted_secret"
    assert credential.is_active is True
    assert credential.created_at == now
    assert credential.updated_at == now

    expected_repr = f"<APICredentialORM(user_id='{user_id}', service_name='Binance', label='My Binance API')>"
    assert repr(credential) == expected_repr

# Test GUID type (basic instantiation, full testing requires a database)
def test_guid_type_process_result_value():
    guid_type = GUID()
    test_uuid_str = str(uuid4())
    result = guid_type.process_result_value(test_uuid_str, None) # dialect is None for basic test
    assert isinstance(result, UUID)
    assert str(result) == test_uuid_str

def test_guid_type_process_bind_param_with_mock_dialect():
    guid_type = GUID()
    test_uuid = uuid4()

    class MockDialect:
        def __init__(self, name):
            self.name = name
        def type_descriptor(self, type_):
            return type_

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
