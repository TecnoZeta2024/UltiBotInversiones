-   **Épica 5: Implementación y Gestión de Estrategias de Trading Base**
    
    -   **Objetivo:** Dotar a UltiBotInversiones con la capacidad de ejecutar y gestionar un conjunto inicial de estrategias de trading algorítmico (Scalping, Day Trading y Arbitraje Simple), permitiendo al usuario configurarlas, activarlas/desactivarlas selectivamente tanto en modo Paper Trading como en Operativa Real Limitada, y monitorear su desempeño individual.
    
    -   **Historias de Usuario Propuestas para la Épica 5:**
        1.  **Historia 5.1: Definición y Configuración Modular de Estrategias de Trading**
            -   Como usuario de UltiBotInversiones, quiero que el sistema permita la definición modular de diferentes estrategias de trading (inicialmente Scalping, Day Trading, Arbitraje Simple), incluyendo sus parámetros configurables específicos, para que puedan ser gestionadas y ejecutadas de forma independiente.
            -   **Criterios de Aceptación (ACs):**
                -   AC1: El sistema debe contar con una estructura interna (ej. clases base, interfaces) que permita definir nuevas estrategias de trading de forma modular, especificando su lógica de entrada, salida y gestión de riesgos básicos.
                -   AC2: Para cada una de las estrategias base (Scalping, Day Trading, Arbitraje Simple), se deben identificar y definir sus parámetros configurables clave (ej. para Scalping: % de ganancia objetivo por operación, % de stop-loss; para Day Trading: indicadores técnicos y umbrales; para Arbitraje: umbral de diferencia de precios).
                -   AC3: El sistema debe permitir persistir la configuración de los parámetros para cada estrategia definida (utilizando la base de la Historia 1.4: Configuración Inicial de la Aplicación y Persistencia de Datos Fundamentales).
                -   AC4: La lógica de cada estrategia debe ser encapsulada de manera que pueda ser invocada por el motor de trading del sistema.
                -   AC5: La documentación interna (a nivel de código y diseño) debe describir claramente cómo añadir nuevas estrategias modulares al sistema en el futuro.
        2.  **Historia 5.2: Integración de Estrategias con el Motor de Análisis IA (Gemini)**
            -   Como usuario de UltiBotInversiones, quiero que cada estrategia de trading definida pueda interactuar con el motor de análisis de IA (Gemini) para refinar sus señales de entrada o validar oportunidades según su lógica particular, para mejorar la toma de decisiones y la efectividad de las estrategias.
            -   **Criterios de Aceptación (ACs):**
                -   AC1: Se debe poder configurar, para cada estrategia individualmente, si esta requiere o utiliza el análisis de IA (Gemini) y de qué manera (ej. para confirmación de tendencia, análisis de sentimiento de noticias relacionado con el activo, validación de patrones de la estrategia).
                -   AC2: Los prompts enviados a Gemini deben poder ser adaptados o extendidos dinámicamente con información o contexto específico proveniente de la estrategia activa que está evaluando una señal u oportunidad.
                -   AC3: El resultado del análisis de Gemini (ej. nivel de confianza, sugerencias, datos adicionales) debe ser devuelto y procesado por la lógica de la estrategia correspondiente para la toma de decisión final sobre ejecutar o no una operación.
                -   AC4: Si una estrategia está configurada para no utilizar IA, debe poder operar de forma autónoma basándose únicamente en sus reglas predefinidas y los datos de mercado disponibles.
                -   AC5: El sistema debe registrar de forma clara (en logs y en los detalles de la operación) si una operación fue influenciada, confirmada o generada con la asistencia de la IA y bajo qué estrategia específica.
        3.  **Historia 5.3: Panel de Control para Selección y Activación de Estrategias en la UI**
            -   Como usuario de UltiBotInversiones, quiero un panel de control en la interfaz de usuario (Dashboard) donde pueda ver las estrategias de trading disponibles (Scalping, Day Trading, Arbitraje Simple), configurar sus parámetros específicos, y activarlas o desactivarlas individualmente tanto para el modo Paper Trading como para la Operativa Real Limitada, para tener control granular y flexible sobre las operaciones que el bot realiza en mi nombre.
            -   **Criterios de Aceptación (ACs):**
                -   AC1: La interfaz de usuario (desarrollada en la Épica 2) debe incluir una nueva sección o panel claramente identificable para la "Gestión de Estrategias".
                -   AC2: En este panel, se deben listar todas las estrategias de trading definidas y disponibles en el sistema (inicialmente Scalping, Day Trading, Arbitraje Simple).
                -   AC3: Para cada estrategia listada, el usuario debe poder acceder a una interfaz donde pueda visualizar y modificar sus parámetros configurables (definidos en la Historia 5.1). Todos los cambios realizados deben persistirse de forma segura.
                -   AC4: El usuario debe poder activar o desactivar cada estrategia de forma independiente. Esta activación/desactivación debe poder realizarse por separado para el modo Paper Trading y para el modo de Operativa Real Limitada.
                -   AC5: La interfaz de usuario debe mostrar de forma clara e inequívoca el estado actual (activo/inactivo) de cada estrategia para cada uno de los modos de operación (Paper y Real).
                -   AC6: El sistema debe asegurar que solamente las estrategias que estén activadas para un modo de operación específico (Paper Trading o Real Limitada) puedan generar señales o ejecutar operaciones dentro de ese modo.
        4.  **Historia 5.4: Ejecución de Operaciones Basada en Estrategias Activas y Configuradas**
            -   Como usuario de UltiBotInversiones, quiero que el motor de trading del sistema solo considere y ejecute operaciones (simuladas en Paper Trading o propuestas para confirmación en Operativa Real Limitada) basadas en las señales generadas por las estrategias que yo he activado y configurado explícitamente, para asegurar que el bot opera estrictamente de acuerdo a mis preferencias y estrategias seleccionadas.
            -   **Criterios de Aceptación (ACs):**
                -   AC1: El motor de trading debe consultar en tiempo real el estado (activo/inactivo) y la configuración actual de todas las estrategias (gestionado a través de la Historia 5.3) antes de procesar cualquier señal de mercado potencial o oportunidad identificada por los MCPs.
                -   AC2: Cuando una oportunidad de trading es detectada (sea por MCPs externos o por un análisis interno del sistema), el sistema debe filtrar y determinar qué estrategias activas son aplicables a dicha oportunidad (basado en el par de monedas, condiciones de mercado, etc., según la lógica de cada estrategia).
                -   AC3: Las señales o datos de la oportunidad deben ser procesados por la lógica interna de la(s) estrategia(s) activa(s) que sean aplicables, incluyendo cualquier interacción con el motor de IA (Gemini) si así está configurado para dicha estrategia (según Historia 5.2).
                -   AC4: Solo se procederá a simular una operación (en modo Paper Trading, como se definió en la Épica 3) o a proponerla para ejecución real (en modo Operativa Real Limitada, como se definió en la Épica 4) si una estrategia activa y correctamente configurada así lo determina y alcanza el umbral de confianza requerido.
                -   AC5: Cada operación ejecutada (simulada o real) debe ser asociada y registrada de forma persistente con la estrategia específica que la originó, para fines de seguimiento y análisis de desempeño.
        5.  **Historia 5.5: Monitoreo Básico del Desempeño por Estrategia en la UI**
            -   Como usuario de UltiBotInversiones, quiero poder ver en el dashboard un resumen básico del desempeño de cada una de mis estrategias activadas (ej. número de operaciones realizadas, Profit & Loss total generado, y tasa de acierto), diferenciado por modo de operación (Paper Trading y Real), para poder evaluar de manera sencilla la efectividad de cada estrategia y tomar decisiones informadas sobre su futura configuración o activación.
            -   **Criterios de Aceptación (ACs):**
                -   AC1: La sección de "Estado del Portafolio" (definida en la Historia 2.4) o, si es más apropiado, una nueva sección dedicada en el dashboard, debe incluir un apartado para el "Desempeño por Estrategia".
                -   AC2: Para cada estrategia que haya ejecutado al menos una operación (tanto en modo Paper Trading como en modo Real), el sistema debe mostrar como mínimo la siguiente información:
                    -   Nombre de la Estrategia.
                    -   Modo de Operación (Paper Trading / Operativa Real Limitada).
                    -   Número total de operaciones ejecutadas por esa estrategia en ese modo.
                    -   Profit & Loss (P&L) total generado por esa estrategia en ese modo.
                    -   Win Rate (porcentaje de operaciones ganadoras sobre el total de operaciones cerradas) para esa estrategia en ese modo.
                -   AC3: Esta información de desempeño por estrategia debe actualizarse dinámicamente en la interfaz de usuario, idealmente después de que cada operación cerrada por dicha estrategia sea registrada.
                -   AC4: Los datos de desempeño deben ser claramente diferenciados y presentados por separado para el modo Paper Trading y para el modo de Operativa Real Limitada.
                -   AC5: El usuario debería poder ver esta información de forma consolidada (sumando todos los modos si tuviera sentido) o tener la opción de filtrar por un modo de operación específico para analizar el desempeño de las estrategias en dicho contexto.
