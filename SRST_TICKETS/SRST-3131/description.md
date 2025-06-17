# SRST-3131: ultibot_backend.core.exceptions.ReportError en unknown

## Error Específico
**Tipo:** `ultibot_backend.core.exceptions.ReportError`
**Archivo:** `tests/unit/services/test_trading_report_service.py:0`
**Mensaje:** `ultibot_backend.core.exceptions.ReportError: Error al calcular métricas de ...`
**Categoría:** `7_BUSINESS_LOGIC_ERRORS`
**Prioridad:** `MEDIUM`

## Contexto Mínimo
- **Test Scope:** `tests/unit/services/test_trading_report_service.py::TestTradingReportService::test_calculate_performance_metrics_only_winning_trades`
- **Archivo a tocar:** `tests/unit/services/test_trading_report_service.py`

## Plan de Fix Sugerido
1. [ ] **Analizar:** Revisar el código en `tests/unit/services/test_trading_report_service.py` en la línea 0.
2. [ ] **Contextualizar:** Entender por qué el test `tests/unit/services/test_trading_report_service.py::TestTradingReportService::test_calculate_performance_metrics_only_winning_trades` causa este error.
3. [ ] **Refactorizar:** Aplicar la corrección necesaria.
4. [ ] **Validar:** Ejecutar `poetry run pytest tests/unit/services/test_trading_report_service.py::TestTradingReportService::test_calculate_performance_metrics_only_winning_trades` para confirmar que el error ha desaparecido.

## Validación Inmediata
```bash
# Validar que el error específico desapareció
poetry run pytest -k "tests/unit/services/test_trading_report_service.py::TestTradingReportService::test_calculate_performance_metrics_only_winning_trades" -v
```

## Criterio de Éxito
- [ ] El error específico ya no aparece en la salida de pytest.
- [ ] La funcionalidad del código modificado sigue siendo la misma.
- [ ] No se han introducido nuevos errores.

**Estado:** `[ ] TODO`
**Tiempo estimado:** `20 minutos`
