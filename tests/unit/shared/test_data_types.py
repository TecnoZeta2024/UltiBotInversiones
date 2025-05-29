import pytest
from src.shared.data_types import add_numbers

def test_add_numbers_positive():
    """
    Verifica que add_numbers suma correctamente dos números positivos.
    """
    assert add_numbers(2, 3) == 5

def test_add_numbers_negative():
    """
    Verifica que add_numbers suma correctamente números negativos.
    """
    assert add_numbers(-2, -3) == -5

def test_add_numbers_zero():
    """
    Verifica que add_numbers suma correctamente con cero.
    """
    assert add_numbers(0, 5) == 5
    assert add_numbers(5, 0) == 5
    assert add_numbers(0, 0) == 0
