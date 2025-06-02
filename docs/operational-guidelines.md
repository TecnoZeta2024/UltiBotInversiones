## Coding Standards

En esta sección, estableceremos las reglas y convenciones que todo el código (generado por IA o escrito manualmente) deberá seguir. Esto es vital para mantener la legibilidad, consistencia, calidad y mantenibilidad del proyecto "UltiBotInversiones". El cumplimiento de estos estándares es obligatorio.

1.  **Primary Runtime(s):**
    
    -   Python: `3.11.9` (según nuestro stack tecnológico). Todo el código Python deberá ser compatible con esta versión específica para garantizar la consistencia y evitar problemas de compatibilidad.
2.  **Style Guide & Linter:**
    
    -   **Herramienta Principal:** `Ruff` se utilizará como linter y formateador único y principal.
        -   _Justificación:_ Su velocidad excepcional y la integración de funcionalidades de múltiples herramientas (Flake8, isort, pyupgrade, pydocstyle, e incluso formateo compatible con Black) simplifican el toolchain y aceleran el feedback.
    -   **Configuración de Ruff:**
        -   Se definirá en el archivo `pyproject.toml` bajo la sección `[tool.ruff]`.
        -   _Reglas Habilitadas:_ Se activará un conjunto robusto y explícito de reglas. Como mínimo:
            -   `E, W`: Errores y advertencias de PEP 8 (similares a Pyflakes).
            -   `F`: Errores lógicos (Pyflakes).
            -   `I`: Ordenación de imports (isort).
            -   `UP`: Actualizaciones de sintaxis (pyupgrade).
            -   `D`: Convenciones de Docstrings (pydocstyle) – ver sección "Comments & Documentation".
            -   Considerar `B` (flake8-bugbear) para detectar posibles bugs y malas prácticas de diseño.
            -   Explorar las reglas de `pylint` (`PLC, PLE`) que Ruff está incorporando progresivamente si se desea un análisis más profundo.
        -   _Formateo:_ Se utilizará el formateador integrado de Ruff.
            -   `Line Length:` Se establece en `100` caracteres. Esta decisión debe ser firme para asegurar consistencia.
        -   _Conformidad:_ El código debe adherirse estrictamente a PEP 8, con las configuraciones específicas gestionadas por Ruff.
    -   **Automatización (Mandatorio para v1.0):**
        -   Se configurarán `pre-commit hooks` utilizando la herramienta `pre-commit`.
        -   Los hooks incluirán, como mínimo, `ruff check --fix` y `ruff format`.
        -   Esto asegura que todo el código subido al repositorio cumpla con los estándares automáticamente, crucial cuando la IA genera código.
    -   **Instalación y Uso:**
        -   Para instalar los hooks de pre-commit en tu repositorio local, ejecuta:
            ```bash
            poetry run pre-commit install
            ```
        -   Esto configurará Git para ejecutar automáticamente los hooks definidos en `.pre-commit-config.yaml` antes de cada commit.
        -   Para ejecutar los hooks manualmente en todos los archivos (útil para verificar el código existente), ejecuta:
            ```bash
            poetry run pre-commit run --all-files
            ```
3.  **Naming Conventions:**
    
    -   Variables y Funciones: `snake_case` (ej. `mi_variable`, `calcular_valor_neto()`).
    -   Métodos de Instancia y Clase: `snake_case` (ej. `obj.hacer_algo()`, `Clase.metodo_de_clase()`).
    -   Clases, Tipos (Pydantic models), y Excepciones: `PascalCase` (ej. `MiClasePrincipal`, `DatosDeConfiguracionUsuario`, `ErrorDeValidacionCustom`).
    -   Constantes: `UPPER_SNAKE_CASE` (ej. `TASA_DE_INTERES_MAXIMA`, `CONFIG_PATH`).
    -   Módulos (archivos `.py`): `snake_case.py` (ej. `gestor_ordenes.py`, `estrategias_scalping.py`).
    -   Paquetes (directorios que contienen `__init__.py`): `snake_case` (ej. `utilidades_core`, `adaptadores_api`).
    -   Atributos/Métodos Internos/Privados:
        -   Un guion bajo (`_nombre_interno`): para uso interno dentro de un módulo o clase. No se considera una API pública.
        -   Doble guion bajo (`__nombre_mangled`): solo si se requiere name mangling explícitamente (raramente necesario). Evitar si no se comprende completamente su propósito.
    -   Funciones Asíncronas: Seguirán `snake_case`. No se requiere un sufijo especial como `_async` a menos que exista una contraparte síncrona con el mismo nombre y sea necesario diferenciarlas claramente.
