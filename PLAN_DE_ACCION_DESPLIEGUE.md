# Plan de Acción Crítico: Estabilización y Mejora del Despliegue

**Fecha:** 2025-06-22
**Autor:** Cline, CTO
**Estado:** INICIADO

## 1. Análisis de la Situación (Diagnóstico)

Se ha detectado un error crítico en producción que impide la carga del estado del portafolio.

- **Síntoma Inmediato:** La UI (frontend) falla con el error `AttributeError: 'UltiBotAPIClient' object has no attribute 'get_real_trading_mode_status'`. Esto indica una ruptura en el contrato de la API entre el frontend y el backend.
- **Causa Raíz Sistémica:** El método de despliegue actual, basado en el script `run_frontend_with_backend.bat`, es inherentemente frágil. Carece de mecanismos de control de dependencias, verificación de estado (health checks) y gestión de procesos, lo que lo hace inadecuado para cualquier entorno que no sea el de desarrollo local aislado. Este script permite que inconsistencias entre componentes (frontend/backend) pasen desapercibidas hasta la ejecución.

## 2. Estrategia de Resolución

Se aplicará una estrategia de dos fases para garantizar una recuperación rápida y una estabilidad a largo plazo.

- **Fase 1: Contención y Corrección Inmediata (Hotfix)**
  - **Objetivo:** Restaurar la funcionalidad básica de la aplicación lo más rápido posible.
  - **Prioridad:** CRÍTICA.

- **Fase 2: Refactorización del Despliegue (Solución Estratégica)**
  - **Objetivo:** Implementar un proceso de despliegue robusto, predecible y resiliente.
  - **Prioridad:** ALTA.

---

## 3. Fase 1: Plan de Ejecución del Hotfix

**Objetivo:** Corregir la llamada a la API rota.

1.  **Identificar la llamada incorrecta en el Frontend:**
    - **Acción:** Inspeccionar el archivo `src/ultibot_ui/workers.py`.
    - **Tarea:** Localizar la línea de código que invoca `get_real_trading_mode_status()` en el cliente de la API.

2.  **Identificar el endpoint correcto en el Backend:**
    - **Acción:** Analizar los archivos de rutas en `src/ultibot_backend/api/v1/`.
    - **Tarea:** Encontrar la definición del endpoint que realmente gestiona y devuelve el estado del modo de trading (ej. `paper_trading`, `real_trading`). El nombre correcto probablemente sea `get_trading_mode` o una variante.

3.  **Aplicar la Corrección:**
    - **Acción:** Modificar la llamada en `src/ultibot_ui/workers.py`.
    - **Tarea:** Reemplazar `get_real_trading_mode_status` por el nombre del método correcto identificado en el paso anterior.

4.  **Validación Rápida:**
    - **Acción:** Ejecutar la aplicación en un entorno controlado.
    - **Tarea:** Verificar que el error ya no aparece y que el estado del portafolio se carga correctamente.

---

## 4. Fase 2: Plan de Ejecución de la Solución Estratégica

**Objetivo:** Reemplazar `run_frontend_with_backend.bat` con una orquestación de contenedores robusta.

1.  **Configurar Docker Compose para Producción:**
    - **Acción:** Revisar y adaptar `docker-compose.yml` y los `Dockerfile` existentes.
    - **Tareas:**
        - Asegurar que el backend (`ultibot-backend`) y el frontend (`ultibot-frontend`) estén definidos como servicios separados.
        - Configurar la red para que ambos contenedores puedan comunicarse.
        - Mapear los volúmenes necesarios para logs y configuraciones si es preciso.

2.  **Implementar Verificaciones de Estado (Health Checks):**
    - **Acción:** Añadir un endpoint de salud en el backend y configurarlo en Docker Compose.
    - **Tareas:**
        - Crear una ruta simple en el backend, como `/api/v1/health`, que devuelva un `200 OK`.
        - Añadir una sección `healthcheck` al servicio del backend en `docker-compose.yml` que consulte este endpoint.
        - Configurar el servicio del frontend con `depends_on` para que espere a que el backend esté en estado `healthy` antes de arrancar.

3.  **Centralizar y Simplificar el Lanzamiento:**
    - **Acción:** Reemplazar el script `.bat` por un único comando.
    - **Tareas:**
        - Declarar obsoleto el archivo `run_frontend_with_backend.bat`.
        - Establecer `docker-compose up --build -d` como el comando estándar para lanzar el entorno completo. El flag `-d` lo ejecutará en segundo plano.

4.  **Documentar el Nuevo Proceso:**
    - **Acción:** Actualizar el `README.md` del proyecto.
    - **Tarea:** Añadir una sección "Despliegue" que explique claramente cómo levantar el entorno utilizando Docker Compose.

## 5. Criterios de Éxito

- **Hotfix:** La aplicación es funcional y el error `AttributeError` ha sido eliminado.
- **Solución Estratégica:** El entorno de producción se lanza de manera consistente y fiable con un solo comando (`docker-compose up`). Los fallos de un componente no causan un fallo en cascada no controlado del otro.
