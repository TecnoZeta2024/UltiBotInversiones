# SRST-3133: Failed en unknown

## Error Específico
**Tipo:** `Failed`
**Archivo:** `tests/unit/test_app_config.py:0`
**Mensaje:** `Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>`
**Categoría:** `7_BUSINESS_LOGIC_ERRORS`
**Prioridad:** `MEDIUM`

## Contexto Mínimo
- **Test Scope:** `tests/unit/test_app_config.py::test_load_credential_encryption_key_missing_raises_validation_error`
- **Archivo a tocar:** `tests/unit/test_app_config.py`

## Plan de Fix Sugerido
1. [ ] **Analizar:** Revisar el código en `tests/unit/test_app_config.py` en la línea 0.
2. [ ] **Contextualizar:** Entender por qué el test `tests/unit/test_app_config.py::test_load_credential_encryption_key_missing_raises_validation_error` causa este error.
3. [ ] **Refactorizar:** Aplicar la corrección necesaria.
4. [ ] **Validar:** Ejecutar `poetry run pytest tests/unit/test_app_config.py::test_load_credential_encryption_key_missing_raises_validation_error` para confirmar que el error ha desaparecido.

## Validación Inmediata
```bash
# Validar que el error específico desapareció
poetry run pytest -k "tests/unit/test_app_config.py::test_load_credential_encryption_key_missing_raises_validation_error" -v
```

## Criterio de Éxito
- [ ] El error específico ya no aparece en la salida de pytest.
- [ ] La funcionalidad del código modificado sigue siendo la misma.
- [ ] No se han introducido nuevos errores.

**Estado:** `[ ] TODO`
**Tiempo estimado:** `20 minutos`
