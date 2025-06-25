---
description: "Protocolo Maestro Unificado de Debugging y Resolución de Tests para Agentes IA"
author: "Cline (consolidado)"
version: 1.0
tags: ["debugging", "testing", "srst", "protocol", "mandatory", "troubleshooting"]
globs: ["*"]
priority: 1100
---

# 🚨 PROTOCOLO MAESTRO DE DEBUGGING Y RESOLUCIÓN DE TESTS

## **MANDATO SUPREMO**
- **ESTA ES LEY NO NEGOCIABLE**: Todo agente IA que trabaje en este proyecto DEBE usar este protocolo unificado.
- **PRINCIPIO FUNDAMENTAL**: UN ERROR A LA VEZ, UN MÓDULO A LA VEZ, UN FIX A LA VEZ.

---

## **HERRAMIENTA 1: Sistema de Resolución Segmentada de Tests (SRST)**

*   **OBJETIVO:**
    *   Identificar, segmentar y resolver fallos de tests de forma metódica y eficiente, garantizando la validación incremental y la no-regresión.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** la tarea principal es "Triage y Resolución de Fallos de Tests".
    *   **O SI** se detectan fallos en la suite de tests durante el desarrollo o CI.
    *   **ENTONCES** el protocolo SRST **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / ITERACIÓN):**
    1.  **Fase de Triage Automático (SECUENCIA - 5 mins max):**
        a.  **Ejecutar diagnóstico específico**:
            ```bash
            poetry run pytest --collect-only -q 2>&1 | head -20
            ```
        b.  **Clasificar errores** por categoría y prioridad.
        c.  **Crear máximo 3 tickets atómicos** para la sesión actual.
        d.  **Validar Ticket Generado:** Antes de proceder, verificar que el ticket apunte a un archivo lógico y que el comando de validación sea correcto.
        e.  **Manejo de Logs Vacíos o Inexistentes:** Si los archivos de log están vacíos o no se generan, **DEBES** intentar ejecutar el punto de entrada de la aplicación directamente para capturar la salida estándar (stdout/stderr) y obtener el traceback del error.
        f.  **Documentar en SRST_TRACKER.md**.
    2.  **Fase de Resolución Micro-Segmentada (ITERACIÓN - 15 mins por ticket):**
        a.  **Seleccionar 1 ticket** de máxima prioridad.
        b.  **Cargar contexto mínimo** (solo archivos relevantes).
        c.  **Aplicar fix quirúrgico** específico.
        d.  **Validar inmediatamente**:
            ```bash
            # Comando específico para validar este fix
            poetry run pytest -xvs {SPECIFIC_TEST}
            ```
        e.  **Refactorizar Tests si es Necesario:** Si la corrección del bug invalida un test, la tarea incluye la refactorización del test.
        f.  **Documentar resultado** en SRST_PROGRESS.md.
    3.  **Fase de Validación y Cierre (SECUENCIA):**
        a.  **Verificar no-regresión**:
            ```bash
            poetry run pytest --collect-only -q
            ```
        b.  **Commit con estado limpio**.

---

## **HERRAMIENTA 2: Protocolos de Emergencia y Workflows de Debugging**

### **Niveles de Alerta (DEFCON)**

-   **DEFCON 1: Suite de Tests Completamente Rota**
    1.  **STOP** - No hacer más cambios.
    2.  **ASSESS** - Ejecutar `poetry run pytest --collect-only -q`.
    3.  **ISOLATE** - Identificar el primer error de importación.
    4.  **FIX** - Corregir un error a la vez.
    5.  **VALIDATE** - Re-ejecutar `collect-only` después de cada fix.

-   **DEFCON 2: Múltiples Errores AsyncIO**
    1.  **RESTART** - Cerrar VS Code y terminal.
    2.  **CLEAN** - `poetry env remove --all && poetry install`.
    3.  **VERIFY** - Ejecutar un test simple primero.

-   **DEFCON 3: Fixtures Rotas Masivamente**
    1.  **BACKUP** - Commit del estado actual.
    2.  **REVERT** - Al último commit funcional conocido.
    3.  **INCREMENTAL** - Aplicar cambios uno por uno y validar.

