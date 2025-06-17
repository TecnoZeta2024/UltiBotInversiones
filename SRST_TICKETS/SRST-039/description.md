# SRST-039: Pytest no recolecta tests en `tests/unit/services/test_trading_mode_state.py`

## Error Específico
**Tipo:** `Pytest Collection Error`
**Archivo:** `tests/unit/services/test_trading_mode_state.py`
**Mensaje:** `collected 0 items` al intentar ejecutar tests específicos del archivo.
**Categoría:** `DEFCON 4 - Arquitectura Rota (Pytest)`
**Prioridad:** `CRITICAL`

## Contexto Mínimo
- **Test Scope:** `tests/unit/services/test_trading_mode_state.py`
- **Archivos a tocar:** Posiblemente `pytest.ini`, `conftest.py`, o el propio archivo de test si hay corrupción sutil.

## Plan de Fix Sugerido
1. [ ] **Diagnóstico Detallado:** Ejecutar `poetry run pytest --collect-only -v tests/unit/services/test_trading_mode_state.py` para obtener la salida más detallada posible.
2. [ ] **Verificar Entorno:** Asegurarse de que el entorno de Poetry esté completamente funcional y que `pytest` esté correctamente instalado.
3. [ ] **Aislar Problema:** Crear un archivo de test mínimo (`temp_test.py`) en el mismo directorio con un test muy simple para ver si `pytest` lo recolecta. Esto ayudará a determinar si el problema es con el archivo específico o con el directorio/entorno.
4. [ ] **Revisar `conftest.py`:** Aunque el mocking de PyQt5 está ahí, podría haber alguna interacción inesperada.
5. [ ] **Considerar Corrupción de Archivo:** Si todo lo demás falla, intentar una recreación manual del archivo de test, copiando y pegando el contenido en un nuevo archivo.

## Validación Inmediata
```bash
# Validar que los tests se recolectan y ejecutan
poetry run pytest tests/unit/services/test_trading_mode_state.py -v
```

## Criterio de Éxito
- [ ] `pytest` recolecta y ejecuta los tests en `tests/unit/services/test_trading_mode_state.py`.
- [ ] El `TypeError` original del ticket `SRST-038` no reaparece.
- [ ] No se han introducido nuevos errores de recolección.

**Estado:** `[ ] TODO`
**Tiempo estimado:** `30 minutos`
