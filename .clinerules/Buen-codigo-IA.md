---
description: "Guía Maestra de Principios de Ingeniería de Software para Agentes IA"
author: "Cline (sintetizado de Software_Ingeniering.md)"
version: 1.0
tags: ["architecture", "clean-code", "best-practices", "development-process", "mandatory"]
globs: ["*"]
priority: 800
---

# Guía Maestra de Ingeniería de Software

## **PROPÓSITO**
Esta guía establece los principios no negociables de ingeniería de software que todos los agentes IA deben seguir. El objetivo es construir sistemas robustos, mantenibles y de alta calidad.

---

## 1. Principios Fundamentales de Arquitectura

### **1.1. Directivas Arquitectónicas Centrales**
- **Separación de Concerns (SoC):** **DEBES** dividir el sistema en secciones distintas. Cada sección debe tener una única responsabilidad funcional (ej. UI, lógica de negocio, acceso a datos).
- **Principio de Responsabilidad Única (SRP):** **CADA** componente (clase, módulo, función) debe tener una, y solo una, razón para cambiar.
- **No te Repitas (DRY):** **DEBES** abstraer y centralizar la funcionalidad común para eliminar la duplicación. Cada pieza de conocimiento debe tener una representación única y autorizada.
- **Mantenlo Simple (KISS):** **DEBES** priorizar la simplicidad sobre la complejidad. Las soluciones directas son más fáciles de mantener y depurar.
- **No lo vas a necesitar (YAGNI):** **NO DEBES** implementar funcionalidad basada en especulaciones futuras. Implementa solo lo que se requiere ahora.
- **Principio Abierto/Cerrado (OCP):** **DEBES** diseñar entidades (clases, módulos) que estén abiertas a la extensión pero cerradas a la modificación. Añade nueva funcionalidad sin alterar el código existente.
- **Inversión de Dependencias (DIP):** Los módulos de alto nivel **NO DEBEN** depender de los de bajo nivel. Ambos deben depender de abstracciones (interfaces).

### **1.2. Selección de Patrones Arquitectónicos**
- **Monolito Modular:** Para este proyecto, **DEBES** favorecer una arquitectura de monolito modular. Los servicios y componentes deben estar bien encapsulados pero desplegados como una unidad.
- **Arquitectura Orientada a Eventos:** **DEBES** usar un modelo basado en eventos (señales y slots en la UI, eventos de dominio en el backend) para la comunicación entre componentes desacoplados.
- **Diseño Guiado por el Dominio (DDD):** **DEBES** alinear el diseño del software con el dominio del negocio (trading, análisis de mercado) utilizando un lenguaje ubicuo.

---

## 2. Calidad de Código y Mantenibilidad

### **2.1. Principios de Código Limpio (Clean Code)**
- **Nombres Significativos:** **DEBES** usar nombres claros y descriptivos para variables, funciones y clases. El código debe ser auto-documentado.
- **Funciones Pequeñas:** **DEBES** mantener las funciones enfocadas en una sola tarea y limitadas en tamaño. Una función hace una cosa bien.
- **Flujo de Control Claro:** **DEBES** minimizar el anidamiento y la lógica condicional compleja. Usa guard clauses y extrae métodos para mejorar la legibilidad.
- **Comentarios:** **DEBES** usar comentarios para explicar el *porqué* (la intención), no el *qué*. El código debe explicar el *qué* por sí mismo.
- **Manejo de Errores:** **DEBES** manejar los errores de forma explícita y consistente. No ignores excepciones.

### **2.2. Organización del Código**
- **Cohesión Lógica:** **DEBES** agrupar la funcionalidad relacionada. Cada módulo debe tener un propósito claro y enfocado.
- **Encapsulación:** **DEBES** ocultar los detalles de implementación detrás de interfaces bien definidas. Minimiza la visibilidad de clases, métodos y variables.
- **Gestión de Dependencias:** **DEBES** controlar las dependencias entre módulos. Usa inyección de dependencias para mantener los componentes débilmente acoplados.

### **2.3. Gestión de la Deuda Técnica**
- **Regla del Boy Scout:** **DEBES** dejar el código más limpio de lo que lo encontraste. Realiza pequeñas mejoras cada vez que trabajes en un área.
- **Refactorización Continua:** **DEBES** mejorar la estructura del código de forma continua como parte del desarrollo normal.

---

## 3. Procesos de Desarrollo y Metodologías

### **3.1. Prácticas Ágiles**
- **Desarrollo Iterativo:** **DEBES** construir software en ciclos pequeños e incrementales que entreguen funcionalidad funcional.
- **Historias de Usuario:** **DEBES** expresar los requisitos desde la perspectiva del valor para el usuario.
- **Retrospectivas:** **DEBES** reflexionar regularmente sobre los procesos del equipo para identificar e implementar mejoras.

### **3.2. DevOps y Entrega Continua (CI/CD)**
- **Integración Continua (CI):** **DEBES** integrar y probar automáticamente los cambios de código para detectar problemas de integración de forma temprana.
- **Infraestructura como Código (IaC):** **DEBES** definir la infraestructura (ej. `docker-compose.yml`) en archivos de configuración versionados.
- **Cultura sin Culpa (Blameless Culture):** **DEBES** ver los fallos como oportunidades de aprendizaje. Realiza post-mortems enfocados en la mejora del sistema.

### **3.3. Prácticas de Excelencia en Ingeniería**
- **Estándares de Codificación:** **DEBES** establecer y hacer cumplir convenciones de codificación consistentes (ej. a través de `.pylintrc`).
- **Revisiones de Código:** **DEBES** implementar un proceso de revisión de código enfocado en la corrección, mantenibilidad y compartición de conocimiento.
- **Desarrollo Guiado por Pruebas (TDD):** **DEBES** escribir pruebas antes de implementar la funcionalidad para asegurar que el código sea comprobable y cumpla con los requisitos.

---

## 4. Seguridad y Fiabilidad

### **4.1. Seguridad por Diseño**
- **Principio de Mínimo Privilegio:** **DEBES** otorgar los permisos mínimos necesarios para que cada componente funcione.
- **Prácticas de Codificación Segura:** **DEBES** seguir pautas establecidas como la validación de todas las entradas (inputs) y el manejo seguro de datos.
- **Dependencias Seguras:** **DEBES** auditar y actualizar regularmente las dependencias de terceros para abordar vulnerabilidades conocidas.

### **4.2. Construcción de Sistemas Fiables**
- **Tolerancia a Fallos:** **DEBES** implementar redundancia y mecanismos de conmutación por error (failover) para los componentes críticos.
- **Degradación Agraciada (Graceful Degradation):** Si partes de un sistema fallan, **DEBE** continuar proporcionando la funcionalidad esencial.
- **Planificación de Recuperación ante Desastres:** **DEBES** prepararte para interrupciones importantes con procedimientos de recuperación documentados y probados.

### **4.3. Ingeniería de Rendimiento**
- **Requisitos de Rendimiento:** **DEBES** definir objetivos de rendimiento claros y medibles.
- **Medición y Perfilado:** **DEBES** establecer líneas de base y medir regularmente las métricas de rendimiento. Usa herramientas de perfilado para identificar cuellos de botella.
- **Estrategias de Caché:** **DEBES** implementar un almacenamiento en caché apropiado en diferentes niveles del sistema.
