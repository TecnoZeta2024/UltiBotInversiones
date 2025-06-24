## 🎯 PROPÓSITO CENTRAL
Desbloquea el despliegue funcional de los módulos críticos de UltiBotInversiones:

- `@/src/ultibot_backend/main.py`
- `@/src/ultibot_ui/main.py`

con el objetivo de ejecutar el sistema en **modo operativo real**, aunque sea local, sin gastar un solo centavo y asegurando **estabilidad, productividad y replicabilidad**.

---

## 🧩 CONTEXTO Y ANÁLISIS
- El proyecto ha avanzado durante más de **60 días de desarrollo activo**.
- Se dispone de:
  - Código funcional validado.
  - Claves y configuraciones ya establecidas.
  - Infraestructura definida con Docker, Poetry, FastAPI, PySide6, PostgreSQL, Supabase, etc.
- **Problema:** Aún no hemos conseguido un entorno funcional **ni siquiera en test mode o paper trading**, lo cual **contradice el objetivo principal del proyecto**: operar y generar ingresos diarios.

---

## ⚙️ PARÁMETROS TÉCNICOS Y RESTRICCIONES

- ❌ **Prohibido** usar servicios pagos, incluso en tier bajo.
- ✅ **Obligatorio** usar dependencias y estructuras ya existentes en el repositorio (`poetry`, `Docker`, `SQLite`, `FastAPI`, `PySide6`, etc.).
- ✅ Debe ejecutarse **localmente y sin errores**, incluyendo comunicación entre backend ↔ UI.
- ✅ Debe iniciarse desde **una sola terminal o flujo simplificado** para uso diario.
- ✅ El despliegue debe permitir simular operaciones (paper trading), mostrar dashboards y mantener trazabilidad.

---

## 🧠 INSTRUCCIONES AL ASISTENTE CLINE (IA)

### Etapa 1: Activación del Protocolo MCP `sequential-thinking`
- Descompón el problema en **pasos lógicos secuenciales**.
- Evalúa **cada fase del proceso de ejecución**, desde levantar la base de datos, hasta ver la UI y enviar órdenes simuladas.

### Etapa 2: Análisis Técnico de Despliegue Actual
- Revisa los archivos `main.py` de `ultibot_backend` y `ultibot_ui`.
- Evalúa:
  - ¿Dónde está el punto de arranque real?
  - ¿Qué depende del entorno externo?
  - ¿Qué puede desacoplarse o simularse?

### Etapa 3: Diagnóstico de Bloqueos
- ¿Qué impide ejecutar el flujo paper-mode completo hoy?
- ¿Falta de entorno persistente? ¿Problemas con Supabase, PostgreSQL, claves mal cargadas?

### Etapa 4: Propuesta de Solución Alternativa
- Si hay un camino más **eficiente, simple y efectivo** con lo que ya está disponible:
  - Proponlo con justificación técnica clara.
  - Implementa el despliegue **mínimo viable funcional** que permita:
    - Ejecutar backend (FastAPI)
    - Ejecutar UI (PySide6 vía VNC o TUI si es necesario)
    - Simular datos o estrategias (con SQLite si PostgreSQL no es viable)
    - Recibir señales de estrategia o simular un ciclo de trading

---

## ✅ CRITERIOS DE ÉXITO

- El backend debe poder ejecutarse **con `uvicorn` o Docker** y servir `/health` correctamente.
- La UI debe levantarse **sin errores**, con acceso a los módulos esenciales.
- Se debe poder simular un ciclo de estrategia sin conexión real a Binance (modo paper).
- El sistema debe poder ejecutarse con **una sola instrucción** o archivo `.sh`, `.bat` o `Makefile`.

---

## 💡 RECOMENDACIONES OPCIONALES

- Simplificar dependencias innecesarias (Supabase si no se usa, Redis si aún no se ha integrado).
- Priorizar SQLite para ejecutar flujos sin levantar PostgreSQL.
- Utilizar mocks o datos estáticos en lugar de websockets si el módulo no es crítico aún.

