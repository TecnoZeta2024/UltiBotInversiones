---
description: "Protocolos de emergencia para debugging crítico"
author: reloj-atomico-optico
version: 2.0
tags: ["emergency", "debugging", "crisis", "recovery"]
globs: ["*"]
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
```

## Workflow de Crisis Management

### Escalación Nivel 1: Error Individual
```bash
# Diagnóstico inmediato
F5 → "🎯 Debug Pytest: Current File"

# Si falla, escalate a Nivel 2
```

### Escalación Nivel 2: Múltiples Errores
```bash
# Análisis de patrón
poetry run pytest --collect-only -q | head -20

# Identificar causa común
grep -r "ImportError\|ModuleNotFoundError" tests/

# Si falla, escalate a Nivel 3
```

### Escalación Nivel 3: Crisis Sistémica
```bash
# Full reset + reinstall
poetry env remove --all
poetry install
poetry run pytest --collect-only -q

# Si persiste, escalate a Nivel 4
```

### Escalación Nivel 4: Arquitectura Rota
```python
# Crear test mínimo para aíslar problema
# En test_minimal.py:

import sys
sys.path.insert(0, 'src')

def test_imports():
    """Test mínimo para verificar imports básicos."""
    try:
        from ultibot_backend.core.domain_models import *
        print("✅ Core models OK")
    except Exception as e:
        print(f"❌ Core models FAIL: {e}")
        
    try:
        from ultibot_backend.services import *
        print("✅ Services OK")
    except Exception as e:
        print(f"❌ Services FAIL: {e}")

if __name__ == "__main__":
    test_imports()
```

## Crisis Response Checklist

### Pre-Crisis Prevention
- [ ] Tests ejecutándose en CI/CD
- [ ] Backup de configuración funcional
- [ ] Documentación de última configuración estable
- [ ] Branch de trabajo separado de main

### Durante Crisis
- [ ] **NO** hacer múltiples cambios a la vez
- [ ] Documentar cada paso en AUDIT_MORTEN.md
- [ ] Validar cada fix antes del siguiente
- [ ] Mantener comunicación con stakeholders

### Post-Crisis Recovery
- [ ] Ejecutar suite completa de tests
- [ ] Validar performance no degradada
- [ ] Actualizar documentación de protocolos
- [ ] Post-mortem en AUDIT_MORTEN.md

## Comandos de Emergencia por Tipo de Error

### ImportError / ModuleNotFoundError
```bash
# Verificar PYTHONPATH
echo $PYTHONPATH

# Verificar estructura de paquetes
find src/ -name "__init__.py" | head -10

# Verificar imports específicos
poetry run python -c "import sys; sys.path.insert(0, 'src'); import ultibot_backend"
```

### RuntimeError: Event loop is closed
```bash
# Verificar pytest-asyncio
poetry show pytest-asyncio

# Test específico de event loop
poetry run python -c "import asyncio; loop = asyncio.new_event_loop(); print('✅ Loop OK')"

# Reset completo de fixtures
# Verificar conftest.py tiene scope="session" para event_loop
```

### ValidationError (Pydantic)
```bash
# Verificar versión de Pydantic
poetry show pydantic

# Test de modelo específico
poetry run python -c "from ultibot_backend.core.domain_models.trading import Trade; print('✅ Trade model OK')"

# Verificar datos de test con factory
```

### psycopg / Database Errors
```bash
# Verificar libpq installation
where psql

# Test conexión básica
poetry run python scripts/verify_psycopg.py

# Verificar variables de entorno
poetry run python -c "import os; print(os.getenv('DATABASE_URL'))"
```

## Debugging Escalation Matrix

| Error Type | Level 1 | Level 2 | Level 3 | Level 4 |
|------------|---------|---------|---------|---------|
| Import | Check paths | Reinstall deps | Reset env | Restructure |
| AsyncIO | Check fixtures | Reset conftest | New event loop | Refactor async |
| Pydantic | Check data | Update models | Migrate V2 | Rewrite schemas |
| Database | Check config | Reset pools | New engine | DB migration |

## Emergency Contact & Escalation

### Technical Escalation
1. **Local troubleshooting** (30 min max)
2. **Documentation review** (15 min max)
3. **Community resources** (Stack Overflow, GitHub Issues)
4. **Expert consultation** (if available)

### Communication Protocol
- **Immediate**: Log issue in AUDIT_MORTEN.md
- **15 min**: Update stakeholders on scope
- **30 min**: Provide ETA for resolution
- **60 min**: Escalate to senior team

## Recovery Validation Checklist

Post-crisis, validate these systems:
- [ ] All tests passing (`poetry run pytest`)
- [ ] Coverage reports generating (`poetry run pytest --cov=src`)
- [ ] Import statements working
- [ ] Database connections stable
- [ ] API endpoints responding
- [ ] UI launching successfully

## Crisis Prevention Best Practices

### Daily Hygiene
- [ ] Run `poetry run pytest --collect-only -q` before starting work
- [ ] Commit working state frequently
- [ ] Test after each significant change
- [ ] Monitor logs for warnings

### Weekly Maintenance
- [ ] Full test suite execution
- [ ] Dependency updates review
- [ ] Performance baseline check
- [ ] Configuration backup

### Monthly Review
- [ ] Architecture debt assessment
- [ ] Tool upgrades evaluation
- [ ] Protocol effectiveness review
- [ ] Team knowledge transfer
