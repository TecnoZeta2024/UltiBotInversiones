# Documento de Requisitos del Producto (PRD) para UltiBotInversiones

## Meta, Objetivo y Contexto

**Introducción / Planteamiento del Problema:** UltiBotInversiones es una plataforma de trading personal avanzada y de alto rendimiento, diseñada para la ejecución de múltiples estrategias de trading sofisticadas (como scalping, day trading y arbitraje) en tiempo real. El sistema se apoya en un potente análisis potenciado por Inteligencia Artificial, una arquitectura modular orientada a eventos (con microservicios opcionales) basada en Protocolos de Contexto de Modelo (MCPs), y un stack tecnológico de vanguardia para asegurar latencia ultra-baja y procesamiento paralelo. Este proyecto representa una evolución significativa del anterior 'Bot_Arbitraje2105', expandiendo sus capacidades para satisfacer la necesidad urgente del usuario de gestionar y hacer crecer activamente un capital inicial de 500 USDT en la plataforma Binance, buscando generar ganancias diarias desde el inicio. El objetivo es una implementación completa y robusta, enfocada en la potencia y velocidad, desplegada directamente a producción para uso personal e inmediato.

**Visión:** Convertir a UltiBotInversiones en una plataforma de trading personal de vanguardia, altamente potente, rápida y con capacidades profesionales. Permitirá la ejecución eficiente de múltiples estrategias de trading (como scalping, day trading y arbitraje) mediante un análisis avanzado por Inteligencia Artificial, una arquitectura modular robusta y una experiencia de usuario profesional, superando significativamente las capacidades de sistemas anteriores y optimizada para una latencia ultra-baja y procesamiento paralelo.

**Metas Primarias (para el Despliegue Inicial a Producción v1.0):**

-   **Despliegue Rápido a Producción:** Poner en marcha "UltiBotInversiones" en el entorno de producción personal del usuario lo antes posible, permitiendo la operación con sus 500 USDT de capital real en Binance.
    
-   **Rentabilidad Inicial Ambiciosa:** Alcanzar una funcionalidad de trading robusta y estable que permita generar ganancias netas diarias significativas, aplicando las reglas de gestión de capital definidas. (El objetivo de alto impacto es que las ganancias netas diarias superen el 50% del capital total arriesgado en dichas operaciones durante ese día ).
    
-   **Interfaz de Usuario Funcional:** Implementar la interfaz de usuario principal con PyQt5, permitiendo el control y monitoreo efectivos de las operaciones y las estrategias iniciales. (Esto se aborda en la Épica 2).
    
-   **Integración de MCPs Esenciales:** Integrar los Model Context Protocols (MCPs) fundamentales para el análisis de mercado y la toma de decisiones de trading asistida por IA. (Esto se aborda en la Épica 3).
    
-   **Operatividad Confiable del Núcleo:** Asegurar que el sistema de datos unificado y el motor de ejecución de operaciones funcionen de manera fiable y eficiente para las estrategias que se activen inicialmente, adhiriéndose a las reglas de gestión de capital y riesgo. (Esto se aborda en las Épicas 1, 3, 4 y 5).

## **Funcionalidades Principales del MVP:**

1.  **Configuración Segura y Conectividad Esencial:**
    
    -   Permitir la configuración inicial de la aplicación y la persistencia segura de datos fundamentales y credenciales (Binance, Telegram, etc.).
        
    -   Establecer y verificar la conectividad con servicios externos clave: Binance para operaciones y datos de mercado, y Telegram para notificaciones.
        
2.  **Interfaz de Usuario (Dashboard) y Visualización de Datos:**
    
    -   Proveer un dashboard principal con un diseño claro y profesional (tema oscuro) implementado en PyQt5.
        
    -   Mostrar datos de mercado de Binance en tiempo real para pares de criptomonedas configurables por el usuario (precio, cambio 24h, volumen 24h).
        
    -   Visualizar gráficos financieros esenciales (velas japonesas, volumen) con selección de temporalidades para análisis técnico.
        
    -   Presentar el estado del portafolio, diferenciando claramente entre saldos y operaciones de Paper Trading y Reales (limitado a USDT y activos adquiridos).
        
    -   Integrar un centro de notificaciones dentro de la UI para alertas del sistema y eventos de trading.
        
