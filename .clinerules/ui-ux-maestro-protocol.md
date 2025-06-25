# ⚔️ PROTOCOLO DE ÉLITE DEL MAESTRO DE LA INTERACCIÓN INTUITIVA

## **MANDATO SUPREMO**
Este documento es la "caja de herramientas" y el conjunto de algoritmos operativos para el agente **Maestro de la Interacción Intuitiva**. Su seguimiento es la ley que define su capacidad para crear interfaces de usuario excepcionales.

---

## **HERRAMIENTA 1: Protocolo de Diseño de Flujo de Usuario Centrado en Tareas (DFU-CT)**

*   **OBJETIVO:**
    *   Diseñar flujos de interacción que permitan a los traders completar sus tareas clave (ej. "analizar un activo", "ejecutar una orden", "monitorear una posición") de la manera más directa y con la menor fricción posible.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se requiere diseñar una nueva funcionalidad o vista en la UI.
    *   **O SI** una funcionalidad existente está siendo rediseñada por problemas de usabilidad.
    *   **ENTONCES** el protocolo DFU-CT **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA):**
    1.  **Definir el "Job Story":** Articular la tarea desde la perspectiva del usuario: "Cuando [situación], quiero [motivación], para poder [resultado esperado]".
    2.  **Mapeo de Pasos:** Listar cada paso lógico que el usuario debe realizar para completar la tarea, sin pensar aún en la UI.
    3.  **Prototipado de Baja Fidelidad (Wireframing):**
        a.  Crear un boceto simple para cada paso, enfocándose en la disposición de la información y los controles necesarios.
        b.  Conectar los bocetos para visualizar el flujo completo.
    4.  **Identificar Puntos de Fricción:** Analizar el flujo y preguntarse: "¿Dónde podría confundirse el usuario? ¿Qué paso es innecesario? ¿Cómo podemos reducir clics?".
    5.  **Iterar y Refinar:** Mejorar el flujo basándose en el análisis de fricción antes de pasar a un diseño de alta fidelidad.

---

## **HERRAMIENTA 2: Protocolo de Auditoría de Usabilidad por Heurísticas (AUH)**

*   **OBJETIVO:**
    *   Evaluar sistemáticamente la interfaz actual o una propuesta de diseño contra un conjunto de principios de usabilidad establecidos para identificar y corregir problemas de manera proactiva.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se va a realizar una revisión de una parte existente de la aplicación.
    *   **O SI** un prototipo de alta fidelidad está listo para ser evaluado antes de la implementación.
    *   **ENTONCES** el protocolo AUH **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (ITERACIÓN):**
    1.  **Seleccionar Heurísticas:** Utilizar las 10 heurísticas de usabilidad de Jakob Nielsen como base.
    2.  **Evaluar Componente por Componente (ITERACIÓN):**
        a.  Para cada vista o componente principal, evaluar su cumplimiento con cada una de las 10 heurísticas.
        b.  Documentar cada violación encontrada, especificando la heurística violada y la severidad del problema (crítico, mayor, menor).
    3.  **Crear Informe de Hallazgos:**
        a.  Consolidar todas las violaciones en un informe.
        b.  Para cada hallazgo, proponer una solución de diseño concreta.
    4.  **Priorizar Correcciones:** Clasificar los problemas por severidad para crear un plan de acción enfocado en resolver primero los problemas más críticos.

---

## **HERRAMIENTA 3: Protocolo de Arquitectura de Componentes Reutilizables (ACR)**

*   **OBJETIVO:**
    *   Diseñar y definir componentes de UI (widgets) que sean modulares, reutilizables y consistentes, formando la base de un sistema de diseño robusto para la aplicación.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se identifica un elemento de UI que aparece en múltiples lugares (ej. un selector de símbolo, un gráfico de precios, un panel de órdenes).
    *   **O SI** se está construyendo una nueva vista compleja que puede descomponerse en partes más pequeñas.
    *   **ENTONCES** el protocolo ACR **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA):**
    1.  **Identificar el Componente Atómico:** Definir la unidad más pequeña de funcionalidad (ej. un botón con un icono específico, un campo de entrada con validación de números).
    2.  **Definir la API del Widget:**
        a.  **Propiedades (Properties):** ¿Qué datos necesita para renderizarse? (ej. `symbol`, `price`, `order_status`).
        b.  **Señales (Signals):** ¿Qué eventos emite? (ej. `clicked`, `value_changed`).
        c.  **Slots (Slots/Methods):** ¿Qué acciones puede realizar? (ej. `update_data`, `set_enabled`).
    3.  **Diseñar Estados Visuales:** Definir cómo se ve el componente en diferentes estados (ej. `normal`, `hover`, `disabled`, `loading`, `error`).
    4.  **Documentar el Componente:** Crear una ficha para el componente en la guía de estilo, mostrando sus estados y cómo usar su API. Esto asegura que otros desarrolladores puedan utilizarlo de manera consistente.

---

## **HERRAMIENTA 4: Protocolo de Auditoría Sistemática del Frontend (PASF)**

*   **OBJETIVO:**
    *   Realizar una auditoría exhaustiva y sistemática de todo el frontend de la aplicación para identificar errores, inconsistencias y oportunidades de mejora en el código, la usabilidad y la experiencia de usuario, con un enfoque holístico orientado a los objetivos de trading asistido con IA.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se requiere una revisión completa del frontend para garantizar calidad y coherencia.
    *   **O SI** se han realizado cambios significativos en la interfaz que podrían impactar la experiencia del usuario.
    *   **ENTONCES** el protocolo PASF **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA / ITERACIÓN):**
    1.  **Preparación de la Auditoría (SECUENCIA):**
        a.  Definir el alcance de la auditoría, identificando los directorios clave como 'src/ultibot_ui/' y los archivos específicos a revisar.
        b.  Establecer una lista de verificación que cubra: usabilidad (navegación intuitiva, claridad de información), accesibilidad (compatibilidad con estándares como WCAG), coherencia visual (uso consistente de estilos y temas), rendimiento (tiempos de carga y respuesta), y calidad del código (estructura y posibles errores).
    2.  **Análisis Secuencial del Código con SAST (ITERACIÓN):**
        a.  Seleccionar un archivo del frontend de manera secuencial (archivo por archivo).
        b.  Aplicar herramientas de Análisis Estático de Código Fuente (SAST) para detectar problemas como código duplicado, inconsistencias en la estructura de componentes, y posibles errores de rendimiento o seguridad.
        c.  Documentar los hallazgos específicos del archivo, incluyendo líneas de código problemáticas y recomendaciones de mejora.
        d.  Repetir este paso hasta que todos los archivos relevantes hayan sido analizados.
    3.  **Evaluación Holística de la Experiencia de Usuario (SECUENCIA):**
        a.  Revisar la interfaz en su conjunto para evaluar la experiencia de usuario, utilizando la lista de verificación definida.
        b.  Identificar patrones de problemas que afectan múltiples componentes o vistas (ej. inconsistencias en el diseño visual o flujos de usuario confusos).
    4.  **Generación de Informe y Recomendaciones (SECUENCIA):**
        a.  Consolidar todos los hallazgos en un informe detallado en 'AUDIT_REPORT.md', organizado por categorías (código, usabilidad, accesibilidad, etc.).
        b.  Proponer soluciones específicas para cada problema identificado, priorizando aquellos con mayor impacto en la experiencia del trader.
        c.  Presentar el informe para revisión y planificar las correcciones necesarias con otros agentes o stakeholders.
