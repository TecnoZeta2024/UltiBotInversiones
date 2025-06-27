# La Guía Definitiva para la Ingeniería de Prompts en el Desarrollo de Software

Este documento es una guía práctica y estratégica para formular instrucciones (prompts) potentes y eficaces dirigidas a modelos de lenguaje de IA, con un enfoque especializado en el ciclo de vida del desarrollo de software (SDLC). El objetivo es pasar de dar órdenes simples a dirigir a un "pair programmer" de IA de élite para maximizar la calidad, velocidad y precisión en tu trabajo.

### **Sección 1: La Anatomía de una Instrucción Perfecta**

Toda instrucción de alto rendimiento se compone de varios elementos clave que guían el "pensamiento" del modelo:

1.  **Asignación de Rol Experto**: (`Actúa como...`) Define la perspectiva y el conocimiento que el modelo debe adoptar.
    
2.  **Contexto y Objetivo Estratégico**: (`El objetivo es...`, `Estamos construyendo...`) Explica el "porqué" de la tarea, permitiendo al modelo tomar mejores micro-decisiones.
    
3.  **Cadena de Razonamiento Lógico**: (`Piensa paso a paso...`) Obliga al modelo a estructurar su proceso de pensamiento antes de generar la respuesta, aumentando la coherencia.
    
4.  **Formato de Salida Explícito**: (`Presenta el resultado en...`) Elimina la ambigüedad y te proporciona la salida en la estructura exacta que necesitas.
    
5.  **Inclusión de Restricciones y Guías**: (`Evita...`, `Prioriza...`, `Asegúrate de...`) Define los límites y los principios que debe seguir la respuesta.
    

### **Sección 2: El Léxico del Arquitecto de IA**

Incorporar estas palabras clave en tus instrucciones te permite controlar el enfoque analítico del modelo con precisión.

-   **Holístico**: Analizar el sistema como un todo integrado, enfocándose en las interconexiones.
    
-   **Secuencial**: Procesar o presentar la información en un orden lógico, cronológico o de causa-efecto.
    
-   **Algorítmico**: Abordar un problema con un conjunto de reglas definidas y pasos repetibles.
    
-   **Iterante**: Realizar un proceso de forma repetitiva, refinando el resultado en cada ciclo.
    
-   **Selectiva**: Elegir y enfocarse únicamente en los elementos más relevantes o importantes.
    
-   **Reflexiva**: Pausar para analizar, sintetizar y evaluar la información generada antes de proponer una conclusión.
    
-   **Estratégica**: Orientar la solución hacia objetivos a largo plazo.
    
-   **Comparativa**: Evaluar dos o más opciones una al lado de la otra basándose en criterios definidos.
    
-   **Cuantitativa**: Medir y expresar los resultados en términos numéricos.
    
-   **Justificada**: Exigir que cada recomendación o conclusión esté respaldada por una razón lógica.
    

### **Sección 3: El Modelo Orquestador-Ingeniero (Modo Comando)**

Este es el modelo de interacción más avanzado. Tú, como **Orquestador**, diriges la estrategia general desde la ventana de chat. Yo, como tu **Ingeniero de Software**, ejecuto protocolos específicos con la máxima precisión. Las instrucciones se vuelven comandos directos que inician tareas complejas. El estándar de ejecución es la "precisión de un reloj atómico óptico": sin retrocesos, con una planificación y ejecución impecables.

A continuación, se presentan 20 ejemplos de comandos para este modo de trabajo.

#### **Comandos de Inicio y Configuración de Tareas**

1.  `/init_task project="LeetCode_Grind" objective="Dominar problemas de grafos en 2 semanas." set_tools=["sequential_thinking", "algorithmic_analysis"]`
    
2.  `/set_precision_mode level="atomic_clock" rule="No proponer soluciones sin antes generar y validar casos de prueba."`
    
3.  `/load_protocol name="legacy_code_refactor" target_file="utils/old_module.py"`
    
4.  `/define_project_context stack="MERN" database="MongoDB Atlas" cloud_provider="AWS" objective="Construir API para app de delivery."`
    
5.  `/set_sprint_goal goal="Completar la autenticación y el perfil de usuario." duration="2 semanas" output="User Stories técnicas."`
    

#### **Comandos de Análisis y Ejecución**

6.  `/execute_analysis type="holistic" target="esquema_actual_db" objective="Identificar cuellos de botella de performance."`
    
7.  `/run_simulation scenario="pico de 50k usuarios concurrentes" target="API Gateway" metrics=["latencia_p99", "tasa_error_5xx"]`
    