3.  **Paper Trading (Simulación con Asistencia de IA):**
    
    -   Permitir la activación y configuración del modo Paper Trading con un capital virtual inicial.
        
    -   Integrar con servidores MCP externos para la detección de oportunidades de trading ("trending coins", "winner coins").
        
    -   Analizar las oportunidades detectadas utilizando la IA de Gemini, con verificación de datos vía Mobula/Binance API, para obtener una evaluación de confianza.
        
    -   Simular la ejecución de órdenes de entrada (compra/venta) para oportunidades validadas por IA con alta confianza (>80%).
        
    -   Gestionar automáticamente órdenes simuladas de Trailing Stop Loss (TSL) y Take Profit (TP) para las posiciones abiertas en Paper Trading.
        
    -   Visualizar los resultados históricos y el rendimiento general del Paper Trading (P&L por operación, P&L total, Win Rate).
        
4.  **Operativa Real Limitada y Gestión de Capital:**
    
    -   Permitir la configuración y activación de un modo de "Operativa Real Limitada" (hasta 5 operaciones con dinero real en Binance para la v1.0).
        
    -   Identificar y presentar al usuario únicamente oportunidades de trading con muy alta confianza (>95%) evaluadas por Gemini para la operativa real.
        
    -   Requerir confirmación explícita del usuario en la UI antes de ejecutar cualquier orden con dinero real en Binance.
        
    -   Aplicar reglas de gestión de capital (límite de inversión diaria del 50%, ajuste dinámico al 25% basado en riesgo) a las operaciones reales.
        
    -   Aplicar gestión automatizada de Trailing Stop Loss y Take Profit a las operaciones reales.
        
    -   Mostrar de forma diferenciada las operaciones, saldos y rendimiento del portafolio real en la UI.
        
5.  **Gestión de Estrategias de Trading Base:**
    
    -   Permitir la definición y configuración modular de estrategias de trading base (Scalping, Day Trading, Arbitraje Simple) con sus parámetros específicos.
    -   Integrar las estrategias definidas con el motor de análisis de IA (Gemini) para refinar señales o validar oportunidades según la lógica de cada estrategia.
    -   Proveer un panel de control en la UI para que el usuario pueda seleccionar, configurar y activar/desactivar estas estrategias para los modos Paper Trading y Operativa Real Limitada.
    -   Ejecutar operaciones (simuladas o reales) basadas únicamente en las señales generadas por las estrategias activas y configuradas.
    -   Permitir el monitoreo básico del desempeño (P&L, win rate, Nro. operaciones) por cada estrategia activada en la UI, diferenciado por modo de operación.

 
## ** Requisitos No Funcionales (MVP) **

Los Requisitos No Funcionales (NFRs) describen los atributos de calidad y las restricciones bajo las cuales el sistema "UltiBotInversiones" debe operar. Definen "cómo" debe ser el sistema, complementando los requisitos funcionales que definen "qué" debe hacer.

**1. Rendimiento:**

-   **Latencia de Operación:** El ciclo completo desde la detección de una oportunidad hasta la ejecución de la orden (para estrategias activas) debe ser consistentemente inferior a 500 milisegundos.
-   **Procesamiento Paralelo:** El sistema debe estar diseñado para el procesamiento paralelo con el fin de optimizar la velocidad y la capacidad de respuesta, especialmente en la ingesta y análisis de datos de mercado y la ejecución de estrategias.
-   **Actualización de Datos en UI:** Los datos de mercado en el dashboard (precios, cambios, volumen) deben actualizarse en tiempo real o cuasi real (ej. WebSockets para precios, REST API con actualizaciones frecuentes cada 5-15 segundos para datos de 24h).
-   **Respuesta de la Interfaz:** La interfaz de usuario debe ser fluida y responsiva a las interacciones del usuario, sin bloqueos o retrasos notables.

**2. Fiabilidad y Disponibilidad:**

