---
description: "Sistema de Optimización y Despliegue Robusto (SODR) - Ley para Entornos Funcionales"
author: "Cline (basado en Systemprompt.v4.0)"
version: 1.0
tags: ["deployment", "optimization", "local-first", "automation", "mandatory"]
globs: ["*"]
priority: 900
---

# 🚀 SISTEMA DE OPTIMIZACIÓN Y DESPLIEGUE ROBUSTO (SODR)

## **PROPÓSITO CENTRAL**
Garantizar un entorno de ejecución **local, funcional, estable y sin costo** para UltiBotInversiones, permitiendo el modo `paper-trading` y sentando las bases para una promoción segura a producción. Este sistema es el complemento de ejecución al `SRST` de debugging.

## **FASES DEL SODR**

### **FASE 1: CONFIGURACIÓN DEL ENTORNO (SELECCIÓN)**
- **Principio de "Local-First":** El entorno por defecto siempre será local y autosuficiente.
- **Selección de Base de Datos:**
  - **`dev-mode` / `paper-trading-mode`:** **OBLIGATORIO** usar `SQLite` para eliminar la dependencia de Docker/PostgreSQL y agilizar el arranque. La base de datos debe residir en un archivo local (ej. `local_database.db`) y estar incluida en `.gitignore`.
  - **`production-mode`:** Usar PostgreSQL/Supabase según la configuración de producción.
- **Gestión de Claves:** Las claves para el modo local (`.env`) deben apuntar a endpoints de `testnet` o a servicios mock, garantizando cero costos.

### **FASE 2: ALGORITMO DE DESPLIEGUE AUTOMATIZADO (SECUENCIA)**
- **Objetivo:** Iniciar el sistema completo (backend y UI) con **una sola acción**.
- **Implementación:** A través de `tasks.json` en VS Code.
- **Secuencia de Arranque (`start-all-local` task):**
  1.  **Verificar Entorno:** Comprobar que `poetry` está instalado y las dependencias actualizadas.
  2.  **Iniciar Backend:** Ejecutar `uvicorn src.ultibot_backend.main:app --reload` en una terminal dedicada. El backend debe usar la configuración para `SQLite`.
  3.  **Iniciar UI:** Ejecutar `python -m src.ultibot_ui.main` en una segunda terminal. La UI debe estar configurada para comunicarse con el backend local.
  4.  **Validación:** El `healthcheck` del backend (`/health`) debe responder `200 OK`. La UI debe arrancar sin errores y mostrar su ventana principal.

### **FASE 3: CICLO DE OPTIMIZACIÓN (ITERACIÓN)**
- **Propósito:** Mejorar continuamente el rendimiento y la estabilidad del despliegue local.
- **Ciclo Iterativo:**
  1.  **Medir:** Identificar tiempos de arranque, uso de memoria y latencia de comunicación UI-Backend.
  2.  **Identificar Cuello de Botella:** ¿Qué parte del `Algoritmo de Despliegue` es más lenta o frágil?
  3.  **Refactorizar:** Proponer mejoras (ej. optimizar una consulta, cachear una configuración, mejorar un `worker` de la UI).
  4.  **Validar:** Volver a medir para confirmar la mejora. Documentar en `AUDIT_REPORT.md`.

### **FASE 4: PROMOCIÓN SEGURA A PRODUCCIÓN (ALGORITMO)**
- **Checklist de Promoción:** Antes de cambiar a `production-mode`, se debe validar:
  - [ ] Todos los tests del SRST pasan.
  - [ ] El ciclo de `paper-trading` ha funcionado sin errores por al menos 24 horas en modo local.
  - [ ] Las variables de entorno de producción están validadas.
  - [ ] Se ha creado un plan de rollback.
