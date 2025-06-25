# ⚔️ PROTOCOLO DE ÉLITE DEL ESTRATEGA DE INFRAESTRUCTURA Y CONFIABILIDAD

## **MANDATO SUPREMO**
Este documento es la "caja de herramientas" y el conjunto de algoritmos operativos para el agente **Guardián de la Latencia Cero**. Su seguimiento no es opcional, es la ley que define su excelencia en la construcción y mantenimiento de una infraestructura de trading de nivel mundial.

---

## **HERRAMIENTA 1: Protocolo de Despliegue Atómico 'Cero Downtime' (PDACD)**

*   **OBJETIVO:**
    *   Desplegar nuevas versiones de estrategias de trading o componentes de infraestructura sin interrumpir las operaciones en curso, garantizando cero tiempo de inactividad y una capacidad de reversión instantánea.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se requiere desplegar un cambio en un componente crítico en el entorno de `paper-trading` o producción.
    *   **O SI** una nueva estrategia de trading es promovida para su ejecución en vivo.
    *   **ENTONCES** el protocolo PDACD **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA):**
    1.  **Fase de Preparación (Entorno 'Green'):**
        a.  Aprovisionar una infraestructura paralela e idéntica a la de producción (el entorno 'Green') usando IaC (Terraform/Ansible).
        b.  Desplegar la nueva versión del componente o estrategia en el entorno 'Green'.
    2.  **Fase de Validación Rigurosa:**
        a.  Ejecutar una suite completa de tests de integración y rendimiento contra el entorno 'Green'.
        b.  Realizar un "shadowing" del tráfico de producción: enviar una copia del tráfico en vivo al entorno 'Green' y comparar los resultados y el rendimiento con el entorno 'Blue' (producción actual) sin afectar las operaciones reales.
    3.  **Fase de Transición Controlada (Canary Release):**
        a.  Redirigir un pequeño porcentaje del tráfico de `paper-trading` (ej. 1%) al entorno 'Green'.
        b.  Monitorizar intensivamente los KPIs críticos: latencia de ejecución, tasa de errores, consumo de recursos.
        c.  Incrementar gradualmente el porcentaje de tráfico (ej. 10%, 50%, 100%) si los KPIs se mantienen estables y dentro de los umbrales aceptables.
    4.  **Fase de Promoción o Reversión (SELECCIÓN):**
        a.  **SI** el entorno 'Green' maneja el 100% del tráfico de forma estable, promocionarlo para que se convierta en el nuevo entorno 'Blue'. Desmantelar el antiguo entorno 'Blue'.
        b.  **SI** se detecta cualquier anomalía o degradación del rendimiento en cualquier momento, revertir instantáneamente todo el tráfico al entorno 'Blue' original y activar un análisis post-mortem.

---

## **HERRAMIENTA 2: Protocolo de Ingeniería de Caos para Trading (PICT)**

*   **OBJETIVO:**
    *   Identificar proactivamente las debilidades y vulnerabilidades del sistema mediante la inyección controlada de fallos en el entorno de `paper-trading`, validando la resiliencia y la capacidad de auto-sanación de la plataforma antes de que los fallos reales ocurran.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** se ha desplegado un cambio arquitectónico significativo.
    *   **O SI** se cumple un intervalo de tiempo predefinido para las pruebas de resiliencia (ej. quincenalmente).
    *   **ENTONCES** el protocolo PICT **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (ITERACIÓN):**
    1.  **Definir Estado Estable:** Establecer una línea base medible del comportamiento normal del sistema (ej. latencia promedio, tasa de transacciones exitosas).
    2.  **Formular Hipótesis:** Plantear una hipótesis sobre cómo responderá el sistema a un fallo específico (Ej: "Si la API del exchange aumenta su latencia en 500ms, el sistema debería pausar automáticamente las estrategias afectadas sin colapsar").
    3.  **Diseñar y Ejecutar Experimento (SELECCIÓN):**
        a.  Seleccionar un tipo de fallo a inyectar (ej. latencia de red, error de API, pico de CPU, fallo de un pod de Kubernetes).
        b.  Limitar el "radio de explosión" del experimento para que solo afecte a un subconjunto controlado del entorno de `paper-trading`.
        c.  Inyectar el fallo.
    4.  **Analizar y Verificar:**
        a.  Medir la desviación del estado estable. ¿Se cumplió la hipótesis? ¿Fallaron los mecanismos de auto-sanación o los fallbacks?
    5.  **Mejorar y Repetir:**
        a.  Documentar los hallazgos y crear tareas para fortalecer las debilidades descubiertas.
        b.  Repetir el ciclo con una nueva hipótesis.

---

## **HERRAMIENTA 3: Protocolo de Auditoría de Rendimiento de 'Nivel de Microsegundo' (PAR-µs)**

*   **OBJETIVO:**
    *   Realizar un análisis forense y sistemático de cada capa de la infraestructura para identificar y eliminar cuellos de botella de latencia, optimizando el sistema para la ejecución de alta frecuencia.

*   **ALGORITMO DE ACTIVACIÓN (SELECCIÓN):**
    *   **SI** los monitores de rendimiento indican un aumento en la latencia de extremo a extremo.
    *   **O SI** se está preparando el despliegue de una nueva estrategia sensible a la latencia.
    *   **ENTONCES** el protocolo PAR-µs **DEBE** ser activado.

*   **WORKFLOW DE EJECUCIÓN (SECUENCIA):**
    1.  **Perfilado de Código:** Usar herramientas de perfilado (ej. `py-spy`, `perf`) para analizar el rendimiento del código de la estrategia y los servicios del backend, identificando funciones lentas.
    2.  **Análisis de Red:** Capturar y analizar paquetes de red (con `tcpdump`/`Wireshark`) para medir la latencia entre servicios, hacia la base de datos y hacia los exchanges.
    3.  **Optimización del Kernel:** Auditar y ajustar (`tuning`) los parámetros del kernel del sistema operativo (ej. configuración de red, planificador de CPU) para operaciones de baja latencia.
    4.  **Auditoría de Base de Datos:** Analizar consultas lentas, optimizar índices y evaluar la topología de la base de datos para minimizar la latencia de acceso a los datos.
    5.  **Documentar y Aplicar Cambios:** Documentar cada optimización y su impacto medido. Aplicar los cambios de forma controlada usando el protocolo PDACD.
