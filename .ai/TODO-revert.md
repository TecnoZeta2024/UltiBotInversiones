# Debugging Log & Resolved Issues

## Story/Task: Solución de problemas de conexión a Supabase (test_persistence_connection.py y test_persistence.py)
- **Date Resolved:** 2025-05-30
- **Status:** Resolved
- **Issue:** Múltiples errores de conexión a la base de datos Supabase, incluyendo fallos de autenticación (`'NoneType' object has no attribute 'group'`, `Wrong password`) y problemas con el bucle de eventos de asyncio en Windows (`ProactorEventLoop`).
- **Resolution Steps:**
    1.  **Intentos iniciales con `asyncpg`:**
        -   Se añadió configuración SSL explícita (`sslmode=verify-full`, `sslrootcert`).
        -   Se intentó decodificar la contraseña (`unquote`).
        -   Se probó con Transaction Pooler (puerto 6543) y Session Pooler (puerto 5432).
        -   Se intentó conexión directa a la BD (falló por DNS).
        -   Se intentó pasar DSN completo y `server_settings` explícitos.
        -   Ninguno de estos pasos resolvió el error de autenticación persistente con `asyncpg`.
    2.  **Cambio a `psycopg`:**
        -   Se añadió `psycopg[binary,pool]` como dependencia del proyecto.
        -   Se refactorizó `src/ultibot_backend/adapters/persistence_service.py` para usar `psycopg` en lugar de `asyncpg`.
            -   Se ajustó la lógica de conexión para usar el DSN de `DATABASE_URL` y parámetros SSL (`sslmode='verify-full'`, `sslrootcert='supabase/prod-ca-2021.crt'`).
            -   Se configuró `row_factory=dict_row` en los cursores para obtener resultados como diccionarios.
            -   Se adaptó la sintaxis de las consultas y el manejo de parámetros (de `$1` a `%s`).
    3.  **Ajustes en Scripts de Prueba:**
        -   Se añadió `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())` al inicio de `test_persistence_connection.py` y `test_persistence.py` para compatibilidad con Windows.
        -   Se corrigió el uso de `fetchone()` y la creación de cursores en los scripts de prueba para alinearlos con `psycopg`.
        -   Se corrigieron los nombres de las variables de configuración accedidas desde `settings` en `test_persistence.py`.
    4.  **Resolución de Contraseña:**
        -   Se actualizó la contraseña de la base de datos Supabase a una sin caracteres especiales.
        -   Se actualizó la `DATABASE_URL` en el archivo `.env` con la nueva contraseña (sin codificación URL, ya que `psycopg` la maneja).
        -   Se modificó `SupabasePersistenceService` para leer la `DATABASE_URL` directamente de `os.environ` en el método `connect` para asegurar que se usa el valor más reciente.
- **Outcome:** Ambos scripts de prueba (`test_persistence_connection.py` y `test_persistence.py`) ahora se ejecutan exitosamente, confirmando la conexión y las operaciones CRUD básicas con la base de datos Supabase.
- **Files Modified:**
    - `src/ultibot_backend/adapters/persistence_service.py` (Refactorizado a psycopg)
    - `test_persistence_connection.py` (Actualizado para psycopg y política de bucle de eventos)
    - `test_persistence.py` (Actualizado para psycopg, política de bucle de eventos y nombres de settings)
    - `.env` (Actualizada DATABASE_URL con nueva contraseña y formato)
    - `pyproject.toml` (Añadida dependencia `psycopg`)

---