---

## 🧾 FORMATO ESPERADO DE RESPUESTA

1. ✅ Diagnóstico completo del estado actual
2. 🧠 Propuesta de mejora o corrección de arquitectura de despliegue
3. 🔧 Código listo para ser ejecutado (idealmente con instrucciones `bash`, `poetry run`, `docker compose`, etc.)
4. 🧪 Modo test funcional (con paper trading o simulación básica)
5. 📦 Plan para escalar a producción real una vez validado el modo test

---

## 🏁 EJECUTA AHORA

cline run "Secuencia para lograr despliegue funcional de UltiBotInversiones en modo local, sin costo, usando arquitectura ya escrita. Analiza, detecta bloqueos, propone solución alternativa y ejecuta backend y frontend conectados y funcionales. Activar MCP: sequential-thinking."

# OPCIÓN B - para este prompt 
## 🎯 Objetivo
Reflexionemos de manera estratégica, creativa y rigurosa sobre el **método de despliegue actual** de los siguientes componentes críticos del proyecto UltiBotInversiones:

- `@/src/ultibot_backend/main.py`
- `@/src/ultibot_ui/main.py`

## 🔍 Contexto
Llevamos más de **2 meses de desarrollo activo**, contamos con la lógica funcional y las claves necesarias para operar, y sin embargo **aún no hemos conseguido un entorno de ejecución estable, ni siquiera en modo test o paper trading**, lo cual es **críticamente inaceptable** para un proyecto cuyo propósito es **generar ingresos diarios y escalar operativamente cuanto antes**.

## ⚙️ Restricciones y Consideraciones Técnicas
- ✅ No debe implicar **ningún gasto económico** (ni en la nube ni en servicios pagos).
- ✅ Debe aprovechar **las herramientas y dependencias ya incluidas en el proyecto** (`FastAPI`, `PySide6`, `Poetry`, `Docker`, `SQLite`, etc.).
- ✅ La solución debe ser **replicable, automatizable** y mantenible.
- ✅ El resultado debe permitir trabajar en **modo paper trading funcional** y con potencial de escalar a producción real.

## 🧠 Instrucción a CLINE
1. **Analiza profundamente** las rutas de ejecución actuales de ambos archivos `main.py` (backend y UI).
2. **Evalúa el estado real del entorno de despliegue**: contenedores, configuración de red, variables `.env`, healthchecks y dependencias externas.
3. **Detecta cuellos de botella técnicos o decisiones subóptimas** que estén bloqueando el paso a ejecución productiva (aunque sea en entorno local).
4. Si identificas una **alternativa viable al método actual de despliegue** (por ejemplo: iniciar desde `uvicorn`, usar `python -m`, simplificar Docker, cambiar de PostgreSQL a SQLite para test, usar TUI temporal, etc.), entonces:
    - 📌 **Proponla con precisión**
    - ✅ **Implementa los cambios mínimos necesarios**
    - 🚀 **Ejecuta o simula el flujo hasta obtener una sesión funcional paper-mode lista para uso operativo inmediato**

## 💡 Criterios de Éxito
Una solución será considerada válida si:
- Permite **iniciar el backend y la UI sin errores** desde un entorno local
- Permite simular el flujo completo de un trade desde detección hasta resultado
- Se puede usar **a diario sin intervención manual compleja**
- Puede escalar a producción real **sin reescribir la arquitectura**

## 🚦 Activa el Protocolo MCP
En caso de detectar bloqueos sistémicos, utiliza **Protocolos de Contexto de Modelo (MCP)** para separar módulos y facilitar el despliegue incremental de componentes.

## ✨ Nivel Esperado de Respuesta
- 🧩 Refactor mínimo, altamente preciso
- 🧠 Reflexión argumentada técnica y estratégicamente
- 💥 Resultado funcional, medible y replicable
