# Capa de Interacción API en el Front-End (PyQt5 con Backend FastAPI)

Este documento describe la estrategia y los mecanismos mediante los cuales la interfaz de usuario (UI) de UltiBotInversiones, desarrollada con PyQt5, interactuará con la API interna del backend (FastAPI).

## 1. Introducción

La UI de PyQt5 necesita comunicarse con el backend FastAPI para:
- Enviar solicitudes de configuración y acciones del usuario.
- Obtener datos para visualización (estado del portafolio, datos de mercado, historial, etc.).
- Recibir actualizaciones y notificaciones.

La API del backend está definida en `docs/Architecture.md` (sección "Internal APIs Provided"), sirviendo en `http://localhost:8000/api/v1/` y utilizando JSON.

## 2. Cliente HTTP

Para realizar las llamadas HTTP desde la UI de PyQt5 al backend FastAPI, se recomienda utilizar la biblioteca **`httpx`**.

-   **Justificación:**
    -   **Consistencia:** `httpx` ya está en el stack tecnológico del backend (`docs/Architecture.md` sección "Definitive Tech Stack Selections"). Usarlo en la UI promueve la consistencia.
    -   **Capacidades Asíncronas:** `httpx` soporta operaciones `async/await`, lo cual es ideal para no bloquear el hilo principal de la UI de PyQt5. Esto es crucial para mantener una interfaz de usuario responsiva, especialmente durante llamadas de red que pueden tener latencia.
    -   **Características Modernas:** Es una biblioteca moderna con una API amigable, similar a `requests` pero con soporte asíncrono.

-   **Alternativa (Síncrona):**
    -   Si la integración de `async/await` con el bucle de eventos de PyQt5 resultara compleja para la v1.0, se podría considerar la biblioteca `requests` (síncrona) ejecutando las llamadas en `QThread`s separados para evitar el bloqueo de la UI. Sin embargo, `httpx` con un manejo adecuado de asincronía es la opción preferida.

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

-   **Estrategia Recomendada:**
    1.  **Utilizar `asyncio` y `httpx` para las llamadas API.**
    2.  **Integrar el bucle de eventos de `asyncio` con el de Qt.** Una biblioteca como `quamash` o `asyncqt` puede facilitar esto, permitiendo que las tareas `asyncio` se ejecuten y sus resultados se procesen de vuelta en el hilo de la UI de Qt de forma segura.
    3.  **Alternativa con `QThread`:** Si la integración directa de `asyncio` es compleja para v1.0, las llamadas `httpx` (incluso las síncronas) pueden ejecutarse en un `QThread` separado. El `QThread` emitirá señales Qt con los resultados (datos o errores) que serán capturadas por slots en el hilo principal de la UI para actualizar los widgets. Esto asegura que la UI permanezca responsiva.

    ```python
    # Ejemplo conceptual usando QThread y httpx (síncrono en el hilo)
    from PyQt5.QtCore import QThread, pyqtSignal
    import httpx

    class ApiWorker(QThread):
        result_ready = pyqtSignal(object)
        error_occurred = pyqtSignal(str)

        def __init__(self, url, method='GET', json_data=None, params=None):
            super().__init__()
            self.url = url
            self.method = method
            self.json_data = json_data
            self.params = params

        def run(self):
            try:
                with httpx.Client() as client:
                    if self.method == 'GET':
                        response = client.get(self.url, params=self.params)
                    elif self.method == 'POST':
                        response = client.post(self.url, json=self.json_data, params=self.params)
                    # ... otros métodos
                    response.raise_for_status() # Lanza HTTPStatusError para 4xx/5xx
                    self.result_ready.emit(response.json())
            except httpx.HTTPStatusError as e:
                error_details = e.response.json() if e.response.content else {}
                self.error_occurred.emit(f"Error API {e.response.status_code}: {error_details.get('detail', e.response.text)}")
            except httpx.RequestError as e:
                self.error_occurred.emit(f"Error de red/solicitud: {e}")
            except Exception as e:
                self.error_occurred.emit(f"Error inesperado: {e}")

    # En la UI:
    # self.worker = ApiWorker(url="http://localhost:8000/api/v1/portfolio/summary")
    # self.worker.result_ready.connect(self.handle_portfolio_data)
    # self.worker.error_occurred.connect(self.show_error_message)
    # self.worker.start()
    ```