-   **Disponibilidad del Sistema:** El sistema debe tener una disponibilidad superior al 99.9% durante las horas de mercado activas.
-   **Tasa de Error en Ejecución:** La tasa de error en la ejecución de operaciones (tanto simuladas como reales) debe mantenerse por debajo del 1%.
-   **Manejo de Errores Externos:** El sistema debe gestionar de forma robusta los errores de conexión o las respuestas inesperadas de servicios externos (Binance, Telegram, MCPs, Mobula), informando al usuario y reintentando operaciones o conexiones de manera inteligente cuando sea apropiado.
-   **Persistencia de Datos:** Las configuraciones críticas de la aplicación, las credenciales (encriptadas) y el estado de las operaciones deben persistir de forma segura y fiable entre sesiones.

**3. Seguridad:**

-   **Almacenamiento de Credenciales:** Todas las claves API y secretos del usuario deben ser encriptados utilizando algoritmos robustos (ej. AES-256 o Fernet) antes de ser almacenados en la base de datos (Supabase/PostgreSQL).
-   **Prohibición de Texto Plano:** Bajo ninguna circunstancia las credenciales sensibles deben ser almacenadas o registradas (logueadas) en texto plano.
-   **Acceso a Credenciales:** La desencriptación de credenciales debe realizarse de forma segura y solo en el momento necesario para su uso, minimizando su exposición en memoria.
-   **Protección General:** El sistema debe contar con un nivel adecuado de seguridad para proteger los fondos del usuario, las API keys y la integridad de los datos.

**4. Usabilidad:**

-   **Interfaz de Usuario (UI):** Debe ser clara, intuitiva, profesional y estéticamente agradable, utilizando un tema oscuro consistente (PyQt5 con QDarkStyleSheet o similar).
-   **Organización del Dashboard:** El layout principal debe estar bien organizado, con áreas designadas para diferentes tipos de información (mercado, portafolio, gráficos, notificaciones) que faciliten el acceso rápido a funciones clave.
-   **Notificaciones:** Las notificaciones al usuario (tanto en la UI como vía Telegram) deben ser claras, concisas, oportunas y relevantes.
-   **Facilidad de Uso:** La interacción general con el sistema debe ser lo más sencilla y fluida posible para el usuario, a pesar de la complejidad interna.

**5. Mantenibilidad y Escalabilidad:**

-   **Arquitectura:** El sistema debe seguir una arquitectura modular (evolución de Monolito Modular hacia Arquitectura Orientada a Eventos con Microservicios Opcionales) que facilite el mantenimiento, la prueba y la adición de nuevas funcionalidades o estrategias.
-   **Principios de Diseño:** Se valorará la aplicación de principios como Domain-Driven Design (DDD) y Command Query Responsibility Segregation (CQRS) donde aporten claridad y mantenibilidad.
-   **Base de Código:** El código debe ser comprensible y estar bien organizado. Se deben seguir los estándares de codificación que se definirán en el documento de arquitectura.
-   **Stack Tecnológico:** Se debe adherir estrictamente al stack tecnológico definido: Python 3.11+, PyQt5 5.15.9+, FastAPI 0.104.0+, PostgreSQL 15+, Redis 7.2+, google-generativeai 0.3.2+, Poetry 1.7.0+, Docker 24.0+.

**6. Compatibilidad:**

-   **Plataforma de Exchange:** Inicialmente, el sistema operará exclusivamente con la plataforma Binance.
-   **Sistema Operativo:** La aplicación de escritorio (PyQt5) debe ser compatible con el sistema operativo del usuario (a especificar, comúnmente Windows, macOS, o Linux).

**7. Eficacia (Metas de Negocio Cuantificables):**

-   **Win Rate (Tasa de Acierto):** Para las estrategias activas, el sistema debe aspirar a un Win Rate consistentemente superior al 75%.
-   **Rentabilidad Neta Diaria:** El sistema debe facilitar la consecución de una rentabilidad neta diaria de las operaciones que supere el 50% del capital total arriesgado en dichas operaciones durante ese día.
    -   _Nota: La gestión de capital (no arriesgar más del 50% del total diario, con posible reducción al 25%) es una regla funcional que apoya esta meta no funcional._
-   **Sharpe Ratio:** A mediano plazo, una vez se disponga de un historial de operaciones suficiente, se apuntará a un Sharpe Ratio superior a 1.5.

**8. Auditabilidad y Registros:**

