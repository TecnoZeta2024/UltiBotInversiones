# Épica 3: Implementación del Ciclo Completo de Paper Trading con Asistencia de IA

**Objetivo de la Épica:** Permitir al usuario simular un ciclo completo de trading (detección de oportunidad, análisis IA, ejecución simulada, gestión automatizada de Trailing Stop Loss y Take Profit, y visualización de resultados) en modo paper trading, con el apoyo de Gemini y los MCPs externos.

## Historias de Usuario Propuestas para la Épica 3:

### Historia 3.1: Activación y Configuración del Modo Paper Trading
Como usuario de UltiBotInversiones,
quiero poder activar el modo Paper Trading y configurar mi capital virtual inicial,
para poder empezar a simular operaciones de forma segura sin arriesgar dinero real y familiarizarme con el sistema.

##### Criterios de Aceptación:
*   AC1: UI con opción clara para activar/desactivar modo Paper Trading.
*   AC2: Al activar por primera vez, solicitar capital virtual inicial o asignar defecto configurable.
*   AC3: Capital virtual y estado de activación deben persistir entre sesiones.
*   AC4: UI debe indicar prominentemente cuándo el modo Paper Trading está activo.
*   AC5: En modo Paper Trading, todas las ejecuciones de órdenes deben ser simuladas internamente, sin interactuar con API real de Binance.

### Historia 3.2: Integración del Flujo de Detección de Oportunidades (MCPs) para Paper Trading
Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que el sistema utilice activamente los servidores MCP externos que he configurado para identificar "trending coins" o "winner coins",
para que estas potenciales oportunidades de trading puedan ser subsecuentemente analizadas por la IA de Gemini dentro del entorno de simulación.

##### Criterios de Aceptación:
*   AC1: En modo Paper Trading, el sistema debe conectarse a la lista configurable de servidores MCP externos.
*   AC2: El sistema debe recibir, interpretar y procesar señales de MCPs que indiquen oportunidades.
*   AC3: Oportunidades identificadas deben ser dirigidas al módulo de análisis IA (Gemini).
*   AC4: Registrar oportunidades crudas de MCPs para trazabilidad.

### Historia 3.3: Análisis de Oportunidades con Gemini y Verificación de Datos para Paper Trading
Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que las oportunidades identificadas por los MCPs sean analizadas en detalle por Gemini (utilizando los prompts de estrategias refinadas) y que los datos clave de los activos sean verificados (vía Mobula/Binance REST API),
para obtener una evaluación de confianza robusta por parte de la IA antes de proceder a simular cualquier operación.

##### Criterios de Aceptación:
*   AC1: Para cada oportunidad de MCPs, enviar datos relevantes a Gemini para análisis profundo con prompts de estrategias.
*   AC2: Recibir de Gemini análisis con dirección sugerida y nivel de confianza numérico.
*   AC3: Si confianza > umbral Paper Trading (ej. >80%), verificar datos de activos con Mobula/Binance REST API.
*   AC4: Solo si verificación de datos es exitosa, la oportunidad se considera validada.
*   AC5: Notificar al usuario (UI y Telegram) sobre oportunidades validadas de alta confianza (>80%).

### Historia 3.4: Simulación de Ejecución de Órdenes de Entrada en Paper Trading
Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que el sistema simule la ejecución de órdenes de entrada (compra/venta) para las oportunidades que han sido validadas por la IA con una confianza superior al 80%,
para poder observar cómo se habrían comportado estas decisiones en el mercado y comenzar a construir un historial de operaciones simuladas.

##### Criterios de Aceptación:
*   AC1: Para oportunidad validada con confianza IA >80%, simular automáticamente apertura de posición en portafolio Paper Trading.
*   AC2: Simulación de ejecución de orden de entrada debe usar precio de mercado realista (con slippage simulado opcional).
*   AC3: Tamaño de posición simulada calculado según reglas de gestión de capital sobre capital virtual.
*   AC4: Apertura de posición simulada debe reflejarse inmediatamente en UI de portafolio Paper Trading.
*   AC5: Notificar al usuario (UI y Telegram) confirmando apertura de operación simulada.

### Historia 3.5: Gestión Automatizada de Trailing Stop Loss y Take Profit en Paper Trading
Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que una vez abierta una posición simulada, el sistema calcule, coloque (simuladamente) y gestione automáticamente las correspondientes órdenes de Trailing Stop Loss (TSL) y Take Profit (TP),
para simular una gestión completa del ciclo de vida de la operación y evaluar la efectividad de las estrategias de salida.

##### Criterios de Aceptación:
*   AC1: Tras abrir posición simulada, calcular automáticamente niveles iniciales de TSL y TP.
*   AC2: Registrar internamente niveles calculados de TSL y TP asociados a posición simulada.
*   AC3: Simular seguimiento de TSL, ajustando nivel si precio se mueve favorablemente, basado en datos de mercado en tiempo real.
*   AC4: Simular cierre de posición si precio alcanza nivel actual de TSL o TP.
*   AC5: UI debe mostrar niveles activos de TSL y TP para cada posición simulada abierta.
*   AC6: Notificar al usuario (UI y Telegram) cuando TSL o TP simulado se ejecute y cierre posición.

### Historia 3.6: Visualización de Resultados y Rendimiento del Paper Trading
Como usuario de UltiBotInversiones,
quiero poder revisar de forma clara los resultados históricos de todas mis operaciones de paper trading, incluyendo el Profit & Loss (P&L) por operación y un resumen del rendimiento general de mi portafolio virtual,
para poder evaluar la efectividad de las estrategias implementadas, el análisis de la IA, y mi propia curva de aprendizaje con el sistema.

##### Criterios de Aceptación:
*   AC1: UI con sección o vista listando operaciones Paper Trading cerradas (par, dirección, precios entrada/salida, cantidad, P&L).
*   AC2: Impacto acumulado de operaciones Paper Trading debe reflejarse en saldo de capital virtual.
*   AC3: Calcular y mostrar en UI métricas básicas de rendimiento consolidadas para Paper Trading (P&L total, Win Rate, # operaciones, P&L promedio/operación).
*   AC4: Permitir filtros básicos a lista de operaciones cerradas (ej. por par, fecha).
