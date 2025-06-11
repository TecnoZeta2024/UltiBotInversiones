# Adding New Modular Trading Strategies

Esta guía explica cómo extender el sistema de estrategias modulares de UltiBotInversiones para agregar nuevos tipos de estrategias de trading. El diseño modular permite añadir estrategias sin modificar código existente, siguiendo el principio Open/Closed.

## Arquitectura del Sistema de Estrategias

El sistema de estrategias está compuesto por:

1. **Modelos de Dominio** (`src/ultibot_backend/core/domain_models/trading_strategy_models.py`)
2. **Capa de Servicio** (`src/ultibot_backend/services/strategy_service.py`)
3. **Endpoints de API** (`src/ultibot_backend/api/v1/endpoints/strategies.py`)
4. **Esquema de Base de Datos** (tabla `trading_strategy_configs`)

## Pasos para Añadir una Nueva Estrategia

### Paso 1: Definir el Modelo de Parámetros

Crear una nueva clase Pydantic que defina los parámetros específicos de la estrategia:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class MiNuevaEstrategiaParameters(BaseModel):
    """Parámetros específicos para Mi Nueva Estrategia."""
    
    parametro_obligatorio: float = Field(
        ..., 
        gt=0, 
        le=1, 
        description="Descripción del parámetro obligatorio"
    )
    parametro_opcional: Optional[int] = Field(
        None, 
        ge=1, 
        le=100, 
        description="Parámetro opcional con límites"
    )
    
    @validator('parametro_obligatorio')
    def validar_parametro_obligatorio(cls, v):
        """Validación personalizada para el parámetro."""
        if v < 0.01:
            raise ValueError('El parámetro debe ser al menos 0.01')
        return v
    
    @validator('parametro_opcional')
    def validar_relacion_parametros(cls, v, values):
        """Validación cruzada entre parámetros."""
        if v is not None and 'parametro_obligatorio' in values:
            if v * 0.1 > values['parametro_obligatorio']:
                raise ValueError('Relación inválida entre parámetros')
        return v
```

### Paso 2: Actualizar el Enum de Tipos de Estrategia

Añadir el nuevo tipo al enum `BaseStrategyType`:

```python
class BaseStrategyType(str, Enum):
    """Enumeration of base trading strategy types."""
    
    # ... tipos existentes
    MI_NUEVA_ESTRATEGIA = "MI_NUEVA_ESTRATEGIA"
```

### Paso 3: Actualizar el Union Type

Incluir el nuevo modelo en la unión de tipos:

```python
StrategySpecificParameters = Union[
    ScalpingParameters,
    DayTradingParameters,
    # ... otros tipos existentes
    MiNuevaEstrategiaParameters,
    Dict[str, Any]  # Fallback
]
```

### Paso 4: Añadir Validación en TradingStrategyConfig

Actualizar el método de validación para incluir el nuevo tipo:

```python
@validator('parameters')
def validate_parameters_match_strategy_type(cls, v, values):
    """Validate that parameters match the strategy type."""
    if 'base_strategy_type' not in values:
        return v
    
    strategy_type = values['base_strategy_type']
    
    expected_types = {
        # ... mapeos existentes
        BaseStrategyType.MI_NUEVA_ESTRATEGIA: MiNuevaEstrategiaParameters,
    }
    
    # ... resto de la lógica de validación
```

### Paso 5: Actualizar StrategyService

Añadir la conversión de parámetros en el método `_convert_parameters_by_type`:

```python
def _convert_parameters_by_type(
    self, 
    strategy_type: BaseStrategyType, 
    parameters_data: Dict[str, Any]
) -> StrategySpecificParameters:
    """Convert parameters data to the appropriate type."""
    try:
        # ... casos existentes
        elif strategy_type == BaseStrategyType.MI_NUEVA_ESTRATEGIA:
            return MiNuevaEstrategiaParameters(**parameters_data)
        else:
            return parameters_data
    except ValidationError as e:
        logger.warning(f"Failed to validate parameters for {strategy_type}: {e}")
        return parameters_data
