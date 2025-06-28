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

### KB-0006: Mocking de Módulos (ej. `axios`) en Vitest para Tests de React
- **Problema:** Los tests de componentes de React que usan `axios` (a través de un `apiClient` wrapper) fallan con errores de TypeScript (`Property 'mockResolvedValue' does not exist...`) o errores de ejecución (`Timeout - Async callback was not invoked`).
- **Causa Raíz:** El sistema de mocking de `vitest` puede tener dificultades para mockear correctamente una instancia de `axios` debido a su complejidad interna. Intentos de usar `vi.mocked()` o `vi.spyOn()` directamente sobre la instancia pueden no funcionar como se espera.
- **Solución Canónica:** Utilizar un enfoque explícito de mocking a nivel de módulo y casteo de tipos.
    1.  **Mockear el Módulo:** En la parte superior del archivo de prueba, mockear el módulo que exporta el cliente API: `vi.mock('@/lib/apiClient');`
    2.  **Importar Tipos de Mock:** Importar `Mock` de `vitest`: `import { vi, Mock } from 'vitest';`
    3.  **Castear y Usar:** En cada test, castear la función mockeada (`apiClient.get`) al tipo `Mock` antes de encadenar métodos como `.mockResolvedValue()` o `.mockRejectedValue()`.
- **Ejemplo:**
  ```typescript
  // En el archivo de test
  import { vi, Mock } from 'vitest';
  import apiClient from '@/lib/apiClient';

  vi.mock('@/lib/apiClient');

  it('should fetch data successfully', async () => {
    const mockData = { message: 'Success' };
    (apiClient.get as Mock).mockResolvedValue({ data: mockData });
    
    render(<MyComponent />);
    
    expect(await screen.findByText('Success')).toBeInTheDocument();
  });
  ```
- **Nota sobre `verbatimModuleSyntax`**: Si esta opción de `tsconfig.json` está habilitada, la importación de tipos debe ser explícita: `import type { Mock } from 'vitest';`. Si no, `import { Mock } from 'vitest';` es suficiente.

### KB-0007: Desafíos de Pruebas de Componentes de React con `jsdom` y `react-testing-library`
- **Problema:** Los tests de componentes de React que involucran interacciones complejas (ej. clics en elementos de árbol que desencadenan llamadas a la API y actualizaciones de `textarea`) fallan con errores como `Unable to find an element with the display value` o `AssertionError` en llamadas a la API que no se registran.
- **Causa Raíz:** `jsdom` (el entorno de DOM simulado) puede tener limitaciones en la forma en que maneja las actualizaciones asíncronas del DOM, la propagación de eventos en componentes complejos (especialmente si tienen estado interno o usan librerías de UI como Radix UI), y la interacción con elementos como `textarea` que cambian de `readOnly`. Los mocks de componentes de UI pueden no replicar completamente el comportamiento del DOM real.
- **Solución/Mitigación:**
    1.  **Simplificar Mocks de UI:** Mockear componentes de UI complejos (ej. `magicui/file-tree`) con implementaciones simples que solo rendericen sus hijos y pasen las props relevantes. Esto reduce la complejidad del DOM de prueba.
    2.  **Aserciones Robustas:** Utilizar `await waitFor(() => expect(element).toHaveValue(expectedValue));` para esperar explícitamente las actualizaciones asíncronas del DOM.
    3.  **Verificación de Llamadas a la API:** Priorizar la verificación de que las llamadas a la API mockeadas se realizaron con los argumentos correctos, ya que esto valida la lógica de negocio independientemente de los problemas de renderizado del DOM.
    4.  **Considerar Entornos de Navegador Real:** Para interacciones de UI muy complejas o problemas persistentes con `jsdom`, considerar el uso de herramientas de prueba de navegador real como Playwright o Cypress para tests de integración de UI.
    5.  **Depuración con `screen.debug()`:** Aunque no siempre funciona en todos los entornos, `screen.debug()` puede ser útil para inspeccionar el DOM en un punto específico del test.
- **Lección Aprendida:** Los tests unitarios y de integración de componentes deben centrarse en la lógica de negocio y las interacciones con las APIs, y no depender excesivamente de la fidelidad del renderizado del DOM en entornos simulados. Si un test de UI es demasiado frágil, puede ser un indicio de que la lógica de UI es demasiado compleja o que el entorno de prueba no es el adecuado para ese nivel de detalle.