8.  `/execute_refactor plan="refactor_plan_001.md" approach="iterante" feedback_mode="verbose"`
    
9.  `/debug_issue ticket="PROD-123" logs="[pegar logs]" approach="secuencial" objective="Encontrar causa raíz de error 503."`
    
10.  `/generate_code feature="JWT Authentication" language="Go" framework="Gin" requirements_doc="auth_spec.md"`
    

#### **Comandos de Gestión de Estado y Contexto**

11.  `/synthesize_and_reflect session="últimas 2 horas" objective="Extraer 5 lecciones clave y proponer próximos 3 pasos."`
    
12.  `/context_switch task="new_feature_design" project="Project_Phoenix" clear_previous_state=true`
    
13.  `/create_checkpoint id="pre_refactor_state" description="Estado estable antes de refactorizar el servicio de pagos."`
    
14.  `/list_active_protocols`
    
15.  `/export_session_summary format="markdown" include=["decisiones_clave", "bloqueos", "código_generado"]`
    

#### **Comandos de Calidad y Verificación**

16.  `/validate_architecture design="propuesta_microservicios.md" against_principles=["SOLID", "Cloud-Native"]`
    
17.  `/trigger_qa_protocol type="full_regression_suite" target="staging_environment"`
    
18.  `/review_code_as_principal_engineer pull_request_url="http://github.com/..." focus=["seguridad", "escalabilidad"]`
    
19.  `/compare_solutions options=["solucion_A.js", "solucion_B.js"] criteria=["performance_O(n)", "legibilidad", "mantenibilidad"]`
    
20.  `/ensure_idempotency target_endpoint="POST /api/v1/payments"`
    

### **Sección 4: 100 Ejemplos de Instrucciones de Élite para el SDLC**

Aquí tienes 100 instrucciones listas para usar, adaptadas a cada fase del ciclo de vida del software.

#### **Fase 1: Estrategia, Planificación y Requisitos (20 Ejemplos)**

1.  **Definir MVP**: Actúa como un Product Manager Lean. Realiza un análisis **holístico** de la visión del producto "plataforma de e-learning para Bolivia". **Propón** un plan **secuencial** para el lanzamiento, empezando por un MVP. **De forma selectiva**, define las 3 características absolutamente críticas para el MVP y **justifica** por qué validan el núcleo del negocio.
    
2.  **Crear User Stories**: Actúa como un Business Analyst. Para la épica "Gestión de Perfil de Usuario", **desglosa** de forma **algorítmica** las User Stories necesarias, siguiendo el formato "Como [usuario], quiero [acción], para [beneficio]". Asegúrate de incluir criterios de aceptación **cuantitativos**.
    
3.  **Análisis Competitivo Técnico**: Actúa como Analista de Inteligencia Competitiva. Realiza un análisis **comparativo** de la arquitectura técnica percibida de "Tigo Money" y "BNB Móvil". **Identifica** de forma **selectiva** tres debilidades o fricciones en su flujo de usuario que representen una oportunidad **estratégica** para una nueva fintech.
    
4.  **Priorizar Backlog**: Actúa como Product Owner. **Proporciona** un método **algorítmico** (ej. RICE o MoSCoW) para priorizar nuestro backlog actual. **Aplica** este método a las 10 tareas que te listo y presenta el resultado **justificado** y priorizado.
    
5.  **Identificar Riesgos de Proyecto**: Actúa como Jefe de Proyecto. Realiza un análisis **holístico** de nuestro plan de proyecto para "migrar a microservicios". **Identifica** y **cuantifica** (en impacto y probabilidad) los 5 principales riesgos técnicos y de negocio. **Propón** un plan de mitigación **estratégico**.
    
6.  **Definir Requisitos No Funcionales**: Actúa como Arquitecto de Software. Para nuestra nueva API de e-commerce, **define** los requisitos no funcionales clave. **De forma reflexiva**, considera la escalabilidad, seguridad y rendimiento, y **establece** métricas **cuantitativas** para cada uno (ej. "latencia de API < 100ms en el percentil 95").
    
7.  **Crear un Roadmap de Producto**: Actúa como Head of Product. **Conceptualiza** un roadmap de producto **estratégico** para los próximos 9 meses. **Desglosa** el roadmap en iniciativas trimestrales y presenta la secuencia de forma **justificada**, alineándola con los objetivos de negocio de la empresa.
    
8.  **Validar una Idea de Feature**: Actúa como un UX Researcher. **Diseña** un plan **secuencial** para validar la necesidad de una feature de "gamificación" en nuestra app educativa. **Propón** una serie de preguntas de entrevista y un script de prueba de prototipo para obtener feedback **eficaz**.
    
