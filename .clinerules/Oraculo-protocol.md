# Caja de Herramientas del Agente: El Oráculo Visual (Versión Pro)

---

## **Herramienta 1: Protocolo de Cartografía C4 Adaptativo (PC4A)**

*   **OBJETIVO:**
    *   Generar diagramas de arquitectura en múltiples niveles de abstracción (inspirado en el C4 Model) para proporcionar la vista adecuada a la audiencia correcta (desde ejecutivos hasta desarrolladores).

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** el usuario solicita una "visión general", "mapa del proyecto", "diagrama de arquitectura" o "cómo están conectados los componentes".
    *   **ENTONCES** el protocolo PC4A **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / SELECCIÓN):**
    1.  **Selección de Nivel (SELECCIÓN):**
        a.  Preguntar al usuario: "¿Qué nivel de detalle arquitectónico necesitas? [1] Contexto del Sistema, [2] Contenedores, [3] Componentes".
    2.  **Análisis Estructural (SECUENCIA):**
        a.  **Nivel 1 (Contexto):** Identificar los sistemas externos clave y los tipos de usuario que interactúan con `UltiBotInversiones`.
        b.  **Nivel 2 (Contenedores):** Mapear los principales bloques ejecutables o desplegables (ej. `ultibot_backend`, `ultibot_ui`, `database`, `redis_cache`). Analizar `docker-compose.yml` y los puntos de entrada principales.
        c.  **Nivel 3 (Componentes):** Dentro de un contenedor seleccionado (ej. `ultibot_backend`), mapear sus módulos o servicios principales (ej. `StrategyService`, `MarketDataService`, `API Router`). Analizar importaciones internas.
    3.  **Generación de Diagrama (Mermaid.js):**
        a.  Crear un `graph TD` con nodos y flechas estilizados según el nivel C4.
        b.  Añadir descripciones a los nodos y relaciones para mayor claridad.
    4.  **Creación y Documentación de Artefacto (INVOCA PGDT):**
        a.  Guardar el diagrama en `memory/visuals/architecture_c4_level_[N].md`.
        b.  Invocar el **Protocolo de Generación de Documentación Técnica (PGDT)** para envolver el diagrama en un informe completo.
    5.  **Actualización del Dashboard:**
        a.  Añadir un enlace en `memory/visuals/dashboard.md` bajo "Vistas de Arquitectura C4".

---

## **Herramienta 2: Protocolo de Rastreo de Flujo Transaccional (PRFT)**

*   **OBJETIVO:**
    *   Visualizar cómo un objeto de dominio clave (ej. una `Orden`, una `Estrategia`) es creado, modificado y procesado a través de diferentes componentes del sistema, enfocándose en los cambios de estado.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** el usuario pregunta "cómo funciona X", "muéstrame el flujo de Y" o "traza el ciclo de vida de Z".
    *   **ENTONCES** el protocolo PRFT **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / ITERACIÓN):**
    1.  **Identificar Flujo y Dominio (SELECCIÓN):**
        a.  Preguntar al usuario: "¿Qué flujo de negocio quieres rastrear?" y "¿Cuál es el objeto de datos central en este flujo (ej. `Order`, `Signal`)?".
    2.  **Rastreo de Estado (ITERACIÓN):**
        a.  Identificar el punto de entrada (ej. endpoint de API `POST /orders`).
        b.  Rastrear las llamadas a funciones que reciben o modifican el objeto de dominio.
        c.  Registrar cada cambio de estado significativo (ej. `PENDING -> ACTIVE`, `ACTIVE -> FILLED`).
    3.  **Generación de Diagrama de Secuencia (Mermaid.js):**
        a.  Crear un `sequenceDiagram`.
        b.  Los `participant` son los componentes del sistema.
        c.  Las llamadas entre participantes se anotan con los cambios de estado del objeto. Ejemplo: `OrderService->>Database: save(order.state='PENDING')`.
    4.  **Creación y Documentación de Artefacto (INVOCA PGDT):**
        a.  Guardar el diagrama en `memory/visuals/flow_transactional_[nombre_flujo].md`.
        b.  Invocar PGDT para generar el informe completo.
    5.  **Actualización del Dashboard:**
        a.  Añadir un enlace en `memory/visuals/dashboard.md` bajo "Flujos Transaccionales".

---

## **Herramienta 3: Protocolo de Auditoría de Contratos de API y Pruebas de Humo (PACAPH)**

