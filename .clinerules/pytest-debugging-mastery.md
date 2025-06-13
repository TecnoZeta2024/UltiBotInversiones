---
description: "Workflow maestro para debugging de tests asíncronos"
author: reloj-atomico-optico
version: 2.0
tags: ["pytest", "asyncio", "debugging", "workflow"]
globs: ["*"]
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

### Nivel 4: Debug por Categorías
1. **🚀 Debug Integration Tests** - Para problemas de integración
2. **⚡ Debug Unit Tests Only** - Para lógica de negocio aislada
3. **🔬 Debug Specific Strategy Test** - Para estrategias de trading
4. **🛠️ Debug Services Tests** - Para servicios del núcleo

## Comandos de Emergencia

### Diagnóstico Rápido
```bash
# Test collection check (verifica imports)
poetry run pytest --collect-only -q

# Solo tests que fallan (feedback rápido)
poetry run pytest --lf -v

# Tests rápidos (sin los marcados como slow)
poetry run pytest -m "not slow" -v
```

### Debugging Interactivo
```bash
# PDB completo con IPython
poetry run pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb

# Stop en primer fallo con trace corto
poetry run pytest -x --tb=short

# Failed first, fast feedback
poetry run pytest --lf --ff
```

### Análisis de Coverage
```bash
# Coverage con reporte HTML
poetry run pytest --cov=src --cov-report=html

# Coverage con reporte en terminal
poetry run pytest --cov=src --cov-report=term-missing
```

## Workflow de Tareas VS Code

### Acceso Rápido (Ctrl+Shift+P)
1. **"Tasks: Run Task"** → **"🧪 Run All Tests"**
2. **"Tasks: Run Task"** → **"🔥 Run Failed Tests"**
3. **"Tasks: Run Task"** → **"📊 Coverage Report"**
4. **"Tasks: Run Task"** → **"🔍 Test Collection Check"**

### Debugging con Emojis (F5)
- **🐞** = Todos los tests con debugging completo
- **🎯** = Solo el archivo actual
- **💥** = Solo tests que fallan
- **🚀** = Integration tests
- **⚡** = Unit tests
- **🔬** = Strategy tests
- **🛠️** = Service tests
- **🏃‍♂️** = Tests rápidos (no slow)

## Patrones de Debugging para Tests Asíncronos

### 1. Event Loop Issues
```python
# Breakpoint en fixture de event loop
@pytest.fixture(scope="session")
def event_loop():
    # BREAKPOINT AQUÍ para inspeccionar loop
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
```

### 2. Database Session Issues
```python
# Breakpoint en db_session fixture
@pytest_asyncio.fixture
async def db_session(db_engine):
    # BREAKPOINT AQUÍ para verificar conexión
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
```

### 3. Service Initialization Issues
```python
# Breakpoint en constructor de servicio
def test_service_method(service_fixture):
    # BREAKPOINT AQUÍ para inspeccionar service_fixture
    result = await service_fixture.method_under_test()
    assert result.is_valid()
```

## Indicadores de Problemas Comunes

### 🔴 RuntimeError: Event loop is closed
- **Causa**: Event loop cerrado prematuramente
- **Debug**: Breakpoint en fixture `event_loop`
- **Solución**: Scope="session" para event_loop

### 🔴 ValidationError de Pydantic
- **Causa**: Datos de test inválidos
- **Debug**: Breakpoint antes de crear modelo
- **Solución**: Usar factory patterns

### 🔴 TypeError en __init__
- **Causa**: Fixture no provee argumentos correctos
- **Debug**: Breakpoint en fixture del servicio
- **Solución**: Verificar signature del constructor

### 🔴 AttributeError en async_generator
- **Causa**: TestClient mal usado
- **Debug**: Breakpoint en test de API
- **Solución**: Usar `async with client` pattern

## Escalación de Debugging

### Si Nivel 1-3 fallan:
1. **Revisar logs** con timestamps
2. **Verificar fixtures** en conftest.py
3. **Analizar dependencies** del servicio
4. **Usar protocols de emergencia** (.clinerules/debugging-emergency-protocols.md)

### Si problemas persisten:
1. **Reset completo**: `poetry env remove --all && poetry install`
2. **Verificar imports**: `poetry run python -c "import sys; sys.path.insert(0, 'src'); from ultibot_backend.core.domain_models import *; print('✅ Imports OK')"`
3. **Crear minimal test**: Aísla el problema en test simple
