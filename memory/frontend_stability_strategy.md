# Estrategia de Solución Definitiva: "Operación Reloj Atómico"

## 1. Objetivo

Erradicar de forma sistemática y permanente los problemas de desincronización (DB, API) y de inestabilidad asíncrona que actualmente plagan el sistema UltiBotInversiones, aplicando un enfoque basado en la prevención, validación automática y robustez del código.

## 2. Pilares de la Estrategia

### Pilar I: Integridad de la Base de Datos (Solución al `OperationalError`)

La desincronización entre el modelo de la aplicación y el esquema de la base de datos es inaceptable.

**Acciones Inmediatas:**
1.  **Eliminar el Estado Corrupto:** El archivo `ultibot_local.db` debe ser eliminado. El sistema lo recreará con el esquema correcto en el próximo inicio.
2.  **Modificar el Modelo de Datos:** El modelo `MarketData` en `src/ultibot_backend/core/domain_models/market_data_models.py` debe ser corregido para incluir las columnas que faltan (`open`, `high`, `low`, `close`).

**Solución a Largo Plazo:**
1.  **Implementar Migraciones de Base de Datos:** Se introducirá **Alembic** para gestionar las migraciones del esquema de la base de datos.
    *   **Tarea:** Configurar Alembic en el proyecto.
    *   **Tarea:** Generar una migración inicial que refleje el estado actual y correcto de los modelos de SQLAlchemy.
    *   **Tarea:** Integrar un comando `poetry run alembic upgrade head` en el script de inicio del backend para asegurar que la base de datos esté siempre actualizada antes de que la aplicación se inicie.

### Pilar II: Sincronización del Contrato API (Solución al `TypeError`)

Las discrepancias entre el cliente y el servidor de la API deben ser detectadas antes del despliegue.

**Acciones Inmediatas:**
1.  **Corregir la Llamada del Cliente:** Modificar `src/ultibot_ui/widgets/paper_trading_report_widget.py` para que no envíe los parámetros `date_from` y `date_to`.
2.  **O BIEN, Mejorar el Endpoint:** Modificar el endpoint del backend en `src/ultibot_backend/api/v1/endpoints/trades.py` para que acepte y filtre por los parámetros de fecha, lo cual es una funcionalidad deseable.

**Solución a Largo Plazo:**
1.  **Tests de Contrato Automatizados:** Implementar una nueva suite de tests de integración (`tests/integration/test_api_contracts.py`).
    *   **Tarea:** Estos tests no mockearán la lógica de negocio, sino que iniciarán una instancia real del backend (con una DB de prueba en memoria) y un cliente `httpx` real.
    *   **Tarea:** Se probará cada endpoint, verificando que las solicitudes y respuestas se adhieran a los modelos Pydantic definidos. Esto atrapará cualquier discrepancia en parámetros, tipos de datos o estructura de los objetos.
2.  **Documentación de API Compartida:** Generar y mantener una especificación OpenAPI (o similar) directamente desde el código del backend de FastAPI. Esta especificación se convertirá en la "única fuente de verdad" para el equipo de frontend.

### Pilar III: Estabilidad del Bucle de Eventos Asíncrono (Solución a `AsyncLibraryNotFoundError`)

El código asíncrono debe ser gestionado de forma predecible y robusta, especialmente en un entorno híbrido como PySide6 + asyncio.

**Acciones Inmediatas:**
1.  **Gestión Explícita del Ciclo de Vida del Cliente API:**
    *   **Tarea:** Refactorizar `src/ultibot_ui/main.py` y `src/ultibot_ui/services/api_client.py`. El cliente `httpx` debe ser inicializado explícitamente junto con la aplicación y cerrado de forma segura y `awaited` durante el evento de cierre de la aplicación.
    *   **Ejemplo de `main.py`:**
        ```python
        async def main(app):
            # ... inicialización ...
            api_client = UltiBotAPIClient()
            await api_client.initialize()
            main_window.set_api_client(api_client)
            # ...
            await app.exec()
            await api_client.close() # Cierre explícito y esperado
        ```

**Solución a Largo Plazo:**
1.  **Centralizar la Creación de Tareas Asíncronas:** Crear un `TaskManager` o un servicio similar en la UI que sea el único responsable de crear tareas de `asyncio`. Esto asegura que todas las tareas se ejecuten en el contexto del bucle de eventos correcto gestionado por `qasync`.
2.  **Refactorizar Workers:** Todas las llamadas asíncronas en los `workers` y `widgets` deben ser delegadas a través de este `TaskManager`. Se deben evitar las llamadas directas a `asyncio.create_task`.
3.  **Principio de "Inyección de Dependencias" para el Event Loop:** Si un componente necesita interactuar con el bucle de eventos, el bucle debe ser pasado a su constructor (inyectado) en lugar de intentar obtenerlo globalmente con `asyncio.get_running_loop()`.

## 3. Plan de Implementación Inmediato

1.  **[Bloqueante]** Corregir el modelo `MarketData` y eliminar `ultibot_local.db`.
2.  **[Backend]** Añadir el filtrado por fecha al endpoint de historial de trades.
3.  **[Frontend]** Refactorizar el ciclo de vida del `APIClient` para su correcta inicialización y cierre.
4.  **[Testing]** Escribir un test de contrato inicial para el endpoint de historial de trades que verifique los nuevos parámetros de fecha.
5.  Validar que la aplicación se inicia y funciona sin errores en los tres frentes.
