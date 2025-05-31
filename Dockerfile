# Usa una imagen base de Python
FROM python:3.11.9-slim-bullseye

# Establece el directorio de trabajo en /app
WORKDIR /app

# Instala Poetry
RUN pip install poetry

# Copia pyproject.toml y poetry.lock (si existe) para instalar dependencias
COPY pyproject.toml poetry.lock* ./

# Instala las dependencias del proyecto
RUN poetry install --no-root --no-dev

# Copia el resto del código fuente
COPY . .

# Expone el puerto que usará FastAPI
EXPOSE 8000

# IMPORTANT: Ensure CREDENTIAL_ENCRYPTION_KEY and other necessary environment variables
# (e.g., SUPABASE_URL, SUPABASE_ANON_KEY, DATABASE_URL)
# are provided when running the container in production/staging.
# Comando para ejecutar la aplicación FastAPI
CMD ["poetry", "run", "uvicorn", "src.ultibot_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
