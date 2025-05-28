# Project Brief: UltiBotInversiones
## Introducción / Planteamiento del Problema
UltiBotInversiones es una plataforma de trading personal avanzada y de alto rendimiento, diseñada para la ejecución de múltiples estrategias de trading sofisticadas (como scalping, day trading y arbitraje) en tiempo real. El sistema se apoya en un potente análisis potenciado por Inteligencia Artificial, una arquitectura modular orientada a eventos (con microservicios opcionales) basada en Protocolos de Contexto de Modelo (MCPs), y un stack tecnológico de vanguardia para asegurar latencia ultra-baja y procesamiento paralelo. Este proyecto representa una evolución significativa del anterior 'Bot_Arbitraje2105', expandiendo sus capacidades para satisfacer la necesidad urgente del usuario de gestionar y hacer crecer activamente un capital inicial de 500 USDT en la plataforma Binance, buscando generar ganancias diarias desde el inicio. El objetivo es una implementación completa y robusta, enfocada en la potencia y velocidad, desplegada directamente a producción para uso personal e inmediato.

## Visión y Metas
### Visión:

Convertir a UltiBotInversiones en una plataforma de trading personal de vanguardia, altamente potente, rápida y con capacidades profesionales. Permitirá la ejecución eficiente de múltiples estrategias de trading (como scalping, day trading y arbitraje) mediante un análisis avanzado por Inteligencia Artificial, una arquitectura modular robusta y una experiencia de usuario profesional, superando significativamente las capacidades de sistemas anteriores y optimizada para una latencia ultra-baja y procesamiento paralelo.

### Metas Primarias (para el Despliegue Inicial a Producción):

- Despliegue Rápido a Producción: Poner en marcha "UltiBotInversiones" en tu entorno de producción personal lo antes posible, permitiendo la operación con tus 500 USDT de capital real en Binance.
- Rentabilidad Inicial Ambiciosa: Alcanzar una funcionalidad de trading robusta y estable que permita generar ganancias netas diarias significativas, aplicando las reglas de gestión de capital definidas.
- Interfaz de Usuario Funcional: Implementar la interfaz de usuario principal con PyQt5, permitiendo el control y monitoreo efectivos de las operaciones y las estrategias iniciales.
- Integración de MCPs Esenciales: Integrar los Model Context Protocols (MCPs) fundamentales para el análisis de mercado y la toma de decisiones de trading asistida por IA.
- Operatividad Confiable del Núcleo: Asegurar que el sistema de datos unificado y el motor de ejecución de operaciones funcionen de manera fiable y eficiente para las estrategias que se activen inicialmente, adhiriéndose a las reglas de gestión de capital y riesgo.

### Métricas de Éxito (Revisadas para la Fase de Producción Temprana):

- Win Rate (Tasa de Acierto Clave): Para las estrategias activas, que sea consistentemente superior al 75%.
- Rentabilidad Neta de Operaciones Diarias (Objetivo de Alto Impacto): Las ganancias netas generadas por las operaciones efectivamente realizadas en un día deben superar el 50% del capital total arriesgado en dichas operaciones durante ese día. (El capital arriesgado se gestionará según las reglas definidas: no más del 50% del total disponible, con posible reducción al 25% bajo ciertas condiciones).
- Estrategia de Capitalización (Guía del Usuario): Aplicarás tu estrategia personal donde el 50% de las ganancias netas diarias se reinvertirán para incrementar el capital operativo, y el otro 50% se reservará como ahorro.
- Tasa de Error en Ejecución: Mantenerla inferior al 1% en las operaciones ejecutadas.
Latencia de Operación: El ciclo completo (detección de oportunidad a ejecución) consistentemente por debajo de los 500 milisegundos para las estrategias activas.
- Disponibilidad del Sistema: Superior al 99.9% durante las horas de mercado activas.
- Sharpe Ratio (a Mediano Plazo): Una vez que tengamos un historial de operaciones suficiente, apuntar a un Sharpe Ratio superior a 1.5.

## Audiencia Objetivo / Usuarios
El usuario principal de "UltiBotInversiones" es el visionario y propietario de la plataforma: un inversor individual con metas financieras claras (operar con 500 USDT en Binance para generar >50% de retorno diario sobre el capital invertido diariamente, con un win rate >75%) y la ambición de utilizar una herramienta de trading algorítmico de vanguardia.

### Es crucial destacar que, si bien el usuario tiene una visión audaz y ha proporcionado una base documental muy detallada para el sistema:

- No se considera a sí mismo un experto técnico con la capacidad actual de gestionar la complejidad intrínseca del sistema a largo plazo o de evolucionarlo técnicamente por su cuenta.
- Admite tener conocimientos limitados sobre trading algorítmico y busca que la herramienta le proporcione un apoyo integral en este aspecto.
Por ello, las características clave de este usuario y sus necesidades son:

- Dependencia Estratégica del Equipo de IA (BMAD Agente y su equipo): El usuario confía explícitamente en el equipo de agentes de IA (orquestado por BMad) para el diseño, desarrollo, despliegue de la v1.0, y crucialmente, para proyectar y gestionar la evolución técnica de "UltiBotInversiones" post-lanzamiento. La complejidad inherente al sistema debe ser abstraída o manejada por los agentes, presentando al usuario interfaces y controles que sean lo más intuitivos y manejables posible.
- Necesidad de una Herramienta de Apoyo Integral y Educativa: Dado su actual nivel de conocimiento en trading algorítmico, "UltiBotInversiones" no es solo una herramienta de ejecución, sino que debe asistirle activamente. Esto implica simplificar la toma de decisiones complejas, ofrecer análisis claros y comprensibles (a través de su "Motor de Análisis Multi-IA"  y los Model Context Protocols ), y guiar la operativa de manera que le ayude a navegar este dominio.
- Orientado a Resultados y Alto Rendimiento (con Soporte Experto): Busca maximizar la rentabilidad de su capital mediante estrategias sofisticadas (scalping, day trading, arbitraje ) y una ejecución de latencia ultra-baja. Sin embargo, espera que la herramienta y los algoritmos subyacentes, desarrollados y mantenidos por el equipo de IA, realicen el trabajo pesado del análisis profundo y la ejecución estratégica.
- Uso Personal e Inmediato con Visión de Futuro: Requiere un despliegue rápido a producción de la v1.0 para uso privado y para comenzar a operar con su capital real de forma urgente, pero con la expectativa de que el sistema crecerá en capacidades bajo la dirección técnica del equipo de IA.
- Gestor Activo de Capital (con Metas Claras): Planea aplicar su estrategia personal de inversión compuesta (reinvirtiendo el 50% de las ganancias diarias), y el bot debe ser la fuente que genere consistentemente dichas ganancias.
- Proveedor de Visión y Documentación Detallada: Ha sentado las bases con una documentación exhaustiva (1_System_Design.md, 2_Architecture_Pattern.md, Plan_accion_26-5.md, 5_Technical_Stack.md ) que establece una visión "a lo grande". El equipo de IA tiene la tarea de interpretar esta visión, convertirla en una realidad funcional y asegurar su sostenibilidad y crecimiento.

## Funcionalidades Clave / Alcance para el Despliegue Inicial a Producción (v1.0)
### Interfaz de Usuario (UI) con PyQt5 Clave para la Operativa:
- Un Dashboard principal para visualización de datos de mercado (Binance), estado del portafolio, y rendimiento básico.
- Un Panel de Control de Estrategias que te permita activar, desactivar y monitorear en tiempo real las estrategias de trading iniciales.
- Visualización de Gráficos Financieros esenciales (usando mplfinance ) para los pares con los que operes en Binance.
- Un Sistema de Notificaciones integrado para alertarte sobre eventos cruciales.

