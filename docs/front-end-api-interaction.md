# Capa de Interacción API en el Front-End (PyQt5 con Backend FastAPI)

Este documento describe la estrategia y los mecanismos mediante los cuales la interfaz de usuario (UI) de UltiBotInversiones, desarrollada con PyQt5, interactuará con la API interna del backend (FastAPI).

## 1. Introducción

La UI de PyQt5 necesita comunicarse con el backend FastAPI para:
- Enviar solicitudes de configuración y acciones del usuario.
- Obtener datos para visualización (estado del portafolio, datos de mercado, historial, etc.).
- Recibir actualizaciones y notificaciones.

La API del backend está definida en `docs/Architecture.md` (sección "Internal APIs Provided"), sirviendo en `http://localhost:8000/api/v1/` y utilizando JSON.

## 2. Cliente HTTP

Para realizar las llamadas HTTP desde la UI de PyQt5 al backend FastAPI, se utiliza la biblioteca **`httpx`**.

-   **Justificación:**
    -   **Consistencia:** `httpx` está en el stack tecnológico del backend (`docs/Architecture.md` sección "Definitive Tech Stack Selections"). Usarlo en la UI promueve la consistencia.
    -   **Capacidades Asíncronas:** `httpx` soporta operaciones `async/await`, lo cual es ideal para no bloquear el hilo principal de la UI de PyQt5. Esto es crucial para mantener una interfaz de usuario responsiva.
    -   **Características Modernas:** Es una biblioteca moderna con una API amigable.

Todas las llamadas `httpx` están encapsuladas dentro de la clase `UltiBotAPIClient` (ubicada en `src/ultibot_ui/services/api_client.py`). Esta clase sirve como la interfaz estandarizada y centralizada para toda la comunicación entre la UI y el backend.

## 3. Estructura de las Solicitudes API

-   **URL Base:** Todas las solicitudes a la API interna utilizarán la URL base definida: `http://localhost:8000/api/v1/`.
-   **Endpoints:** Se construirán concatenando la URL base con las rutas específicas de los recursos definidas en `Architecture.md` (ej. `/config/`, `/credentials/{service_name}/`).
-   **Métodos HTTP:** Se utilizarán los métodos HTTP apropiados (GET, POST, PUT, DELETE, PATCH) según la acción a realizar.
-   **Headers:**
    -   `Content-Type: application/json` para solicitudes con cuerpo (POST, PUT, PATCH).
    -   `Accept: application/json` para indicar que se espera una respuesta JSON.
    -   No se requiere autenticación compleja para la v1.0 ya que la API se enlaza a `localhost`.
-   **Cuerpo de la Solicitud (Request Body):** Para métodos POST, PUT, PATCH, los datos se enviarán como un payload JSON, serializados desde modelos Pydantic o diccionarios Python.

## 4. Manejo de Respuestas API

-   **Respuestas Exitosas:**
    -   Se esperarán códigos de estado HTTP `2xx` (ej. `200 OK`, `201 Created`, `204 No Content`).
    -   El cuerpo de la respuesta, si lo hay, será JSON y se deserializará en modelos Pydantic (preferiblemente compartidos con el backend o definidos en la UI) o diccionarios Python para su uso en la UI.
-   **Respuestas de Error:**
    -   Se manejarán códigos de estado HTTP `4xx` (errores del cliente, ej. `400 Bad Request`, `404 Not Found`, `422 Unprocessable Entity` para errores de validación de FastAPI) y `5xx` (errores del servidor).
    -   FastAPI devuelve errores de validación (422) con un cuerpo JSON detallado que la UI puede interpretar para mostrar mensajes específicos al usuario.
    -   Otros errores (ej. `401 Unauthorized`, `403 Forbidden`, aunque menos probables en v1.0 local) también deben ser manejados.
-   **Actualización de la UI:**
    -   Tras recibir una respuesta exitosa, los datos se utilizarán para actualizar los widgets correspondientes de la UI (ej. tablas, etiquetas, gráficos).
    -   En caso de error, se mostrará un mensaje apropiado al usuario (ver sección "Manejo de Errores").

## 5. Integración de Asincronía con PyQt5

Dado que `httpx` permite llamadas asíncronas y PyQt5 tiene su propio bucle de eventos, es crucial integrarlos correctamente para evitar bloquear la UI.

