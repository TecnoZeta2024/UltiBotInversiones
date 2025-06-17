---
description: "Mejores prácticas para tests asíncronos robustos"
author: reloj-atomico-optico
version: 2.0
tags: ["asyncio", "testing", "fixtures", "best-practices"]
globs: ["*"]
---

# Mejores Prácticas para Tests Asíncronos

## Reglas Fundamentales

### 1. Gestión de Event Loop
- **SIEMPRE** usar `scope="session"` para event_loop fixture
- **NUNCA** crear múltiples event loops en la misma sesión
- **SIEMPRE** cerrar recursos explícitamente

### 2. Fixtures de Base de Datos
- **Usar transacciones** para aislamiento entre tests
- **Rollback automático** en teardown
- **Session única** por test suite

### 3. Mocking de Servicios Asíncronos
- **AsyncMock** para métodos async
- **patch.object** para servicios específicos
- **pytest-asyncio** para decoradores

## Patrones Obligatorios

### Fixture de Servicio Estándar:
```python
@pytest_asyncio.fixture
async def service_instance(db_session):
    service = ServiceClass(db_session=db_session)
    yield service
    await service.cleanup()  # Si aplica
```

### Test Asíncrono Estándar:
```python
@pytest.mark.asyncio
async def test_async_operation(service_instance):
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = await service_instance.async_method(input_data)
    
    # Assert
    assert result.is_valid()
```

### Fixture de Event Loop Robusta:
```python
@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture de event loop para toda la sesión.
    Previene errores de "Event loop is closed".
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
```

### Fixture de Base de Datos Transaccional:
```python
@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """
    Fixture de sesión de BD con rollback automático.
    Aislamiento completo entre tests.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()
    
    async_session = AsyncSession(bind=connection)
    
    try:
        yield async_session
    finally:
        await async_session.close()
        await transaction.rollback()
        await connection.close()
```

## Antipatrones a Evitar

### ❌ Event Loop Múltiple
```python
# MAL - Crea múltiples loops
@pytest.fixture
def event_loop():  # scope="function" es problemático
    return asyncio.new_event_loop()
```

### ❌ Fixtures Sin Cleanup
```python
# MAL - Sin cleanup de recursos
@pytest_asyncio.fixture
async def db_session():
    session = AsyncSession()
    yield session
    # ❌ Sin cleanup explícito
```

### ❌ Mocking Sincrónico para Async
```python
# MAL - Mock sincrónico para método async
@patch('service.async_method', return_value="result")
async def test_method(mock_method):
    # ❌ Esto causará problemas
    result = await service.async_method()
```

## Patterns Correctos

### ✅ Event Loop de Sesión
```python
@pytest.fixture(scope="session")
def event_loop():
    """Event loop único para toda la sesión."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
```

### ✅ Fixture con Cleanup Robusto
```python
@pytest_asyncio.fixture
async def trading_service(db_session):
    """Fixture de servicio con cleanup completo."""
    service = TradingService(db_session=db_session)
    await service.initialize()
    
    yield service
    
    # Cleanup explícito
    await service.shutdown()
    await service.cleanup_resources()
```

### ✅ AsyncMock para Métodos Async
```python
@patch('service.external_api_call', new_callable=AsyncMock)
async def test_with_external_api(mock_api):
    """Mock correcto para método asíncrono."""
    mock_api.return_value = {"data": "test"}
    
    result = await service.process_data()
    
    assert result.is_success()
    mock_api.assert_called_once()
```

## Debugging de Tests Asíncronos

### Detectar Event Loop Issues
```python
import asyncio

def test_event_loop_status():
    """Verificar estado del event loop."""
    loop = asyncio.get_event_loop()
    print(f"Loop running: {loop.is_running()}")
    print(f"Loop closed: {loop.is_closed()}")
    assert not loop.is_closed()
```

### Timeout en Tests Largos
```python
@pytest.mark.asyncio
@pytest.mark.timeout(30)  # 30 segundos máximo
async def test_long_operation():
    """Test con timeout para operaciones largas."""
    result = await long_async_operation()
    assert result is not None
```

### Logging para Debugging
```python
import logging

@pytest_asyncio.fixture
async def service_with_logging(db_session):
    """Fixture con logging para debugging."""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    service = ServiceClass(db_session=db_session, logger=logger)
    logger.info("Service initialized for test")
    
    yield service
    
    logger.info("Service cleanup starting")
    await service.cleanup()
    logger.info("Service cleanup completed")
```

## Configuración de conftest.py Robusta

### Template Básico:
```python
import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

@pytest.fixture(scope="session")
def event_loop():
    """Event loop único para toda la sesión."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Motor de BD para toda la sesión."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    """Sesión de BD con rollback automático."""
    async with AsyncSession(db_engine) as session:
        async with session.begin():
            yield session
            await session.rollback()
```

## Markers Útiles

### Clasificación de Tests:
```python
# En pyproject.toml
markers = [
    "slow: tests que tardan más de 5 segundos",
    "integration: tests de integración",
    "unit: tests unitarios",
    "asyncio: tests asíncronos",
    "database: tests que requieren BD"
]
```

### Uso en Tests:
```python
@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.integration
async def test_full_trading_flow():
    """Test completo del flujo de trading."""
    pass

@pytest.mark.asyncio
@pytest.mark.unit
async def test_strategy_calculation():
    """Test unitario de cálculo de estrategia."""
    pass
```

## Troubleshooting Common Issues

### "Event loop is closed"
- **Causa**: Event loop scope incorrecto
- **Solución**: Usar `scope="session"` en event_loop fixture

### "Task was destroyed but it is pending"
- **Causa**: Tareas async sin await o cleanup
- **Solución**: Asegurar cleanup en fixtures

### "RuntimeError: no running event loop"
- **Causa**: Llamada async sin decorador @pytest.mark.asyncio
- **Solución**: Decorar test con @pytest.mark.asyncio

### "Database connection pool timeout"
- **Causa**: Sesiones de BD sin cerrar
- **Solución**: Usar context managers y rollback explícito
