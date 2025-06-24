# UltiBotInversiones

Plataforma de trading personal avanzada y de alto rendimiento.

## Lanzamiento del Entorno de Desarrollo/Producción

Para lanzar la aplicación completa (Backend y Frontend) de UltiBot, se utiliza Docker Compose. Este método asegura un entorno consistente y gestiona las dependencias entre los servicios.

### Requisitos Previos

Asegúrese de tener Docker y Docker Compose instalados en su sistema.

### Pasos para el Lanzamiento

1.  **Construir y Levantar los Servicios:**
    Desde la raíz del proyecto, ejecute el siguiente comando:
    ```bash
    docker-compose up --build -d
    ```
    -   `up`: Inicia los contenedores definidos en `docker-compose.yml`.
    -   `--build`: Reconstruye las imágenes de los servicios si hay cambios en los `Dockerfile` o en el contexto de construcción.
    -   `-d`: Ejecuta los contenedores en modo "detached" (en segundo plano).

    Este comando:
    -   Construirá las imágenes de Docker para el backend y el frontend.
    -   Inicializará la base de datos PostgreSQL.
    -   Esperará a que la base de datos esté saludable.
    -   Lanzará el servicio del backend y esperará a que su API esté disponible.
    -   Finalmente, lanzará el servicio del frontend.

2.  **Acceder a la Interfaz de Usuario (UI):**
    El frontend de UltiBot se ejecuta dentro de un contenedor Docker con acceso VNC.
    -   **VNC Client:** Conéctese a `localhost:5900` usando su cliente VNC preferido.
    -   **Contraseña VNC:** La contraseña por defecto es `1234` (puede configurarse en el archivo `.env`).

### Detener los Servicios

Para detener todos los servicios y eliminar los contenedores, ejecute:
```bash
docker-compose down
```

### Acceso a Logs

Los logs de los servicios del backend y frontend se montan en el directorio `./logs` de la raíz del proyecto. Puede consultarlos directamente allí.

### Notas Importantes

-   El script `run_frontend_with_backend.bat` ha sido declarado obsoleto. Por favor, utilice Docker Compose para todas las operaciones de lanzamiento.
-   Asegúrese de que el archivo `.env` en la raíz del proyecto esté configurado correctamente con las variables de entorno necesarias, como `CREDENTIAL_ENCRYPTION_KEY` y `VNC_PASSWORD`.
