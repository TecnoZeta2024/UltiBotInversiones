# SRST-3174: pydantic_core._pydantic_core.ValidationError en unknown

## Error Específico
**Tipo:** `pydantic_core._pydantic_core.ValidationError`
**Archivo:** `tests/unit/services/test_performance_service.py:0`
**Mensaje:** `pydantic_core._pydantic_core.ValidationError: 1 validation error for Tradin...`
**Categoría:** `8_VALIDATION_ERRORS`
**Prioridad:** `HIGH`

## Contexto Mínimo
- **Test Scope:** `tests/unit/services/test_performance_service.py::test_get_all_strategies_performance_win_rate_edge_cases[trades_pnl3-expected_win_rate3-Mixed with one breakeven, win rate 50% of non-breakeven]`
- **Archivo a tocar:** `tests/unit/services/test_performance_service.py`

## Plan de Fix Sugerido
1. [ ] **Analizar:** Revisar el código en `tests/unit/services/test_performance_service.py` en la línea 0.
2. [ ] **Contextualizar:** Entender por qué el test `tests/unit/services/test_performance_service.py::test_get_all_strategies_performance_win_rate_edge_cases[trades_pnl3-expected_win_rate3-Mixed with one breakeven, win rate 50% of non-breakeven]` causa este error.
3. [ ] **Refactorizar:** Aplicar la corrección necesaria.
4. [ ] **Validar:** Ejecutar `poetry run pytest tests/unit/services/test_performance_service.py::test_get_all_strategies_performance_win_rate_edge_cases[trades_pnl3-expected_win_rate3-Mixed with one breakeven, win rate 50% of non-breakeven]` para confirmar que el error ha desaparecido.

## Validación Inmediata
```bash
# Validar que el error específico desapareció
poetry run pytest -k "tests/unit/services/test_performance_service.py::test_get_all_strategies_performance_win_rate_edge_cases[trades_pnl3-expected_win_rate3-Mixed with one breakeven, win rate 50% of non-breakeven]" -v
```

## Criterio de Éxito
- [ ] El error específico ya no aparece en la salida de pytest.
- [ ] La funcionalidad del código modificado sigue siendo la misma.
- [ ] No se han introducido nuevos errores.

**Estado:** `[ ] TODO`
**Tiempo estimado:** `20 minutos`