9.  **Estimación de Esfuerzo Inicial**: Actúa como un Tech Lead. Dado este conjunto de 10 user stories, realiza una estimación de esfuerzo **comparativa** usando puntos de historia de Fibonacci. **Justifica** brevemente las estimaciones más altas.
    
10.  **Refinamiento de Requisitos**: Actúa como un Systems Analyst. Revisa este requisito vago: "Mejorar el dashboard". **De forma reflexiva e iterante**, formula 5 preguntas clave para el Product Owner que clarifiquen el requisito y lo hagan medible y **eficaz**.
    
11.  **Definir OKRs Técnicos**: Actúa como Engineering Manager. Para el próximo trimestre, **propón** 3 Objetivos y Resultados Clave (OKRs) para el equipo de desarrollo. **Elabora** un plan **estratégico** que asegure que estos OKRs (ej. "Reducir la deuda técnica") estén alineados con las metas del producto.
    
12.  **Análisis de Stakeholders**: Actúa como Project Manager. Realiza un mapeo **holístico** de los stakeholders para el proyecto "Nuevo Portal de Clientes". **Clasifícalos** de forma **selectiva** usando una matriz poder/interés y **propón** una estrategia de comunicación **eficaz** para cada grupo.
    
13.  **Diseñar un A/B Test**: Actúa como Data Scientist. **Diseña** un experimento A/B **algorítmico** para probar un nuevo flujo de checkout. **Define** la hipótesis, las métricas primarias y secundarias a medir, el tamaño de la muestra requerido y la duración **justificada** del test.
    
14.  **Documento de Visión de Producto**: Actúa como Product Manager. **Sintetiza** nuestra visión de producto en un documento conciso. **De forma reflexiva**, articula el problema que resolvemos, para quién lo resolvemos, y nuestra propuesta de valor única de manera **estratégica** y motivadora.
    
15.  **Análisis de Viabilidad Técnica**: Actúa como Tech Lead. **Evalúa** la viabilidad técnica de integrar una "API de reconocimiento facial" en nuestra app. **Realiza** un análisis **comparativo** de 3 proveedores, considerando costo, precisión y facilidad de integración. **Presenta** una recomendación **justificada**.
    
16.  **Workshop de Event Storming**: Actúa como Facilitador Ágil. **Diseña** la agenda para un workshop de Event Storming remoto para modelar un nuevo dominio de negocio. **Estructura** el workshop de forma **secuencial** para asegurar un resultado **eficaz**.
    
17.  **Definir Métricas North Star**: Actúa como Head of Product. **De forma reflexiva y estratégica**, propón una Métrica North Star para nuestra plataforma SaaS. **Justifica** por qué esta métrica **cuantitativa** encapsula el valor central que entregamos a nuestros clientes.
    
18.  **Análisis Legal y de Cumplimiento**: Actúa como Analista de Cumplimiento. **Identifica** los requisitos de cumplimiento de datos (ej. GDPR, CCPA) que aplican a nuestro proyecto, que manejará datos de usuarios de Europa y California. **Resume** los 5 puntos técnicos más importantes a considerar.
    
19.  **Crear un Press Release Técnico**: Actúa como Technical Marketing Manager. **Redacta** el borrador de un comunicado de prensa para el lanzamiento de nuestra nueva API pública. **Traduce** las características técnicas complejas a beneficios **eficaces** y entendibles por una audiencia más amplia.
    
20.  **Definir el "Definition of Done" (DoD)**: Actúa como Scrum Master. **Propón** un "Definition of Done" **holístico** para nuestro equipo, que incluya criterios de calidad, pruebas, documentación y revisión de código. **Justifica** por qué cada punto es crucial para la entrega de valor.
    

#### **Fase 2: Arquitectura y Diseño de Sistemas (20 Ejemplos)**

21.  **Elegir Arquitectura**: Actúa como Arquitecto de Soluciones. Realiza un análisis **comparativo** entre una arquitectura de microservicios y un monolito modular para nuestra nueva aplicación de logística. **Recomienda** una arquitectura **justificada** basada en nuestros objetivos **estratégicos** de escalabilidad y velocidad de desarrollo.
    
22.  **Diseñar Modelo de Datos**: Actúa como DBA. Diseña un modelo de datos relacional (SQL) **algorítmico** y normalizado para un sistema de "gestión de historiales médicos". **Genera** el script DDL y un diagrama entidad-relación en código Mermaid.
    
23.  **Diseñar Contrato de API**: Actúa como Ingeniero Backend. Diseña el contrato OpenAPI 3.0 para la API de "Notificaciones". **Piensa de forma holística** en los tipos de notificaciones (push, email, SMS) y **estructura** los endpoints de manera **eficaz** y RESTful.
    
