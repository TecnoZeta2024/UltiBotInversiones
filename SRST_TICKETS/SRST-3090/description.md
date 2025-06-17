# SRST-3090: assert False en unknown

## Error Específico
**Tipo:** `assert False`
**Archivo:** `tests/integration/api/v1/endpoints/test_performance_endpoints.py:0`
**Mensaje:** `assert False`
**Categoría:** `7_BUSINESS_LOGIC_ERRORS`
**Prioridad:** `MEDIUM`

## Contexto Mínimo
- **Test Scope:** `tests/integration/api/v1/endpoints/test_performance_endpoints.py::test_get_strategies_performance_endpoint_invalid_mode_parameter`
- **Archivo a tocar:** `tests/integration/api/v1/endpoints/test_performance_endpoints.py`

## Plan de Fix Sugerido
1. [ ] **Analizar:** Revisar el código en `tests/integration/api/v1/endpoints/test_performance_endpoints.py` en la línea 0.
2. [ ] **Contextualizar:** Entender por qué el test `tests/integration/api/v1/endpoints/test_performance_endpoints.py::test_get_strategies_performance_endpoint_invalid_mode_parameter` causa este error.
3. [ ] **Refactorizar:** Aplicar la corrección necesaria.
4. [ ] **Validar:** Ejecutar `poetry run pytest tests/integration/api/v1/endpoints/test_performance_endpoints.py::test_get_strategies_performance_endpoint_invalid_mode_parameter` para confirmar que el error ha desaparecido.

## Validación Inmediata
```bash
# Validar que el error específico desapareció
poetry run pytest -k "tests/integration/api/v1/endpoints/test_performance_endpoints.py::test_get_strategies_performance_endpoint_invalid_mode_parameter" -v
```

## Criterio de Éxito
- [ ] El error específico ya no aparece en la salida de pytest.
- [ ] La funcionalidad del código modificado sigue siendo la misma.
- [ ] No se han introducido nuevos errores.

**Estado:** `[ ] TODO`
**Tiempo estimado:** `20 minutos`