-   **Registros (Logging):** El sistema debe mantener registros (logs) básicos pero suficientes para entender su comportamiento, diagnosticar problemas y para que el usuario pueda tener una trazabilidad de las decisiones y operaciones importantes. No se deben loguear datos sensibles en texto plano.

**9. Gestión de Datos y Políticas de Retención:**

Para asegurar la integridad, disponibilidad y el cumplimiento normativo (si aplicara en el futuro), así como para gestionar eficientemente los recursos de almacenamiento, se establecen las siguientes políticas básicas de retención de datos para "UltiBotInversiones":

* **a. Datos de Configuración del Usuario:**
    * **Datos Incluidos:** Preferencias de la aplicación, configuraciones de estrategias, listas de seguimiento de pares de criptomonedas, y cualquier otra configuración personalizada del usuario.
    * **Política de Retención:** Estos datos se mantendrán de forma persistente mientras la cuenta del usuario esté activa o según la configuración local de la aplicación. Si se implementara una cuenta de usuario en el futuro, la eliminación de la cuenta implicaría la eliminación de estos datos, previo aviso. Para la versión actual (uso personal), los datos persistirán indefinidamente en la base de datos Supabase/PostgreSQL hasta que el usuario los modifique o elimine a través de las funcionalidades de la aplicación.
    * **Nota:** Las credenciales sensibles (claves API) se gestionan según los "Requisitos de Seguridad" (encriptadas en reposo) y su ciclo de vida está ligado a la configuración del usuario.

* **b. Historial de Operaciones (Paper Trading y Real Limitada):**
    * **Datos Incluidos:** Detalles de cada operación simulada y real ejecutada por el sistema, incluyendo par, dirección, precio de entrada/salida, cantidad, P&L, y estrategia asociada.
    * **Política de Retención:**
        * **Paper Trading:** El historial de operaciones de Paper Trading se retendrá por un mínimo de **12 meses** para permitir el análisis de rendimiento y el aprendizaje. Después de este período, los datos más antiguos podrían ser archivados o eliminados para optimizar el almacenamiento, previa notificación o configuración por parte del usuario si se implementa tal funcionalidad.
        * **Operativa Real Limitada:** El historial de operaciones reales se retendrá por un mínimo de **36 meses** para fines de auditoría personal y análisis de rendimiento a largo plazo. Se recomienda al usuario realizar copias de seguridad personales de esta información crítica.

* **c. Logs del Sistema y Auditoría:**
    * **Datos Incluidos:** Logs generados por la aplicación para el seguimiento de eventos importantes del sistema, errores, decisiones de trading (sin incluir datos sensibles en texto plano), y actividad de conexión con servicios externos.
    * **Política de Retención:** Los logs detallados del sistema se retendrán por un período de **3 meses** para facilitar la depuración y el análisis de problemas recientes. Logs de auditoría de alta importancia (ej. cambios críticos en configuración, inicio/fin de operaciones reales) podrían tener una retención más larga si se definen como tales, alineándose con la retención del historial de operaciones reales.

* **d. Datos de Mercado Externos:**
    * **Datos Incluidos:** Datos de precios, volumen, u otros indicadores de mercado obtenidos de Binance o Mobula.
    * **Política de Retención:** "UltiBotInversiones" no tiene como objetivo principal el almacenamiento a largo plazo de datos históricos de mercado. Los datos de mercado se utilizarán en tiempo real o se almacenarán en caché a corto plazo (ej. para gráficos o análisis inmediatos) según sea necesario para la operativa y visualización, pero no se garantiza su retención extendida dentro de la aplicación. Se asumirá que las fuentes externas (Binance, Mobula) son el origen primario de estos datos históricos.

**Nota General:** Estas políticas podrán ser revisadas y ajustadas en futuras versiones de "UltiBotInversiones", especialmente si evoluciona a un sistema con múltiples usuarios o requisitos de cumplimiento más estrictos. Para la v1.0 de uso personal, la responsabilidad principal de la gestión de datos a muy largo plazo y copias de seguridad extensivas recae en el usuario.


## Metas de Interacción del Usuario y Diseño

Esta sección describe la visión y los objetivos de alto nivel para la experiencia de usuario (UX) y la interfaz de usuario (UI) de "UltiBotInversiones". Servirá como guía inicial para el Arquitecto de Diseño.