```

## Consideraciones de Diseño

### Principios de Validación

1. **Validación Exhaustiva**: Usar type hints y validators de Pydantic
2. **Mensajes de Error Claros**: Proporcionar mensajes descriptivos para facilitar debugging
3. **Validación Cruzada**: Implementar validators que verifiquen relaciones entre parámetros
4. **Valores por Defecto**: Proporcionar defaults sensatos para parámetros opcionales

### Convenciones de Nomenclatura

1. **Clases de Parámetros**: `{NombreEstrategia}Parameters`
2. **Enum Values**: `UPPER_SNAKE_CASE`
3. **Campos de Parámetros**: `snake_case`
4. **Validators**: `validar_{nombre_campo}` o descripción funcional

### Seguridad y Referencias

1. **Credenciales API**: Nunca almacenar directamente, usar referencias a `APICredential.credentialLabel`
2. **Validación de Entrada**: Todos los parámetros deben ser validados estrictamente
3. **Rangos Sensatos**: Establecer límites realistas para parámetros numéricos

## Ejemplo Completo: Estrategia Mean Reversion

```python
class MeanReversionParameters(BaseModel):
    """Parameters for mean reversion trading strategy."""
    
    lookback_period: int = Field(
        ..., 
        ge=5, 
        le=200, 
        description="Número de períodos para calcular la media"
    )
    deviation_threshold: float = Field(
        ..., 
        gt=0, 
        le=5, 
        description="Desviación estándar para señal de entrada"
    )
    profit_target_multiplier: float = Field(
        2.0, 
        gt=1, 
        le=10, 
        description="Multiplicador para profit target"
    )
    max_position_size_pct: Optional[float] = Field(
        None, 
        gt=0, 
        le=1, 
        description="Tamaño máximo de posición como % del capital"
    )
    
    @validator('deviation_threshold')
    def validate_deviation_threshold(cls, v):
        """Validar que el threshold sea razonable."""
        if v < 0.5:
            raise ValueError('Threshold muy bajo, puede generar muchas señales falsas')
        return v
    
    @validator('profit_target_multiplier')
    def validate_profit_target(cls, v, values):
        """Validar relación risk/reward."""
        if 'deviation_threshold' in values:
            risk_reward_ratio = v * values['deviation_threshold']
            if risk_reward_ratio < 1:
                raise ValueError('Risk/reward ratio debe ser al menos 1:1')
        return v
```

## Testing de Nuevas Estrategias

### Tests Unitarios Requeridos

1. **Validación de Parámetros**:
```python
def test_mean_reversion_parameters_validation():
    """Test parameter validation for mean reversion strategy."""
    # Test valid parameters
    valid_params = {
        "lookback_period": 20,
        "deviation_threshold": 2.0,
        "profit_target_multiplier": 3.0
    }
    params = MeanReversionParameters(**valid_params)
    assert params.lookback_period == 20
    
    # Test invalid parameters
    with pytest.raises(ValidationError):
        MeanReversionParameters(
            lookback_period=300,  # Too high
            deviation_threshold=2.0
        )
```

2. **Integración con StrategyService**:
```python
async def test_strategy_service_mean_reversion():
    """Test strategy service with mean reversion strategy."""
    strategy_data = {
        "config_name": "Test Mean Reversion",
        "base_strategy_type": "MEAN_REVERSION",
        "parameters": {
            "lookback_period": 20,
            "deviation_threshold": 2.0
        }
    }
    
    strategy = await strategy_service.create_strategy_config(
        user_id="test_user",
        strategy_data=strategy_data
    )
    
    assert strategy.base_strategy_type == BaseStrategyType.MEAN_REVERSION
    assert isinstance(strategy.parameters, MeanReversionParameters)
```

### Tests de Integración

1. **API Endpoints**: Verificar que los endpoints manejen correctamente la nueva estrategia
2. **Database Persistence**: Confirmar que los parámetros se serialicen/deserialicen correctamente
3. **Error Handling**: Probar escenarios de error y validación

## Deployment y Migración

### Consideraciones de Base de Datos

1. **Sin Migración Requerida**: El sistema usa JSONB para parámetros, soporta nuevos tipos automáticamente
2. **Validación Retroactiva**: Estrategias existentes no se ven afectadas
3. **Versionado**: Considerar implementar versionado de esquemas si hay cambios breaking

### Despliegue Gradual

1. **Desarrollo**: Implementar y probar en entorno local
2. **Validación**: Crear estrategias de prueba con nuevos parámetros
3. **Producción**: Desplegar con feature flag si es necesario

Esta metodología asegura que las nuevas estrategias se integren sin problemas con el sistema existente, manteniendo la estabilidad y extensibilidad del código.

## Checklist para Nueva Estrategia

### Desarrollo
- [ ] Definir modelo de parámetros con validación Pydantic
- [ ] Actualizar enum BaseStrategyType
- [ ] Actualizar union StrategySpecificParameters
- [ ] Añadir validación en TradingStrategyConfig
- [ ] Actualizar conversión en StrategyService
- [ ] Escribir tests unitarios para parámetros
- [ ] Escribir tests de integración para API

### Documentación
- [ ] Actualizar docstrings en modelos
- [ ] Documentar parámetros y su propósito
- [ ] Añadir ejemplos de uso
- [ ] Actualizar documentación de API

### Testing
- [ ] Tests de validación de parámetros
- [ ] Tests de persistencia en base de datos
- [ ] Tests de endpoints de API
- [ ] Tests de error handling
- [ ] Validación manual en UI

### Deployment
- [ ] Verificar migración de base de datos (si necesaria)
- [ ] Deploy en entorno de desarrollo
- [ ] Validación funcional completa
- [ ] Deploy en producción

Esta guía proporciona un marco sistemático para extender el sistema de estrategias de trading manteniendo la calidad y consistencia del código.
