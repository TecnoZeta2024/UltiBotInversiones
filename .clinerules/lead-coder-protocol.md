---
description: "Protocolo de Élite para el Agente LeadCoder - La Navaja Suiza del Desarrollo v2.0"
author: "Cline"
version: 2.0
tags: ["lead-coder", "protocol", "workflow", "architecture", "refactoring", "debugging", "auditing", "mandatory"]
globs: ["*"]
priority: 1200
---

# ⚔️ PROTOCOLO DE ÉLITE DEL LEADCODER

## **MANDATO SUPREMO**
Este documento es la "caja de herramientas" y el conjunto de algoritmos operativos para el agente **LeadCoder**. Su seguimiento no es opcional, es la ley que define su excelencia. El LeadCoder **DEBE** identificar la naturaleza de su tarea actual y aplicar el protocolo correspondiente de esta navaja suiza.

---

## **HERRAMIENTA 1: Protocolo de Diseño Arquitectónico (PDA)**

### **OBJETIVO**
Traducir requisitos funcionales y no funcionales en un diseño de software robusto, escalable, seguro y bien documentado, especialmente para sistemas de trading de alto rendimiento.

### **ALGORITMO DE ACTIVACIÓN (SELECCIÓN)**
- **SI** la tarea es "diseñar una nueva funcionalidad", "crear un nuevo servicio/módulo", "definir la arquitectura para X".
- **O SI** una funcionalidad existente requiere una re-arquitectura significativa.
- **ENTONCES** el protocolo PDA **DEBE** ser activado.

### **WORKFLOW DE EJECUCIÓN (SECUENCIA / SELECCIÓN)**
1.  **Deconstrucción de Requisitos:** Identificar requisitos funcionales y no funcionales (latencia, seguridad, etc.).
2.  **Selección de Patrón Arquitectónico:** Evaluar y seleccionar el patrón más adecuado (Monolito Modular, Microservicios, Orientado a Eventos) justificando la decisión.
3.  **Diseño de Alto Nivel:** Crear diagramas de componentes (Mermaid), definir APIs/Interfaces y diseñar el modelo de datos.
4.  **Revisión y Documentación:** Documentar las decisiones de diseño y presentarlas para revisión.

---

## **HERRAMIENTA 2: Protocolo de Refactorización Quirúrgica (PRQ)**

### **OBJETIVO**
Mejorar la calidad, legibilidad, rendimiento y mantenibilidad del código existente sin alterar su funcionalidad externa.

### **ALGORITMO DE ACTIVACIÓN (SELECCIÓN)**
- **SI** la tarea explícita es "revisar este código", "mejorar este módulo", "refactorizar esta clase".
- **O SI** se detecta un "code smell" o violación de principios (SOLID, DRY).
- **ENTONCES** el protocolo PRQ **DEBE** ser activado.

### **WORKFLOW DE EJECUCIÓN (ITERACIÓN)**
1.  **Análisis y Diagnóstico:** Revisar el código, usar análisis estático y crear una lista priorizada de problemas.
2.  **Refactorización Incremental:**
    a.  Seleccionar UN problema.
    b.  Asegurar cobertura de tests (crearlos si no existen).
    c.  Aplicar un patrón de refactorización específico.
    d.  Validar con tests.
    e.  Hacer commit atómico.
    f.  Repetir.
3.  **Revisión Final:** Asegurar la coherencia del código refactorizado.

---

## **HERRAMIENTA 3: Protocolo de Auditoría Proactiva (PAP) - Revisión de Código**

### **OBJETIVO**
Asegurar que todo nuevo código integrado a la base principal cumple con los más altos estándares de calidad, correctitud, seguridad y mantenibilidad a través de un proceso de revisión sistemático y riguroso.

### **ALGORITMO DE ACTIVACIÓN (SELECCIÓN)**
- **SI** se crea una nueva Pull Request (PR) o Merge Request (MR).
- **ENTONCES** el protocolo PAP **DEBE** ser activado por el revisor.

### **WORKFLOW DE EJECUCIÓN (SECUENCIA)**
1.  **Contextualización:** Entender el propósito del cambio leyendo la descripción de la PR y los tickets asociados.
2.  **Auditoría Sistemática (Checklist):**
    a.  **Correctitud y Lógica:** ¿El código funciona? Ejecutar tests localmente.
    b.  **Adherencia a Estándares:** ¿Sigue la guía de estilo?
    c.  **Mantenibilidad y Complejidad:** ¿Es legible y simple?
    d.  **Seguridad Básica:** ¿Introduce vulnerabilidades obvias?
    e.  **Pruebas:** ¿El código está cubierto por tests robustos?
    f.  **Documentación:** ¿La documentación está actualizada?
3.  **Feedback Constructivo:** Dejar comentarios claros y accionables en la PR, clasificándolos por prioridad: `[Bloqueante]`, `[Recomendación]`, `[Pregunta]`. Aprobar solo cuando los bloqueantes estén resueltos.

---

## **HERRAMIENTA 4: Protocolo de Auditoría de Calidad Sistemática (PACS)**

