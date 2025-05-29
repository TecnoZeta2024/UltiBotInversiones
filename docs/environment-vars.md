## Environment Variables Documentation

Esta sección detalla las variables de entorno requeridas y opcionales para la configuración y ejecución de "UltiBotInversiones". Es crucial que estas variables estén correctamente definidas en el entorno donde se ejecute la aplicación (ej. a través de un archivo `.env` cargado por Pydantic `BaseSettings` o directamente en el sistema).

**Convenciones:**

-   **Prioridad:** Las variables de entorno suelen tener la máxima prioridad al cargar la configuración, sobrescribiendo valores de archivos de configuración si así se diseña.
-   **Sensibilidad:** Las variables marcadas como "Sensible" (ej. claves API) deben manejarse con extremo cuidado, nunca deben ser versionadas en Git (excepto en un archivo `.env.example` con valores ficticios) y deben almacenarse de forma segura. Para "UltiBotInversiones", las claves API sensibles se gestionarán a través del `CredentialManager` y se almacenarán encriptadas en la base de datos, no directamente como variables de entorno una vez configuradas por el usuario. Sin embargo, la clave maestra para encriptar/desencriptar esas credenciales podría ser una variable de entorno o gestionada de otra forma segura.
-   **Formato:** Se espera que los valores de las variables de entorno sean strings. La aplicación (Pydantic `BaseSettings`) se encargará de castearlos a los tipos correctos (integer, boolean, etc.).

---

### Variables de Entorno Principales de la Aplicación

1.  **`APP_ENV`**
    -   **Descripción:** Define el entorno de ejecución de la aplicación.
    -   **Ejemplo:** `development`, `production` (para v1.0, `development` será el más común).
    -   **Obligatoria:** Sí.
    -   **Sensible:** No.
    -   **Notas:** Puede influir en el nivel de logging, carga de configuraciones específicas del entorno, etc.

2.  **`LOG_LEVEL`**
    -   **Descripción:** Define el nivel mínimo de severidad para los mensajes de log que se registrarán.
    -   **Ejemplo:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
    -   **Obligatoria:** No (se usará un default, ej. `INFO`).
    -   **Sensible:** No.

3.  **`DATABASE_URL` (Gestionado por Supabase)**
    -   **Descripción:** La URL de conexión a la base de datos PostgreSQL gestionada por Supabase.
    -   **Ejemplo:** `postgresql://postgres:[YOUR-PASSWORD]@db.[SUPABASE-PROJECT-REF].supabase.co:5432/postgres`
    -   **Obligatoria:** Sí (para la persistencia de datos).
    -   **Sensible:** Sí.
    -   **Notas:** Esta URL es proporcionada por Supabase. El `[YOUR-PASSWORD]` es la contraseña de la base de datos que se configuró en Supabase.

4.  **`SUPABASE_URL` (Gestionado por Supabase)**
    -   **Descripción:** La URL base para la API de Supabase (si se utiliza el cliente `supabase-py` para interactuar con las APIs de Supabase además de la conexión directa a PostgreSQL).
    -   **Ejemplo:** `https://[SUPABASE-PROJECT-REF].supabase.co`
    -   **Obligatoria:** Sí, si se usa `supabase-py` para más que solo la BD.
    -   **Sensible:** No (es pública, la seguridad la da la `SUPABASE_ANON_KEY` o `SUPABASE_SERVICE_ROLE_KEY`).

5.  **`SUPABASE_ANON_KEY` (Gestionado por Supabase)**
    -   **Descripción:** La clave anónima (pública) para la API de Supabase. Se usa para operaciones que no requieren privilegios elevados, típicamente desde el cliente.
    -   **Ejemplo:** `eyJhGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
    -   **Obligatoria:** Sí, si se usa `supabase-py`.
    -   **Sensible:** No (es pública, pero debe tratarse como parte de la configuración).

6.  **`SUPABASE_SERVICE_ROLE_KEY` (Gestionado por Supabase)**
    -   **Descripción:** La clave de rol de servicio para la API de Supabase. Otorga permisos de superadministrador y debe usarse con extrema precaución, solo desde el backend seguro.
    -   **Ejemplo:** `eyJhGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
    -   **ObligatorIA:** Sí, si el backend necesita realizar operaciones privilegiadas vía API de Supabase.
    -   **Sensible:** Sí, extremadamente.

7.  **`REDIS_URL`**
    -   **Descripción:** La URL de conexión a la instancia de Redis.
    -   **Ejemplo:** `redis://localhost:6379/0` (para Redis local sin contraseña).
    -   **Obligatoria:** Sí, si Redis se usa para caché L2 u otras funcionalidades.
    -   **Sensible:** Depende (si Redis tiene contraseña, la URL la incluirá).
    -   **Notas:** Para v1.0, se asume Redis local.

---

### Variables de Entorno para Credenciales de Servicios Externos