### **Estrategias de Resolución de Problemas Complejos**

-   **Uso de Sequential Thinking:** Para problemas complejos que requieren un análisis paso a paso y una lógica de resolución estructurada (como la depuración de entornos de despliegue o interacciones entre múltiples servicios), se **DEBE** utilizar la herramienta `sequential-thinking`. Esto ayuda a desglosar el problema, mantener un registro del proceso de pensamiento y asegurar una resolución metódica.

### **Manejo de Falsos Positivos de Linter**
-   **Identificación:** Cuando un linter (ej. Pylint) reporta errores de "No name in module" para importaciones de bibliotecas de terceros (ej. PySide6, SQLAlchemy), especialmente para módulos compilados, se debe investigar si son falsos positivos.
-   **Prioridad:** La funcionalidad correcta y la convención del framework tienen prioridad sobre la supresión ciega de linter.
-   **Estrategias de Resolución:**
    1.  **Verificación de Código:** Asegurarse de que el código sigue las convenciones de la biblioteca y funciona correctamente en tiempo de ejecución.
    2.  **Importaciones Explícitas:** Si es posible y mejora la claridad, usar importaciones de módulo completo (ej. `import PySide6.QtWidgets as QtWidgets`) y referenciar las clases con el prefijo (ej. `QtWidgets.QWidget`).
    3.  **Supresión Dirigida:** Si las soluciones de código no son viables o afectan negativamente la legibilidad, considerar añadir supresiones de Pylint específicas y bien documentadas (ej. `# pylint: disable=no-name-in-module`) solo para las líneas o bloques afectados, con una justificación clara.
    4.  **Validación de Ejecución:** Confirmar que el código se ejecuta sin errores en el entorno de destino, independientemente de las advertencias del linter.

### **Debugging de Contenedores y Dependencias**
-   **Verificación de Healthchecks:** **DEBES** asegurar que todos los servicios externos o adaptadores (ej. bases de datos, Redis, APIs externas) utilizados en un `healthcheck` de Docker Compose tengan un método `test_connection()` robusto y explícito en su implementación. Este método debe realizar una operación ligera para verificar la conectividad.
-   **Inicialización de Dependencias:** **DEBES** verificar que todas las dependencias de la aplicación dentro de un contenedor estén completamente inicializadas y listas antes de que el `healthcheck` de Docker Compose las evalúe. Ajusta `start_period` en `docker-compose.yml` si es necesario.
-   **Problemas de `poetry.lock` en Builds de Docker:** Si un build de Docker falla con un mensaje como "`pyproject.toml changed significantly since poetry.lock was last generated`", **DEBES** ejecutar `poetry lock` en el host para actualizar el archivo `poetry.lock` antes de intentar reconstruir las imágenes.

### **Debugging de Contratos de Datos (API/UI Mismatch)**
-   **Identificación:** Cuando un error de validación (ej. `pydantic.ValidationError`) ocurre en la frontera entre dos servicios (ej. UI consumiendo una API de backend).
-   **Workflow de Resolución:**
    1.  **Verificar el Payload Real:** Loggear el payload JSON/diccionario exacto que el cliente recibe, justo antes del punto de validación, para ver la estructura de datos "cruda".
    2.  **Comparar Modelos:**
        a.  Inspeccionar el modelo Pydantic del **cliente** (el que falla).
        b.  Inspeccionar el modelo o serializador del **servidor** (el que genera la respuesta).
    3.  **Detectar Discrepancias Comunes:**
        -   **Nombres de Campos:** Buscar discrepancias `camelCase` (en JSON) vs. `snake_case` (en Python).
        -   **Tipos de Datos:** ¿Un campo es `list` donde se esperaba un `dict` o viceversa?
        -   **Nulabilidad y Campos Opcionales:** ¿Un campo requerido está llegando como `null`?
    4.  **Aplicar Corrección (Priorizada):**
        a.  **Usar Alias (Preferido):** En el modelo del cliente, usar `Field(..., alias='nombreEnCamelCase')` para mapear el JSON sin cambiar las convenciones de Python.
        b.  **Alinear Tipos:** Corregir los tipos de datos para que coincidan en ambos extremos.
        c.  **Configurar Serializador del Servidor:** Como último recurso, configurar el servidor para que emita `snake_case` si es una política global.