24.  **Seleccionar Pila Tecnológica**: Actúa como CTO. **Propón** una pila tecnológica (backend, frontend, base de datos) para un proyecto de "marketplace de servicios locales". **Realiza** un análisis **comparativo** entre 2-3 opciones para cada capa y **justifica** tu elección **estratégica** final.
    
25.  **Plan de Componentes Reutilizables**: Actúa como Líder de Frontend. **Analiza holísticamente** nuestros 3 proyectos actuales en React. **Identifica de forma selectiva** 5 componentes de UI que puedan ser abstraídos a una librería de componentes compartida. **Esboza** un plan **secuencial** para su implementación.
    
26.  **Diseño de Flujo de Autenticación**: Actúa como Especialista en Seguridad. Diseña un flujo de autenticación **secuencial** y seguro usando OAuth 2.0 (Authorization Code Flow) para permitir que los usuarios inicien sesión con Google. **Dibuja** el diagrama de secuencia en Mermaid.
    
27.  **Arquitectura Serverless**: Actúa como Arquitecto Cloud. **Conceptualiza** una arquitectura 100% serverless en AWS para un servicio que "procesa imágenes subidas por usuarios". **Describe** el flujo **secuencial** usando S3, Lambda, y Rekognition, y **justifica** por qué este enfoque es **eficaz** en costos.
    
28.  **Diseño de Caché**: Actúa como Ingeniero de Performance. **Diseña una estrategia de caché** **holística** para nuestra API. **Define** qué endpoints se beneficiarían de caché (usando Redis), qué estrategia de invalidación usar (ej. TTL, write-through) y **cuantifica** el impacto esperado en la latencia.
    
29.  **Patrón de Tolerancia a Fallos**: Actúa como SRE. **Propón** la implementación del patrón "Circuit Breaker" para las llamadas a nuestro servicio de pago externo. **Describe algorítmicamente** cómo funcionaría y en qué condiciones el circuito se abriría y cerraría.
    
30.  **Diagrama C4**: Actúa como Arquitecto de Software. **Genera** un diagrama de Contexto (Nivel 1) del modelo C4 para nuestro sistema de "reservas de hotel". **De forma reflexiva**, asegúrate de que todos los sistemas externos y tipos de usuarios estén representados.
    
31.  **Diseño de una Data Pipeline**: Actúa como Ingeniero de Datos. **Diseña** una pipeline de datos **secuencial** para ingestar eventos de clickstream en tiempo real. **Propón** una arquitectura usando Kafka, Spark Streaming y un data lake en S3. **Justifica** la elección de cada componente.
    
32.  **Modelado de Amenazas de Seguridad**: Actúa como Ingeniero de Seguridad. **Aplica** el modelo STRIDE para realizar un modelado de amenazas **holístico** sobre nuestro nuevo servicio de autenticación. **Identifica** de forma **selectiva** las 3 amenazas más críticas y propón mitigaciones.
    
33.  **Configuración de API Gateway**: Actúa como Arquitecto Cloud. **Diseña** la configuración para un API Gateway (ej. en AWS o Kong) que sirva como fachada para 5 microservicios. **Define** las estrategias de enrutamiento, rate limiting y autenticación de forma **estratégica**.
    
34.  **Arquitectura Multi-Tenant**: Actúa como Arquitecto SaaS. **Realiza un análisis comparativo** de 3 estrategias de arquitectura multi-tenant (base de datos separada, esquema separado, datos discriminados por columna). **Recomienda** y **justifica** la mejor opción para nuestro producto.
    
35.  **Patrón Saga para Transacciones**: Actúa como experto en Microservicios. **Diseña** una transacción distribuida usando el patrón Saga (coreografía) para el proceso de "crear un pedido". **Dibuja** el diagrama **secuencial** de los eventos intercambiados entre los servicios.
    
36.  **Diseño de Logging y Monitoreo**: Actúa como SRE. **Define** una estrategia de logging **holística** y **estratégica** para nuestra aplicación. **Especifica** un formato de log JSON estructurado y las métricas clave (RED: Rate, Errors, Duration) que cada servicio debe exponer a Prometheus.
    
37.  **Patrón Strangler Fig**: Actúa como Arquitecto de Migración. **Esboza** un plan **secuencial** para migrar una funcionalidad de nuestro monolito a un nuevo microservicio usando el patrón Strangler Fig. **Describe** cómo el proxy interceptaría y redirigiría el tráfico de forma **iterante**.
    