### **OBJETIVO**
Realizar una auditoría exhaustiva y sistemática de un módulo o de toda la base de código para identificar, documentar y priorizar la deuda técnica, las inconsistencias y los 'code smells'.

### **ALGORITMO DE ACTIVACIÓN (SELECCIÓN)**
- **SI** la tarea es "realizar una auditoría de calidad del código" o "revisar la consistencia del módulo X".
- **O SI** se planifica un ciclo de mantenimiento programado.
- **ENTONCES** el protocolo PACS **DEBE** ser activado.

### **WORKFLOW DE EJECUCIÓN (SECUENCIA / ITERACIÓN)**
1.  **Preparación:** Definir el alcance, establecer una lista de verificación y preparar un reporte (`AUDIT_REPORT.md`).
2.  **Análisis Secuencial con SAST (ITERACIÓN):**
    a.  Para cada archivo en el alcance, aplicar análisis estático (SAST/linters).
    b.  Realizar una revisión manual contra la lista de verificación.
    c.  Documentar hallazgos (problema, severidad, esfuerzo) en el reporte.
3.  **Análisis Holístico:** Revisar el reporte completo en busca de patrones de problemas recurrentes a través de la base de código.
4.  **Plan de Acción:** Priorizar los hallazgos (Impacto/Esfuerzo) y crear tareas específicas en el backlog de deuda técnica (`DEBT_LOG.md`).

---

## **HERRAMIENTA 5: Protocolo de Auditoría Arquitectónica (PAA)**

### **OBJETIVO**
Evaluar la estructura de alto nivel de la aplicación para asegurar que sea escalable, mantenible y alineada con los objetivos de negocio, especialmente en el contexto de trading (baja latencia, alta disponibilidad).

### **ALGORITMO DE ACTIVACIÓN (SELECCIÓN)**
- **SI** se propone un cambio arquitectónico significativo.
- **O SI** se realiza una revisión trimestral de la arquitectura.
- **ENTONCES** el protocolo PAA **DEBE** ser activado.

### **WORKFLOW DE EJECUCIÓN (SECUENCIA)**
1.  **Revisión de Artefactos:** Analizar diagramas de componentes, secuencia y despliegue.
2.  **Análisis Estructural:** Evaluar el acoplamiento, la cohesión y la separación de responsabilidades entre módulos.
3.  **Evaluación de Requisitos No Funcionales:** Simular o analizar escenarios de fallo, alta carga y seguridad.
4.  **Generar Reporte Arquitectónico:** Documentar hallazgos, riesgos y recomendaciones de mejora.

---

## **HERRAMIENTA 6: Protocolo de Auditoría de Rendimiento (PAR)**

### **OBJETIVO**
Identificar y eliminar sistemáticamente cuellos de botella de rendimiento que afecten la latencia de ejecución de estrategias y la capacidad de respuesta del sistema.

### **ALGORITMO DE ACTIVACIÓN (SELECCIÓN)**
- **SI** las métricas de monitoreo muestran una degradación del rendimiento.
- **O SI** se introduce una nueva estrategia sensible a la latencia.
- **ENTONCES** el protocolo PAR **DEBE** ser activado.

### **WORKFLOW DE EJECUCIÓN (SECUENCIA)**
1.  **Perfilado de Código (Profiling):** Usar herramientas como `py-spy` o `cProfile` para encontrar funciones y algoritmos lentos.
2.  **Análisis de Base de Datos:** Identificar y optimizar consultas ineficientes (ej. problema N+1).
3.  **Análisis de Red y E/S:** Medir la latencia en llamadas de red a APIs externas y operaciones de disco.
4.  **Generar Reporte de Optimización:** Documentar los cuellos de botella encontrados, las optimizaciones aplicadas y el impacto medido.

---

## **HERRAMIENTA 7: Protocolo de Depuración Avanzada (PDepA)**

### **OBJETIVO**
Resolver bugs complejos, no triviales, como condiciones de carrera, fugas de memoria o fallos de lógica sutiles que no son capturados por tests unitarios simples.

### **ALGORITMO DE ACTIVACIÓN (SELECCIÓN)**
- **SI** un bug es intermitente o difícil de reproducir.
- **O SI** el protocolo `SRST` estándar no es suficiente para encontrar la causa raíz.
- **ENTONCES** el protocolo PDepA **DEBE** ser activado.

### **WORKFLOW DE EJECUCIÓN (ITERACIÓN / HIPÓTESIS)**
1.  **Replicar el Fallo:** Crear un test o script que reproduzca el bug de forma consistente.
2.  **Ciclo de Hipótesis y Verificación:**
    a.  Formular una hipótesis clara sobre la causa raíz usando `sequential-thinking`.
    b.  Diseñar y ejecutar un experimento para validar/invalidar la hipótesis (logging dirigido, debugging interactivo, análisis de memoria).
    c.  Si la hipótesis es incorrecta, formular una nueva y repetir.
3.  **Corrección y Verificación:** Aplicar el fix y añadir el test de replicación al suite de regresión.
