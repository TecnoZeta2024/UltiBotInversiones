# Usa una imagen base de Python
FROM python:3.11.9-slim-bullseye

# Establece el directorio de trabajo en /app
WORKDIR /app

# Instala curl y otras utilidades básicas, luego Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    pip install poetry && \
    poetry config virtualenvs.create false

# Crea el directorio de logs
RUN mkdir -p /app/logs && \
    chmod 777 /app/logs

# Copia pyproject.toml y poetry.lock (si existe) para instalar dependencias
COPY pyproject.toml poetry.lock* ./

# Instala solo las dependencias necesarias para el backend
# Excluimos dependencias de desarrollo y UI
RUN poetry install --no-root --no-interaction \
    && rm -rf /root/.cache/pypoetry

# Copia el código fuente - solo lo necesario para el backend
COPY src/ultibot_backend /app/src/ultibot_backend
COPY src/shared /app/src/shared
COPY src/__init__.py /app/src/__init__.py

# Copia el certificado de Supabase
COPY supabase /app/supabase

# Expone el puerto que usará FastAPI
EXPOSE 8000

# Variables de entorno predeterminadas (se deben sobrescribir en producción)
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# IMPORTANT: Ensure CREDENTIAL_ENCRYPTION_KEY and other necessary environment variables
# (e.g., SUPABASE_URL, SUPABASE_ANON_KEY, DATABASE_URL)
# are provided when running the container in production/staging.

# Comando para ejecutar la aplicación FastAPI
CMD ["uvicorn", "src.ultibot_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