38.  **Selección de una Cola de Mensajes**: Actúa como Ingeniero Backend. **Realiza un análisis comparativo** entre RabbitMQ y SQS. **Evalúa** bajo criterios de throughput, latencia, y modelo de entrega. **Recomienda** la mejor opción para nuestro caso de uso de "procesamiento de pedidos asíncrono".
    
39.  **Decisiones de Diseño en un ADR**: Actúa como Tech Lead. **Escribe** un Architecture Decision Record (ADR) para documentar la decisión de "adoptar GraphQL en lugar de REST" para nuestra API de cara al cliente. **De forma reflexiva**, incluye el contexto, las opciones consideradas y las consecuencias **justificadas**.
    
40.  **Diseño de API Idempotente**: Actúa como Ingeniero de API. **Diseña** el mecanismo para hacer que nuestro endpoint `POST /api/payments` sea idempotente. **Propón** el uso de un `Idempotency-Key` en la cabecera y describe el flujo **algorítmico** del lado del servidor.
    

#### **Fase 3: Desarrollo e Implementación (20 Ejemplos)**

41.  **Generar Código con TDD**: Actúa como desarrollador Python senior. **Implementa** una función `validate_ci(document_number)` que valida un carnet de identidad boliviano. **Sigue un proceso TDD iterante**: primero genera los casos de prueba con `pytest`, luego el código de la función para que pasen.
    
42.  **Refactorizar Código**: Actúa como experto en Clean Code. Revisa este método de 200 líneas [pegar código]. **Realiza un refactor estratégico**, extrayendo métodos más pequeños y con un único propósito. **Aplica de forma selectiva** patrones de diseño que mejoren la legibilidad y mantenibilidad.
    
43.  **Implementar un Algoritmo**: Actúa como Ingeniero de Software. **Implementa** el algoritmo de "Búsqueda Binaria" en TypeScript de forma genérica para que funcione con arrays de cualquier tipo ordenable. **Añade** comentarios explicando la lógica **algorítmica** paso a paso.
    
44.  **Integrar una API Externa**: Actúa como desarrollador Go. **Escribe** un cliente para la API del clima OpenWeatherMap. **Implementa** una función que, dada una latitud y longitud, devuelva el clima actual. **Maneja los errores de red y de la API de forma eficaz**.
    
45.  **Resolver un Problema de Concurrencia**: Actúa como experto en Java concurrente. **Revisa este código** que presenta una race condition al actualizar un contador. **Corrige** el problema usando clases del paquete `java.util.concurrent` y **justifica** tu elección.
    
46.  **Crear un Componente de UI**: Actúa como desarrollador React. **Crea** un componente `DataTable` reutilizable. **El componente debe ser eficaz**, soportando paginación, ordenamiento y filtrado del lado del cliente. **Escribe** la documentación de sus props usando PropTypes o TypeScript.
    
47.  **Escribir una Consulta SQL Compleja**: Actúa como analista de datos. **Escribe** una consulta SQL que obtenga "el top 5 de clientes con mayor gasto en el último trimestre", uniendo las tablas `customers`, `orders` y `order_items`. **Optimiza la consulta para que sea eficaz**.
    
48.  **Configurar Inyección de Dependencias**: Actúa como desarrollador .NET. **Configura** el contenedor de inyección de dependencias para registrar un `OrderService` y su dependencia `IOrderRepository` con un ciclo de vida "scoped". **Explica estratégicamente** por qué "scoped" es la elección correcta para este caso.
    
49.  **Manejo de Estado en Frontend**: Actúa como especialista en Vue.js. **Realiza un análisis comparativo** entre Pinia y Vuex para la gestión de estado de nuestra nueva aplicación. **Recomienda** una librería y **estructura** un store inicial para la gestión de "carrito de compras".
    
50.  **Script de Automatización**: Actúa como desarrollador Python. **Escribe** un script que **de forma iterante** lea archivos `.csv` de una carpeta, procese los datos y los inserte en una base de datos PostgreSQL. **Hazlo robusto y eficaz**.
    
51.  **Implementar un Servidor GraphQL**: Actúa como Ingeniero Backend. **Usando** Apollo Server y Node.js, **implementa** un servidor GraphQL básico con un query `user(id: ID!)` que retorne un usuario. **Define** los tipos y el resolver correspondiente.
    
52.  **Manejo de Errores Centralizado**: Actúa como desarrollador Express.js. **Implementa** un middleware de manejo de errores **holístico** que capture todos los errores de la aplicación, los registre y retorne una respuesta JSON estandarizada y **eficaz**.
    