**Visión General y Experiencia Deseada:**

-   **Aspecto y Sensación (Look and Feel):** Se busca una interfaz profesional, moderna, y clara, con un tema oscuro consistente implementado con QDarkStyleSheet o similar. El objetivo es reducir la fatiga visual y alinearse con la estética de las aplicaciones de trading avanzadas.
-   **Experiencia del Usuario (UX):** La experiencia debe ser intuitiva, fluida y de gran apoyo. Aunque "UltiBotInversiones" es un sistema internamente potente y complejo, la interacción del usuario debe ser lo más sencilla posible, especialmente considerando que el usuario no se considera un experto técnico ni en trading algorítmico. El sistema debe asistir activamente al usuario, simplificando la toma de decisiones complejas y ofreciendo análisis claros y comprensibles.

**Paradigmas Clave de Interacción:**

-   **Dashboard Centralizado:** Un dashboard principal será el centro de operaciones, proporcionando acceso a visualizaciones de datos de mercado, estado del portafolio, gráficos y notificaciones.
-   **Configuración Simplificada:** La configuración de elementos como la lista de pares de criptomonedas a seguir o los parámetros de las estrategias de trading se realizará mediante interfaces claras, como listas seleccionables y formularios de configuración.
-   **Interacción con Gráficos:** Los usuarios podrán interactuar directamente con los gráficos financieros para realizar análisis técnicos, incluyendo la selección del par de criptomonedas y el cambio entre diferentes temporalidades.
-   **Notificaciones Integradas:** El sistema proveerá notificaciones en tiempo real sobre eventos cruciales, tanto dentro de la interfaz de usuario como a través de Telegram.
-   **Confirmaciones Explícitas:** Para acciones críticas que involucren capital real, como la ejecución de operaciones en modo real, se requerirá una confirmación explícita e inequívoca por parte del usuario.

**Pantallas/Vistas Centrales (Conceptuales):**

-   **Autenticación de Usuario:** Pantallas para el inicio de sesión y la gestión segura del acceso.
-   **Dashboard Principal:** Será la pantalla central y deberá incluir, como mínimo, las siguientes áreas funcionales designadas:
    -   Resumen de Datos de Mercado.
    -   Estado del Portafolio (diferenciando Paper Trading y Real).
    -   Visualización de Gráficos Financieros.
    -   Centro de Notificaciones del Sistema.
-   **Configuración del Sistema:**
    -   Gestión de Conexiones y Credenciales (Binance, Telegram, Servidores MCP).
-   **Panel de Gestión de Estrategias:** Una sección donde el usuario pueda ver, configurar, activar/desactivar las estrategias de trading disponibles (Scalping, Day Trading, Arbitraje Simple) para los diferentes modos de operación.
-   **Historial y Detalles de Operaciones:** Vistas para revisar el historial de operaciones cerradas y el estado de las operaciones activas, con detalles relevantes (P&L, estrategia, etc.).

**Aspiraciones de Accesibilidad (Alto Nivel):**

-   Se priorizará una alta legibilidad mediante el uso del tema oscuro, tipografía clara y buen contraste.
-   La navegación y la interacción buscarán ser lógicas y predecibles.
    -   _(Nota: Se podrán definir requisitos de accesibilidad más específicos, como compatibilidad con lectores de pantalla, en la fase de Diseño de UI/UX si así lo requieres)._

**Consideraciones de Branding (Alto Nivel):**

-   El diseño debe mantener una imagen profesional, tecnológica y confiable, consistente con una herramienta de trading de alto rendimiento.
    -   _(Nota: Si tienes directrices de branding específicas (colores, logos), por favor indícalas para que el Arquitecto de Diseño las considere)._

**Dispositivos/Plataformas Objetivo:**

-   La aplicación principal será una aplicación de escritorio desarrollada con PyQt5. Esto implica que deberá ser compatible con los principales sistemas operativos de escritorio donde PyQt5 y sus dependencias puedan operar (Windows, macOS, Linux).



## Suposiciones Técnicas

Esta sección consolida las directrices técnicas de alto nivel, las preferencias ya conocidas y las decisiones fundamentales que orientarán el diseño arquitectónico de "UltiBotInversiones".

