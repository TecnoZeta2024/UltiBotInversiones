# 🚀 UltiBot - Guía de Deployment

## Prerrequisitos

### Requerimientos del Sistema
- **Python:** 3.11.9
- **Poetry:** Instalado y disponible en PATH
- **Sistema Operativo:** Windows (scripts batch optimizados)

### Verificación Inicial
```bash
# Verificar Python
python --version

# Verificar Poetry
poetry --version

# Verificar directorio del proyecto
dir pyproject.toml
```

## 📁 Estructura de Deployment

```
UltiBotInversiones/
├── run_ultibot.bat          # ✅ Script principal (CORREGIDO)
├── run_ultibot_dev.bat      # ✅ Script desarrollo rápido (NUEVO)
├── pyproject.toml           # Configuración Poetry
├── src/
│   ├── ultibot_backend/     # Backend FastAPI
│   ├── ultibot_ui/          # Frontend PyQt5
│   └── shared/              # Módulos compartidos
└── logs/                    # ✅ Logs automáticos (creado al ejecutar)
```

## 🎯 Opciones de Deployment

### Opción 1: Deployment Completo (Recomendado)
**Script:** `run_ultibot.bat`

#### Características:
- ✅ Validación completa de prerrequisitos
- ✅ Verificación automática de dependencias
- ✅ Manejo robusto de errores
- ✅ Logging automático
- ✅ Información detallada de estado

#### Uso:
```cmd
# Desde el directorio raíz del proyecto
.\run_ultibot.bat
```

#### Lo que hace:
1. Verifica estructura del proyecto
2. Confirma instalación de Poetry
3. Valida dependencias (`poetry check`)
4. Auto-instala dependencias si es necesario
5. Crea directorio `logs/`
6. Inicia Backend: `poetry run uvicorn src.ultibot_backend.main:app --reload --host 127.0.0.1 --port 8000`
7. Inicia Frontend: `poetry run python src/ultibot_ui/main.py`

### Opción 2: Desarrollo Rápido
**Script:** `run_ultibot_dev.bat`

#### Características:
- ⚡ Inicio rápido sin validaciones extensas
- 🔧 Ideal para desarrollo cuando ya sabes que todo funciona
- 📝 Mínimo output, máxima velocidad

#### Uso:
```cmd
# Desde el directorio raíz del proyecto
.\run_ultibot_dev.bat
```

## 🔧 Solución de Problemas

### Error: "Poetry no está instalado"
```bash
# Instalar Poetry
curl -sSL https://install.python-poetry.org | python3 -
# O usar pip
pip install poetry
```

### Error: "No se encontró pyproject.toml"
- Ejecuta el script desde el directorio raíz del proyecto UltiBotInversiones
- Verifica que el archivo `pyproject.toml` existe

### Error: "Falló la instalación de dependencias"
```bash
# Limpiar caché y reinstalar
poetry cache clear pypi --all
poetry install
```

### Problemas de Puerto
- Backend usa puerto 8000 por defecto
- Verifica que no hay otros servicios ejecutándose en ese puerto
- Cierra otros procesos: `netstat -ano | findstr :8000`

## 📊 Servicios y URLs

### Backend (FastAPI)
- **URL Principal:** http://127.0.0.1:8000
- **Documentación API:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/health
- **OpenAPI Schema:** http://127.0.0.1:8000/openapi.json

### Frontend (PyQt5)
- **Interfaz:** Aplicación de escritorio independiente
- **Logs:** Disponibles en `logs/frontend.log`

## 📝 Logs y Monitoreo

### Ubicación de Logs
```
logs/
├── backend.log      # Logs del servidor FastAPI
└── frontend.log     # Logs de la aplicación PyQt5
```

### Monitoreo en Tiempo Real
```bash
# Ver logs del backend
tail -f logs/backend.log

# Ver logs del frontend  
tail -f logs/frontend.log
```

## 🛑 Detener Servicios

### Método Recomendado
1. Cierra las ventanas de terminal que aparecieron
2. O presiona `Ctrl+C` en cada terminal

### Método Alternativo
```bash
# Encontrar procesos
tasklist | findstr python
tasklist | findstr uvicorn

# Terminar procesos por PID
taskkill /PID <PID_NUMBER> /F
```

## ⚠️ Notas Importantes

1. **Directorio de Trabajo:** Siempre ejecuta desde la raíz del proyecto
2. **Poetry Environment:** Los scripts manejan automáticamente el entorno virtual
3. **Primera Ejecución:** Puede tardar más debido a la instalación de dependencias
4. **Desarrollo:** Usa `run_ultibot_dev.bat` para iteraciones rápidas
5. **Producción:** Usa `run_ultibot.bat` para deployment completo con validaciones

## 🎯 Scripts Corregidos - Changelog

### Problemas Resueltos en `run_ultibot.bat`:
- ❌ **Backend sin Poetry** → ✅ `poetry run uvicorn` implementado
- ❌ **Falta verificación directorio** → ✅ Validación completa
- ❌ **Sin manejo de errores** → ✅ Validaciones robustas
- ❌ **Inconsistencia Poetry** → ✅ Uso consistente
- ❌ **Sin verificación dependencias** → ✅ Auto-check y install

### Mejoras Añadidas:
- ✅ Logging automático en directorio `logs/`
- ✅ Host y puerto explícitos para FastAPI
- ✅ Mensajes informativos y de estado
- ✅ Script adicional para desarrollo rápido
- ✅ Documentación completa de deployment