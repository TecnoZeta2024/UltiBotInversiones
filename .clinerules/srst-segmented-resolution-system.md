---
description: "Sistema de Resolución Segmentada de Tests - Ley Máxima para Agentes IA"
author: reloj-atomico-optico
version: 3.0
tags: ["segmentation", "context-management", "test-resolution", "mandatory"]
globs: ["*"]
priority: 1000
---

# 🚨 SISTEMA DE RESOLUCIÓN SEGMENTADA DE TESTS (SRST) - LEY MÁXIMA

## **MANDATO SUPREMO**
- **ESTA ES LEY NO NEGOCIABLE**: Todo agente IA que trabaje en este proyecto DEBE usar el SRST
- **LÍMITE DE CONTEXTO ABSOLUTO**: Máximo 500k tokens por sesión de trabajo
- **PRINCIPIO FUNDAMENTAL**: UN ERROR A LA VEZ, UN MÓDULO A LA VEZ, UN FIX A LA VEZ

## **REGLAS DE HIERRO DEL SRST**

### **Regla 1: Segmentación Obligatoria**
- **NUNCA** intentar resolver más de **3 errores relacionados** en una sesión
- **SIEMPRE** usar tickets individuales de máximo **15-20 minutos** de trabajo
- **OBLIGATORIO** validar cada fix antes del siguiente

### **Regla 2: Gestión de Contexto Estricta**
- **MONITOREO CONTINUO**: Revisar uso de contexto cada 5 tools ejecutados
- **LIMITE ROJO**: Al llegar a 400k tokens → **PARAR INMEDIATAMENTE**
- **HANDOFF AUTOMÁTICO**: Crear nueva tarea con contexto preservado

### **Regla 3: Documentación Continua**
- **CADA FIX** debe ser documentado en `SRST_PROGRESS.md`
- **CADA SESIÓN** debe actualizar `SRST_TRACKER.md` con estado
- **ROLLBACK INMEDIATO**: Si algo falla, rollback y documentar en post-mortem

## **ESTRUCTURA OBLIGATORIA DEL SRST**

### **Nivel 1: Categorización por Tipo de Error**
```
SRST_CATEGORIES/
├── 1_IMPORT_ERRORS/        # ModuleNotFoundError, ImportError
├── 2_TYPE_ERRORS/          # TypeError, AttributeError  
├── 3_ASYNC_ERRORS/         # Event loop, AsyncIO issues
├── 4_DATABASE_ERRORS/      # Connection, pool, query issues
├── 5_UI_ERRORS/            # PyQt, widget, rendering issues
├── 6_INTEGRATION_ERRORS/   # Service communication issues
└── 7_BUSINESS_LOGIC_ERRORS/ # Domain logic, validation issues
```

### **Nivel 2: Segmentación por Módulo**
```
1_IMPORT_ERRORS/
├── adapters/               # Errores en adaptadores
├── services/               # Errores en servicios
├── core_domain/            # Errores en core
├── api_endpoints/          # Errores en API
└── ui_components/          # Errores en UI
```

### **Nivel 3: Tickets Atómicos**
```
TICKET_SRST_001/
├── description.md          # Descripción del error específico
├── context.md              # Contexto mínimo necesario
├── solution.md             # Plan de solución
├── validation.md           # Comandos de validación
└── status.md               # Estado actual
```

## **WORKFLOW OBLIGATORIO DEL SRST**

### **FASE 1: TRIAGE AUTOMÁTICO (5 mins max)**
1. **Ejecutar diagnóstico específico** (Omitir si es una continuación directa de tarea con ticket SRST activo y error principal sin cambios):
   ```bash
   poetry run pytest --collect-only -q 2>&1 | head -20
   ```
2. **Clasificar errores** por categoría y prioridad.
3. **Crear máximo 3 tickets** para la sesión actual (o continuar con el ticket activo si es una continuación de tarea).
4. **Validar Ticket Generado:** Antes de proceder, realizar una verificación rápida del ticket de mayor prioridad. ¿Apunta a un archivo de código fuente lógico? ¿El comando de validación es sintácticamente correcto? Si no, la primera acción será corregir la comprensión del ticket, no el código.
5. **Documentar en SRST_TRACKER.md**.