**Stack Tecnológico Principal (Confirmado según Project Brief):**

-   **Lenguaje Principal:** Python 3.11+
-   **Interfaz de Usuario (UI):** PyQt5 versión 5.15.9+
-   **Backend y Servidores MCP (si se desarrollan internamente):** FastAPI versión 0.104.0+
-   **Base de Datos Principal:** PostgreSQL (versión 15+), gestionada a través de Supabase
-   **Caché L2:** Redis versión 7.2+
-   **Proveedor IA Inicial:** Gemini (utilizando la librería `google-generativeai` 0.3.2+)
-   **Fuente de Oportunidades MCP:** Servidores MCP externos identificados en `https://github.com/punkpeye/awesome-mcp-servers#finance--fintech`
-   **Gestión de Dependencias:** Poetry 1.7.0+
-   **Containerización:** Docker 24.0+

**Preferencias Arquitectónicas Iniciales (Confirmado según Project Brief):**

-   **Patrón General:** El sistema comenzará como un "Monolito Modular" con la visión de evolucionar hacia una "Arquitectura Orientada a Eventos con Microservicios Opcionales".
-   **Modularidad:** Se pondrá un fuerte énfasis en la modularidad, posiblemente a través de los Protocolos de Contexto de Modelo (MCPs) o principios similares para la separación de responsabilidades.
-   **Principios de Diseño:** Se valoran los principios de Domain-Driven Design (DDD) y Command Query Responsibility Segregation (CQRS) para guiar el diseño.
-   **Rendimiento:** La optimización para "latencia ultra-baja" y "procesamiento paralelo" es una prioridad.

**Decisión Crítica: Estructura de Repositorio y Arquitectura de Servicios para v1.0:** Esta es una decisión fundamental que debemos tomar ahora para guiar al Arquitecto. Basándome en la preferencia por un "Monolito Modular" inicial y la necesidad de "Máxima prioridad para llevar UltiBotInversiones a producción rápidamente", te propongo lo siguiente para la v1.0:

1.  **Estructura de Repositorio:** **Monorepo.**
    -   _Racionalización Propuesta:_ Para la v1.0, un monorepo simplificará la gestión de dependencias, la configuración del entorno de desarrollo y los procesos de CI/CD iniciales. Facilitará la coherencia y la refactorización a medida que el sistema evoluciona, y es adecuado para un equipo de desarrollo inicial (en este caso, los agentes IA y tú).
2.  **Arquitectura de Servicios (v1.0):** **Monolito Modular.**
    -   _Racionalización Propuesta:_ Iniciar con un Monolito Modular bien estructurado (con módulos claramente definidos para UI, núcleo de trading, gestión de datos, servicios de IA, notificaciones, etc.) permitirá un desarrollo más rápido para la v1.0. Los módulos internos se diseñarán con interfaces claras, lo que facilitará la posible extracción a microservicios en el futuro, alineándose con la visión a largo plazo.

### Gestión de Deuda Técnica

Reconocemos que en el desarrollo ágil y rápido, especialmente en las etapas iniciales de un MVP, puede surgir deuda técnica. Nuestro enfoque para gestionarla será el siguiente:

1.  **Identificación y Registro:** Cualquier miembro del equipo (incluyendo al usuario principal o los agentes IA) que identifique una posible deuda técnica (ej. atajos tomados para acelerar la entrega, código que podría ser refactorizado para mayor claridad o eficiencia, documentación pendiente, configuraciones subóptimas) deberá registrarla. Esto se hará idealmente como un issue específico en el backlog del proyecto o en una lista designada de "Deuda Técnica", detallando la naturaleza de la deuda, su ubicación, el impacto potencial y una sugerencia de solución.
2.  **Revisión Periódica:** La deuda técnica registrada será revisada al final de cada Épica completada, o con mayor frecuencia si se considera que su impacto es significativo. Esta revisión será parte de la retrospectiva o de una sesión de planificación técnica.
3.  **Priorización:** La priorización de la deuda técnica a abordar se basará en:
    * El impacto en la funcionalidad actual o futura.
    * El riesgo de que la deuda genere problemas mayores si no se aborda.
    * El esfuerzo estimado para solucionarla versus el beneficio obtenido.
    * La alineación con los objetivos inmediatos del proyecto.
