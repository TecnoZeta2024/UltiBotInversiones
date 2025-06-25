# Registro del Proyecto: UltiBotInversiones

## Resumen General del Proyecto
UltiBotInversiones es una plataforma de trading personal avanzada y de alto rendimiento, diseñada para la ejecución de múltiples estrategias de trading sofisticadas (scalping, day trading, arbitraje) en tiempo real. Se apoya en análisis potenciado por IA (Gemini), una arquitectura modular orientada a eventos (con microservicios opcionales) basada en Protocolos de Contexto de Modelo (MCPs), y un stack tecnológico de vanguardia (Python 3.11+, PyQt5, FastAPI, PostgreSQL, Redis, Docker) para asegurar latencia ultra-baja y procesamiento paralelo. El objetivo principal es gestionar y hacer crecer un capital inicial de 500 USDT en Binance, buscando generar ganancias diarias significativas.

## Metas Primarias (MVP - v1.0)
- Despliegue rápido a producción para operar con capital real.
- Rentabilidad inicial ambiciosa (ganancias netas diarias >50% del capital arriesgado).
- Interfaz de Usuario funcional con PyQt5 para control y monitoreo.
- Integración de fuentes de datos de mercado clave (Binance, Mobula, WebSockets).
- Operatividad confiable del núcleo de trading y gestión de capital.

## Funcionalidades Principales del MVP
1.  **Configuración Segura y Conectividad Esencial:** Gestión de credenciales encriptadas y conexión con Binance/Telegram.
2.  **Interfaz de Usuario (Dashboard) y Visualización de Datos:** Dashboard con datos de mercado en tiempo real, gráficos, estado del portafolio (Paper y Real), y notificaciones.
3.  **Paper Trading (Simulación con Asistencia de IA):** Simulación completa de trading con capital virtual, detección de oportunidades por MCPs, análisis IA (Gemini), ejecución simulada de órdenes, TSL/TP automatizado, y visualización de resultados.
4.  **Operativa Real Limitada y Gestión de Capital:** Modo controlado para hasta 5 operaciones reales en Binance, con confirmación explícita del usuario, aplicación de reglas de gestión de capital y TSL/TP automatizado.
5.  **Gestión de Estrategias de Trading Base:** Definición modular de estrategias (Scalping, Day Trading, Arbitraje Simple), integración con IA, panel de control en UI, ejecución basada en estrategias activas, y monitoreo de desempeño.

## Estado Actual de las Épicas
- **Épica 1: Configuración Fundacional y Conectividad Segura:**
    - **Objetivo:** Establecer la configuración base del sistema, asegurar conectividad con Binance y Telegram, y gestión segura de credenciales.
    - **Historias Clave:** Configuración de repositorio, entorno de desarrollo (Docker/Poetry), andamiaje de monolito modular, framework de pruebas, configuración inicial Supabase, almacenamiento seguro de credenciales, verificación bot Telegram, verificación conectividad Binance.
    - **Estado:** Completada la definición de historias y criterios. Implementación en curso.

- **Épica 2: Diseño e Implementación del Dashboard Principal y Visualizaciones Esenciales:**
    - **Objetivo:** Implementar la UI principal con PyQt5, incluyendo dashboard, visualizaciones de mercado, gráficos, estado del portafolio y notificaciones.
    - **Historias Clave:** Layout principal, datos de mercado en tiempo real, gráficos financieros (mplfinance), estado del portafolio (Paper/Real), notificaciones integradas.
    - **Estado:** Completada la definición de historias y criterios. Implementación en curso.

- **Épica 3: Implementación del Ciclo Completo de Paper Trading con Asistencia de IA:**
    - **Objetivo:** Permitir simulación completa de trading con IA (detección, análisis, ejecución simulada, gestión de TSL/TP, resultados).
    - **Historias Clave:** Activación/configuración Paper Trading, integración detección oportunidades (MCPs), análisis con Gemini y verificación de datos, simulación ejecución órdenes, gestión TSL/TP, visualización resultados.
    - **Estado:** Completada la definición de historias y criterios. Implementación en curso.

- **Épica 4: Habilitación de Operativa Real Limitada y Gestión de Capital:**
    - **Objetivo:** Configurar modo "Operativa Real Limitada" (hasta 5 operaciones reales), con confirmación explícita, gestión de capital y TSL/TP automatizado.
    - **Historias Clave:** Configuración/activación Operativa Real Limitada, identificación oportunidades alta confianza (>95%), confirmación explícita y ejecución órdenes reales, aplicación reglas gestión capital/salidas automatizadas, visualización diferenciada operaciones/portafolio real.
    - **Estado:** Completada la definición de historias y criterios. Implementación en curso.