4.  **File Structure:**
    
    -   Se adherirá estrictamente a la estructura definida en la sección "Project Structure" del `Architecture.md`. La consistencia aquí es clave para la navegabilidad y la comprensión del proyecto.
5.  **Unit Test File Organization:**
    
    -   **Ubicación:** Los archivos de pruebas unitarias se ubicarán en el directorio `tests/unit/`, replicando la estructura del directorio `src/` correspondiente al módulo bajo prueba (ej. `tests/unit/services/` para `src/ultibot_backend/services/`).
    -   **Nomenclatura de Archivos:** `test_<nombre_del_modulo_bajo_prueba>.py` (ej. `tests/unit/services/test_trading_engine_service.py`).
    -   **Nomenclatura de Funciones/Métodos de Prueba:** `test_<condicion_o_comportamiento_esperado>` (ej. `test_calcula_pnl_correctamente_para_trade_positivo`, `test_levanta_excepcion_si_falta_parametro_obligatorio`). Usar nombres descriptivos.
6.  **Asynchronous Operations (`async`/`await`):**
    
    -   Se utilizará `async` y `await` para todas las operaciones de I/O que puedan ser no bloqueantes:
        -   Llamadas a APIs externas (`httpx`).
        -   Interacciones con la base de datos si se utiliza un driver asíncrono con `supabase-py` o directamente con PostgreSQL.
        -   Comunicaciones WebSocket.
        -   Operaciones de lectura/escritura de archivos si son intensivas y pueden beneficiarse del asincronismo (raro en este contexto, pero posible).
    -   Todas las funciones de endpoint de FastAPI (definidas con `@router.get`, `@router.post`, etc.) serán `async def` por defecto, a menos que una operación sea puramente síncrona, computacionalmente intensiva y muy corta (en cuyo caso FastAPI puede manejarla eficientemente en un threadpool separado, pero `async def` es la norma).
    -   Evitar mezclar código bloqueante síncrono dentro de funciones `async` sin delegarlo explícitamente a un ejecutor de hilos (ej. `asyncio.to_thread` en Python 3.9+).
7.  **Type Safety:**
    
    -   **Type Hints Obligatorios:** Se utilizarán type hints de Python de forma exhaustiva y precisa en:
        -   Firmas de funciones y métodos (argumentos y tipo de retorno).
        -   Declaraciones de variables donde el tipo no sea obvio o para mayor claridad.
    -   **Pydantic Models:** Se usarán de forma preferente para:
        -   Validación de datos en endpoints de FastAPI (request bodies, query/path parameters, response models).
        -   Definición de modelos de datos claros y estructurados dentro de la lógica de negocio.
        -   Configuraciones de la aplicación.
    -   **Análisis Estático de Tipos (Mandatorio para v1.0):**
        -   _Ruff Type Checking:_ Se configurarán y habilitarán las reglas de chequeo de tipos de `Ruff` (`PYI` para type checking y otras que puedan aplicar).
        -   _MyPy (Alternativa/Complemento):_ Si las capacidades de Ruff no son suficientes o se prefiere un chequeo más exhaustivo y configurable, se integrará `MyPy`. La configuración (ej. `strict = true` o un subconjunto de opciones estrictas) se definirá en `pyproject.toml`. Recomendación: Empezar con las capacidades de Ruff y evaluar MyPy si se encuentran limitaciones. Para un proyecto de esta naturaleza, un chequeo estático fuerte es muy valioso.
    -   **Type Definitions:**
        -   Los tipos complejos o compartidos se definirán en archivos `types.py` dentro de los módulos correspondientes o en un directorio `shared/domain_types.py` o similar si son transversales.
        -   Se evitará el uso de `typing.Any` en la medida de lo posible. Su uso debe ser una excepción justificada y documentada con un comentario `# type: ignore[misc]` si es necesario para MyPy/Ruff, explicando por qué `Any` es la única opción viable. Preferir `TypeVar`, `ParamSpec`, `Protocol`, o uniones más específicas.
        -   Utilizar los tipos genéricos de `collections.abc` (ej. `Mapping`, `Sequence`) en lugar de `dict`, `list` en type hints para mayor flexibilidad, a menos que se requiera la mutabilidad específica de `list` o `dict`.