### **FASE 2: RESOLUCIÓN MICRO-SEGMENTADA (15 mins por ticket)**
1. **Seleccionar 1 ticket** de máxima prioridad.
2. **Cargar contexto mínimo** (solo archivos relevantes).
3. **Aplicar fix quirúrgico** específico.
4. **Validar inmediatamente**:
   - **Si el comando del ticket es válido:**
     ```bash
     poetry run pytest -xvs {SPECIFIC_TEST}
     ```
   - **Si el comando del ticket es inválido o el error es sistémico:** Ejecutar la suite completa o un subconjunto relevante para verificar el fix.
     ```bash
     poetry run pytest
     ```
5. **Refactorizar Tests si es Necesario:** Si la corrección del bug causa que un test falle porque el test dependía del comportamiento erróneo anterior, la tarea incluye la refactorización del test para que se alinee con la nueva lógica correcta.
6. **Documentar resultado** en SRST_PROGRESS.md.
*   **Análisis Profundo:** Si un ticket requiere un análisis más profundo o si los logs iniciales no revelan la causa raíz, utilizar la herramienta `sequential-thinking` para desglosar el problema y formular hipótesis antes de proponer cambios en el código.

### **FASE 3: VALIDACIÓN Y HANDOFF (5 mins)**
1. **Verificar no-regresión**:
   ```bash
   poetry run pytest --collect-only -q
   ```
2. **Commit con estado limpio**
3. **Si contexto > 400k tokens**: **HANDOFF OBLIGATORIO**

## **TEMPLATES OBLIGATORIOS**

### **Template de Ticket SRST**
```markdown
# SRST-{ID}: {ERROR_TYPE} en {MODULE}

## Error Específico
**Tipo:** `{ImportError|TypeError|AsyncIOError|etc}`
**Archivo:** `{FILE_PATH}:{LINE_NUMBER}`
**Mensaje:** `{ERROR_MESSAGE}`

## Contexto Mínimo
- **Scope:** `{ISOLATED|MODULE|SERVICE}`
- **Dependencias:** `{LIST_DEPENDENCIES}`
- **Archivos a tocar:** `{MAX_3_FILES}`

## Plan de Fix (máx 3 pasos)
1. [ ] **Paso 1:** {ACCION_ESPECIFICA}
2. [ ] **Paso 2:** {ACCION_ESPECIFICA}  
3. [ ] **Paso 3:** {VALIDACION}

## Validación Inmediata
```bash
# Comando específico para validar este fix
{COMANDO_VALIDACION}
```

## Criterio de Éxito
- [ ] Error específico resuelto
- [ ] Test collection exitosa
- [ ] No nuevos errores introducidos

**Estado:** `[ ] TODO | [ ] IN_PROGRESS | [ ] DONE | [ ] FAILED`
**Tiempo estimado:** `{15|20} minutos`
**Prioridad:** `{CRITICAL|HIGH|MEDIUM|LOW}`
```

### **Template de SRST_PROGRESS.md**
```markdown
# SRST Progress Tracker - {FECHA}

## Sesión Actual
**Tiempo inicio:** {TIMESTAMP}
**Contexto usado:** {XXXk / 500k tokens}
**Tickets en progreso:** {N}/3

## Tickets Completados Hoy
- [x] **SRST-001:** ImportError en binance_adapter.py - ✅ RESUELTO
- [x] **SRST-002:** TypeError en trading_service.py - ✅ RESUELTO

## Tickets En Progreso
- [ ] **SRST-003:** AsyncIO error en conftest.py - 🔄 EN_PROGRESO

## Tickets Pendientes (Próxima Sesión)
- [ ] **SRST-004:** Database connection error
- [ ] **SRST-005:** UI rendering issue

## Notas de Sesión
- **Decisiones importantes:** {LISTA}
- **Patrones encontrados:** {LISTA}
- **Bloqueos:** {LISTA}

## Handoff Requirements
**Si contexto > 400k tokens:**
- [ ] Estado actual documentado
- [ ] Contexto preservado en nueva tarea
- [ ] Tickets pendientes transferidos
```

## **COMANDOS OBLIGATORIOS DEL SRST**

### **Diagnóstico Rápido por Categoría**
```bash
# Import Errors
grep -r "ModuleNotFoundError\|ImportError" tests/ | head -5

# Type Errors  
grep -r "TypeError\|AttributeError" tests/ | head -5

# Async Errors
grep -r "Event loop\|asyncio\|RuntimeError" tests/ | head -5

# Database Errors
grep -r "psycopg\|database\|connection" tests/ | head -5
```