4.  **Planificación:** La deuda técnica priorizada se incorporará al backlog como historias técnicas o tareas específicas y se planificará para su ejecución en sprints o iteraciones futuras, según corresponda. No toda la deuda técnica se abordará de inmediato; se buscará un equilibrio pragmático entre la velocidad de desarrollo de nuevas funcionalidades y el mantenimiento de la salud del código base.

**Requisitos de Pruebas (Testing Requirements):** Para asegurar la robustez del sistema y alcanzar la métrica de "Tasa de Error en Ejecución < 1%", se contemplan los siguientes tipos de pruebas:

-   **Pruebas Unitarias:** Cobertura exhaustiva para todas las funciones y módulos críticos, especialmente la lógica de trading, cálculos de gestión de capital, procesamiento de datos y la lógica de las estrategias.
-   **Pruebas de Integración:** Para validar la interacción entre los módulos clave del sistema (ej. motor de trading con el gestor de credenciales, UI con el backend, estrategias con el motor de IA y los MCPs). Se probará también la correcta integración con las APIs externas (Binance, Telegram, Mobula) utilizando mocks o entornos de prueba dedicados si es factible.
-   **Pruebas End-to-End (E2E):** Se definirán y ejecutarán pruebas E2E para los flujos de usuario críticos, incluyendo pero no limitado a:
    -   Configuración inicial del sistema, ingreso de credenciales y verificación de conectividad (Épica 1).
    -   Visualización y actualización de datos y gráficos en el dashboard (Épica 2).
    -   El ciclo completo de Paper Trading: detección de oportunidad, análisis por IA, ejecución simulada, gestión de TSL/TP y visualización de resultados (Épica 3 y 5).
    -   El flujo de Operativa Real Limitada: detección de oportunidad de alta confianza, presentación al usuario, confirmación, ejecución real, gestión de TSL/TP y visualización de portafolio (Épica 4 y 5).
    -   Activación, configuración y monitoreo de estrategias de trading (Épica 5).
-   **Pruebas de Usabilidad (Manuales):** Se realizarán pruebas manuales continuas por parte del equipo de desarrollo (agentes IA y tú como usuario principal) para asegurar la facilidad de uso y la claridad de la interfaz de usuario.

**Otras Suposiciones Técnicas:**

-   El desarrollo inicial y el MVP se centrarán exclusivamente en la integración con la plataforma **Binance**.
-   La **velocidad de desarrollo y el despliegue rápido** de la v1.0 son prioritarios.
-   La **asistencia de IA (Gemini)** es un componente central para el análisis de oportunidades y la toma de decisiones de trading.
-   Se utilizará **Poetry** para la gestión de dependencias y **Docker** para la containerización, facilitando entornos consistentes.



## Resumen de Épicas (Epic Overview)

Esta sección consolida las Épicas que hemos definido para el MVP de "UltiBotInversiones". Las Épicas 1 a 4 fueron detalladas en el documento `Epicas.md` (que incluye sus Historias de Usuario y Criterios de Aceptación completos), y la Épica 5 fue definida en nuestra conversación reciente.

A continuación, se presenta un resumen de cada una:

-   **Épica 1: Configuración Fundacional y Conectividad Segura**
    
    -   **Objetivo:** Establecer la configuración base del sistema "UltiBotInversiones", asegurar la conectividad con Binance y servicios de notificación (Telegram), y permitir la gestión segura de credenciales.
    -   _(Las Historias de Usuario detalladas y sus Criterios de Aceptación se encuentran en el documento `Epicas.md`)_.

-   **Épica 2: Diseño e Implementación del Dashboard Principal y Visualizaciones Esenciales**
    
    -   **Objetivo:** Implementar la interfaz de usuario principal de "UltiBotInversiones" utilizando PyQt5, incluyendo un dashboard con un layout claro y profesional, visualizaciones de datos de mercado en tiempo real, gráficos financieros esenciales, el estado del portafolio (Paper y Real) y un sistema de notificaciones integrado en la UI.
    -   _(Las Historias de Usuario detalladas (2.1 a 2.5) y sus Criterios de Aceptación se encuentran en el documento `Epicas.md`)_.

