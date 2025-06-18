---
description: "Preservación del contexto de auditoría y post-mortem"
author: sistema
version: 1.0
tags: ["audit", "context-preservation", "incremental-updates"]
globs: ["*"]
---

# Preservación de Contexto de Auditoría

## Objetivo
Mantener un historial completo y cronológico de todos los análisis, decisiones y correcciones realizadas en el proyecto, permitiendo que futuros agentes tengan contexto completo del trabajo previo.

## Reglas de Preservación

### **MANDATORIO** Para AUDIT_REPORT.md
- **NUNCA sobrescribir** el contenido existente
- **SIEMPRE añadir** nuevas entradas con timestamp
- **Mantener formato**: `### INFORME DE ESTADO Y PLAN DE ACCIÓN - [Fecha y Hora]`
- **Incluir referencias** a informes previos cuando sea relevante

### **MANDATORIO** Para AUDIT_MORTEN.md  
- **NUNCA sobrescribir** el contenido existente
- **SIEMPRE añadir** nuevos post-mortems con timestamp
- **Mantener formato**: `### INFORME POST-MORTEM - [Fecha y Hora]`
- **Analizar patrones** de fallos previos documentados

## Patrón de Actualización

### Estructura para AUDIT_REPORT.md:
```markdown
[CONTENIDO EXISTENTE PRESERVADO]

---

### INFORME DE ESTADO Y PLAN DE ACCIÓN - [Nueva Fecha y Hora]

**ESTADO ACTUAL:**
* [Situación actual]

**REFERENCIA A INFORMES PREVIOS:**
* [Referencias específicas a trabajo anterior]

[... resto de la estructura estándar ...]
```

### Mejora sugerida (2025-06-18):
- Si tras 2 intentos consecutivos de replace_in_file para AUDIT_REPORT.md el SEARCH falla por longitud o autoformato, debe usarse write_to_file para preservar el historial y evitar bloqueos de auditoría.
- Documentar explícitamente este fallback en el protocolo.

### Estructura para AUDIT_MORTEN.md:
```markdown
[CONTENIDO EXISTENTE PRESERVADO]

---

### INFORME POST-MORTEM - [Nueva Fecha y Hora]

**REFERENCIA A INTENTOS PREVIOS:**
* [Referencias a post-mortems anteriores]

**Resultado Esperado:**
[...]

**Resultado Real:**
[...]

[... resto de la estructura estándar ...]
```

## Implementación en Workflow

1. **Siempre leer** el archivo completo antes de modificar
2. **Identificar** la última entrada existente
3. **Añadir separador** (`---`) 
4. **Agregar nueva entrada** preservando todo el contenido anterior
5. **Verificar** que no se perdió información previa

## Beneficios
- Trazabilidad completa de decisiones técnicas
- Aprendizaje de patrones de fallo recurrentes  
- Contexto para nuevos agentes que trabajen en el proyecto
- Historial forense de la evolución del proyecto
