---
description: "Validación automática de datos de test y factory patterns"
author: reloj-atomico-optico
version: 2.0
tags: ["pydantic", "validation", "test-data", "factories"]
globs: ["*"]
---

# Validación de Datos de Test

## Principios Fundamentales

### 1. Datos de Test Siempre Válidos
- **NUNCA** usar datos hardcoded sin validar
- **SIEMPRE** validar contra esquemas Pydantic
- **USAR** factory patterns para datos complejos
- **VERIFICAR** que todos los campos requeridos estén presentes

### 2. Factory Pattern Obligatorio
- **Datos base válidos** como punto de partida
- **Overrides opcionales** para casos específicos
- **Validación automática** en cada creación
- **Reutilización** entre tests

### 3. Separación por Dominio
- **Una factory** por modelo de dominio
- **Métodos específicos** para diferentes scenarios
- **Composición** para modelos relacionados

## Patrones para Datos de Test Válidos

### 1. Factory Pattern para Modelos Pydantic
```python
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from ultibot_backend.core.domain_models.trading import Trade, MarketData

class TradeDataFactory:
    """Factory para crear datos de Trade válidos."""
    
    @staticmethod
    def create_valid_trade_data(**overrides) -> dict:
        """Crea datos válidos para Trade con overrides opcionales."""
        base_data = {
            "id": str(uuid4()),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": Decimal("1.0"),
            "price": Decimal("50000.0"),
            "status": "FILLED",
            "timestamp": datetime.utcnow(),
            "strategy_id": "test_strategy",
            "commission": Decimal("0.001")
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_buy_trade(**overrides) -> Trade:
        """Crea Trade de compra validado."""
        data = TradeDataFactory.create_valid_trade_data(side="BUY", **overrides)
        return Trade.model_validate(data)
    
    @staticmethod
    def create_sell_trade(**overrides) -> Trade:
        """Crea Trade de venta validado."""
        data = TradeDataFactory.create_valid_trade_data(side="SELL", **overrides)
        return Trade.model_validate(data)
    
    @staticmethod
    def create_failed_trade(**overrides) -> Trade:
        """Crea Trade fallido para tests de error."""
        data = TradeDataFactory.create_valid_trade_data(
            status="FAILED",
            **overrides
        )
        return Trade.model_validate(data)

class MarketDataFactory:
    """Factory para crear datos de MarketData válidos."""
    
    @staticmethod
    def create_valid_market_data(**overrides) -> MarketData:
        """Crea MarketData válido."""
        base_data = {
            "symbol": "BTCUSDT",
            "price": Decimal("50000.0"),
            "volume": Decimal("100.0"),
            "timestamp": datetime.utcnow(),
            "source": "BINANCE",
            "high_24h": Decimal("51000.0"),
            "low_24h": Decimal("49000.0"),
            "change_24h": Decimal("0.02")
        }
        base_data.update(overrides)
        return MarketData.model_validate(base_data)
```

### 2. Fixtures para Modelos Complejos
```python
@pytest.fixture
def valid_trade_data():
    """Datos válidos para Trade."""
    return TradeDataFactory.create_valid_trade_data()

@pytest.fixture
def valid_market_data():
    """MarketData válido."""
    return MarketDataFactory.create_valid_market_data()

@pytest.fixture
def trade_factory():
    """Factory para Trade."""
    return TradeDataFactory

@pytest.fixture
def market_data_factory():
    """Factory para MarketData."""
    return MarketDataFactory
```

### 3. Validación Pre-Test
```python
def test_trade_creation_with_validation(trade_factory):
    """Test que valida datos antes de usar."""
    # Arrange - Datos válidos garantizados
    trade_data = trade_factory.create_valid_trade_data()
    
    # Pre-validación explícita
    trade = Trade.model_validate(trade_data)
    assert trade.is_valid()
    
    # Act - Usar datos validados
    result = process_trade(trade)
    
    # Assert
    assert result.success
```

## Factory Patterns Avanzados

### 1. Factory con Relaciones
```python
class TradingSessionFactory:
    """Factory para sesiones de trading completas."""
    
    @staticmethod
    def create_complete_session(**overrides) -> dict:
        """Crea sesión completa con trades y market data."""
        base_session = {
            "session_id": str(uuid4()),
            "start_time": datetime.utcnow(),
            "strategy": "SuperTrend",
            "trades": [],
            "market_data": []
        }
        
        # Crear trades relacionados
        for i in range(3):
            trade = TradeDataFactory.create_buy_trade(
                timestamp=base_session["start_time"]
            )
            base_session["trades"].append(trade)
        
        # Crear market data relacionado
        for i in range(10):
            market_data = MarketDataFactory.create_valid_market_data(
                timestamp=base_session["start_time"]
            )
            base_session["market_data"].append(market_data)
        
        base_session.update(overrides)
        return base_session
```

### 2. Factory con Estados Específicos
```python
class StrategyParametersFactory:
    """Factory para parámetros de estrategia."""
    
    @staticmethod
    def create_supertrend_params(**overrides) -> dict:
        """Parámetros válidos para SuperTrend."""
        base_params = {
            "period": 14,
            "multiplier": 3.0,
            "min_volatility_percentile": 25.0,
            "max_volatility_percentile": 75.0,
            "volume_threshold": 1000000
        }
        base_params.update(overrides)
        return base_params
    
    @staticmethod
    def create_macd_params(**overrides) -> dict:
        """Parámetros válidos para MACD."""
        base_params = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "threshold": 0.0001
        }
        base_params.update(overrides)
        return base_params
```