-   **Épica 3: Implementación del Ciclo Completo de Paper Trading con Asistencia de IA**
    
    -   **Objetivo:** Permitir al usuario simular un ciclo completo de trading (detección de oportunidad mediante MCPs, análisis y validación con IA de Gemini y datos de Mobula/Binance, ejecución simulada de órdenes de entrada, gestión automatizada de Trailing Stop Loss y Take Profit) en modo paper trading, y visualizar los resultados y el rendimiento de estas operaciones simuladas.
    -   _(Las Historias de Usuario detalladas (3.1 a 3.6) y sus Criterios de Aceptación se encuentran en el documento `Epicas.md`)_.

-   **Épica 4: Habilitación de Operativa Real Limitada y Gestión de Capital**
    
    -   **Objetivo:** Configurar y activar un modo de "Operativa Real Limitada" que permita al usuario ejecutar hasta un máximo de 5 operaciones con dinero real en Binance, presentando solo oportunidades de muy alta confianza (>95%) identificadas por la IA, requiriendo confirmación explícita del usuario, aplicando reglas de gestión de capital y salidas automatizadas, y visualizando de forma diferenciada estas operaciones y el portafolio real.
    -   _(Las Historias de Usuario detalladas (4.1 a 4.5) y sus Criterios de Aceptación se encuentran en el documento `Epicas.md`)_.

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



## Ideas Fuera de Alcance Post MVP

En esta sección, documentaremos aquellas funcionalidades e ideas valiosas que, si bien no forman parte del alcance del MVP actual, se consideran para futuras versiones o evoluciones de "UltiBotInversiones". Esto nos ayuda a mantener el enfoque en el MVP sin perder de vista el potencial a largo plazo.

Basándome en el `Project Brief_UltiBotInversiones.md` (sección "Funcionalidades / Alcance Post-v1.0 e Ideas Futuras"), las ideas identificadas son:

-   **Automatización Completa del Trading:** Avanzar hacia una operativa progresivamente más autónoma del bot, donde requiera menos intervención manual para iniciar o gestionar operaciones una vez que las estrategias estén configuradas y validadas.

-   **Sistema de Backtesting Avanzado y Detallado:** Implementar herramientas de backtesting más profundas y con mayor nivel de detalle para una validación rigurosa y continua de estrategias sobre datos históricos.

-   **Expansión Acelerada a Múltiples Exchanges:** Integrar rápidamente otros exchanges de criptomonedas además de Binance para ampliar las oportunidades de trading y arbitraje.

-   **Desarrollo Ágil de Capacidades de Machine Learning Propio:** Incorporar modelos de Machine Learning personalizados, entrenados con datos específicos del sistema o del usuario, para refinar continuamente el análisis de oportunidades y la toma de decisiones.

-   **Potenciación Avanzada del Análisis de IA (considerando Pinecone):** Integrar herramientas como bases de datos vectoriales (ej. Pinecone) para llevar el análisis de IA (especialmente con Gemini) a un nuevo nivel de profundidad semántica, contextual y de memoria a largo plazo.
-   **API para Terceros (Exploratorio):** Evaluar y potencialmente desarrollar una API que permita a otras aplicaciones o servicios interactuar con "UltiBotInversiones", si decides expandir su uso o capacidades externamente.
-   **Aplicación Móvil Complementaria (Companion App):** Desarrollar una aplicación móvil para el monitoreo básico del bot, recepción de notificaciones importantes y quizás la ejecución de interacciones esenciales de forma remota.
-   **Funcionalidades de Social Trading (Exploratorio):** Considerar la adición de características que permitan compartir estrategias (de forma anónima o pública), seguir a otros traders (si el sistema evolucionara a una plataforma multiusuario), o interactuar con una comunidad.
-   **Marketplace de Estrategias (Visión a Futuro):** Explorar la creación de un marketplace donde los usuarios puedan compartir, vender o comprar estrategias de trading probadas, si el proyecto se orienta en esa dirección y escala.
-   **Adición Continua de Características de Nivel Institucional:** Incrementar progresivamente la sofisticación del bot con herramientas de análisis, tipos de órdenes avanzadas, y gestión de riesgos más complejas, acercándolo a las capacidades de herramientas de trading de nivel profesional o institucional.
