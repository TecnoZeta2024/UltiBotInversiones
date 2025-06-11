# Environment Variables

Este documento detallará las variables de entorno utilizadas por UltiBotInversiones.

## Variables de Entorno Principales

A continuación, se listarán las variables de entorno clave requeridas para la configuración y ejecución de la aplicación.

-   **`GEMINI_API_KEY`**:
    -   Descripción: Clave API para acceder a los servicios de Google Gemini.
    -   Ejemplo: `AIzaSy...`
    -   Uso: Requerida por el `AI_Orchestrator` para realizar análisis y tomar decisiones.

-   **`BINANCE_API_KEY`**:
    -   Descripción: Clave API para la cuenta de Binance.
    -   Uso: Requerida por el `CredentialManager` y utilizada por los adaptadores de Binance para obtener datos de mercado y ejecutar operaciones. Se almacena encriptada.

-   **`BINANCE_API_SECRET`**:
    -   Descripción: Clave secreta para la API de Binance.
    -   Uso: Requerida por el `CredentialManager` y utilizada junto con la `BINANCE_API_KEY`. Se almacena encriptada.

-   **`TELEGRAM_BOT_TOKEN`**:
    -   Descripción: Token para el bot de Telegram utilizado para enviar notificaciones.
    -   Uso: Requerido por el `CredentialManager` y utilizado por el `NotificationService`. Se almacena encriptado.

-   **`TELEGRAM_CHAT_ID`**:
    -   Descripción: ID del chat de Telegram donde se enviarán las notificaciones.
    -   Uso: Requerido por el `CredentialManager` y utilizado por el `NotificationService`. Se almacena encriptado (como parte de `otherDetails` de la credencial de Telegram).

-   **`MOBULA_API_KEY`**:
    -   Descripción: Clave API para el servicio Mobula.
    -   Uso: Requerida por el `CredentialManager` y utilizada como herramienta por el `AI_Orchestrator` para verificación de datos de activos. Se almacena encriptada.

-   **`SUPABASE_URL`**:
    -   Descripción: URL del proyecto Supabase.
    -   Uso: Requerida por el `DataPersistenceService` para conectarse a la base de datos PostgreSQL.

-   **`SUPABASE_KEY`**:
    -   Descripción: Clave anónima (anon key) o de servicio (service_role key) para el proyecto Supabase.
    -   Uso: Requerida por el `DataPersistenceService` para autenticarse con Supabase.

-   **`APP_ENCRYPTION_KEY`**:
    -   Descripción: Clave maestra utilizada para encriptar y desencriptar las credenciales API almacenadas en la base de datos. Esta clave debe ser gestionada de forma segura por el usuario.
    -   Uso: Utilizada por el `CredentialManager`.

-   **`FASTAPI_HOST`**:
    -   Descripción: Host en el que se ejecutará el servidor FastAPI.
    -   Default: `127.0.0.1` (localhost)
    -   Uso: Configuración del servidor Uvicorn.

-   **`FASTAPI_PORT`**:
    -   Descripción: Puerto en el que se ejecutará el servidor FastAPI.
    -   Default: `8000`
    -   Uso: Configuración del servidor Uvicorn.

-   **`REDIS_HOST`**:
    -   Descripción: Host del servidor Redis.
    -   Default: `localhost`
    -   Uso: Conexión a Redis para caché L2.

-   **`REDIS_PORT`**:
    -   Descripción: Puerto del servidor Redis.
    -   Default: `6379`
    -   Uso: Conexión a Redis para caché L2.

## Notas de Configuración

-   Las claves API sensibles (Binance, Telegram, Mobula, Gemini) no se definen directamente como variables de entorno para la aplicación en ejecución, sino que se gestionan a través del `CredentialManager` y se almacenan encriptadas en la base de datos. La `APP_ENCRYPTION_KEY` es crucial para este proceso.
-   Se recomienda utilizar un archivo `.env` (no versionado en Git) para gestionar estas variables en el entorno de desarrollo local. Un archivo `.env.example` debe estar presente en el repositorio.
-   La carga de estas variables en la aplicación se realizará mediante Pydantic `BaseSettings` para validación y tipado.

_(Este documento se actualizará a medida que se definan o modifiquen más variables de entorno durante el desarrollo.)_