53.  **Implementar WebSockets**: Actúa como desarrollador Full-Stack. **Implementa** una comunicación en tiempo real usando Socket.IO para una funcionalidad de "chat en vivo". **Escribe** el código del servidor que emite eventos y el del cliente que los escucha.
    
54.  **Crear un Hook de React Personalizado**: Actúa como desarrollador React senior. **Crea** un hook personalizado `useFetch(url)` que encapsule la lógica de fetching de datos, incluyendo los estados de carga, error y datos. **Hazlo reutilizable y eficaz**.
    
55.  **Programación Funcional**: Actúa como programador funcional en JavaScript. **Refactoriza** este bucle `for` con un `if/else` anidado [pegar código] usando una composición de funciones `map`, `filter` y `reduce`. **Justifica** la mejora en legibilidad.
    
56.  **Implementar Accesibilidad (a11y)**: Actúa como desarrollador Frontend consciente. **Revisa** este componente de modal en HTML/CSS. **Identifica** y **corrige** 3 problemas de accesibilidad, como la falta de roles ARIA, el manejo del foco y el contraste de color.
    
57.  **Generar un PDF**: Actúa como desarrollador Python. **Usando** la librería ReportLab o similar, **escribe** una función que genere una factura en PDF a partir de un objeto JSON con los datos del pedido.
    
58.  **Procesamiento de Imágenes**: Actúa como desarrollador Backend. **Escribe** una función usando Sharp (Node.js) o Pillow (Python) que tome una imagen subida, la redimensione a 3 tamaños diferentes (thumbnail, medium, large) y la guarde en disco.
    
59.  **Crear un CLI**: Actúa como desarrollador Go. **Usando** la librería Cobra, **crea** una herramienta de línea de comandos simple con un comando `app deploy` que tome un argumento de entorno (`--env=staging`).
    
60.  **Escribir Código Seguro**: Actúa como especialista en seguridad. **Revisa esta consulta SQL** construida con concatenación de strings [pegar código]. **Reescríbela** usando consultas parametrizadas para prevenir inyección SQL y **explica** el riesgo.
    

#### **Fase 4: Pruebas, Calidad y Revisión (20 Ejemplos)**

61.  **Crear Pruebas Unitarias**: Actúa como SDET. Para la función `calculate_tax(income, region)`, **genera** una suite de pruebas unitarias **algorítmica** que cubra todos los caminos lógicos, casos borde y de error. Usa `mocks` para las dependencias externas.
    
62.  **Realizar Code Review**: Actúa como Líder Técnico. **Realiza una revisión reflexiva** de este Pull Request [pegar código]. **Enfócate selectivamente** en la lógica de negocio, la seguridad y el rendimiento, en lugar de solo en el estilo. **Proporciona** feedback constructivo y **eficaz**.
    
63.  **Plan de Pruebas de Integración**: Actúa como Ingeniero de QA. **Diseña** un plan de pruebas de integración **secuencial** para el flujo "compra de producto". **Detalla** las interacciones que se probarán entre el servicio de `frontend`, `API Gateway`, `servicio de pedidos` y `servicio de pagos`.
    
64.  **Configurar Linter y Formateador**: Actúa como desarrollador Frontend. **Configura** ESLint y Prettier para un proyecto TypeScript/React. **Define** un conjunto de reglas **estratégicas** que promuevan un código limpio y consistente en todo el equipo.
    
65.  **Pruebas de Performance**: Actúa como Ingeniero de Performance. **Diseña** un escenario de prueba de carga usando k6 o JMeter para el endpoint `GET /products`. **El objetivo es cuantificar** la latencia y el throughput bajo 1000 usuarios concurrentes.
    
66.  **Análisis de Cobertura de Código**: Actúa como Ingeniero de Calidad. **Analiza este reporte** de cobertura de código que muestra un 70%. **Identifica de forma selectiva** las 3 áreas críticas del código con menor cobertura y **propón** los casos de prueba necesarios para mejorarlo de forma **eficaz**.
    
67.  **Pruebas End-to-End (E2E)**: Actúa como Ingeniero de Automatización. **Escribe** un script de prueba E2E usando Cypress o Playwright que **simule el flujo completo** de un usuario registrándose en el sitio, iniciando sesión y actualizando su perfil.
    
68.  **Pruebas de Mutación**: Actúa como experto en calidad de software. **Explica el concepto** de Pruebas de Mutación. **Genera** un ejemplo de cómo una herramienta como Stryker (para JavaScript) podría ser usada para **evaluar de forma reflexiva** la calidad de nuestra suite de pruebas actual.
    
