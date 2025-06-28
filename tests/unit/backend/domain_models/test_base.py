import pytest
from sqlalchemy.ext.declarative import declarative_base

# Test that Base is defined and is a declarative base
def test_base_definition():
    Base = declarative_base()
    assert Base is not None
    assert hasattr(Base, 'metadata') # Check for metadata attribute instead of _decl_class_registry