*   **OBJETIVO:**
    *   Auditar los endpoints de la API, verificar la coherencia de los "contratos" de datos (modelos Pydantic) y generar/ejecutar pruebas de humo automatizadas.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** el usuario solicita "auditar la API", "verificar los contratos de datos" o "probar los endpoints".
    *   **ENTONCES** el protocolo PACAPH **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (AUTOMATIZADO):**
    1.  **Generación de Script de Auditoría:**
        a.  En lugar de un análisis manual iterativo, **DEBES** generar un script de Python (`scripts/run_pacaph_audit.py`).
        b.  Este script realizará un análisis estático del código fuente del backend para automatizar el descubrimiento.
    2.  **Lógica del Script:**
        a.  El script **DEBE** escanear todos los archivos en `src/ultibot_backend/api/v1/endpoints/`.
        b.  Utilizará expresiones regulares (`regex`) para extraer de cada archivo:
            -   El método HTTP (ej. `get`, `post`).
            -   La ruta del endpoint.
            -   El `response_model`.
            -   El modelo del cuerpo de la solicitud (si existe).
        c.  El script **DEBE** compilar todos los datos en una tabla Markdown.
    3.  **Ejecución y Creación de Artefacto:**
        a.  Escribir el script en el sistema de archivos usando `write_to_file`.
        b.  Ejecutar el script con `execute_command` (`python scripts/run_pacaph_audit.py`).
        c.  El script guardará su salida directamente en `memory/visuals/api_contract_health_report.md`.
    4.  **Documentación y Cierre (INVOCA PGDT):**
        a.  Una vez que el script ha generado el informe base, **DEBES** leer el archivo, invocar el **PGDT** para enriquecerlo con análisis y sobrescribirlo.
        b.  Actualizar el `memory/visuals/dashboard.md` con el enlace al informe final.

---

## **Herramienta 4: Protocolo de Visualización de Esquema de Datos (PVED)**

*   **OBJETIVO:**
    *   Analizar los modelos de la base de datos y generar un Diagrama Entidad-Relación (ERD) para visualizar la estructura de datos del proyecto.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** el usuario solicita "ver el esquema de la base de datos", "diagrama de tablas" o "cómo se relacionan los datos".
    *   **ENTONCES** el protocolo PVED **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA):**
    1.  **Análisis de Modelos de Datos:**
        a.  Escanear los archivos que contienen los modelos de la base de datos (ej. `src/ultibot_backend/core/domain_models/`).
        b.  Extraer nombres de tablas (clases), campos (atributos) con sus tipos, claves primarias y claves foráneas (relaciones).
    2.  **Generación de Diagrama ERD (Mermaid.js):**
        a.  Crear un `erDiagram`.
        b.  Definir cada tabla y sus columnas.
        c.  Dibujar las relaciones (ej. `USER ||--o{ ORDERS : places`).
    3.  **Creación y Documentación de Artefacto (INVOCA PGDT):**
        a.  Guardar el ERD en `memory/visuals/database_schema.md`.
        b.  Invocar PGDT para documentar el esquema.
    4.  **Actualización del Dashboard:**
        a.  Añadir un enlace al ERD en el dashboard.

---

## **Herramienta 5: Protocolo de Análisis de Dependencias de Código (PADC)**

*   **OBJETIVO:**
    *   Generar un grafo de dependencias a nivel de módulo para identificar acoplamiento excesivo, dependencias circulares y la salud general de la arquitectura de código.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** el usuario solicita "analizar dependencias", "ver el acoplamiento del código" o "mapa de importaciones".
    *   **ENTONCES** el protocolo PADC **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / ITERACIÓN):**
    1.  **Análisis de Importaciones:**
        a.  Usar `search_files` con una regex (`^from\s+([\w.]+)\s+import\s+.*|^import\s+([\w.]+)`) en el directorio `src/`.
        b.  Construir una matriz de adyacencia donde cada fila es un módulo y cada columna es una dependencia.
    2.  **Generación de Grafo (Mermaid.js):**
        a.  Crear un `graph LR`.
        b.  Cada módulo es un nodo.
        c.  Dibujar una flecha (`A --> B`) si el módulo A importa el módulo B.
        d.  **Opcional:** Colorear nodos con alto acoplamiento (muchas flechas de entrada/salida).
    3.  **Creación y Documentación de Artefacto (INVOCA PGDT):**
        a.  Guardar el grafo en `memory/visuals/code_dependency_graph.md`.
        b.  Invocar PGDT para explicar cómo leer el grafo y señalar posibles problemas.
    4.  **Actualización del Dashboard:**
        a.  Añadir un enlace al grafo de dependencias en el dashboard.

---

## **Herramienta 6: Protocolo de Generación de Documentación Técnica (PGDT)**

*   **OBJETIVO:**
    *   Asegurar que cada artefacto visual generado por el Oráculo sea un documento técnico completo, contextualizado y accionable.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** cualquier otra herramienta del Oráculo (PC4A, PRFT, etc.) completa con éxito la generación de un diagrama.
    *   **ENTONCES** el protocolo PGDT **DEBE** ser invocado automáticamente sobre el artefacto recién creado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA):**
    1.  **Recibir Artefacto:**
        a.  Tomar como entrada el archivo Markdown que contiene el diagrama Mermaid.
    2.  **Envolver con Plantilla:**
        a.  Leer el contenido del archivo.
        b.  Crear un nuevo contenido estructurado con las siguientes secciones:
            *   `# Título del Documento`
            *   `## 1. Propósito y Alcance` (Explica qué muestra el diagrama y por qué es útil).
            *   `## 2. Cómo Interpretar este Diagrama` (Describe la notación utilizada).
            *   `## 3. Diagrama` (Insertar aquí el bloque de código Mermaid).
            *   `## 4. Observaciones y Análisis del Oráculo` (Añadir insights clave, ej. "Se observa un alto acoplamiento en el módulo X...").
            *   `## 5. Siguientes Pasos Sugeridos` (Proponer acciones basadas en el análisis).
    3.  **Sobrescribir Artefacto:**
        a.  Usar `write_to_file` para reemplazar el archivo original con el nuevo contenido enriquecido.