### **Workflow de Debugging Escalonado (VS Code)**

-   **Nivel 1: Debug Rápido (Tests Individuales)**
    1.  Colocar breakpoint.
    2.  **F5 → "🎯 Debug Pytest: Current File"**.
    3.  Inspeccionar variables.

-   **Nivel 2: Debug Profundo (Suite Completa)**
    1.  **F5 → "🐞 Debug Pytest: ALL Tests"**.
    2.  Usar `--pdb` para modo interactivo si es necesario.

-   **Nivel 3: Debug Quirúrgico (Solo Fallos)**
    1.  **F5 → "💥 Debug Failed Tests Only"**.
    2.  Usar `--tb=long` para un trace completo.

### **Comandos de Diagnóstico Esenciales**
```bash
# Test collection check (verifica imports)
poetry run pytest --collect-only -q

# Solo tests que fallan (feedback rápido)
poetry run pytest --lf -v

# Tests rápidos (sin los marcados como slow)
poetry run pytest -m "not slow" -v

# PDB completo con IPython
poetry run pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb

# Stop en primer fallo con trace corto
poetry run pytest -x --tb=short

# Coverage con reporte HTML
poetry run pytest --cov=src --cov-report=html

# Logs de un contenedor Docker específico
docker logs {container_name}

# Reconstruir y levantar servicios Docker Compose
docker-compose up --build -d

# Actualizar poetry.lock después de modificar pyproject.toml
poetry lock
```

---

## **HERRAMIENTA 3: Reglas de Oro para Pruebas Robustas**

*   **OBJETIVO:**
    *   Asegurar la creación de pruebas de alta calidad, fiables y mantenibles que garanticen la integridad del sistema y prevengan regresiones.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se está escribiendo un nuevo test.
    *   **O SI** se está refactorizando un test existente.
    *   **O SI** se está investigando un fallo intermitente en un test.
    *   **ENTONCES** el protocolo de Reglas de Oro para Pruebas Robustas **DEBE** ser consultado y aplicado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / SELECCIÓN):**

### **3.1. Gestión de Datos de Test**

-   **Validación Obligatoria:** **SIEMPRE** validar datos de test contra esquemas Pydantic antes de usarlos.
-   **Factory Pattern Obligatorio:** **DEBES** usar el patrón Factory para generar datos de test complejos y consistentes. Las factories deben proporcionar datos base válidos y permitir `overrides`.

    ```python
    # Ejemplo de Factory Pattern para Trade
    class TradeDataFactory:
        @staticmethod
        def create_valid_trade_data(**overrides) -> dict:
            base_data = {
                "id": str(uuid4()), "symbol": "BTCUSDT", "side": "BUY",
                "quantity": Decimal("1.0"), "price": Decimal("50000.0"),
                "status": "FILLED", "timestamp": datetime.utcnow()
            }
            base_data.update(overrides)
            return base_data

        @staticmethod
        def create_buy_trade(**overrides) -> Trade:
            data = TradeDataFactory.create_valid_trade_data(side="BUY", **overrides)
            return Trade.model_validate(data)
    ```

### **3.2. Consistencia de Fixtures**

-   **Cleanup Robusto:** **TODA** fixture que adquiera un recurso (sesión de BD, conexión de red) **DEBE** tener un `teardown` explícito para liberar dicho recurso (ej. `yield` seguido de `await service.close()`).
-   **Naming Convencional:** Usar nombres consistentes: `{service_name}_fixture`, `{model_name}_data`, `mock_{external_service}`.
-   **Inyección de Dependencias:** Las fixtures complejas **DEBEN** construirse componiendo fixtures más simples.

    ```python
    # Ejemplo de Fixture Robusta
    @pytest_asyncio.fixture
    async def trading_service_fixture(db_session: AsyncSession) -> TradingService:
        """Fixture para TradingService con cleanup completo."""
        service = TradingService(db_session=db_session)
        await service.initialize()
        
        yield service
        
        # Cleanup explícito y robusto
        await service.shutdown()
    ```