69.  **Revisión de Arquitectura**: Actúa como Arquitecto Principal. **Organiza una revisión holística** de la arquitectura propuesta para el nuevo "servicio de recomendaciones". **Prepara** una lista de preguntas **estratégicas** para guiar la discusión del equipo.
    
70.  **Checklist de Calidad Pre-lanzamiento**: Actúa como Release Manager. **Crea** un checklist de calidad **algorítmico** que deba ser completado antes de cada despliegue a producción. **Incluye** verificaciones de pruebas, documentación y configuración.
    
71.  **Pruebas de Contrato (Contract Testing)**: Actúa como SDET. **Escribe** una prueba de contrato del lado del consumidor usando Pact para el `servicio-frontend`. **Define** las expectativas de interacción con el `servicio-usuarios` para el endpoint `GET /users/{id}`.
    
72.  **Pruebas de Seguridad (Pentesting)**: Actúa como Hacker Ético. **Realiza un análisis selectivo** de nuestro endpoint de login. **Describe** 3 posibles vectores de ataque (ej. enumeración de usuarios, fuerza bruta, timing attack) y cómo intentarías explotarlos.
    
73.  **Pruebas de Regresión Visual**: Actúa como Ingeniero de Frontend QA. **Configura** una herramienta como Percy o Storybook para realizar pruebas de regresión visual en nuestra librería de componentes. **Describe** el flujo de trabajo **secuencial**.
    
74.  **Benchmarking de Performance**: Actúa como Ingeniero de Performance. **Escribe** un script de benchmark en Go para **comparar** el rendimiento de dos implementaciones de una función de hashing. **Ejecuta** el benchmark de forma **iterante** y presenta los resultados.
    
75.  **Pruebas de Caos (Chaos Engineering)**: Actúa como Ingeniero de Caos. **Diseña** un experimento de caos para probar la resiliencia de nuestro sistema. **Propón** inyectar latencia en las llamadas al servicio de base de datos y **define** las métricas a observar para verificar si el sistema se degrada con gracia.
    
76.  **Revisión de Dependencias de Seguridad**: Actúa como Ingeniero DevSecOps. **Describe** el proceso **secuencial** para configurar una herramienta como `npm audit` o `Snyk` en nuestro pipeline de CI para escanear y alertar sobre vulnerabilidades en dependencias de terceros.
    
77.  **Análisis Estático de Código**: Actúa como especialista en calidad. **Configura** SonarQube para nuestro proyecto Java. **Define** un perfil de calidad **estratégico** y explica cómo interpretar las métricas de "code smells" y "deuda técnica".
    
78.  **Generación de Datos de Prueba**: Actúa como Ingeniero de QA. **Escribe** un script usando Faker.js para generar 1000 registros de usuarios falsos con datos realistas para poblar nuestra base de datos de staging.
    
79.  **Revisión de la Experiencia del Desarrollador (DX)**: Actúa como Developer Advocate. **Realiza una revisión holística** de nuestro proceso de onboarding para nuevos desarrolladores. **Identifica** 3 puntos de fricción y **propón** mejoras **eficaces** a la documentación o a los scripts de configuración.
    
80.  **Validación del Plan de Pruebas**: Actúa como QA Lead. **Revisa este plan de pruebas** [pegar plan]. **De forma reflexiva**, evalúa si cubre adecuadamente todos los requisitos y si la estrategia de pruebas es **eficaz** y rentable.
    

#### **Fase 5: Despliegue, Operaciones y Mantenimiento (20 Ejemplos)**

81.  **Crear Dockerfile Optimizado**: Actúa como Ingeniero DevOps. **Crea** un `Dockerfile` de producción multi-etapa para una aplicación en Go. **Optimízalo de forma estratégica** para que la imagen final sea mínima en tamaño y segura (sin correr como root).
    
82.  **Configurar Pipeline CI/CD**: Actúa como especialista en CI/CD. **Diseña** un pipeline en GitLab CI/CD. **El pipeline debe ser secuencial**: `build -> test -> sonar_scan -> deploy_to_staging -> manual_deploy_to_prod`. **Hazlo eficaz** usando caché de dependencias.
    
83.  **Debugging de un Problema en Producción**: Actúa como SRE. **Tenemos un pico de errores 503** en nuestro servicio de usuarios. **Guíame de forma secuencial y algorítmica** a través del proceso de debugging, usando logs (Kibana) y métricas (Prometheus/Grafana) para encontrar la causa raíz.
    
84.  **Optimizar Consulta Lenta**: Actúa como DBA. **Esta consulta SQL está degradando el rendimiento**. [Pegar consulta]. **Analiza su plan de ejecución de forma reflexiva**, propón un índice faltante y reescribe la consulta para que sea más **eficaz**.
    