### 3. Factory con Validación Automática
```python
class ValidatedDataFactory:
    """Factory que valida automáticamente."""
    
    @staticmethod
    def create_and_validate(model_class, **data):
        """Crea y valida automáticamente cualquier modelo."""
        try:
            instance = model_class.model_validate(data)
            return instance
        except ValidationError as e:
            raise ValueError(f"Factory data invalid for {model_class.__name__}: {e}")
    
    @staticmethod
    def create_trade(**overrides) -> Trade:
        """Crea Trade con validación automática."""
        data = TradeDataFactory.create_valid_trade_data(**overrides)
        return ValidatedDataFactory.create_and_validate(Trade, **data)
```

## Patrones de Validación

### 1. Validación en Setup de Test
```python
@pytest.fixture(autouse=True)
def validate_test_data():
    """Fixture que valida automáticamente datos de test."""
    def _validate_model_data(model_class, data):
        """Valida datos contra modelo Pydantic."""
        if isinstance(data, dict):
            try:
                model_class.model_validate(data)
                return True
            except ValidationError as e:
                pytest.fail(f"Invalid test data for {model_class.__name__}: {e}")
        return True
    
    # Retornar función de validación para uso en tests
    return _validate_model_data
```

### 2. Validación de Factory Outputs
```python
def test_factory_outputs_are_valid():
    """Test que valida todas las factories."""
    # Test TradeDataFactory
    trade_data = TradeDataFactory.create_valid_trade_data()
    trade = Trade.model_validate(trade_data)  # Debe pasar
    assert trade.quantity > 0
    
    # Test MarketDataFactory
    market_data = MarketDataFactory.create_valid_market_data()
    assert market_data.price > 0
    assert market_data.volume >= 0
    
    # Test con overrides
    custom_trade_data = TradeDataFactory.create_valid_trade_data(
        quantity=Decimal("2.5")
    )
    custom_trade = Trade.model_validate(custom_trade_data)
    assert custom_trade.quantity == Decimal("2.5")
```

### 3. Validación de Edge Cases
```python
class EdgeCaseFactory:
    """Factory para casos extremos."""
    
    @staticmethod
    def create_minimal_trade() -> Trade:
        """Trade con datos mínimos válidos."""
        minimal_data = {
            "id": str(uuid4()),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": Decimal("0.00000001"),  # Cantidad mínima
            "price": Decimal("0.01"),  # Precio mínimo
            "status": "FILLED",
            "timestamp": datetime.utcnow()
        }
        return Trade.model_validate(minimal_data)
    
    @staticmethod
    def create_maximum_trade() -> Trade:
        """Trade con valores máximos."""
        max_data = {
            "id": str(uuid4()),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": Decimal("999999999.99999999"),
            "price": Decimal("999999999.99"),
            "status": "FILLED",
            "timestamp": datetime.utcnow()
        }
        return Trade.model_validate(max_data)
```

## Debugging de Datos de Test

### 1. Logging de Validación
```python
import logging

def debug_validation_error(model_class, data, error):
    """Debug helper para errores de validación."""
    logger = logging.getLogger(__name__)
    logger.error(f"Validation failed for {model_class.__name__}")
    logger.error(f"Data: {data}")
    logger.error(f"Error: {error}")
    
    # Mostrar campos requeridos vs proporcionados
    required_fields = model_class.model_fields
    provided_fields = set(data.keys()) if isinstance(data, dict) else set()
    missing_fields = set(required_fields.keys()) - provided_fields
    
    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
```

### 2. Test de Schemas
```python
def test_model_schemas_are_valid():
    """Valida que los schemas de modelos sean correctos."""
    from ultibot_backend.core.domain_models import Trade, MarketData
    
    # Verificar que los modelos tienen schemas válidos
    trade_schema = Trade.model_json_schema()
    assert "properties" in trade_schema
    assert "required" in trade_schema
    
    market_data_schema = MarketData.model_json_schema()
    assert "properties" in market_data_schema
    assert "required" in market_data_schema
```

### 3. Validación de Serialización
```python
def test_model_serialization():
    """Test que los modelos se serialicen correctamente."""
    trade = TradeDataFactory.create_buy_trade()
    
    # Test JSON serialization
    json_data = trade.model_dump_json()
    assert isinstance(json_data, str)
    
    # Test round-trip
    reconstructed = Trade.model_validate_json(json_data)
    assert reconstructed == trade
```

## Best Practices

### 1. Organización de Factories
```python
# tests/factories/__init__.py
from .trade_factory import TradeDataFactory
from .market_data_factory import MarketDataFactory
from .strategy_factory import StrategyParametersFactory

__all__ = [
    "TradeDataFactory",
    "MarketDataFactory", 
    "StrategyParametersFactory"
]
```

### 2. Fixtures Centralizadas
```python
# tests/conftest.py
from tests.factories import TradeDataFactory, MarketDataFactory

@pytest.fixture
def trade_factory():
    return TradeDataFactory

@pytest.fixture
def market_data_factory():
    return MarketDataFactory
```

### 3. Validación en CI/CD
```bash
# En pipeline de CI/CD
poetry run pytest tests/test_factories.py -v
poetry run pytest tests/test_data_validation.py -v
```

## Troubleshooting

### ValidationError en Tests
1. **Verificar campos requeridos** en el modelo
2. **Comprobar tipos de datos** (Decimal vs float)
3. **Validar formato de fechas** (timezone aware)
4. **Revisar restricciones** (min/max values)

### Factory Inconsistencies
1. **Ejecutar test de factory validation**
2. **Verificar overrides** no rompen validación
3. **Comprobar relaciones** entre modelos
4. **Validar edge cases** funcionan correctamente