8.  **Comments & Documentation:**
    
    -   **Comentarios en Código:**
        -   Deben explicar el "porqué" de una decisión de diseño o una lógica compleja, no el "qué" hace el código (el código bien escrito debe ser autoexplicativo en el "qué").
        -   Evitar comentarios obvios o que parafrasean el código.
        -   Usar `TODO:`, `FIXME:`, `XXX:` para marcar tareas pendientes o problemas, idealmente con una referencia a un issue tracker si existe.
    -   **Docstrings (Mandatorio y Estilo Único):**
        -   Todas las funciones públicas, clases, métodos y módulos (archivos `.py`) deberán tener docstrings.
        -   _Estilo Adoptado:_ Se utilizará **Google Style** para los docstrings. Esto incluye secciones como `Args:`, `Returns:`, `Raises:`.
        -   `Ruff` (con reglas de `pydocstyle`) se configurará para verificar la conformidad con este estilo.
        -   El contenido debe ser conciso pero completo, explicando el propósito, los parámetros, el valor de retorno, y las excepciones que puede lanzar.
    -   **READMEs:**
        -   El `README.md` principal del proyecto es fundamental y debe estar bien mantenido.
        -   Módulos o componentes complejos (ej. `ultibot_backend`, `ultibot_ui`) deben tener su propio `README.md` explicando su propósito, cómo configurarlo (si aplica), y cómo usarlo o probarlo. Para la v1.0, esto puede ser conciso pero útil.
    -   **Documentación de API:** Se aprovechará la generación automática de documentación OpenAPI (Swagger UI / ReDoc) proporcionada por FastAPI. Los docstrings de los endpoints y los modelos Pydantic contribuirán a esta documentación.
9.  **Dependency Management:**
    
    -   **Herramienta:** Poetry `1.8.3` (o la versión definida en el stack).
    -   **Archivo de Definición:** Todas las dependencias (producción y desarrollo) se gestionarán exclusivamente a través del archivo `pyproject.toml`.
    -   **Versionado:**
        -   Se preferirán rangos de versiones específicos y restrictivos (ej. `~1.2.3` que permite `1.2.x` pero no `1.3.0`, o `^1.2.3` que permite `1.x.y` donde `x >= 2` y `y >= 3` pero no `2.0.0`).
        -   Para dependencias críticas o aquellas con APIs menos estables, se considerará el "pineo" a versiones exactas (`package = "1.2.3"`) en `pyproject.toml` si es necesario, aunque `poetry.lock` siempre contendrá versiones exactas.
        -   El archivo `poetry.lock` debe ser versionado en Git para asegurar compilaciones reproducibles.
    -   **Política de Adición de Dependencias:**
        -   Antes de añadir una nueva dependencia, se debe evaluar críticamente si su funcionalidad ya puede ser cubierta por dependencias existentes o por la librería estándar de Python.
        -   Se priorizarán dependencias bien mantenidas, con buena documentación y una comunidad activa.
        -   Se analizará el impacto de la nueva dependencia en el tamaño total del proyecto y el grafo de sub-dependencias.
