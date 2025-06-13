# 🧪 Suite de Pruebas UltiBot

Esta carpeta contiene scripts especializados para probar todos los componentes del sistema UltiBot de manera sistemática y completa.

## 📋 Índice de Scripts

### 🚀 Script Principal
- **`run_quick_tests.bat`** - Script batch para Windows que ejecuta todas las pruebas en secuencia

### 🔍 Scripts de Pruebas Específicas
- **`test_environment_setup.py`** - Verifica que el entorno de desarrollo esté configurado correctamente
- **`test_backend_components.py`** - Prueba todos los componentes del backend
- **`test_frontend_components.py`** - Prueba todos los componentes del frontend/UI
- **`test_database_connection.py`** - Prueba conexiones y funcionalidad de base de datos
- **`test_api_endpoints.py`** - Prueba endpoints de la API REST
- **`run_all_tests.py`** - Script maestro que ejecuta todas las validaciones

## 🎯 Uso Rápido

### Para Windows:
```bash
# Ejecutar todas las pruebas de una vez
.\test\run_quick_tests.bat

# O ejecutar el script de verificación del entorno primero
python test\test_environment_setup.py
```

### Para Linux/Mac:
```bash
# Ejecutar script de verificación del entorno
python test/test_environment_setup.py

# Ejecutar pruebas individuales
python test/test_backend_components.py
python test/test_frontend_components.py
python test/test_database_connection.py
python test/test_api_endpoints.py

# Ejecutar suite completa
python test/run_all_tests.py
```

## 📊 Descripción Detallada de Scripts

### 1. 🏗️ `test_environment_setup.py`
**Propósito:** Verificar que el entorno de desarrollo esté listo para trabajar.

**Verifica:**
- ✅ Versión de Python (3.11+)
- ✅ Instalación de Poetry
- ✅ Estructura del proyecto
- ✅ Archivos de configuración (.env, .env.example)
- ✅ Dependencias críticas
- ✅ Dependencias opcionales
- ✅ Repositorio Git
- ✅ Directorio de logs y permisos

**Cuándo usar:** Antes de empezar a trabajar en el proyecto o después de clonar el repositorio.

### 2. ⚙️ `test_backend_components.py`
**Propósito:** Validar que todos los componentes del backend se puedan importar y funcionen.

**Verifica:**
- ✅ Imports del backend (main, config, core)
- ✅ Servicios (MarketData, Strategy, Portfolio, etc.)
- ✅ Adaptadores (Binance, Mobula, Telegram)
- ✅ Endpoints de la API

**Cuándo usar:** Después de cambios en el backend o para verificar integridad del código.

### 3. 🖥️ `test_frontend_components.py`
**Propósito:** Validar componentes de la interfaz de usuario.

**Verifica:**
- ✅ Disponibilidad de Qt (PyQt5/6, PySide2/6)
- ✅ Imports del frontend
- ✅ Ventanas principales
- ✅ Widgets personalizados
- ✅ Diálogos
- ✅ Servicios de UI
- ✅ Vistas

**Cuándo usar:** Después de cambios en la UI o para verificar dependencias gráficas.

### 4. 🗄️ `test_database_connection.py`
**Propósito:** Validar conectividad y configuración de base de datos.

**Verifica:**
- ✅ Imports de librerías de BD (asyncpg, psycopg, supabase)
- ✅ Variables de entorno de BD
- ✅ Conexión con asyncpg
- ✅ Conexión con Supabase
- ✅ Servicio de persistencia
- ✅ Scripts de BD

**Cuándo usar:** Para verificar configuración de BD o solucionar problemas de conexión.

### 5. 🌐 `test_api_endpoints.py`
**Propósito:** Validar API REST y endpoints.

**Verifica:**
- ✅ Imports de FastAPI
- ✅ Modelos de la API
- ✅ Imports de endpoints
- ✅ API mock funcional
- ✅ Aplicación principal
- ✅ TestClient
- ✅ Configuración de app
- ✅ Dependencias

**Cuándo usar:** Para verificar que la API REST esté funcionando correctamente.

### 6. 🎮 `run_all_tests.py`
**Propósito:** Script maestro que ejecuta todas las validaciones y genera reporte completo.

**Características:**
- ✅ Ejecuta todas las pruebas de componentes
- ✅ Incluye pruebas de pytest si están disponibles
- ✅ Genera reporte JSON con resultados
- ✅ Logging con timestamps
- ✅ Códigos de salida apropiados

**Cuándo usar:** Para validación completa del sistema o antes de despliegue.

### 7. 🚀 `run_quick_tests.bat`
**Propósito:** Script batch para Windows que automatiza la ejecución de todas las pruebas.

**Características:**
- ✅ Ejecuta pruebas en secuencia lógica
- ✅ Se detiene en el primer error
- ✅ Muestra progreso visual
- ✅ Pausa al final para revisar resultados

**Cuándo usar:** Método más fácil para ejecutar todas las pruebas en Windows.

## 📝 Interpretación de Resultados

### ✅ Símbolos de Estado
- ✅ **Verde:** Prueba exitosa
- ❌ **Rojo:** Prueba falló - requiere atención
- ⚠️ **Amarillo:** Advertencia - no crítico pero recomendado

### 📊 Reportes
Los scripts generan reportes detallados que incluyen:
- Total de pruebas ejecutadas
- Número de pruebas exitosas/fallidas
- Tiempo de ejecución
- Detalles específicos de cada error
- Recomendaciones de acción

### 📄 Archivos de Salida
- `test/test_report.json` - Reporte detallado en formato JSON
- Logs en pantalla con timestamps para debugging

## 🔧 Solución de Problemas Comunes

### ❌ "Module not found" Errors
**Solución:**
```bash
# Instalar dependencias
poetry install

# Verificar que estás en el directorio raíz del proyecto
cd /ruta/a/UltiBotInversiones
```

### ❌ Errores de Base de Datos
**Solución:**
1. Verificar que `.env` existe y tiene las variables correctas
2. Verificar conectividad de red
3. Verificar credenciales de Supabase

### ❌ Errores de Qt/UI
**Solución:**
```bash
# Instalar dependencias de Qt
poetry add PyQt5
# o
poetry add PySide6
```

### ❌ Errores de Poetry
**Solución:**
```bash
# Reinstalar dependencias
poetry env remove --all
poetry install
```

## 🎯 Flujo de Trabajo Recomendado

1. **Primera vez:**
   ```bash
   python test/test_environment_setup.py
   ```

2. **Durante desarrollo:**
   ```bash
   # Después de cambios en backend
   python test/test_backend_components.py
   
   # Después de cambios en frontend
   python test/test_frontend_components.py
   ```

3. **Antes de commit:**
   ```bash
   .\test\run_quick_tests.bat
   ```

4. **Antes de despliegue:**
   ```bash
   python test/run_all_tests.py
   ```

## 📚 Información Adicional

### Requisitos del Sistema
- Python 3.11+
- Poetry
- Variables de entorno configuradas
- Acceso a internet (para pruebas de BD)

### Dependencias Verificadas
- **Críticas:** FastAPI, Pydantic, asyncpg, Supabase, pytest
- **Opcionales:** PyQt5/6, PySide2/6, matplotlib, pandas

### Contribuir
Para añadir nuevas pruebas:
1. Crear script específico en `test/`
2. Seguir el patrón de naming: `test_[componente].py`
3. Actualizar `run_all_tests.py` y `run_quick_tests.bat`
4. Documentar en este README

---

**💡 Tip:** Ejecuta `python test/test_environment_setup.py` si es tu primera vez trabajando con este proyecto para asegurar que todo esté configurado correctamente.
