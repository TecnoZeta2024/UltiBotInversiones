# Épica 4: Habilitación de Operativa Real Limitada y Gestión de Capital

**Objetivo de la Épica:** Implementar un modo de "Operativa Real Limitada" que permita al usuario ejecutar un máximo de 5 operaciones con dinero real en Binance, aplicando reglas estrictas de gestión de capital y requiriendo confirmación explícita del usuario para cada operación.

## Historias de Usuario Propuestas para la Épica 4:

### Historia 4.1: Configuración y Activación del Modo de "Operativa Real Limitada"
Como usuario de UltiBotInversiones,
quiero poder configurar y activar un modo específico de "Operativa Real Limitada" que me permita realizar hasta un máximo de 5 operaciones con mi dinero real en Binance,
para comenzar a probar el sistema en el mercado real de una forma controlada, con bajo riesgo inicial y total transparencia sobre cuándo se está usando capital real.

##### Criterios de Aceptación:
*   AC1: UI con opción clara, explícita y separada para activar/desactivar modo "Operativa Real Limitada".
*   AC2: Al intentar activar, verificar conexión funcional con Binance y saldo USDT real disponible.
*   AC3: Mantener conteo persistente de las 5 operaciones reales permitidas (ejecutadas o intentadas).
*   AC4: UI debe mostrar claramente cuántas operaciones reales quedan disponibles.
*   AC5: Tras 5 operaciones reales, impedir automáticamente nuevas operaciones reales (permitir gestión de abiertas).
*   AC6: Al activar modo, UI debe presentar advertencia prominente e inequívoca sobre uso de dinero real, podría requerir confirmación adicional.

### Historia 4.2: Identificación y Presentación de Oportunidades de Muy Alta Confianza para Operativa Real
Como usuario de UltiBotInversiones operando en el modo de "Operativa Real Limitada",
quiero que el sistema me presente únicamente aquellas oportunidades de trading que la IA (Gemini) haya evaluado con un nivel de confianza superior al 95%,
para asegurar que solo se consideren las probabilidades de éxito más altas para mis escasas y valiosas operaciones con dinero real.

##### Criterios de Aceptación:
*   AC1: Flujo completo de detección de oportunidades (MCPs -> análisis Gemini -> verificación datos) debe operar en modo "Operativa Real Limitada".
*   AC2: Solo oportunidades con confianza Gemini >95% serán candidatas válidas para operación real.
*   AC3: Oportunidades >95% confianza deben presentarse en UI de forma destacada y diferenciada.
*   AC4: Presentación de oportunidad candidata debe incluir: par, dirección, resumen análisis Gemini, nivel de confianza exacto.
*   AC5: Notificación prioritaria y distintiva (UI y Telegram) cuando se identifique oportunidad >95% confianza y queden operaciones reales disponibles.

### Historia 4.3: Confirmación Explícita del Usuario y Ejecución de Órdenes Reales en Binance
Como usuario de UltiBotInversiones,
quiero, ante una oportunidad de muy alta confianza (>95%) que se me presente para operativa real, tener que confirmar explícitamente dicha operación en la UI antes de que cualquier orden se envíe al exchange de Binance,
para mantener el control final y absoluto sobre las decisiones que involucran mi dinero real.

##### Criterios de Aceptación:
*   AC1: Ante oportunidad >95% confianza en modo "Operativa Real Limitada" con cupos, UI debe solicitar confirmación explícita e inequívoca (ej. botón "Confirmar y Ejecutar Operación REAL").
*   AC2: Solicitud de confirmación debe mostrar detalles: par, dirección, cantidad a operar (calculada según gestión de capital real), precio estimado.
*   AC3: Solo si usuario confirma explícitamente, enviar orden real a Binance.
*   AC4: Si usuario no confirma o cancela, no ejecutar orden real (podría ofrecer registrar como paper trade).
*   AC5: Tras enviar orden a Binance, UI debe reflejar estado de la orden.
*   AC6: Una vez enviada orden real, decrementar contador de operaciones reales disponibles.

### Historia 4.4: Aplicación de Reglas de Gestión de Capital y Salidas Automatizadas a Operaciones Reales
Como usuario de UltiBotInversiones,
quiero que cuando se ejecute una operación con dinero real, el sistema aplique automáticamente mis reglas de gestión de capital (límite de inversión diaria del 50% y ajuste dinámico al 25% basado en riesgo) y también la gestión automatizada de Trailing Stop Loss y Take Profit,
para proteger mi capital real y asegurar una operativa disciplinada y consistente con mi estrategia.

##### Criterios de Aceptación:
*   AC1: Antes de presentar propuesta de operación real para confirmación, calcular tamaño de posición según reglas de gestión de capital sobre saldo real.
*   AC2: Tras confirmación de operación real y aceptación por Binance, calcular y colocar automáticamente en Binance órdenes TSL y TP.
*   AC3: Estado de órdenes TSL y TP reales debe ser visible en UI, asociado a posición real abierta.
*   AC4: Ejecución de TSL o TP en operación real debe ser notificada (UI y Telegram) y cerrar posición en Binance.
*   AC5: Monitorear y respetar regla de no exceder 50% capital total disponible para inversión diaria.

### Historia 4.5: Visualización y Seguimiento Diferenciado de Operaciones y Portafolio Real
Como usuario de UltiBotInversiones,
quiero que la sección de portafolio en la UI muestre de forma clara y separada mis operaciones, saldos y rendimiento con dinero real en Binance, distinguiéndolos de los datos de paper trading,
para poder hacer un seguimiento preciso y sin confusiones de mi rendimiento y situación financiera real.

##### Criterios de Aceptación:
*   AC1: Sección "Estado del Portafolio" en UI debe tener subsección diferenciada o método visual inequívoco para posiciones abiertas reales y saldo real.
*   AC2: Mostrar P&L realizado (reales cerradas) y P&L no realizado (reales abiertas) separadamente para componente real.
*   AC3: Saldo USDT real y cantidades de otros criptoactivos reales deben actualizarse con precisión.
*   AC4: Historial de operaciones debe permitir filtrar o distinguir claramente entre Paper Trading y operaciones reales.
