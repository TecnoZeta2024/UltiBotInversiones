"""
Este archivo contendrá definiciones de tipos de datos compartidos,
por ejemplo, modelos Pydantic comunes si la UI los consume directamente
o si hay tipos de datos que tanto el backend como la UI necesitan conocer.
"""

def add_numbers(a: int, b: int) -> int:
    """
    Suma dos números enteros y devuelve el resultado.

    Args:
        a: El primer número entero.
        b: El segundo número entero.

    Returns:
        La suma de los dos números.
    """
    return a + b