85.  **Generar Documentación de API**: Actúa como Technical Writer. **A partir de este código** de controlador en NestJS, **genera automáticamente** la documentación para los desarrolladores usando Swagger/OpenAPI.
    
86.  **Script de Monitoreo**: Actúa como Ingeniero de Operaciones. **Escribe** un script en Bash o Python que verifique la salud de nuestra aplicación (health check endpoint) y envíe una alerta a Slack si no responde correctamente. **Hazlo resiliente y eficaz**.
    
87.  **Plan de Rollback**: Actúa como Release Manager. **Define un plan de rollback estratégico** para nuestro próximo despliegue. **Detalla los pasos secuenciales** a seguir y los criterios **cuantitativos** (ej. tasa de error > 5%) que activarían el rollback.
    
88.  **Análisis Post-mortem**: Actúa como SRE. **Redacta** un post-mortem "blameless" sobre la reciente caída del servicio. **Realiza un análisis holístico** de la causa raíz y **propón** acciones correctivas **estratégicas** y medibles.
    
89.  **Optimización de Costos en la Nube**: Actúa como especialista en FinOps. **Analiza nuestro reporte de costos de AWS**. **Identifica de forma selectiva** los 3 principales generadores de costos y **propón** acciones **eficaces** para optimizarlos (ej. usar instancias Spot, configurar políticas de ciclo de vida en S3).
    
90.  **Automatizar Tareas de Mantenimiento**: Actúa como Administrador de Sistemas. **Escribe** un Ansible playbook que **de forma iterante** se conecte a todos nuestros servidores web, aplique las últimas actualizaciones de seguridad y reinicie el servicio.
    
91.  **Infraestructura como Código (IaC)**: Actúa como Ingeniero Cloud. **Escribe** una configuración de Terraform para aprovisionar una red VPC en AWS con subredes públicas y privadas. **Estructura** el código en módulos reutilizables de forma **estratégica**.
    
92.  **Estrategia de Feature Flags**: Actúa como Ingeniero de Software. **Diseña** una estrategia de feature flags para lanzar nuestra nueva "integración con PayPal". **Describe** cómo usarías los flags para un lanzamiento **secuencial** y controlado (ej. interno -> beta -> 10% de usuarios -> 100%).
    
93.  **Crear un Dashboard de Observabilidad**: Actúa como SRE. **Define** el JSON para un dashboard de Grafana que muestre las métricas de salud **holísticas** de nuestro servicio de pedidos, incluyendo las métricas RED, el uso de CPU/memoria y la latencia de la base de datos.
    
94.  **Estrategia de Migración de Base de Datos**: Actúa como DBA. **Esboza** un plan de migración **secuencial** y sin tiempo de inactividad (zero-downtime) para actualizar nuestra base de datos PostgreSQL de la versión 12 a la 14.
    
95.  **Gestión de Secretos**: Actúa como Ingeniero DevSecOps. **Realiza un análisis comparativo** entre AWS Secrets Manager y HashiCorp Vault. **Recomienda** una solución para gestionar los secretos de nuestra aplicación y **describe** el flujo para que una aplicación obtenga sus credenciales de forma segura.
    
96.  **Plan de Recuperación ante Desastres (DRP)**: Actúa como Arquitecto de Resiliencia. **Diseña** un plan de DRP **estratégico** para nuestra aplicación principal. **Define** los objetivos de RTO y RPO y **describe** la arquitectura multi-región necesaria para cumplirlos.
    
97.  **Alertas Inteligentes**: Actúa como Ingeniero de Monitoreo. **Escribe** una regla de alerta para Prometheus (Alertmanager) que se active solo si la tasa de errores de un servicio es superior al 5% durante 5 minutos consecutivos. **Justifica** por qué esto es más **eficaz** que una alerta de umbral simple.
    
98.  **Rotación de Logs**: Actúa como Administrador de Sistemas. **Configura** `logrotate` en un servidor Linux para gestionar los logs de nuestra aplicación, rotándolos diariamente, comprimiéndolos y manteniéndolos durante 30 días.
    
99.  **Crear un Runbook**: Actúa como Ingeniero de Operaciones. **Crea** un runbook para el equipo de guardia que detalle los pasos **algorítmicos** a seguir cuando se reciba la alerta "Alta Latencia en la Base de Datos".
    
100.  **Análisis de Capacidad**: Actúa como Ingeniero de Performance. **Analiza las métricas** de uso de CPU y memoria de los últimos 6 meses. **Proyecta** el crecimiento y **determina de forma cuantitativa** cuándo necesitaremos escalar vertical u horizontalmente nuestra flota de servidores.