### **3.3. Prácticas para Tests Asíncronos**

-   **Event Loop Único:** La fixture `event_loop` **DEBE** tener `scope="session"` para prevenir errores de "Event loop is closed".
-   **Mocking Asíncrono:** **SIEMPRE** usar `AsyncMock` de `unittest.mock` para mockear corutinas y métodos asíncronos.
-   **Aislamiento de BD:** **DEBES** usar transacciones con `rollback` automático en el `teardown` de la fixture de sesión de base de datos para garantizar el aislamiento entre tests.

    ```python
    # Ejemplo de Fixture de Event Loop
    @pytest.fixture(scope="session")
    def event_loop():
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        yield loop
        loop.close()

    # Ejemplo de Mock Asíncrono
    @patch('service.external_api_call', new_callable=AsyncMock)
    async def test_with_external_api(mock_api):
        mock_api.return_value = {"data": "test"}
        result = await service.process_data()
        mock_api.assert_called_once()

### **3.1. Gestión de Datos de Test**

-   **Validación Obligatoria:** **SIEMPRE** validar datos de test contra esquemas Pydantic antes de usarlos.
-   **Factory Pattern Obligatorio:** **DEBES** usar el patrón Factory para generar datos de test complejos y consistentes. Las factories deben proporcionar datos base válidos y permitir `overrides`.

    ```python
    # Ejemplo de Factory Pattern para Trade
    class TradeDataFactory:
        @staticmethod
        def create_valid_trade_data(**overrides) -> dict:
            base_data = {
                "id": str(uuid4()), "symbol": "BTCUSDT", "side": "BUY",
                "quantity": Decimal("1.0"), "price": Decimal("50000.0"),
                "status": "FILLED", "timestamp": datetime.utcnow()
            }
            base_data.update(overrides)
            return base_data

        @staticmethod
        def create_buy_trade(**overrides) -> Trade:
            data = TradeDataFactory.create_valid_trade_data(side="BUY", **overrides)
            return Trade.model_validate(data)
    ```

### **3.2. Consistencia de Fixtures**

-   **Cleanup Robusto:** **TODA** fixture que adquiera un recurso (sesión de BD, conexión de red) **DEBE** tener un `teardown` explícito para liberar dicho recurso (ej. `yield` seguido de `await service.close()`).
-   **Naming Convencional:** Usar nombres consistentes: `{service_name}_fixture`, `{model_name}_data`, `mock_{external_service}`.
-   **Inyección de Dependencias:** Las fixtures complejas **DEBEN** construirse componiendo fixtures más simples.

    ```python
    # Ejemplo de Fixture Robusta
    @pytest_asyncio.fixture
    async def trading_service_fixture(db_session: AsyncSession) -> TradingService:
        """Fixture para TradingService con cleanup completo."""
        service = TradingService(db_session=db_session)
        await service.initialize()
        
        yield service
        
        # Cleanup explícito y robusto
        await service.shutdown()
    ```

### **3.3. Prácticas para Tests Asíncronos**

-   **Event Loop Único:** La fixture `event_loop` **DEBE** tener `scope="session"` para prevenir errores de "Event loop is closed".
-   **Mocking Asíncrono:** **SIEMPRE** usar `AsyncMock` de `unittest.mock` para mockear corutinas y métodos asíncronos.
-   **Aislamiento de BD:** **DEBES** usar transacciones con `rollback` automático en el `teardown` de la fixture de sesión de base de datos para garantizar el aislamiento entre tests.

    ```python
    # Ejemplo de Fixture de Event Loop
    @pytest.fixture(scope="session")
    def event_loop():
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        yield loop
        loop.close()

    # Ejemplo de Mock Asíncrono
    @patch('service.external_api_call', new_callable=AsyncMock)
    async def test_with_external_api(mock_api):
        mock_api.return_value = {"data": "test"}
        result = await service.process_data()
        mock_api.assert_called_once()
