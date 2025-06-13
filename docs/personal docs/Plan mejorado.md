## __PLAN MEJORADO Y AMPLIADO: "OPERACIÓN RELOJ ATÓMICO ÓPTICO"__ ⚡

### __DIAGNÓSTICO PROFUNDO ACTUALIZADO__

__Problemas Sistémicos Identificados:__

1. ✅ __Configuración pytest deficiente__: Falta `asyncio_mode = "auto"` y warnings ocultos
2. ✅ __VS Code sub-optimizado__: Sin configuraciones específicas para debugging de tests asíncronos
3. 🔥 __CRÍTICO__: Suite de tests desintegrada (97 fallos, 139 errores)
4. 🔥 __CRÍTICO__: Gestión de ciclo de vida asyncio defectuosa
5. 🔥 __CRÍTICO__: Fixtures desincronizadas con constructores actuales
6. ⚠️ __Deuda técnica__: Migración Pydantic V1→V2 incompleta

### __PLAN EXPANDIDO EN 5 FASES COORDINADAS__

---

### __FASE 1: MOTOR DE ALTA PRECISIÓN (pyproject.toml + pytest)__

__Objetivo__: Establecer la base sólida para testing asíncrono

__Configuración Optimizada:__

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "*Tests"
python_functions = "test_*"
dotenv_files = ".env.test"
# ✨ NUEVA: Habilita modo asíncrono automático
asyncio_mode = "auto"
# ✨ NUEVA: Configuración avanzada para debugging
log_cli = true
log_cli_level = "INFO"
log_cli_format = "%(asctime)s [%(levelname)8s] %(message)s"
log_cli_date_format = "%Y-%m-%d %H:%M:%S"
# ✨ NUEVA: Configuración para tests paralelos futuros
addopts = "--tb=short --strict-markers --disable-warnings"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "asyncio: marks tests as asyncio tests"
]
```

---

### __FASE 2: SUPERPODERES DE VS CODE AVANZADOS__

#### __2A: Configuración de Debugging (.vscode/launch.json)__

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "🐞 Debug Pytest: ALL Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "justMyCode": false,
            "args": ["-v", "--tb=short", "--log-cli-level=DEBUG"],
            "console": "integratedTerminal",
            "env": {"PYTHONPATH": "${workspaceFolder}/src"},
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "🎯 Debug Pytest: Current File",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "justMyCode": false,
            "args": ["${file}", "-v", "-s", "--log-cli-level=INFO"],
            "console": "integratedTerminal",
            "env": {"PYTHONPATH": "${workspaceFolder}/src"},
            "cwd": "${workspaceFolder}"
        },
        {
            "name": "💥 Debug Failed Tests Only",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "justMyCode": false,
            "args": ["--lf", "-v", "--tb=long"],
            "console": "integratedTerminal",
            "env": {"PYTHONPATH": "${workspaceFolder}/src"}
        },
        {
            "name": "🚀 Debug Integration Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "justMyCode": false,
            "args": ["tests/integration/", "-v", "-m", "integration"],
            "console": "integratedTerminal",
            "env": {"PYTHONPATH": "${workspaceFolder}/src"}
        },
        {
            "name": "⚡ Debug Unit Tests Only",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "justMyCode": false,
            "args": ["tests/unit/", "-v", "-m", "unit"],
            "console": "integratedTerminal",
            "env": {"PYTHONPATH": "${workspaceFolder}/src"}
        }
    ]
}
```

#### __2B: Tareas Automatizadas (.vscode/tasks.json)__

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "🧪 Run All Tests",
            "type": "shell",
            "command": "poetry",
            "args": ["run", "pytest", "-v"],
            "group": "test",
            "presentation": {"echo": true, "reveal": "always", "focus": false, "panel": "shared"}
        },
        {
            "label": "🔥 Run Failed Tests",
            "type": "shell",
            "command": "poetry",
            "args": ["run", "pytest", "--lf", "-v"],
            "group": "test"
        },
        {
            "label": "📊 Coverage Report",
            "type": "shell", 
            "command": "poetry",
            "args": ["run", "pytest", "--cov=src", "--cov-report=html"],
            "group": "test"
        }
    ]
}
```

#### __2C: Configuración de Workspace (.vscode/settings.json)__

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["-v", "--tb=short"],
    "python.testing.unittestEnabled": false,
    "python.testing.autoTestDiscoverOnSaveEnabled": true,
    "python.defaultInterpreterPath": "./.venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "files.associations": {
        "*.md": "markdown"
    },
    "python.analysis.extraPaths": ["./src"],
    "pytest.enabled": true
}
```