## 6. Manejo de Errores de API en la UI

-   **Errores de Red/Conexión:** Se deben capturar excepciones como `httpx.ConnectError`, `httpx.TimeoutException`. La UI debe informar al usuario que no se pudo conectar al backend.
-   **Errores HTTP (4xx, 5xx):**
    -   Para errores `422 Unprocessable Entity` de FastAPI, el cuerpo de la respuesta JSON contendrá detalles de validación por campo. La UI debe intentar parsear estos detalles y mostrar mensajes de error específicos cerca de los campos de entrada correspondientes si es posible.
    -   Para otros errores 4xx/5xx, se mostrará un mensaje genérico pero informativo al usuario (ej. "Error al guardar configuración: El servidor respondió con un error.").
-   **Notificaciones al Usuario:** Los errores se comunicarán mediante:
    -   Diálogos de mensaje (`QMessageBox`).
    -   Indicadores en una barra de estado.
    -   Resaltado de campos erróneos en formularios.
-   **Logging:** Todos los errores de API deben ser registrados detalladamente en los logs del frontend (si se implementa un sistema de logging para la UI) para facilitar la depuración.

## 7. Interacción con Endpoints Específicos (Ejemplos)

La UI interactuará con los diversos grupos de endpoints definidos en `Architecture.md`.

-   **`/config/` (Gestor de Configuración):**
    -   `GET /config/`: Al inicio de la aplicación para cargar la configuración del usuario.
    -   `PATCH /config/`: Para guardar cambios en las preferencias del usuario (ej. tema, listas de seguimiento, capital de paper trading). La UI enviará solo los campos modificados.
-   **`/credentials/` (Gestor de Credenciales):**
    -   `GET /credentials/status`: Para obtener el estado de configuración de todas las credenciales.
    -   `POST /credentials/{service_name}`: Para añadir/actualizar credenciales de un servicio (ej. Binance, Telegram). La UI enviará un payload JSON con `apiKey`, `apiSecret` (si aplica), `otherDetails`, etc.
    -   `POST /credentials/{service_name}/verify`: Para solicitar una prueba de conexión de una credencial.
    -   `DELETE /credentials/{credential_id}`: Para eliminar una credencial.
-   **`/portfolio/` (Gestor de Portafolio):**
    -   `GET /portfolio/summary?mode=paper`: Para obtener el resumen del portafolio de paper trading.
    -   `GET /portfolio/summary?mode=real`: Para obtener el resumen del portafolio real.
    -   Estos datos se usarán para poblar las secciones correspondientes del dashboard.
-   **`/strategies/` (Gestor de Estrategias):**
    -   `GET /strategies/`: Para listar todas las configuraciones de estrategias.
    -   `POST /strategies/`: Para crear una nueva configuración de estrategia.
    -   `PUT /strategies/{strategy_id}`: Para actualizar una configuración de estrategia existente.
    -   `POST /strategies/{strategy_id}/activate?mode=paper`: Para activar/desactivar una estrategia en modo paper.
-   **`/notifications/` (Servicio de Notificaciones):**
    -   `GET /notifications/history`: Para obtener el historial de notificaciones para mostrar en el panel de la UI.
    -   La UI podría usar WebSockets (si el backend los expone para notificaciones) o polling periódico a este endpoint para actualizaciones en tiempo real.

## 8. Consideraciones Adicionales

-   **Timeouts:** Todas las llamadas API deben tener timeouts configurados (conexión y lectura) para evitar que la UI se quede esperando indefinidamente.
-   **Cancelación de Solicitudes:** Si es posible, implementar la capacidad de cancelar solicitudes API en curso si el usuario navega fuera de la vista o cierra una ventana modal antes de que la solicitud se complete. `httpx` ofrece soporte para cancelación.

Este documento servirá como guía para implementar una capa de interacción API robusta y eficiente en el frontend de UltiBotInversiones.