### Núcleo de Trading Algorítmico para Binance:
- La fuente principal para la Detección de Oportunidades provendrá de los servidores MCP (Model Context Protocol) externos identificados (en https://github.com/punkpeye/awesome-mcp-servers#finance--fintech), buscando optimizar la latencia en la ingesta de información para su procesamiento por Gemini.
- Las estrategias iniciales a implementar serán: scalping, day trading y arbitraje simple.
- Un Sistema de Ejecución de Órdenes confiable y rápido, conectado directamente a tu cuenta de Binance para operar con tu capital inicial de 500 USDT.
- Gestión de Capital y Riesgo Personalizada (Según tus Reglas):
- Implementación estricta de tu regla de no exceder el 50% del capital total disponible para la inversión diaria.
- Un mecanismo, idealmente influenciado por el análisis de la IA, para ajustar dinámicamente el capital expuesto (ej. reduciéndolo al 25% para las estrategias consideradas más agresivas) si las condiciones del mercado se tornan desfavorables o si se activan stop-loss.
- Funcionalidad básica pero efectiva de stop-loss por operación para proteger tu capital.

### Asistencia Activa por Inteligencia Artificial (IA) para Trading:
- La asistencia de IA estará potenciada inicialmente por el proveedor Gemini.
- Se deberá elaborar un algoritmo de "búsqueda de oportunidades" que recopile y estructure la información obtenida a través de los MCPs externos, adecuándola a los parámetros específicos que la IA de Gemini necesita para realizar sus análisis.
- El sistema procederá con una operación únicamente si el nivel de confianza de éxito proporcionado por Gemini excede el 80%.
- Sistema de Datos y Operaciones Fundamentales:
- Un Sistema de Datos Unificado  para la ingesta, normalización y almacenamiento eficiente de los datos de mercado de Binance.
La base de datos principal será PostgreSQL, gestionada a través de Supabase ( bajo "Producción Personal", compatible con PostgreSQL 15+ listado en ).

## Mecanismos de caché para optimizar el acceso a datos frecuentes y lograr la máxima velocidad: Caché L1 en memoria y Caché L2 con Redis 7.2+.
### Modo de Paper Trading Esencial:
- Una funcionalidad crucial que te permita simular operaciones en tiempo real utilizando datos de mercado de Binance, pero sin arriesgar tu capital real. Esto será vital para que te familiarices con el comportamiento del bot y valides las estrategias antes de pasar a operar con tus 500 USDT.

## Funcionalidades / Alcance Post-v1.0 e Ideas Futuras (Enfoque Rápido y Evolutivo)
- Una vez que "UltiBotInversiones v1.0" esté en pleno funcionamiento, la visión es continuar su desarrollo y expansión de manera ágil y rápida con las siguientes capacidades y mejoras (inspiradas en tu "Roadmap de Evolución"  y nuestras conversaciones):

- Automatización Completa del Trading: Avanzar hacia una operativa progresivamente más autónoma del bot.
- Sistema de Backtesting Avanzado y Detallado: Implementar herramientas de backtesting más profundas para una validación rigurosa y continua de estrategias.
- Expansión Acelerada a Múltiples Exchanges: Integrar rápidamente otros exchanges para ampliar las oportunidades de trading.
- Desarrollo Ágil de Capacidades de Machine Learning Propio: Incorporar modelos de ML personalizados para refinar continuamente el análisis y la toma de decisiones.
- Potenciación Avanzada del Análisis de IA (considerando Pinecone): Integrar herramientas como bases de datos vectoriales (ej. Pinecone) para llevar el análisis de IA (especialmente con Gemini) a un nuevo nivel de profundidad semántica y contextual.
- API para Terceros (Exploratorio): Evaluar y potencialmente desarrollar una API si decides expandir el uso o las capacidades de "UltiBotInversiones" externamente.
- Aplicación Móvil Complementaria (Companion App): Desarrollar una app móvil para monitoreo y quizás interacciones esenciales.
- Funcionalidades de Social Trading (Exploratorio): Considerar la adición de características sociales si el proyecto se orienta en esa dirección.
- Marketplace de Estrategias (Visión a Futuro): Explorar la creación de un marketplace si surge la oportunidad.
- Adición Continua de Características de Nivel Institucional: Incrementar progresivamente la sofisticación con herramientas y análisis de nivel profesional.

## Restricciones Técnicas o Preferencias Conocidas
### Restricciones y Mandatos Tecnológicos Clave:

### Stack Tecnológico Principal:
- Lenguaje Principal: Python 3.11+.
- Interfaz de Usuario (UI): PyQt5 versión 5.15.9+.
- Backend y Servidores MCP: FastAPI versión 0.104.0+.
- Base de Datos Principal: PostgreSQL (versión 15+), gestionada a través de Supabase.

### Caché L2: Redis versión 7.2+.
- Proveedor IA Inicial: Gemini (utilizando la librería google-generativeai 0.3.2+ ).
- Fuente de Oportunidades MCP: Servidores MCP externos (https://github.com/punkpeye/awesome-mcp-servers#finance--fintech).
- Gestión de Dependencias: Poetry 1.7.0+.
- Containerización: Docker 24.0+.
- Contexto Operativo Inicial:
- Capital Inicial de Operaciones: 500 USDT en la plataforma Binance.
- Tipo de Aplicación: Uso privado y personal.
- Prioridad Alta: Evitar problemas de compatibilidad entre librerías.

### Preferencias Arquitectónicas Iniciales:

- Patrón General: Evolución hacia una "Arquitectura Orientada a Eventos con Microservicios Opcionales", permitiendo un inicio como "Monolito Modular".
- Modularidad: Fuerte énfasis en la modularidad a través de los Protocolos de Contexto de Modelo (MCPs).
- Principios de Diseño: Se valoran los principios de Domain-Driven Design (DDD) y Command Query Responsibility Segregation (CQRS).
- Rendimiento: Optimización para "latencia ultra-baja" y "procesamiento paralelo".

### Riesgos Identificados (a considerar y mitigar):

- Dependencia del Usuario en el Equipo IA: La capacidad del usuario para gestionar y evolucionar técnicamente el sistema post-v1.0 es limitada; se dependerá del equipo de agentes IA (BMAD) para esta tarea.
- Curva de Aprendizaje en Trading Algorítmico: El conocimiento limitado del usuario en trading algorítmico requiere que "UltiBotInversiones" ofrezca una asistencia muy robusta, guía y análisis simplificados.
- Volatilidad del Mercado y Riesgos de Trading: Inherentes al dominio de inversión en criptomonedas.

### Dependencias Externas:
- Fiabilidad y posibles cambios en los servidores MCP externos.
- Disponibilidad, costos y posibles cambios en la API del proveedor de IA (Gemini).
- Metas de Rendimiento Ambiciosas: Alcanzar y mantener los objetivos de Win Rate (>75%) y Rentabilidad Diaria (>50% sobre capital invertido) representa un desafío técnico y estratégico considerable.
- Seguridad y Operativa Personal: Aunque la aplicación es de uso personal, la operación con capital real exige un nivel adecuado de seguridad para proteger los fondos y las API keys, así como registros básicos para entender el comportamiento del sistema, alineado con las secciones de seguridad de los documentos de diseño del usuario.

## Preferencias del Usuario Clave (Resumen de nuestras interacciones):

- Velocidad de Desarrollo y Despliegue: Máxima prioridad para llevar "UltiBotInversiones" a producción rápidamente. Los documentos de planificación son una referencia flexible.
- Enfoque Inicial: Plataforma Binance.
- Reglas de Gestión de Capital (funcionalidad del bot):
- Límite de inversión diaria no superior al 50% del capital total disponible.
- Ajuste dinámico del capital expuesto (ej. reducción al 25% para estrategias agresivas) basado en stop-loss o análisis de mercado desfavorables por la IA.
- Estrategia personal de reinversión de ganancias (50% a capital, 50% a ahorro).
- Experiencia de Usuario: Aunque el sistema sea internamente potente y complejo, la interacción del usuario debe ser lo más "sencilla" y fluida posible.
- Soporte Algorítmico: La herramienta debe compensar la experiencia limitada del usuario en trading algorítmico mediante fuerte asistencia de la IA.
- Consideración Futura: Se dispone de una API key de Pinecone para eventuales mejoras en las capacidades de análisis de IA post-v1.0.

## Investigación Relevante (Opcional)

### Documentos Fundacionales Proporcionados por el Usuario:
1_System_Design.md: Documento que detalla la visión general del sistema "UltiBotInversiones", sus componentes principales, interacciones, flujo de trabajo, consideraciones de alta disponibilidad, seguridad, escalabilidad, modelos de despliegue, métricas y una hoja de ruta inicial.
2_Architecture_Pattern.md: Especificación del patrón arquitectónico para "UltiBotInversiones", describiendo una Arquitectura Orientada a Eventos con Microservicios Opcionales, principios de Domain-Driven Design (DDD), diagramas, principios arquitectónicos fundamentales (EDA, CQRS, etc.), patrones de diseño adicionales y la aplicación de principios SOLID.
Plan_accion_26-5.md: Un plan de acción detallado para el despliegue a producción de "UltiBotInversiones", estructurado en múltiples fases. (Nota: Los plazos específicos de este plan se consideran flexibles según la directiva del usuario de priorizar la velocidad).
5_Technical_Stack.md: Documento que especifica el stack tecnológico detallado para el proyecto, incluyendo lenguajes de programación, frameworks, bases de datos, herramientas de IA, DevOps, y versiones específicas de cada componente.
Interacciones y Aclaraciones con el Agente Analista (Mary): Las precisiones, correcciones y directivas proporcionadas por el usuario durante la creación de este Resumen del Proyecto, incluyendo la definición del perfil de usuario, metas de rendimiento específicas, y la flexibilidad de los documentos de referencia.

# PM Prompt (Instrucción para el Product Manager)
Este Resumen del Proyecto proporciona el contexto completo para UltiBotInversiones. Por favor, inicia en 'Modo Generación de PRD', revisa este resumen exhaustivamente para trabajar con el usuario en la creación del PRD sección por sección, solicitando las aclaraciones necesarias o sugiriendo mejoras según lo permita tu programación en Modo 1.