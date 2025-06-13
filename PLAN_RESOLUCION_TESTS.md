# Plan de Resolución de Errores y Mejoras para la Ejecución de Tests con pytest

## Contexto General
El objetivo es lograr que todos los tests definidos en la configuración `pytest.ini` se ejecuten correctamente, sin errores de importación, dependencias, ni problemas de sintaxis o configuración. Además, se busca dejar el entorno preparado para futuras migraciones y mejoras, especialmente en lo referente a Pydantic y buenas prácticas de testing.

---

## Tareas Principales y Subtareas

### 1. Diagnóstico y Documentación de Errores Actuales
- [ ] Listar todos los errores detectados en la última ejecución de `pytest`.
- [ ] Clasificar los errores por tipo (importación, dependencias, sintaxis, configuración, deprecaciones).
- [ ] Documentar advertencias relevantes (warnings) que puedan afectar el futuro del proyecto.

### 2. Solución de Errores de Importación
#### 2.1. `TradingEngineService` no encontrado
- [ ] Verificar existencia y correcta exportación de la clase/función en `src/ultibot_backend/services/trading_engine_service.py`.
- [ ] Corregir el nombre o implementar la clase si no existe.
- [ ] Revisar rutas relativas y absolutas en los imports de los tests afectados.

#### 2.2. `OpportunitySourceType` no encontrado
- [ ] Verificar definición y exportación en `src/ultibot_backend/core/domain_models/opportunity_models.py`.
- [ ] Corregir el import o implementar el tipo si es necesario.

#### 2.3. Problemas con `TradingModeStateManager` y typing
- [ ] Revisar definición e importación de `TradingModeStateManager` en `src/ultibot_ui/services/trading_mode_state.py`.
- [ ] Corregir mocks o forward references en los tests.

### 3. Solución de Problemas de Dependencias
#### 3.1. PyQt5 no instalado
- [ ] Instalar PyQt5 en el entorno virtual.
- [ ] Verificar que los imports en los tests de UI sean correctos.

### 4. Solución de Problemas de Sintaxis y Typing
- [ ] Corregir errores de forward references y uso de `Optional` con mocks.
- [ ] Revisar y corregir cualquier error de sintaxis en los archivos afectados.

### 5. Actualización y Migración de Pydantic
- [ ] Identificar todos los usos de validadores V1 (`@validator`).
- [ ] Migrar a la sintaxis de Pydantic V2 (`@field_validator`).
- [ ] Cambiar configuraciones de clase a `ConfigDict` donde sea necesario.
- [ ] Probar que la migración no rompe la funcionalidad existente.

### 6. Limpieza y Mejora de la Configuración de pytest
- [ ] Revisar y optimizar el archivo `pytest.ini`.
- [ ] Asegurar que los patrones de búsqueda de tests sean correctos.
- [ ] Documentar buenas prácticas para futuros tests.

### 7. Validación Final y Documentación
- [ ] Ejecutar todos los tests y asegurar que no haya errores ni advertencias críticas.
- [ ] Documentar los cambios realizados y los pasos para mantener el entorno saludable.
- [ ] Crear una sección de troubleshooting para problemas comunes de testing en el proyecto.

---

## Objetivo Final
- Todos los tests deben ejecutarse correctamente.
- El entorno debe estar libre de errores de importación, dependencias y sintaxis.
- El proyecto debe estar preparado para futuras migraciones y mejoras.
- La documentación debe permitir a cualquier desarrollador continuar el trabajo sin pérdida de contexto.

---

> **Nota:** Este documento debe mantenerse actualizado durante todo el proceso de resolución y puede servir como checklist para el equipo de desarrollo.