-   **Estrategia Implementada:**
    1.  Se utiliza `asyncio` y `httpx` para las llamadas API, encapsuladas dentro de los métodos `async` de `UltiBotAPIClient`.
    2.  Para integrar estas llamadas asíncronas con el hilo de la UI de PyQt5, se emplea un patrón de `QObject` movido a un `QThread` (`ApiWorker` en `src/ultibot_ui/main.py`).
        *   El `ApiWorker` recibe una corutina (una llamada a un método de `UltiBotAPIClient`).
        *   En su método `run` (ejecutado en el `QThread` secundario), crea un nuevo bucle de eventos `asyncio` para ejecutar la corutina.
        *   Emite señales Qt (`result_ready` o `error_occurred`) con los resultados (datos o información de error) de vuelta al hilo principal de la UI.
        *   Los componentes de la UI (vistas, widgets) conectan slots a estas señales para procesar los resultados y actualizarse.
    3.  Este enfoque asegura que la UI permanezca responsiva durante las operaciones de red. El ejemplo conceptual que se mostraba previamente en este documento fue realizado utilizando esta clase `ApiWorker`.

    ```python
    # Ejemplo conceptual de la estructura de ApiWorker (la implementación real está en src/ultibot_ui/main.py)
    # from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
    # import asyncio
    #
    # class ApiWorker(QObject):
    #     result_ready = pyqtSignal(object)
    #     error_occurred = pyqtSignal(str) # O un tipo más específico como APIError
    #
    #     def __init__(self, awaitable_coroutine: asyncio.coroutine):
    #         super().__init__()
    #         self.awaitable_coroutine = awaitable_coroutine
    #
    #     @pyqtSlot()
    #     def run(self):
    #         try:
    #             loop = asyncio.new_event_loop()
    #             asyncio.set_event_loop(loop)
    #             result = loop.run_until_complete(self.awaitable_coroutine)
    #             loop.close()
    #             self.result_ready.emit(result)
    #         except Exception as e: # Captura APIError u otras excepciones
    #             self.error_occurred.emit(str(e)) # Emitir detalles del error
    #
    # # En la UI (ejemplo conceptual):
    # # self.api_client = UltiBotAPIClient()
    # # coroutine = self.api_client.get_some_data(params)
    # # self.worker = ApiWorker(coroutine)
    # # self.thread = QThread()
    # # self.worker.moveToThread(self.thread)
    # # self.worker.result_ready.connect(self.handle_data_success_slot)
    # # self.worker.error_occurred.connect(self.handle_data_error_slot)
    # # self.thread.started.connect(self.worker.run)
    # # self.thread.finished.connect(self.worker.deleteLater) # Limpieza
    # # self.thread.finished.connect(self.thread.deleteLater) # Limpieza
    # # self.thread.start()
    ```

## 6. Manejo de Errores de API en la UI

-   **Errores de Red/Conexión y HTTP (4xx, 5xx):** `UltiBotAPIClient` encapsula errores de `httpx` (como `ConnectError`, `TimeoutException`, `HTTPStatusError`) y los relanza como una `APIError` personalizada. Esta `APIError` contiene el mensaje, código de estado y, opcionalmente, el cuerpo de la respuesta JSON del error.
-   **Notificaciones al Usuario:** Los componentes de la UI (vistas y widgets) capturan estas `APIError` (emitidas a través de la señal `error_occurred` del `ApiWorker`) y comunican los errores al usuario mediante diálogos de mensaje (`QMessageBox.warning` o `QMessageBox.critical`). Se muestran mensajes amigables al usuario, mientras que los detalles técnicos completos se registran para depuración.
-   **Logging:** Los errores de API, incluyendo detalles de `APIError` como `status_code` y `response_json`, se registran usando el módulo `logging` de Python.

Este sistema de manejo de errores se ha implementado en los componentes de UI recientemente refactorizados.

## 7. Interacción con Endpoints Específicos (Ejemplos)

La UI interactúa con el backend exclusivamente a través de `UltiBotAPIClient`. Algunos ejemplos de interacciones actuales:

-   **`/config` (Configuración de Usuario):**
    -   `GET /api/v1/config`: Utilizado por `UltiBotAPIClient.get_user_configuration()` para cargar la configuración del usuario al inicio y en vistas de configuración.
    -   `PATCH /api/v1/config`: Utilizado por `UltiBotAPIClient.update_user_configuration()` para guardar cambios en las preferencias.
-   **`/portfolio/snapshot/{user_id}` (Portafolio):**
    -   `GET /api/v1/portfolio/snapshot/{user_id}`: Utilizado por `UltiBotAPIClient.get_portfolio_snapshot()` para obtener los datos completos del portafolio (paper y real), incluyendo activos. Es la fuente principal para la nueva `PortfolioView`.
-   **`/opportunities/real-trading-candidates` (Oportunidades):**
    -   `GET /api/v1/opportunities/real-trading-candidates`: Utilizado por `UltiBotAPIClient.get_real_trading_candidates()` para poblar la `OpportunitiesView` con oportunidades de alta confianza.
-   **Nuevos Endpoints Soportados por `UltiBotAPIClient`:**
    -   `GET /api/v1/market/tickers` (vía `get_ticker_data`): Para obtener datos de múltiples tickers, usado por `MarketDataWidget`.
    -   `GET /api/v1/market/klines` (vía `get_candlestick_data`): Para obtener datos de velas, usado por `ChartWidget`.
    -   `GET /api/v1/notifications/history` (vía `get_notification_history`): Para obtener el historial de notificaciones, usado por `NotificationWidget`.
-   **Otros Endpoints:** La clase `UltiBotAPIClient` contiene métodos para interactuar con estrategias, trades, y otros endpoints definidos en el backend.

Los endpoints relacionados con credenciales (`/credentials/...`) no son actualmente utilizados por la UI para *escribir* credenciales, ya que esa funcionalidad se maneja a través de variables de entorno o configuración directa del backend por el momento.

## 8. Consideraciones Adicionales

-   **Timeouts:** Todas las llamadas API deben tener timeouts configurados (conexión y lectura) para evitar que la UI se quede esperando indefinidamente.
-   **Cancelación de Solicitudes:** Si es posible, implementar la capacidad de cancelar solicitudes API en curso si el usuario navega fuera de la vista o cierra una ventana modal antes de que la solicitud se complete. `httpx` ofrece soporte para cancelación.

Este documento servirá como guía para implementar una capa de interacción API robusta y eficiente en el frontend de UltiBotInversiones.
