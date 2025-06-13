---
description: "Enforcer de consistencia para fixtures"
author: reloj-atomico-optico
version: 2.0
tags: ["fixtures", "consistency", "validation"]
globs: ["*"]
---

# Enforcer de Consistencia para Fixtures

## Validaciones Obligatorias Pre-Commit

### Antes de cualquier cambio en fixtures:
1. **Validar signatures**: Todos los constructores deben tener argumentos válidos
2. **Validar Pydantic models**: Todos los datos de test deben pasar validación
3. **Validar async context**: Todas las fixtures async deben usar await
4. **Validar cleanup**: Todos los recursos deben tener teardown explícito

## Template Obligatorio para Fixtures

```python
@pytest_asyncio.fixture
async def {service_name}_fixture(
    db_session: AsyncSession,
    {dependencies}
) -> {ServiceType}:
    """
    Fixture para {ServiceType}.
    
    Provides: Instancia configurada de {ServiceType}
    Dependencies: {list_dependencies}
    Cleanup: {cleanup_actions}
    """
    # Arrange
    service = {ServiceType}(
        db_session=db_session,
        # ... argumentos requeridos
    )
    
    # Act
    yield service
    
    # Cleanup
    await service.close()  # Si aplica
```

## Reglas de Naming
- `{service_name}_fixture` para servicios
- `{model_name}_data` para datos de test
- `mock_{external_service}` para mocks externos

## Patrones de Fixtures por Categoría

### 1. Fixtures de Servicios del Core
```python
@pytest_asyncio.fixture
async def trading_engine_fixture(
    db_session: AsyncSession,
    market_data_service_fixture: MarketDataService,
    config_service_fixture: ConfigService
) -> TradingEngine:
    """
    Fixture para TradingEngine con dependencias reales.
    
    Provides: TradingEngine completamente configurado
    Dependencies: MarketDataService, ConfigService, AsyncSession
    Cleanup: Cierre de conexiones y cleanup de recursos
    """
    engine = TradingEngine(
        db_session=db_session,
        market_data_service=market_data_service_fixture,
        config_service=config_service_fixture
    )
    
    await engine.initialize()
    
    yield engine
    
    await engine.shutdown()
    await engine.cleanup()
```

### 2. Fixtures de Adaptadores
```python
@pytest_asyncio.fixture
async def binance_adapter_fixture(
    mock_credentials: dict
) -> BinanceAdapter:
    """
    Fixture para BinanceAdapter con credenciales mock.
    
    Provides: BinanceAdapter configurado para testing
    Dependencies: Mock credentials
    Cleanup: Cierre de conexiones HTTP
    """
    adapter = BinanceAdapter(
        api_key=mock_credentials["api_key"],
        api_secret=mock_credentials["api_secret"],
        testnet=True  # Siempre usar testnet en tests
    )
    
    await adapter.connect()
    
    yield adapter
    
    await adapter.disconnect()
```

### 3. Fixtures de Datos Mock
```python
@pytest.fixture
def valid_trade_data() -> dict:
    """
    Datos válidos para crear instancias de Trade.
    
    Returns: Dict con todos los campos requeridos
    """
    return {
        "id": str(uuid4()),
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": Decimal("1.0"),
        "price": Decimal("50000.0"),
        "status": "FILLED",
        "timestamp": datetime.utcnow(),
        "strategy_id": "test_strategy"
    }

@pytest.fixture
def valid_market_data() -> MarketData:
    """
    Instancia válida de MarketData para tests.
    
    Returns: MarketData completamente configurado
    """
    return MarketData(
        symbol="BTCUSDT",
        price=Decimal("50000.0"),
        volume=Decimal("100.0"),
        timestamp=datetime.utcnow(),
        source="BINANCE"
    )
```

### 4. Fixtures de Mock para APIs Externas
```python
@pytest.fixture
def mock_binance_api():
    """
    Mock para API de Binance.
    
    Returns: AsyncMock configurado con respuestas típicas
    """
    mock = AsyncMock()
    
    # Configurar respuestas estándar
    mock.get_ticker.return_value = {
        "symbol": "BTCUSDT",
        "price": "50000.0",
        "volume": "100.0"
    }
    
    mock.place_order.return_value = {
        "orderId": 12345,
        "status": "FILLED",
        "executedQty": "1.0"
    }
    
    return mock

@pytest_asyncio.fixture
async def mock_gemini_service():
    """
    Mock para servicio de Gemini AI.
    
    Returns: AsyncMock con respuestas de AI simuladas
    """
    mock = AsyncMock()
    
    mock.generate_analysis.return_value = {
        "analysis": "BUY signal detected",
        "confidence": 0.85,
        "reasoning": "Technical indicators show bullish trend"
    }
    
    return mock
```