---

### __FASE 3: REGLAS AVANZADAS .clinerules (5 NUEVOS ARCHIVOS)__

#### __3A: pytest-debugging-mastery.md__

```markdown
---
description: "Workflow maestro para debugging de tests asíncronos"
author: reloj-atomico-optico
version: 2.0
tags: ["pytest", "asyncio", "debugging", "workflow"]
---

# Debugging Mastery para Tests Asíncronos

## Workflow de Debugging Escalonado

### Nivel 1: Debug Rápido (Tests Individuales)
1. **Abrir archivo de test específico**
2. **Colocar breakpoint** en la línea sospechosa
3. **F5 → "🎯 Debug Pytest: Current File"**
4. **Inspeccionar variables** en el panel de debug

### Nivel 2: Debug Profundo (Suite Completa)
1. **F5 → "🐞 Debug Pytest: ALL Tests"**
2. **Usar "--pdb" para modo interactivo**
3. **Analizar logs con timestamps precisos**

### Nivel 3: Debug Quirúrgico (Solo Fallos)
1. **F5 → "💥 Debug Failed Tests Only"**
2. **Trace completo con "--tb=long"**
3. **Análisis de cause root con fixtures**

## Comandos de Emergencia
- `poetry run pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb`
- `poetry run pytest -x --tb=short` (stop at first failure)
- `poetry run pytest --lf --ff` (failed first, fast feedback)
```

#### __3B: async-testing-best-practices.md__

````markdown
---
description: "Mejores prácticas para tests asíncronos robustos"
author: reloj-atomico-optico
version: 2.0
tags: ["asyncio", "testing", "fixtures", "best-practices"]
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
````

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

````javascript

#### **3C: fixtures-consistency-enforcer.md**
```markdown
---
description: "Enforcer de consistencia para fixtures"
author: reloj-atomico-optico
version: 2.0
tags: ["fixtures", "consistency", "validation"]
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
````

## Reglas de Naming

- `{service_name}_fixture` para servicios
- `{model_name}_data` para datos de test
- `mock_{external_service}` para mocks externos

````javascript

#### **3D: test-data-validation.md**
```markdown
---
description: "Validación automática de datos de test"
author: reloj-atomico-optico
version: 2.0
tags: ["pydantic", "validation", "test-data"]
---

# Validación de Datos de Test

## Patrones para Datos de Test Válidos

### 1. Factory Pattern para Modelos Pydantic
```python
def create_valid_trade_data(**overrides):
    """Crea datos válidos para Trade con overrides opcionales."""
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
````

### 2. Fixtures para Modelos Complejos

```python
@pytest.fixture
def valid_market_data():
    """Datos válidos para MarketData."""
    return MarketData(
        symbol="BTCUSDT",
        price=Decimal("50000.0"),
        volume=Decimal("100.0"),
        timestamp=datetime.utcnow(),
        source="BINANCE"
    )
```

### 3. Validación Pre-Test

- __SIEMPRE__ validar datos antes de usar en tests
- __NUNCA__ asumir que datos hardcoded son válidos
- __USAR__ model.model_validate() para verificación

````javascript

#### **3E: debugging-emergency-protocols.md**
```markdown
---
description: "Protocolos de emergencia para debugging crítico"
author: reloj-atomico-optico
version: 2.0
tags: ["emergency", "debugging", "crisis", "recovery"]
---

# Protocolos de Emergencia para Debugging

