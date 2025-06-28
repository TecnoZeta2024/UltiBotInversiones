# =================================================================
# == KNOWLEDGE BASE - UltiBotInversiones
# =================================================================
# Este es un repositorio de patrones aprendidos, soluciones comunes y
# mejores prácticas específicas del proyecto. Es inmutable y de solo-añadir (append-only).
# -----------------------------------------------------------------

### KB-0001: Solución a la Amnesia de Contexto entre Sesiones
- **Problema:** Los agentes pierden el contexto entre ejecuciones de `new_task`, causando retrabajo y bucles de depuración.
- **Solución:** Implementar el **Sistema de Memoria y Seguimiento Centralizado (SMYC)** definido en `workspace.rules.md`.
- **Componentes Clave:**
    1.  `memory/PROJECT_LOG.md`: Registro inmutable de acciones.
    2.  `memory/TASKLIST.md`: Estado actual de las tareas.
    3.  `memory/KNOWLEDGE_BASE.md`: Base de conocimiento persistente.
- **Protocolo de Traspaso:** Utilizar la **Plantilla de Paquete de Traspaso de Sesión (PCC)** al invocar `new_task` para asegurar la continuidad del contexto.

### KB-0002: Resolución de Errores de Configuración en Tests (pydantic.ValidationError)
- **Problema:** Los tests fallan con `pydantic.ValidationError` porque `AppSettings` no puede encontrar variables de entorno requeridas (ej. `SUPABASE_URL`).
- **Causa Raíz:** El entorno de prueba (`TESTING=True`) no se activa globalmente antes de que las fixtures que dependen de la configuración (como `ai_orchestrator_fixture`) sean inicializadas.
- **Solución:** Establecer `os.environ["TESTING"] = "True"` al principio del archivo `tests/conftest.py`, antes de cualquier importación o definición de fixture. Esto garantiza que `get_app_settings()` siempre cargue la configuración desde `.env.test` para toda la sesión de pytest.

### KB-0003: Resolución de `AssertionError` con Mocks de `AsyncMock`
- **Problema:** Los tests fallan con `AssertionError` al comparar un atributo de un objeto mockeado (ej. `trade.side`) con un valor estático (ej. `"buy"`), porque el atributo en sí mismo es otro `AsyncMock`.
- **Causa Raíz:** El método mockeado (ej. `trading_engine_fixture.create_trade_from_decision`) no tiene configurado un `return_value`. Por defecto, devuelve un nuevo `AsyncMock`.
- **Solución:** Configurar explícitamente el `return_value` del método mockeado para que devuelva un objeto (`MagicMock`) con los atributos y valores esperados por las aserciones del test.
- **Ejemplo:**
  ```python
  # En el test
  mock_buy_trade = MagicMock(spec=Trade)
  mock_buy_trade.side = "buy"
  trading_engine_fixture.create_trade_from_decision.return_value = mock_buy_trade
  
  trade = await trading_engine_fixture.create_trade_from_decision(...)
  
  assert trade.side == "buy" # Pasa porque trade.side es "buy"

### KB-0004: Mocking de Métodos en Instancias Reales vs. Mocks Completos
- **Problema:** Un test falla con `AttributeError: 'method' object has no attribute 'return_value'` o `AttributeError: 'function' object has no attribute 'assert_called_once'`.
- **Causa Raíz:** El test intenta tratar un método de una instancia de clase real como si fuera un `MagicMock` o `AsyncMock`. Esto ocurre comúnmente después de refactorizar una fixture para que devuelva una instancia real del servicio en lugar de un mock completo (ej. `trading_engine_fixture`).
- **Solución:** En lugar de asignar `return_value` directamente, se debe usar `unittest.mock.patch.object` para mockear (o espiar) el método específico dentro del contexto del test.
- **Ejemplo:**
  ```python
  # Incorrecto (cuando trading_engine_fixture es una instancia real)
  # trading_engine_fixture.create_trade_from_decision.return_value = my_mock_trade

  # Correcto
  with patch.object(trading_engine_fixture, 'create_trade_from_decision', new_callable=AsyncMock) as mock_create_trade:
      mock_create_trade.return_value = my_mock_trade
      
      await trading_engine_fixture.create_trade_from_decision(...)
      
      mock_create_trade.assert_called_once()

### KB-0005: Resolución de Errores de Colección de Pytest (`fixture not found` y `NameError`)
- **Problema:** La suite de `pytest` falla antes de ejecutar cualquier test, durante la fase de "colección", con errores como `fixture '...' not found` o `NameError: name '...' is not defined`.
- **Causa Raíz:**
    1.  **`fixture not found`**: El nombre de una fixture solicitada en la firma de un test es incorrecto, o la fixture no está definida en un `conftest.py` accesible. A menudo, se solicita un mock de servicio específico (ej. `mock_strategy_service_integration`) cuando se debería usar un contenedor de dependencias mockeado más general (ej. `mock_dependency_container`).
    2.  **`NameError`**: Un tipo o clase (ej. `MagicMock`) se utiliza en la firma de un test sin haber sido importado previamente en el archivo.
- **Solución:**
    1.  **Para `fixture not found`**:
        -   Revisar `tests/conftest.py` para identificar la `fixture` correcta que provee las dependencias mockeadas (ej. `mock_dependency_container`).
        -   Corregir la firma del test para usar la `fixture` correcta.
        -   Acceder al mock específico a través del contenedor (ej. `mock_service = mock_dependency_container.service_name`).
    2.  **Para `NameError`**:
        -   Añadir la importación necesaria en la parte superior del archivo de prueba (ej. `from unittest.mock import MagicMock`).
- **Protocolo de Debugging:** Ver la sección "Debugging de Errores de Colección de Pytest" en `.clinerules/debugging-agent-protocol.md`.