- **Épica 5: Implementación y Gestión de Estrategias de Trading Base:**
    - **Objetivo:** Ejecutar y gestionar estrategias algorítmicas (Scalping, Day Trading, Arbitraje Simple), permitiendo configuración, activación/desactivación y monitoreo de desempeño.
    - **Historias Clave:** Definición modular de estrategias, integración con IA (Gemini), panel de control UI, ejecución basada en estrategias activas, monitoreo desempeño por estrategia.
    - **Estado:** Completada la definición de historias y criterios. Implementación en curso.

## Próximos Pasos
- Crear `project-log-protocol.md` en `.clinerules/` para definir las reglas de interacción con `PROJECT_LOG.md`.
- Integrar `project-log-protocol.md` globalmente en `.clinerules/workspace.rules.md` para que todos los agentes lo utilicen.

## Avances Recientes
- **2025-06-24 22:24 (UTC-4:00) - [LeadCoder] - [TDT-DEBT-LOG]:** Se creó `DEBT_LOG.md` y se documentaron 6 instancias de deuda técnica priorizadas (TODOs, código obsoleto, funcionalidades pendientes) siguiendo el protocolo TDT. Clasificación y prioridades asignadas.
- **2025-06-24 21:43 (UTC-4:00) - [LeadCoder] - [TASK-UI-DEBUG]:** Se ha trabajado en la depuración de la UI. Se resolvieron los errores `ModuleNotFoundError: qasync` y `AttributeError: dateutil`. Se identificó un `RuntimeError` en el cierre de la aplicación relacionado con la limpieza de `QThread`. Se aplicaron correcciones iniciales. La tarea se traspasará al agente "debugger" para una resolución final.
- **Timestamp:** 2025-06-25 11:23 UTC
- **Agente:** Cline
- **ID Tarea:** [TASK-UI-ASYNC-FIX]
- **Ciclo:** [B-MAD-R: Record]
- **Acción:** Se corrigió el error `'Future' object has no attribute 'get_name'` en `src/ultibot_ui/workers.py` ajustando las llamadas a `logger.debug` y la firma de `get_trades` en `src/ultibot_ui/services/api_client.py`.
- **Resultado:** Éxito. Los errores de ejecución relacionados con `get_name()` deberían estar resueltos. Los errores de Pylance sobre `currentThreadId` persisten pero no son críticos para la ejecución.
- **Impacto:** Mayor estabilidad en la gestión de hilos asíncronos de la UI.
- **Timestamp:** 2025-06-25 11:52 UTC
- **Agente:** Cline
- **ID Tarea:** [TASK-UI-ASYNC-FIX]
- **Ciclo:** [B-MAD-R: Record]
- **Acción:** Se continuó con la depuración de la UI, resolviendo `AttributeError: type object 'PySide6.QtCore.QThread' has no attribute 'currentThreadId'` en `src/ultibot_ui/workers.py` y `RuntimeError: Cannot enter into task ... while another task ... is being executed.` mediante la implementación de inicialización tardía en `MainWindow` para las vistas `StrategiesView`, `TradingTerminalView` y `DashboardView`.
- **Resultado:** Éxito. La UI ahora gestiona mejor la concurrencia y la inicialización de workers asíncronos, reduciendo los errores de `asyncio`.
- **Impacto:** Mayor estabilidad y robustez de la aplicación UI, especialmente en el inicio y la gestión de hilos. Archivos modificados: `src/ultibot_ui/main.py`, `src/ultibot_ui/windows/main_window.py`, `src/ultibot_ui/views/strategies_view.py`, `src/ultibot_ui/views/trading_terminal_view.py`, `src/ultibot_ui/windows/dashboard_view.py`, `src/ultibot_ui/workers.py`.

- **2025-06-24 22:43 (UTC-4:00) - [LeadCoder] - [TASK-ORDER-EXECUTION]:** Se implementó el manejo de órdenes LIMIT y STOP_LOSS_LIMIT en `UnifiedOrderExecutionService` y `OrderExecutionService` (real y paper). Se actualizaron los modelos `TradeOrderDetails` con los campos `price`, `stopPrice` y `timeInForce`, y se corrigieron los errores de Pylance relacionados con la inicialización de estos campos.