**Nota Importante:** Como se definió en la arquitectura, las siguientes claves API (Binance, Telegram, Gemini, Mobula, etc.) serán gestionadas por el usuario a través de la UI y almacenadas de forma segura y encriptada en la base de datos mediante el `CredentialManager`. **No se espera que estas claves estén directamente como variables de entorno en producción una vez configuradas por el usuario.**

Sin embargo, para el desarrollo inicial, pruebas, o si se decide un mecanismo de carga inicial diferente antes de que el `CredentialManager` esté completamente operativo, podrían considerarse temporalmente. El archivo `.env.example` debe listarlas con valores ficticios.

1.  **`CREDENTIAL_ENCRYPTION_KEY` (Nombre Sugerido)**
    -   **Descripción:** Clave secreta utilizada por la aplicación para encriptar y desencriptar las credenciales de API almacenadas en la base de datos.
    -   **Ejemplo:** Una cadena larga y aleatoria de alta entropía.
    -   **Obligatoria:** Sí (para la funcionalidad del `CredentialManager`).
    -   **Sensible:** Sí, extremadamente.
    -   **Notas:** Esta es la clave más crítica. Su gestión segura es fundamental. Podría ser ingresada por el usuario al iniciar la aplicación y mantenida en memoria, o derivada de una contraseña maestra, o (con precauciones) ser una variable de entorno en un entorno local muy controlado. **Para la v1.0 de uso personal, el usuario podría ingresarla al inicio.**

2.  **`BINANCE_API_KEY` (Solo para referencia/desarrollo inicial)**
    -   **Descripción:** Clave API para la cuenta de Binance.
    -   **Obligatoria:** No directamente como variable de entorno en el flujo final.
    -   **Sensible:** Sí.

3.  **`BINANCE_API_SECRET` (Solo para referencia/desarrollo inicial)**
    -   **Descripción:** Secreto de la API para la cuenta de Binance.
    -   **Obligatoria:** No directamente como variable de entorno en el flujo final.
    -   **Sensible:** Sí.

4.  **`TELEGRAM_BOT_TOKEN` (Solo para referencia/desarrollo inicial)**
    -   **Descripción:** Token para el Bot de Telegram usado para notificaciones.
    -   **Obligatoria:** No directamente como variable de entorno en el flujo final.
    -   **Sensible:** Sí.

5.  **`TELEGRAM_CHAT_ID` (Solo para referencia/desarrollo inicial)**
    -   **Descripción:** ID del chat de Telegram donde se enviarán las notificaciones.
    -   **Obligatoria:** No directamente como variable de entorno en el flujo final.
    -   **Sensible:** No (pero es específico del usuario).

6.  **`GEMINI_API_KEY` (Solo para referencia/desarrollo inicial)**
    -   **Descripción:** Clave API para Google Gemini.
    -   **Valor Proporcionado por Usuario (para referencia):** `AIzaSyAv6VA8VBLwWwVY5Q_hsj2iQITyJ_CvBDs`
    -   **Obligatoria:** No directamente como variable de entorno en el flujo final.
    -   **Sensible:** Sí.

7.  **`MOBULA_API_KEY` (Solo para referencia/desarrollo inicial)**
    -   **Descripción:** Clave API para Mobula.
    -   **Obligatoria:** No directamente como variable de entorno en el flujo final.
    -   **Sensible:** Sí.

---

### Variables de Entorno para Configuración del Backend (FastAPI/Uvicorn)

1.  **`FASTAPI_HOST`**
    -   **Descripción:** Host en el que se ejecutará el servidor FastAPI.
    -   **Ejemplo:** `127.0.0.1` (para acceso local únicamente, recomendado para v1.0).
    -   **Obligatoria:** No (Uvicorn usa `127.0.0.1` por defecto).
    -   **Sensible:** No.

2.  **`FASTAPI_PORT`**
    -   **Descripción:** Puerto en el que escuchará el servidor FastAPI.
    -   **Ejemplo:** `8000`.
    -   **ObligatorIA:** No (Uvicorn usa `8000` por defecto).
    -   **Sensible:** No.

3.  **`FASTAPI_RELOAD` (Solo para Desarrollo)**
    -   **Descripción:** Habilita el modo de recarga automática para Uvicorn durante el desarrollo.
    -   **Ejemplo:** `true` o `false`.
    -   **Obligatoria:** No (default `false`).
    -   **Sensible:** No.
    -   **Notas:** No usar en un entorno de "producción" (incluso si es local estable).

---

Este documento debe mantenerse actualizado a medida que se identifiquen nuevas necesidades de configuración. Un archivo `.env.example` en la raíz del proyecto debe reflejar todas estas variables (excepto las más sensibles como `CREDENTIAL_ENCRYPTION_KEY` si se gestiona de otra forma) con valores de ejemplo o placeholders.