### KB-0008: Ejecución de Uvicorn en Proyectos con `src-layout` y Patrón de Fábrica
- **Problema:** Al ejecutar `uvicorn src.main:app`, la aplicación falla con `ModuleNotFoundError: No module named 'api'` (o similar), incluso si las importaciones dentro de `src/` son absolutas y correctas.
- **Causa Raíz:** El comando estándar de `uvicorn` no añade automáticamente el directorio `src` al `PYTHONPATH` de Python, por lo que el intérprete no puede localizar los módulos de nivel superior como `api`, `core`, etc., que residen dentro de `src`.
- **Solución Canónica:** Utilizar un comando de `uvicorn` que respete tanto el `src-layout` como el patrón de fábrica (`create_app`):
    1.  **Asegurar Importaciones Absolutas:** Todas las importaciones dentro del directorio `src` deben ser absolutas desde la raíz de `src` (ej. `from api.v1.endpoints import ...`).
    2.  **Asegurar Paquetes:** Todos los subdirectorios que contienen código deben tener un archivo `__init__.py` para ser reconocidos como paquetes.
    3.  **Comando de Ejecución Correcto:** Ejecutar `uvicorn` desde el directorio raíz del proyecto (el que contiene `src`) con el siguiente formato:
        ```bash
        # Para aplicaciones con patrón de fábrica
        poetry run uvicorn main:create_app --app-dir src --factory --host 0.0.0.0 --port 8000 --reload
        ```
- **Desglose del Comando:**
    - `main:create_app`: Apunta al módulo `main.py` y a la función `create_app` dentro de él.
    - `--app-dir src`: **Instrucción CRÍTICA**. Le dice a `uvicorn` que añada el directorio `src` al `PYTHONPATH` antes de intentar importar la aplicación.
    - `--factory`: Le indica a `uvicorn` que `create_app` es una función que debe ser llamada para obtener la instancia de la aplicación, en lugar de buscar una variable global `app`.

### KB-0009: Resolución de Errores de Inicio de Uvicorn (Pydantic y Fernet)
- **Problema:** El backend de Uvicorn falla al iniciar con `pydantic_core._pydantic_core.ValidationError` (campos requeridos faltantes) o `ValueError: Fernet key must be 32 url-safe base64-encoded bytes.`.
- **Causa Raíz:**
    1.  **`ValidationError`**: Faltan variables de entorno críticas (ej. `SUPABASE_URL`, `DATABASE_URL`, `CREDENTIAL_ENCRYPTION_KEY`) en el archivo `.env` que `AppSettings` espera cargar.
    2.  **`Fernet key error`**: La clave proporcionada para `CREDENTIAL_ENCRYPTION_KEY` no cumple con el formato requerido por la librería `cryptography` (32 bytes codificados en base64 seguros para URL).
- **Solución:**
    1.  **Para `ValidationError`**: Asegurarse de que todas las variables de entorno requeridas por `AppSettings` (definidas en `src/app_config.py`) estén presentes en el archivo `.env` del directorio raíz. Utilizar valores de marcador de posición si no son críticos para el desarrollo local.
    2.  **Para `Fernet key error`**: Generar una clave Fernet válida utilizando `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` y actualizar el `.env` con esta nueva clave.

### KB-0010: Encadenamiento de Comandos en PowerShell
- **Problema:** Los intentos de encadenar comandos en PowerShell usando `&&` o `&` fallan con errores de sintaxis.
- **Causa Raíz:** Los operadores `&&` y `&` tienen un comportamiento diferente o están restringidos en PowerShell para el encadenamiento directo de comandos como en `bash` o `cmd.exe`.
- **Solución:** Utilizar el punto y coma `;` para encadenar comandos en PowerShell, o ejecutar los comandos por separado en llamadas consecutivas a `execute_command`.
- **Ejemplo:** `cd src/my_project; npm install`

### KB-0011: Depuración de Errores de Conexión Frontend/Backend
- **Problema:** El frontend muestra un "Error de Conexión" a pesar de que el backend está en ejecución, CORS está configurado para permitir todos los orígenes, y la `VITE_API_BASE_URL` del frontend es correcta.
- **Causa Raíz Potencial:**
    1.  **Caché del Navegador:** El navegador está utilizando una versión en caché del frontend o de las configuraciones de red que impide la conexión.
    2.  **Resolución de Host/Red:** Problemas con la resolución de `localhost` o configuraciones de firewall que bloquean la comunicación entre el puerto del frontend (ej. 5173) y el puerto del backend (ej. 8000).
    3.  **Estado del Servidor Backend:** Aunque `uvicorn --reload` debería reiniciar la aplicación, a veces el estado interno o los recursos no se liberan completamente, o la base de datos local (`ultibot_local.db`) puede estar corrupta de un inicio anterior.
- **Solución/Pasos de Depuración:**
    1.  **Borrar Caché del Navegador:** Instruir al usuario a borrar la caché del navegador o a probar en modo incógnito/navegador diferente.
    2.  **Reiniciar Forzadamente el Backend:** Si el problema persiste, sugerir un reinicio manual del proceso del backend (ej. `taskkill /F /IM python.exe` en Windows o `killall python` en Linux/macOS) y la eliminación de artefactos persistentes como `ultibot_local.db` antes de reiniciar.
    3.  **Verificar Conectividad de Red:** Sugerir al usuario que revise las configuraciones de su firewall o antivirus que puedan estar bloqueando las conexiones locales.