10.  **Detailed Language & Framework Conventions:**
    
    -   **Python General:**
        -   _Inmutabilidad:_ Preferir estructuras de datos inmutables (ej. tuplas en lugar de listas para colecciones que no deben cambiar después de su creación) donde sea práctico y mejore la previsibilidad.
        -   _Expresividad:_ Utilizar comprensiones de listas/diccionarios/conjuntos y expresiones generadoras por su concisión y eficiencia cuando sean legibles.
        -   _Manejo de Recursos:_ Utilizar `with` statements (context managers) para la gestión de recursos que necesitan ser liberados explícitamente (ej. archivos, locks, conexiones de red si el cliente no lo gestiona automáticamente).
        -   _Manejo de Errores:_
            -   Usar excepciones personalizadas (heredando de `Exception` o excepciones estándar más específicas) para errores de dominio propios de la aplicación.
            -   Ser específico al capturar excepciones (`except MiErrorCustom:` en lugar de `except Exception:`).
            -   Utilizar bloques `try...except...else...finally` apropiadamente. El bloque `else` es útil para código que debe ejecutarse si no hay excepciones. `finally` para limpieza.
        -   _Imports Circulares:_ Deben evitarse activamente mediante un diseño modular adecuado y, si es necesario, refactorización o el uso de imports dentro de funciones/métodos (aunque esto último es menos ideal).
        -   _Principio de Responsabilidad Única (SRP):_ Funciones, métodos y clases deben ser cortos, cohesivos y tener una única responsabilidad bien definida.
        -   _Logging:_
            -   Utilizar el módulo `logging` estándar de Python.
            -   Configurar el logging de forma centralizada (ej. en `main.py` o un módulo de configuración).
            -   Utilizar niveles de log apropiados (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            -   En los logs, incluir información contextual útil (ej. timestamps, nombre del módulo, ID de correlación si aplica). Considerar logging estructurado (ej. JSON) para facilitar el análisis por máquinas en producción.
        -   _Configuración:_
            -   Utilizar modelos Pydantic (específicamente `BaseSettings`) para gestionar la configuración de la aplicación (cargada desde variables de entorno, archivos `.env`, etc.). Esto proporciona validación y type hints para la configuración.
        -   _Zen de Python (PEP 20):_ Mantener los principios del Zen de Python en mente al escribir código ("Bello es mejor que feo", "Explícito es mejor que implícito", "Simple es mejor que complejo", etc.).
    -   **FastAPI Específico:**
        -   _Inyección de Dependencias (`Depends`):_ Utilizarla extensivamente para gestionar dependencias como servicios de negocio, conexiones a bases de datos, configuración, y la obtención del usuario actual (si se implementa autenticación). Promueve código desacoplado y fácil de probar.
        -   _Modelos Pydantic:_ Son la base para la validación automática de request/response bodies, path/query parameters y headers. Definir `response_model` explícitamente en los endpoints para asegurar la estructura de la respuesta y para la documentación automática.
        -   _Routers Modulares (`APIRouter`):_ Organizar los endpoints en routers separados por recurso o funcionalidad (ej. `trading_router.py`, `users_router.py`) e incluirlos en la aplicación principal FastAPI. Esto se alinea con tu estructura de proyecto.
        -   _Manejo de Errores HTTP:_ Utilizar `HTTPException` de FastAPI para devolver respuestas de error HTTP estándar. Considerar la creación de manejadores de excepciones personalizados (`@app.exception_handler(MiErrorCustom)`) para convertir errores de dominio en respuestas `HTTPException` consistentes.
        -   _Tareas en Segundo Plano:_ Para tareas cortas que no necesitan bloquear la respuesta, usar `BackgroundTasks`. Para tareas más largas o complejas, considerar una solución más robusta como Celery (aunque para v1.0, `BackgroundTasks` es un buen inicio según tu `Architecture.md`).
        -   _Path Operation Functions:_ Mantener las funciones de los endpoints (decoradas con `@router.get`, etc.) lo más delgadas posible, delegando la lógica de negocio a servicios o "casos de uso" separados.

## Overall Testing Strategy

Considerando nuestro enfoque en una v1.0 ágil y estable para una aplicación local, propongo la siguiente estrategia:

-   **Tools:**
    
    -   **Framework Principal de Pruebas:** `pytest` (ya definido en el stack).
    -   **Pruebas Asíncronas:** `pytest-asyncio` (ya definido en el stack).
    -   **Mocking/Stubbing:** La biblioteca `unittest.mock` (parte de la librería estándar de Python) será nuestra herramienta principal para crear mocks y stubs.
    -   **E2E Testing (si se considera para v1.0 muy limitada):** Para una aplicación de escritorio como esta, las pruebas E2E completas pueden ser complejas de automatizar. Para la v1.0, podríamos enfocarnos en pruebas de integración más robustas y pruebas manuales exhaustivas de los flujos de UI. Si se decide automatizar algo de UI, `Playwright` (mencionado en la plantilla como ejemplo) podría ser una opción, pero su implementación completa podría quedar fuera del alcance de la v1.0 para mantener la simplicidad. _Propongo priorizar pruebas manuales y de integración para la UI en v1.0._
-   **Unit Tests:**
    
    -   **Scope:** Probar unidades individuales de código (funciones, métodos, clases) de forma aislada. Se centrarán en la lógica de negocio de los servicios, funciones de utilidad, y la lógica interna de los componentes (sin UI).
    -   **Location:** `tests/unit/` replicando la estructura de `src/`, con archivos `test_<nombre_modulo>.py`, como se definió en "Coding Standards".
    -   **Mocking/Stubbing:** Todas las dependencias externas (llamadas a API con `httpx`, interacciones con base de datos, llamadas a otros servicios internos) _deben_ ser mockeadas usando `unittest.mock`.
    -   **AI Agent Responsibility:** El agente IA encargado de desarrollar una función o módulo _debe_ generar pruebas unitarias que cubran los caminos lógicos principales, casos límite y manejo de errores esperados para el código que produce.
-   **Integration Tests:**
    
    -   **Scope:** Probar la interacción entre varios componentes o módulos del backend. Por ejemplo:
        -   Interacción entre un endpoint de API (FastAPI), el servicio de negocio que invoca y su interacción con un mock de `DataPersistenceService` o mocks de clientes de API externas.
        -   Flujos que involucren al `TradingEngine` y el `AI_Orchestrator` (con el `AI_Orchestrator` mockeado o sus dependencias externas mockeadas).
    -   **Location:** `tests/integration/`.
    -   **Environment:** Las pruebas de integración pueden requerir una instancia de base de datos de prueba (Supabase ofrece entornos de desarrollo) o mocks muy bien definidos para servicios externos. Se evitará depender de servicios externos reales en pruebas automatizadas para asegurar su fiabilidad y velocidad.
    -   **AI Agent Responsibility:** El agente IA puede ser instruido para generar pruebas de integración para los flujos de API que implementa, asegurando que los diferentes servicios internos se comunican correctamente según los contratos definidos.
-   **End-to-End (E2E) Tests:**
    
    -   **Scope:** Para la v1.0 de una aplicación local, las pruebas E2E automatizadas de la UI (PyQt5) pueden ser complejas y llevar tiempo.
        -   **Propuesta v1.0:** Nos enfocaremos en **pruebas manuales exhaustivas** de los flujos de usuario clave directamente en la aplicación PyQt5.
        -   Si hay lógica crítica en el backend que representa un "flujo completo" sin UI directa (ej. un proceso de análisis de oportunidad disparado internamente), se podría cubrir con una prueba de integración de alto nivel.
    -   **AI Agent Responsibility:** N/A para pruebas E2E automatizadas en v1.0. El agente debe asegurar que los componentes individuales y sus integraciones (probadas unitaria y por integración) funcionen, lo que facilitará las pruebas manuales.
-   **Test Coverage:**
    
    -   **Target:** Si bien no estableceremos un porcentaje estricto de cobertura de código para la v1.0 para no ralentizar el desarrollo, se espera una "cobertura razonable" de la lógica crítica a través de pruebas unitarias y de integración. La calidad y el propósito de las pruebas son más importantes que el porcentaje bruto.
    -   **Measurement:** `pytest-cov` (un plugin de `pytest`) se puede utilizar localmente para generar informes de cobertura si se desea analizar.
-   **Mocking/Stubbing Strategy (General):**
    
    -   Preferir mocks claros y específicos para cada prueba. Evitar mocks globales o demasiado complejos si es posible.
    -   El objetivo es que las pruebas sean rápidas, fiables y fáciles de entender.
-   **Test Data Management:**
    
    -   Para pruebas unitarias y de integración, los datos de prueba se definirán directamente en los archivos de prueba o mediante fixtures de `pytest`.
    -   Se evitará depender de estados de base de datos preexistentes; cada prueba debe configurar y, si es necesario, limpiar sus propios datos.
-   **Ejecución de Pruebas:**
    -   Para ejecutar todas las pruebas unitarias y de integración, utiliza el comando Poetry definido en `pyproject.toml`:
        ```bash
        poetry run test
        ```
    -   Para ejecutar pruebas específicas (ej. solo las pruebas unitarias de un módulo), puedes pasar argumentos adicionales a `pytest`:
        ```bash
        poetry run test tests/unit/shared/test_data_types.py
        ```
    -   Para generar un informe de cobertura de código (requiere `pytest-cov`):
        ```bash
        poetry run test --cov=src
        ```

## Error Handling Strategy

-   **General Approach:**
    
    -   Utilizaremos excepciones de Python como el mecanismo principal para el manejo de errores en el backend.
    -   FastAPI tiene un buen manejo de excepciones incorporado que convierte excepciones HTTP estándar y personalizadas en respuestas HTTP apropiadas.
    -   Definiremos excepciones personalizadas (`CustomException`) que hereden de `Exception` para errores específicos del dominio de la aplicación, lo que permitirá un manejo más granular.
-   **Logging:**
    
    -   **Library/Method:** Utilizaremos la biblioteca `logging` estándar de Python, configurada para ofrecer la flexibilidad necesaria. Se podría considerar `Loguru` por su simplicidad de configuración si la estándar resulta verbosa para nuestros propósitos iniciales. Para la v1.0, `logging` es suficiente.
    -   **Format:** Los logs se escribirán en formato de **texto plano** para la consola durante el desarrollo local, con un formato claro que incluya: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. Para un posible futuro archivo de log, se podría considerar JSON, pero para la v1.0 local, texto es más directo.
    -   **Levels:**
        -   `DEBUG`: Información detallada, típicamente de interés solo al diagnosticar problemas.
        -   `INFO`: Confirmación de que las cosas funcionan como se esperaba.
        -   `WARNING`: Una indicación de que algo inesperado sucedió, o una advertencia de posibles problemas futuros (ej. uso de API deprecada).
        -   `ERROR`: Debido a un problema más serio, el software no ha podido realizar alguna función.
        -   `CRITICAL`: Un error serio, que indica que el programa mismo puede ser incapaz de continuar ejecutándose.
    -   **Context:** Además del timestamp, nombre del logger y nivel, se incluirá el nombre del módulo/función donde se origina el log siempre que sea posible. Para errores en el manejo de solicitudes API, se podría incluir un ID de solicitud si se implementa.
-   **Specific Handling Patterns:**
    
    -   **External API Calls (usando `httpx`):**
        -   Se capturarán las excepciones de `httpx` (ej. `httpx.RequestError`, `httpx.HTTPStatusError`).
        -   **Timeouts:** Se configurarán timeouts explícitos (conexión y lectura) en las instancias del cliente `httpx` para evitar bloqueos indefinidos.
        -   **Retries:** Para la v1.0, implementaremos reintentos simples para errores transitorios (ej. problemas de red, errores 5xx) con un número limitado de intentos (ej. 2-3 reintentos) y un backoff fijo o lineal simple. Bibliotecas como `tenacity` podrían considerarse si la lógica de reintentos se vuelve compleja, pero para iniciar, una implementación manual básica será suficiente.
        -   Los errores persistentes de APIs externas se registrarán como `ERROR` y se propagarán como una excepción personalizada apropiada (ej. `BinanceAPIError`, `MCPServiceError`).
    -   **Internal Errors / Business Logic Exceptions:**
        -   Se utilizarán excepciones personalizadas (ej. `InsufficientFundsError`, `InvalidStrategyParametersError`) para señalar problemas en la lógica de negocio.
        -   Estas excepciones serán capturadas por los manejadores de errores de FastAPI o por la lógica de la aplicación para devolver respuestas adecuadas al cliente (UI) y registrar el error con nivel `ERROR` o `WARNING` según la severidad.
    -   **Transaction Management (con Supabase/PostgreSQL):**
        -   Para operaciones que requieran múltiples escrituras en la base de datos y necesiten atomicidad (ej. registrar un trade y actualizar el portafolio), se utilizarán transacciones de base de datos.
        -   El cliente `supabase-py` o la biblioteca subyacente (`psycopg` o similar si se interactúa más directamente) deberá permitir la gestión de `BEGIN`, `COMMIT`, `ROLLBACK`.
        -   En caso de error dentro de una transacción, se realizará un `ROLLBACK` para asegurar la consistencia de los datos, y se registrará el error.

## Security Best Practices

-   **Input Sanitization/Validation:**
    
    -   Toda entrada de API recibida por el backend FastAPI **debe** ser validada usando modelos Pydantic. Esto incluye tipos de datos, formatos esperados y rangos (si aplican).
        
    -   Las entradas en la UI de PyQt5 (ej. campos de texto para claves API, parámetros de estrategias) deben tener validaciones básicas en el lado del cliente para mejorar la UX, pero la validación autoritativa y final **siempre** ocurrirá en el backend.
-   **Output Encoding:**
    
    -   Dado que la UI es una aplicación de escritorio PyQt5 y no una aplicación web tradicional, los riesgos de XSS a través de la renderización de HTML son diferentes. Sin embargo, si se muestra contenido dinámico que podría originarse de fuentes externas (ej. nombres de monedas, mensajes de error de API), PyQt5 generalmente maneja bien la renderización segura de texto.
    -   Al enviar datos a Telegram, se utilizará el `parse_mode="MarkdownV2"` o `HTML` según se defina en la API de Telegram, asegurándose de escapar correctamente cualquier carácter especial para evitar problemas de formato o inyección si el contenido proviene de entradas no confiables.
-   **Secrets Management:**
    
    -   Las claves API (Binance, Telegram, Mobula, Gemini) **nunca** deben estar hardcodeadas en el código fuente.
    -   Se almacenarán de forma segura. Como se detalló en `Architecture.md` y los esquemas de base de datos, las claves se guardarán en la tabla `api_credentials` de la base de datos Supabase/PostgreSQL, con los campos sensibles (`encrypted_api_key`, `encrypted_api_secret`, `encrypted_other_details`) **encriptados en la capa de aplicación antes de la persistencia**. La clave de encriptación para estos datos debe ser gestionada de forma segura por el usuario (ej. ingresada al iniciar la aplicación y mantenida en memoria, o derivada de una contraseña maestra).
    -   El acceso a los secretos en el código se realizará a través del `CredentialManager`, que se encargará de la desencriptación en el momento del uso.
        
    -   Las variables de entorno (gestionadas con modelos Pydantic `BaseSettings` como se mencionó en "Coding Standards") pueden usarse para configuración no sensible o para la clave de encriptación maestra si se obtiene de forma segura del entorno. No se deben usar para almacenar directamente las claves API externas.
-   **Dependency Security:**
    
    -   Se utilizará `Poetry` para la gestión de dependencias. El archivo `poetry.lock` asegura builds reproducibles.
    -   Se recomienda ejecutar `poetry show --outdated` periódicamente y antes de "releases" (aunque sea para uso personal) para revisar dependencias desactualizadas.
    -   Se puede usar `pip-audit` (integrable con Poetry) o herramientas similares para escanear vulnerabilidades conocidas en las dependencias. Para la v1.0, esto puede ser un proceso manual periódico.
-   **Authentication/Authorization Checks (para la API interna):**
    
    -   La API interna de FastAPI, aunque se ejecute localmente para la UI, podría considerar un mecanismo de autenticación muy ligero (ej. un token simple generado al inicio, o protección de que solo acepte conexiones de `localhost`) si se desea una capa extra de seguridad, aunque para la v1.0, al ser una aplicación local y personal, esto podría simplificarse.
    -   _Propuesta v1.0:_ Dado que es una aplicación de escritorio donde backend y UI corren en la misma máquina para uso personal, la API FastAPI se enlazará exclusivamente a `localhost`, lo que limita la accesibilidad externa. No implementaremos un esquema de autenticación complejo entre la UI y esta API local inicialmente.
-   **Principle of Least Privilege (Implementación):**
    
    -   Las claves API de Binance deben configurarse con los permisos mínimos necesarios para las operaciones que UltiBotInversiones realizará (ej. habilitar trading para spot, pero no necesariamente retiros si el bot no los necesita). Esto se configura en la plataforma de Binance al crear la API key.
    -   El acceso a la base de datos (Supabase) también debe seguir este principio si se definen roles o políticas específicas.
-   **API Security (General - para llamadas salientes):**
    
    -   Todas las llamadas a APIs externas (Binance, Mobula, Gemini, Telegram) **deben** realizarse sobre HTTPS. `httpx` lo hará por defecto.
-   **Error Handling & Information Disclosure:**
    
    -   Como se definió en la "Error Handling Strategy", los mensajes de error detallados (stack traces, SQL errors) no se expondrán directamente en la UI ni se enviarán a Telegram sin sanitizar. Se registrarán detalladamente en el backend y se presentarán mensajes genéricos o códigos de error al usuario.
        
-   **File System Access:**
    
    -   Si la aplicación necesita leer/escribir en el sistema de archivos local (ej. para logs, configuraciones locales adicionales, exportaciones), debe hacerlo en directorios designados y con los permisos adecuados, evitando accesos a rutas sensibles del sistema.

## Panel de Gestión de Estrategias (UI)

El panel de gestión de estrategias proporciona una interfaz gráfica para administrar todas las configuraciones de estrategias de trading dentro de UltiBotInversiones.

### Funcionalidades Principales:

1.  **Visualización de Estrategias:**
    *   Una tabla muestra todas las estrategias configuradas, incluyendo su nombre, descripción, modo (Paper/Real) y estado de activación.
    *   Se pueden ordenar las estrategias haciendo clic en las cabeceras de las columnas.

2.  **Crear Nueva Estrategia:**
    *   Haz clic en el botón "Crear Nueva Estrategia".
    *   Se abrirá un diálogo (`StrategyConfigDialog`) donde podrás definir:
        *   Nombre de la estrategia.
        *   Descripción.
        *   Script de la estrategia (nombre del archivo o identificador).
        *   Parámetros específicos de la estrategia (en formato JSON).
        *   Modo de operación inicial (Paper/Real).
    *   Al guardar, la nueva estrategia aparecerá en la lista.

3.  **Editar Estrategia Existente:**
    *   Selecciona una estrategia de la tabla.
    *   Haz clic en el botón "Editar Estrategia Seleccionada".
    *   El diálogo `StrategyConfigDialog` se abrirá con los datos de la estrategia seleccionada, permitiendo su modificación.
    *   Guarda los cambios para actualizar la estrategia.

4.  **Duplicar Estrategia (Clonar):**
    *   Selecciona una estrategia de la tabla que desees usar como plantilla.
    *   Haz clic en el botón "Duplicar Estrategia Seleccionada".
    *   El diálogo `StrategyConfigDialog` se abrirá con los datos de la estrategia seleccionada, pero en modo de creación (se generará un nuevo ID al guardar).
    *   Esto es útil para crear variaciones de estrategias existentes rápidamente.

5.  **Eliminar Estrategia:**
    *   Selecciona una estrategia de la tabla.
    *   Haz clic en el botón "Eliminar Estrategia Seleccionada".
    *   Se mostrará un diálogo de confirmación (`QMessageBox`) antes de proceder con la eliminación.
    *   Si se confirma, la estrategia será eliminada del sistema.

6.  **Activar/Desactivar Estrategia:**
    *   Cada estrategia en la tabla tiene un interruptor (toggle) en la columna "Activada".
    *   Para cambiar el estado de activación:
        *   Haz clic en el interruptor correspondiente a la estrategia.
        *   Si la estrategia está configurada en modo "Real", se mostrará un diálogo de confirmación adicional antes de activar/desactivar, como medida de seguridad.
        *   El cambio se refleja visualmente de forma optimista en la UI y luego se confirma con el backend. En caso de error en la comunicación con el backend, el estado visual del interruptor se revertirá.
    *   Una estrategia debe estar "Activada" para que el motor de trading (`TradingEngine`) la considere para ejecución.

### Consideraciones Adicionales:

*   **Feedback Visual:** Todas las operaciones (crear, editar, duplicar, eliminar, activar/desactivar) proporcionan feedback visual inmediato (mensajes de éxito o error) a través de diálogos `QMessageBox`.
*   **Modo Paper vs. Real:** Asegúrate de seleccionar el modo correcto para cada estrategia. Las operaciones en modo "Real" interactuarán con fondos reales si la configuración del exchange lo permite.