## Validación de Fixtures

### Checklist de Validación:
```python
def validate_fixture_consistency():
    """
    Valida que todas las fixtures sean consistentes.
    
    Checks:
    - Todos los servicios tienen fixtures correspondientes
    - Todas las fixtures tienen cleanup apropiado
    - Todos los mocks están configurados correctamente
    """
    # 1. Verificar que fixture existe para cada servicio
    services = get_all_service_classes()
    fixtures = get_all_fixture_names()
    
    for service in services:
        fixture_name = f"{service.__name__.lower()}_fixture"
        assert fixture_name in fixtures, f"Missing fixture for {service.__name__}"
    
    # 2. Verificar cleanup en fixtures async
    async_fixtures = get_async_fixtures()
    for fixture in async_fixtures:
        assert has_cleanup_code(fixture), f"Missing cleanup in {fixture.__name__}"
```

### Patrón de Factory para Datos Complejos:
```python
class TradeDataFactory:
    """Factory para crear datos de Trade válidos."""
    
    @staticmethod
    def create_buy_trade(**overrides) -> dict:
        """Crea datos para trade de compra."""
        base_data = {
            "id": str(uuid4()),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": Decimal("1.0"),
            "price": Decimal("50000.0"),
            "status": "FILLED",
            "timestamp": datetime.utcnow()
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_sell_trade(**overrides) -> dict:
        """Crea datos para trade de venta."""
        base_data = TradeDataFactory.create_buy_trade()
        base_data.update({"side": "SELL"})
        base_data.update(overrides)
        return base_data

@pytest.fixture
def trade_factory():
    """Factory para crear datos de Trade."""
    return TradeDataFactory
```

## Gestión de Dependencias en Fixtures

### Patrón de Inyección de Dependencias:
```python
@pytest_asyncio.fixture
async def full_trading_system(
    db_session: AsyncSession,
    mock_binance_api,
    mock_gemini_service,
    valid_config: dict
) -> TradingSystem:
    """
    Sistema de trading completo con todas las dependencias.
    
    Integra todos los servicios necesarios para tests de integración.
    """
    # Crear servicios base
    config_service = ConfigService(config=valid_config)
    market_data_service = MarketDataService(
        binance_adapter=mock_binance_api,
        db_session=db_session
    )
    ai_service = AIService(gemini_adapter=mock_gemini_service)
    
    # Crear sistema principal
    trading_system = TradingSystem(
        config_service=config_service,
        market_data_service=market_data_service,
        ai_service=ai_service,
        db_session=db_session
    )
    
    await trading_system.initialize()
    
    yield trading_system
    
    await trading_system.shutdown()
```

## Debugging de Fixtures

### Fixture de Debug:
```python
@pytest_asyncio.fixture
async def debug_trading_service(
    db_session: AsyncSession,
    caplog
) -> TradingService:
    """
    TradingService con logging detallado para debugging.
    """
    # Configurar logging
    logging.getLogger().setLevel(logging.DEBUG)
    
    service = TradingService(db_session=db_session)
    
    # Log estado inicial
    logger.info(f"TradingService initialized: {service}")
    logger.info(f"DB session: {db_session}")
    
    yield service
    
    # Log estado final
    logger.info(f"TradingService cleanup: {service}")
    await service.cleanup()
```

### Fixture de Timing:
```python
@pytest_asyncio.fixture
async def timed_service(db_session: AsyncSession):
    """
    Servicio con medición de tiempo para detectar bottlenecks.
    """
    start_time = time.time()
    
    service = SlowService(db_session=db_session)
    await service.initialize()
    
    init_time = time.time() - start_time
    logger.info(f"Service initialization took: {init_time:.2f}s")
    
    yield service
    
    cleanup_start = time.time()
    await service.cleanup()
    cleanup_time = time.time() - cleanup_start
    logger.info(f"Service cleanup took: {cleanup_time:.2f}s")
```

## Migración de Fixtures Legacy

### Checklist de Migración:
1. **Identificar fixtures obsoletas** sin async support
2. **Convertir a pytest_asyncio.fixture** si es necesario
3. **Añadir type hints** completos
4. **Implementar cleanup** robusto
5. **Validar con tests** de integración

### Patrón de Migración:
```python
# ANTES (Legacy)
@pytest.fixture
def old_service():
    service = Service()
    return service

# DESPUÉS (Migrado)
@pytest_asyncio.fixture
async def service_fixture(db_session: AsyncSession) -> Service:
    """
    Fixture migrada con cleanup robusto.
    
    Provides: Service completamente configurado
    Dependencies: AsyncSession
    Cleanup: Cierre explícito de recursos
    """
    service = Service(db_session=db_session)
    await service.initialize()
    
    yield service
    
    await service.cleanup()
