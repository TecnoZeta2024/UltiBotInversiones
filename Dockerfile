# Usa una imagen base de Python
FROM python:3.11.9-slim-bullseye

# Establece el directorio de trabajo en /app
WORKDIR /app

# Instala curl, dependencias de sistema para pytest-qt y otras utilidades, luego Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates libglib2.0-0 libgl1-mesa-glx libegl1-mesa libfontconfig1 libxkbcommon0 libdbus-1-3 && \
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

# Copia todo el código fuente
COPY src /app/src
COPY tests /app/tests

# Copia el certificado de Supabase
COPY supabase /app/supabase

# Expone el puerto que usará FastAPI
EXPOSE 8000

# Variables de entorno predeterminadas (se deben sobrescribir en producción)
# Se añade /app/src a PYTHONPATH para que los módulos sean importables directamente
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

# IMPORTANT: Ensure CREDENTIAL_ENCRYPTION_KEY and other necessary environment variables
# (e.g., SUPABASE_URL, SUPABASE_ANON_KEY, DATABASE_URL)
# are provided when running the container in production/staging.

# Comando para ejecutar la aplicación FastAPI
# Con el nuevo PYTHONPATH, se llama directamente al módulo
CMD ["uvicorn", "ultibot_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