## DEFCON 1: Suite de Tests Completamente Rota
1. **STOP** - No hacer más cambios
2. **ASSESS** - Ejecutar `poetry run pytest --collect-only -q`
3. **ISOLATE** - Identificar el primer error de importación
4. **FIX** - Corregir un error a la vez
5. **VALIDATE** - Re-ejecutar collect-only después de cada fix

## DEFCON 2: Múltiples Errores AsyncIO
1. **RESTART** - Cerrar VS Code y terminal
2. **CLEAN** - `poetry env remove --all && poetry install`
3. **VERIFY** - Ejecutar un test simple primero
4. **ESCALATE** - Si persiste, refactorizar conftest.py

## DEFCON 3: Fixtures Rotas Masivamente
1. **BACKUP** - Commit actual state
2. **REVERT** - A último commit funcional conocido
3. **INCREMENTAL** - Aplicar cambios uno por uno
4. **VALIDATE** - Test después de cada cambio

## Kit de Herramientas de Emergencia
```bash
# Comando de diagnóstico completo
poetry run pytest --collect-only -q 2>&1 | grep -E "(ERROR|FAILED|ImportError|ModuleNotFoundError)"

# Reset completo del entorno
poetry env remove --all && poetry install && poetry run pytest --collect-only

# Test mínimo de conectividad
poetry run python -c "import sys; sys.path.insert(0, 'src'); from ultibot_backend.core.domain_models import *; print('✅ Imports OK')"
````

```javascript

---

### **FASE 4: CORRECCIÓN SISTÉMICA DE TESTS**
**Basado en análisis de AUDIT_REPORT.md y AUDIT_MORTEN.md**

#### **4A: Refactorización de conftest.py (Crítico)**
- Implementar gestión robusta de event loop con `scope="session"`
- Crear fixtures de DB con transacciones apropiadas
- Establecer teardown limpio de recursos

#### **4B: Corrección de Fixtures Desincronizadas**
- Audit de todos los constructores vs fixtures
- Corrección de `TypeError` en inicialización
- Validación de argumentos requeridos

#### **4C: Migración Pydantic V2 Completa**
- Corrección de `ValidationError` en datos de test
- Actualización de `@validator` → `@field_validator`
- Migración de `json_encoders` → `model_dump_json`

#### **4D: Corrección de Tests de API**
- Fix de `TestClient` async context managers
- Corrección de `AttributeError` en endpoints
- Validación de responses

---

### **FASE 5: WORKFLOW DE DEBUGGING MAESTRO**

#### **5A: Flujo de Trabajo Post-Implementación**
1. **🎯 Debug Individual**: `F5` → "Debug Pytest: Current File"
2. **🐞 Debug Masivo**: `F5` → "Debug Pytest: ALL Tests" 
3. **💥 Debug Fallos**: `F5` → "Debug Failed Tests Only"
4. **🚀 Debug por Categoría**: Integration/Unit específicos

#### **5B: Comandos de Emergencia**
- `Ctrl+Shift+P` → "Tasks: Run Task" → "🧪 Run All Tests"
- `Ctrl+Shift+P` → "Tasks: Run Task" → "🔥 Run Failed Tests"  
- `Ctrl+Shift+P` → "Tasks: Run Task" → "📊 Coverage Report"

---

## **BENEFICIOS ESTRATÉGICOS DEL PLAN MEJORADO**

### **🎯 Precisión Quirúrgica**
- Debugging granular por tipo de test
- Identificación inmediata de causa raíz
- Flujo de trabajo escalonado por gravedad

### **⚡ Velocidad de Desarrollo**
- Feedback inmediato con logs estructurados
- Automatización de tareas repetitivas
- Recovery protocols para crisis

### **🛡️ Robustez Sistémica**
- Fixtures consistentes y validadas
- Gestión correcta de recursos asíncronos
- Protocols de emergencia documentados

### **📊 Observabilidad Total**
- Logs con timestamps precisos
- Coverage reports automatizados
- Métricas de calidad en tiempo real

¿Qué opinas de este plan expandido? ¿Hay alguna área específica que quieras que profundice más o algún aspecto adicional que consideres crítico?
```