### **Validación Inmediata por Fix**
```bash
# Validar fix específico
poetry run pytest -xvs {SPECIFIC_TEST_FILE}::{SPECIFIC_TEST}

# Validar módulo completo
poetry run pytest -xvs tests/unit/{MODULE}/

# Validar colección general
poetry run pytest --collect-only -q | head -10
```

### **Monitoreo de Contexto**
```bash
# Comando para revisar uso de contexto
# (Simulado - el agente debe monitorear internamente)
echo "Current context: {CURRENT_TOKENS}/500k tokens ({}%)"
```

## **ESCALACIÓN AUTOMÁTICA DEL SRST**

### **Nivel 1: Error Individual (15 mins)**
- **Scope:** 1 archivo, 1 función, 1 error
- **Contexto:** < 100k tokens
- **Acción:** Fix quirúrgico directo

### **Nivel 2: Error de Módulo (30 mins)**
- **Scope:** 1 módulo, errores relacionados
- **Contexto:** < 200k tokens  
- **Acción:** Refactoring localizado

### **Nivel 3: Error Sistémico (45 mins)**
- **Scope:** Múltiples módulos, causa común
- **Contexto:** < 400k tokens
- **Acción:** Cambio arquitectónico menor

### **Nivel 4: HANDOFF OBLIGATORIO**
- **Scope:** Crisis sistémica
- **Contexto:** > 400k tokens
- **Acción:** Nueva tarea con contexto completo

## **MÉTRICAS OBLIGATORIAS DEL SRST**

### **Por Sesión**
- **Tickets completados:** Target 2-3 por sesión
- **Tiempo por ticket:** Target 15-20 minutos
- **Uso de contexto:** < 500k tokens OBLIGATORIO
- **Regresiones introducidas:** Target 0

### **Por Día**
- **Errores resueltos:** Mínimo 6-9 errores/día
- **Módulos rehabilitados:** Target 1-2 módulos/día
- **Test coverage mejorado:** Mínimo +5% por día

### **Por Semana**
- **Suite de tests operativa:** Target 100%
- **Deuda técnica reducida:** Target -20%
- **Documentación actualizada:** Target 100%

## **PROTOCOLOS DE EMERGENCIA SRST**

### **PROTOCOLO RED ALERT: Contexto > 450k tokens**
1. **STOP inmediato** - No más tools
2. **COMMIT estado actual** inmediatamente
3. **CREAR handoff task** con contexto completo
4. **TERMINAR sesión** obligatoriamente

### **PROTOCOLO ORANGE ALERT: Contexto > 350k tokens**
1. **FINALIZAR ticket actual** en progreso
2. **PREPARAR handoff** documentación
3. **VALIDAR estado** antes de continuar
4. **CONSIDERAR nueva tarea** si queda trabajo crítico

### **PROTOCOLO YELLOW ALERT: Contexto > 250k tokens**
1. **MONITOREO intensivo** cada tool
2. **OPTIMIZAR** contexto eliminando archivos no esenciales
3. **ACELERAR** resolución de ticket actual
4. **PREPARAR** documentación de handoff

## **CUMPLIMIENTO OBLIGATORIO**

### **El agente IA DEBE:**
- ✅ **USAR** el SRST en cada sesión de debugging
- ✅ **RESPETAR** el límite de 500k tokens estrictamente
- ✅ **DOCUMENTAR** cada fix en SRST_PROGRESS.md
- ✅ **VALIDAR** cada cambio antes del siguiente
- ✅ **CREAR** handoff si contexto > 400k tokens

### **El agente IA NO PUEDE:**
- ❌ **IGNORAR** el sistema de tickets
- ❌ **EXCEDER** 500k tokens de contexto
- ❌ **RESOLVER** más de 3 errores por sesión
- ❌ **SKIP** validación de fixes
- ❌ **PROCEDER** sin documentar el progreso

## **SANCIONES POR INCUMPLIMIENTO**
- **Violación de contexto > 500k**: TERMINACIÓN INMEDIATA de sesión
- **Skip de validación**: ROLLBACK obligatorio del fix
- **No documentación**: INVALIDACIÓN del trabajo realizado
- **Violación de segmentación**: RESET completo de la sesión
