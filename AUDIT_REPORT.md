# INFORME DE AUDITORÍA ARQUITECTÓNICA - UltiBotInversiones
**Fecha:** 6 de noviembre de 2025  
**Ingeniero:** Cline (Ingeniero Full-Stack Líder)  
**Objetivo:** Evolución arquitectónica hacia plataforma de inversión inteligente

---

## RESUMEN EJECUTIVO

El proyecto `UltiBotInversiones` presenta una base sólida con una arquitectura bien estructurada en PyQt6 y FastAPI. Sin embargo, requiere una evolución significativa para convertirse en una verdadera plataforma de inversión inteligente. Esta auditoría identifica 4 épicas críticas que transformarán el sistema actual en una herramienta de trading de nivel profesional con capacidades de IA avanzadas.

### ESTADO ACTUAL DEL PROYECTO

**Fortalezas Identificadas:**
- ✅ Arquitectura modular bien definida (backend/frontend separados)
- ✅ Sistema de navegación avanzado implementado
- ✅ Servicios básicos de trading y portfolio configurados
- ✅ Integración con APIs externas (Binance, Gemini) establecida
- ✅ Sistema de persistencia con Supabase configurado

**Gaps Arquitectónicos Críticos:**
- ❌ UI actual mezcla incorrectamente niveles de información
- ❌ Motor de estrategias rígido y no extensible
- ❌ Orquestación de IA limitada y sin control de herramientas MCP
- ❌ Ausencia de "AI Prompt Studio" para control total del agente
- ❌ Sistema de detección de oportunidades pasivo vs. proactivo

---

## ANÁLISIS DE ARQUITECTURA ACTUAL

### 1. CAPA DE PRESENTACIÓN (PyQt6)

**Estado Actual:**
- Sistema de navegación moderno con `SidebarNavigationWidget` avanzado
- Ventana principal (`MainWindow`) bien estructurada con `QStackedWidget`
- Vistas especializadas: Dashboard, Strategies, Portfolio, History, Settings

**Problemas Identificados:**
1. **Dashboard sobrecargado:** Mezcla análisis detallados (gráficos) con estado operacional
2. **Configuración fragmentada:** Ubicada en diálogos secundarios en lugar del flujo principal
3. **Ausencia de vista dedicada para análisis:** Los gráficos compiten por espacio con información crítica

### 2. CAPA DE LÓGICA DE NEGOCIO (Backend)

**Estado Actual:**
- Servicios bien separados: `ai_orchestrator_service`, `strategy_service`, `portfolio_service`
- Adaptadores para APIs externas configurados
- Sistema de persistencia funcional

**Problemas Identificados:**
1. **Motor de estrategias rígido:** `strategy_service.py` no implementa patrón Factory
2. **Orquestación de IA limitada:** `ai_orchestrator_service.py` carece del ciclo "Planificación -> Ejecución -> Síntesis"
3. **Ausencia de `MCPAdapter`:** No existe adaptador unificado para herramientas MCP
4. **Control de prompts hardcodeado:** Sin capacidad de gestión dinámica de plantillas de IA

### 3. CAPA DE DATOS

**Estado Actual:**
- Supabase configurado correctamente
- Modelos de dominio bien definidos
- Servicios de persistencia implementados

**Oportunidades:**
- Falta tabla `ai_prompt_templates` para gestión de prompts
- Ausencia de tabla `configuration_presets` para presets de usuario
- Sin estructura para almacenar registro de herramientas MCP

---

## ÉPICAS DE TRANSFORMACIÓN ARQUITECTÓNICA

### ÉPICA 1: Re-arquitectura de la Interfaz de Usuario

**Justificación Técnica:**
La UI actual viola el principio de separación de responsabilidades al mezclar niveles de abstracción diferentes en el dashboard. Esta refactorización implementará una jerarquía clara de información y navegación intuitiva.

**Impacto Arquitectónico:**
- Implementación de patrón MVC más estricto
- Separación clara entre vistas de estado vs. análisis
- Sistema de presets para configuraciones complejas

### ÉPICA 2: Motor de Estrategias "Pluggable"

**Justificación Técnica:**
El sistema actual no permite extensibilidad de estrategias sin modificar código core. La implementación del patrón Factory + Strategy permitirá agregar nuevas estrategias como módulos independientes.

**Impacto Arquitectónico:**
- Implementación de patrón Strategy con Factory
- Interfaz `BaseStrategy` para extensibilidad
- Carga dinámica de estrategias desde directorio

### ÉPICA 3: Módulo de Orquestación de Herramientas MCP

**Justificación Técnica:**
La capacidad actual de IA está limitada por la ausencia de un sistema de herramientas robusto. Esta épica implementará el patrón Adapter + Registry para herramientas MCP externas.

**Impacto Arquitectónico:**
- Patrón Adapter para unificación de APIs MCP
- Registry pattern para gestión de herramientas
- Ciclo de orquestación "Planificación -> Ejecución -> Síntesis"

### ÉPICA 4: Control de Prompts y "AI Prompt Studio"

**Justificación Técnica:**
El control hardcodeado de prompts viola el principio de configurabilidad y limita la capacidad de optimización. El "Prompt Studio" democratizará el control del agente IA.

**Impacto Arquitectónico:**
- Externalización de prompts a base de datos
- CRUD completo para plantillas de IA
- Sistema de testing en vivo para prompts

---

## MÉTRICAS DE ÉXITO

### Técnicas
- **Cobertura de código:** >80% para módulos críticos
- **Tiempo de respuesta:** <500ms para ciclo completo detección-ejecución
- **Modularidad:** 100% de estrategias como plugins independientes
- **Configurabilidad:** 100% de prompts IA externalizados

### Funcionales
- **Extensibilidad:** Agregar nueva estrategia en <30 minutos
- **Usabilidad:** Configurar prompt personalizado en <5 minutos
- **Eficiencia:** Detección proactiva de oportunidades vs. pasiva actual

---

## RECOMENDACIONES ESTRATÉGICAS

### Priorización Sugerida
1. **ÉPICA 1** (UI Re-arquitectura) - Base para experiencia de usuario
2. **ÉPICA 2** (Motor Estrategias) - Core de funcionalidad de trading
3. **ÉPICA 3** (Orquestación MCP) - Potenciación de capacidades IA
4. **ÉPICA 4** (Prompt Studio) - Control total del agente

### Consideraciones de Implementación
- Mantener compatibilidad con sistema actual durante transición
- Implementar migraciones de datos para nuevas estructuras
- Testing exhaustivo de cada módulo antes de integración
- Documentación técnica completa para futura mantenibilidad

---

**Conclusión:** El proyecto está en excelente posición para esta evolución arquitectónica. La base técnica sólida permitirá una implementación eficiente de estas mejoras transformacionales.
