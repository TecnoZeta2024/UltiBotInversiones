Épica 1: Configuración Fundacional y Conectividad Segura

Objetivo de la Épica: Establecer la configuración base del sistema "UltiBotInversiones", asegurar la conectividad con Binance y servicios de notificación (Telegram), y permitir la gestión segura de credenciales.
Siguiendo las directrices de mi tarea "Crear PRD" y los "Principios Guía para la Generación de Épicas e Historias de Usuario", he preparado un primer borrador de las Historias de Usuario para esta Épica. También he pensado en un orden lógico para implementarlas.

Te presento la lista de historias propuestas para esta Épica 1, su secuencia y una breve justificación:

# Historias de Usuario Propuestas para la Épica 1:

Orden Sugerido:

Como usuario de UltiBotInversiones, quiero que el sistema cargue una configuración básica al arrancar y pueda guardar de forma segura y persistente (en la base de datos Supabase/PostgreSQL) cualquier ajuste esencial, como las preferencias iniciales o la ubicación de las credenciales encriptadas, para asegurar que la aplicación inicie correctamente y recuerde mis ajustes importantes entre sesiones.

Historia 1.1: Configuración y Almacenamiento Seguro de Credenciales del Sistema

Como usuario de UltiBotInversiones, quiero poder ingresar y que el sistema almacene de forma segura y encriptada todas mis claves API necesarias (Binance, Gemini, Telegram, Mobula, y para los servidores MCP que configure), para que "UltiBotInversiones" pueda operar en mi nombre e interactuar con estos servicios externos sin exponer mis credenciales sensibles.

Historia 1.2: Inicialización y Verificación del Bot de Notificaciones de Telegram

Como usuario de UltiBotInversiones, quiero que el sistema utilice mis credenciales de Telegram para conectarse a mi bot personal y enviar un mensaje de prueba, para confirmar que puedo recibir notificaciones importantes sobre la actividad del sistema y las operaciones directamente en Telegram.

Historia 1.3: Verificación de Conectividad y Estado Básico de la Cuenta de Binance

Como usuario de UltiBotInversiones, quiero que el sistema utilice mis credenciales de Binance para verificar la conectividad con mi cuenta y mostrarme el estado básico de mis balances (específicamente el saldo de USDT disponible), para asegurar que el sistema está correctamente enlazado y listo para futuras operaciones (simuladas o reales).
Justificación del Orden Propuesto:

Propuesta de Reordenamiento para Épica 1:

Este nuevo "Bloque Fundacional Técnico" (Historias 1.0.1 a 1.0.5) debería ejecutarse primero. Después de completar estas historias, el orden de las historias previamente definidas (1.4, 1.1, 1.2, 1.3) sigue siendo lógico:

Historia 1.0.1: Configuración del Repositorio y Estructura Inicial del Proyecto (Monorepo)
Historia 1.0.2: Configuración del Entorno de Desarrollo Base (Docker y Dependencias)
Historia 1.0.3: Andamiaje Inicial para el Monolito Modular
Historia 1.0.4: Puesta en Marcha del Framework de Pruebas Unitarias
Historia 1.0.5: Configuración Inicial de la Infraestructura en Supabase (Base de Datos)
Historia 1.1: Configuración y Almacenamiento Seguro de Credenciales del Sistema (la original)
Historia 1.2: Inicialización y Verificación del Bot de Notificaciones de Telegram (la original)
Historia 1.3: Verificación de Conectividad y Estado Básico de la Cuenta de Binance (la original)
Historia 1.4: Configuración Inicial de la Aplicación y Persistencia de Datos Fundamentales (la original)


## Historia 1.0.1: Configuración del Repositorio y Estructura Inicial del Proyecto (Monorepo)

Como: Equipo de Desarrollo,
Quiero: Configurar el repositorio Git (Monorepo) y establecer la estructura de directorios inicial del proyecto "UltiBotInversiones",
Para que: Podamos asegurar una base organizada y coherente para todo el desarrollo futuro y facilitar la gestión de dependencias.

### Criterios de Aceptación:

Se crea un nuevo repositorio Git para el proyecto "UltiBotInversiones".
Se define y aplica la estructura de directorios raíz para el Monorepo (ej. src/, docs/, tests/, scripts/, infra/) según la decisión de "Monorepo" y "Monolito Modular" documentada en la sección "Suposiciones Técnicas" del PRD. 


Se incluye un archivo README.md inicial en la raíz del proyecto con el nombre del proyecto y una breve descripción placeholder.
Se configura un archivo .gitignore base para excluir archivos y directorios comúnmente innecesarios en el control de versiones (ej. __pycache__/, *.pyc, venv/, build/, dist/, *.env, secrets/).
La estructura inicial dentro de src/ refleja la arquitectura de "Monolito Modular" (ej. se crean directorios placeholder como src/core_logic/, src/data_management/, src/interfaces/, src/app_ui/ si aplica, etc.). 

## Historia 1.0.2: Configuración del Entorno de Desarrollo Base (Docker y Dependencias)

Como: Equipo de Desarrollo,
Quiero: Configurar el entorno de desarrollo base utilizando Docker y Poetry (para la gestión de dependencias de Python),
Para que: Podamos asegurar un entorno de desarrollo consistente, reproducible y aislado para todos los miembros del equipo y para los futuros procesos de Integración Continua/Despliegue Continuo (CI/CD).

### Criterios de Aceptación:

Se crea un Dockerfile (o un docker-compose.yml si se prefiere para gestionar múltiples servicios localmente) que define el entorno de ejecución principal basado en Python 3.11+. 
Se inicializa Poetry en el proyecto, generando un archivo pyproject.toml para la gestión de dependencias de Python. 
Se añaden las dependencias iniciales del stack tecnológico confirmado (ej. FastAPI, PyQt5, google-generativeai) al pyproject.toml. 
Se incluyen scripts básicos (ej. en una carpeta scripts/) para construir la imagen de Docker y para ejecutar un contenedor en modo de desarrollo (ej. montando el código fuente local).
El entorno de desarrollo permite la instalación exitosa de las dependencias y la ejecución de una aplicación Python básica dentro del contenedor Docker.

## Historia 1.0.3: Andamiaje Inicial para el Monolito Modular

Como: Equipo de Desarrollo,
Quiero: Implementar el andamiaje básico para la arquitectura de "Monolito Modular" dentro del directorio src/, definiendo los directorios para los módulos principales (ej. para la lógica del núcleo, acceso a datos, interfaces/adaptadores, UI si es parte del monolito),
Para que: Se establezca una estructura de código clara desde el principio, que facilite el desarrollo organizado, la separación de responsabilidades y la futura evolución del sistema. 

### Criterios de Aceptación:

Dentro de src/, se crean los directorios que representarán los principales módulos del Monolito Modular (ej. src/core_logic/, src/data_access/, src/api_services/, src/ui_layer/ si aplica), según se alinee con la visión arquitectónica.
Cada directorio de módulo principal contiene un archivo __init__.py (si es Python) y un README.md placeholder que describe brevemente la responsabilidad futura de ese módulo.
Se define conceptualmente (ej. en los READMEs de los módulos) cómo estos módulos principales interactuarán, preparando el terreno para interfaces bien definidas.

## Historia 1.0.4: Puesta en Marcha del Framework de Pruebas Unitarias

Como: Equipo de Desarrollo,
Quiero: Configurar e integrar un framework de pruebas unitarias (ej. PyTest para Python) en el proyecto,
Para que: Podamos escribir y ejecutar pruebas unitarias desde el inicio del desarrollo, asegurando la calidad del código, facilitando la refactorización y promoviendo buenas prácticas de desarrollo.

### Criterios de Aceptación:
El framework de pruebas unitarias (ej. PyTest) y cualquier librería de apoyo necesaria (ej. pytest-cov para cobertura) se añaden como dependencias de desarrollo en pyproject.toml.
Se establece la estructura de directorios para las pruebas unitarias (ej. tests/unit/) según las convenciones del PRD y futuro Documento de Arquitectura. 
Se crea una prueba unitaria de ejemplo simple (ej. para una función de utilidad básica) dentro de la estructura de pruebas, y esta prueba se ejecuta exitosamente.
Se añaden o configuran scripts (ej. en scripts/ o mediante comandos de Poetry en pyproject.toml) para ejecutar fácilmente todas las pruebas unitarias.
Se documenta brevemente en el README.md principal o en docs/operational-guidelines.md (si ya existe) cómo ejecutar las pruebas.

## Historia 1.0.5: Configuración Inicial de la Infraestructura en Supabase (Base de Datos)

Como: Equipo de Desarrollo,
Quiero: Realizar la configuración inicial del proyecto en Supabase, incluyendo la creación de la instancia de base de datos PostgreSQL y la obtención segura de las credenciales de conexión,
Para que: El sistema "UltiBotInversiones" pueda conectarse a una base de datos persistente para almacenar y recuperar datos esenciales de la aplicación desde las primeras etapas de desarrollo.

### Criterios de Aceptación:

Se crea un nuevo proyecto en la plataforma Supabase para "UltiBotInversiones".
Se obtienen las credenciales de conexión a la base de datos PostgreSQL proporcionadas por Supabase (como la URL de conexión, la clave de API de servicio (service_role key)).
Se establece un método seguro para que el equipo de desarrollo acceda a estas credenciales para el entorno local (ej. mediante un archivo .env que NO se commitea al repositorio, con un .env.example como plantilla). 
Se realiza una conexión de prueba exitosa a la base de datos Supabase desde el entorno de desarrollo local utilizando las credenciales obtenidas y una librería de Python para PostgreSQL (ej. psycopg2-binary o asyncpg si se planea asincronismo).

## Historia 1.1: Configuración y Almacenamiento Seguro de Credenciales del Sistema

Como usuario de UltiBotInversiones,
quiero poder ingresar y que el sistema almacene de forma segura y encriptada todas mis claves API necesarias (Binance, Gemini, Telegram, Mobula, y para los servidores MCP que configure),
para que "UltiBotInversiones" pueda operar en mi nombre e interactuar con estos servicios externos sin exponer mis credenciales sensibles.
Para asegurar que esta funcionalidad crítica se implemente de manera robusta y segura, te propongo los siguientes Criterios de Aceptación (ACs):

### Criterios de Aceptación para la Historia 1.1:

AC1 (Interfaz de Gestión de Credenciales - Backend): El sistema deberá tener la capacidad interna de recibir, actualizar y eliminar de forma segura las claves API para cada servicio externo requerido (Binance, Gemini, Telegram, Mobula). También deberá permitir un mecanismo para agregar y gestionar credenciales para múltiples servidores MCP. Nota: La interfaz de usuario (UI) específica para esta gestión se detallará en una historia de la Épica de UI, pero el backend debe estar preparado.

AC2 (Encriptación Fuerte en Reposo): Todas las claves API que el usuario ingrese deberán ser encriptadas utilizando un algoritmo de encriptación robusto y estándar (por ejemplo, AES-256 o Fernet, como se sugiere en la sub-tarea 6.1.1.1 de tu Plan_accion_26-5.md) antes de ser almacenadas de forma persistente en la base de datos Supabase/PostgreSQL.

AC3 (Desencriptación Segura y Oportuna): El sistema deberá implementar un mecanismo seguro para desencriptar las claves API necesarias únicamente en el momento de la ejecución, cuando se necesite interactuar con el servicio externo correspondiente. Se debe minimizar el tiempo que las claves permanezcan desencriptadas en la memoria de la aplicación. El diseño técnico detallará si esto requiere una contraseña maestra u otro mecanismo seguro para la clave de encriptación principal.

AC4 (Prohibición de Almacenamiento en Texto Plano): Bajo ninguna circunstancia las claves API deberán ser almacenadas o registradas (logueadas) en texto plano en ningún componente del sistema, ya sean archivos de configuración, logs del sistema o directamente en la base de datos sin la debida encriptación.

AC5 (Verificación Opcional de Validez de Claves): Al momento de ingresar o actualizar las claves API para servicios críticos (especialmente Binance, Gemini y Telegram), el sistema deberá intentar realizar una conexión de prueba básica o una llamada API no transaccional (que no genere costos ni operaciones) para verificar la validez de dichas credenciales y ofrecer retroalimentación inmediata al usuario en la UI. Si la verificación falla, la clave no se marcará como activa o verificada.

AC6 (Indicación del Estado de Configuración): La interfaz de usuario (cuando se desarrolle) deberá indicar claramente al usuario qué credenciales han sido configuradas y cuál es su estado de verificación (si se implementa AC5), sin nunca mostrar las claves secretas directamente.

## Historia 1.2: Inicialización y Verificación del Bot de Notificaciones de Telegram

Como usuario de UltiBotInversiones,
quiero que el sistema utilice mis credenciales de Telegram para conectarse a mi bot personal y enviar un mensaje de prueba,
para confirmar que puedo recibir notificaciones importantes sobre la actividad del sistema y las operaciones directamente en Telegram.
He aquí los Criterios de Aceptación (ACs) que propongo para asegurar que esta funcionalidad de notificación por Telegram quede perfectamente implementada:

### Criterios de Aceptación para la Historia 1.2:

AC1 (Acceso Seguro a Credenciales de Telegram): El sistema debe poder recuperar de manera segura el Token del Bot de Telegram y el Chat ID del usuario desde el almacén de credenciales encriptadas (cuya funcionalidad se estableció en la Historia 1.1).

AC2 (Conexión y Envío de Mensaje de Prueba Inicial): Al iniciar "UltiBotInversiones" por primera vez después de configurar las credenciales de Telegram, o cuando estas se actualicen, el sistema debe automáticamente intentar conectarse a la API de Telegram y enviar un mensaje de prueba predefinido al Chat ID especificado. Este mensaje podría ser algo como: "¡Hola! UltiBotInversiones se ha conectado correctamente a este chat y está listo para enviar notificaciones."

AC3 (Indicación de Conexión Exitosa en la UI): Si el mensaje de prueba se envía con éxito a Telegram, la interfaz de usuario de "UltiBotInversiones" (en la sección de configuración o en un indicador de estado del sistema) debe reflejar que la conexión con el servicio de notificaciones de Telegram está activa y ha sido verificada.

AC4 (Gestión Clara de Errores de Conexión a Telegram): En caso de que el sistema no pueda conectarse a la API de Telegram o falle al enviar el mensaje de prueba (por ejemplo, debido a un token inválido, un Chat ID incorrecto o problemas de red), debe notificar al usuario de forma clara y concisa dentro de la UI sobre la naturaleza del error. El mensaje debería sugerir posibles causas (ej. "Error al enviar mensaje a Telegram: El Token del Bot podría ser incorrecto.") y la posibilidad de revisar las credenciales.

AC5 (Opción de Re-Verificar Conexión Manualmente): El usuario debe disponer de una opción en la interfaz de usuario (probablemente en la sección donde configuró las credenciales de Telegram) para solicitar manualmente un reintento de conexión y el envío de un nuevo mensaje de prueba. Esto es útil si se corrigen las credenciales o se resuelven problemas de red temporales.

AC6 (Preparación del Módulo de Notificaciones): Una vez que la conexión con Telegram ha sido verificada como exitosa, el módulo de notificaciones interno del sistema debe estar listo para utilizar esta conexión establecida y enviar las futuras alertas y mensajes operativos que se definirán en otras historias funcionales.

## Historia 1.3: Verificación de Conectividad y Estado Básico de la Cuenta de Binance

Como usuario de UltiBotInversiones,
quiero que el sistema verifique la conectividad con mi cuenta de Binance y muestre el estado básico de mis balances (específicamente USDT),
para asegurar que "UltiBotInversiones" está correctamente enlazado y listo para futuras operaciones (simuladas o reales).
Para esta historia, que es vital para confirmar que podemos interactuar con tu cuenta de Binance, te propongo los siguientes Criterios de Aceptación (ACs):

### Criterios de Aceptación para la Historia 1.3:

AC1 (Acceso Seguro a Credenciales de Binance): El sistema debe ser capaz de recuperar de forma segura la API Key y el Secret Key de Binance del usuario desde el almacén de credenciales encriptadas (establecido en la Historia 1.1).

AC2 (Prueba de Conexión y Obtención de Información de Cuenta): Al iniciar "UltiBotInversiones" por primera vez tras configurar las credenciales de Binance, o cuando estas se actualicen, o mediante una acción explícita del usuario, el sistema debe utilizar dichas credenciales para realizar una llamada a un endpoint de la API de Binance que confirme la validez de las claves y permita obtener información básica de la cuenta, como los balances de los activos. Un ejemplo sería consultar el endpoint de balances de la cuenta.

AC3 (Visualización Específica del Saldo de USDT en la UI): Si la conexión es exitosa y se pueden obtener los balances, la interfaz de usuario de "UltiBotInversiones" (en una sección designada, como el estado del portafolio o la configuración de la conexión a Binance) debe mostrar de forma clara y destacada al menos el saldo disponible del activo USDT en la cuenta de Spot de Binance del usuario.

AC4 (Indicación Clara de Conexión Exitosa en la UI): La UI debe proporcionar una indicación visual clara (ej. un ícono de estado, un mensaje de texto) de que la conexión con la API de Binance está activa y que las credenciales proporcionadas son válidas y funcionales.

AC5 (Manejo Detallado de Errores de Conexión o Autenticación con Binance): En caso de que el sistema no pueda establecer conexión con Binance, o si la API de Binance devuelve un error específico indicando credenciales inválidas, problemas de permisos de la API Key (ej. falta de permiso para consultar balances o para operar), restricciones de IP, u otros fallos de autenticación o conexión, el sistema debe notificar al usuario de manera precisa dentro de la UI sobre el tipo de error encontrado. El mensaje debería ser lo suficientemente informativo como para sugerir posibles causas (ej. "Error con API de Binance: Claves incorrectas", "Error con API de Binance: Permisos insuficientes para la clave API. Asegúrate de habilitar 'Permitir Trading de Spot y Margin' y 'Permitir Futuros' si aplica.") y cómo podría solucionarlo.

AC6 (Opción de Reintentar la Verificación de Conexión a Binance): El usuario debe disponer de una opción clara en la interfaz de usuario (probablemente en la sección de configuración de la conexión a Binance) para solicitar manualmente un reintento de la conexión y la verificación de los balances.

AC7 (Disponibilidad de Conexión para Módulos Posteriores): Una vez que la conexión con Binance ha sido establecida y verificada exitosamente (pudiendo obtener información como los balances), el sistema debe considerar esta conexión como lista y disponible para ser utilizada por otros módulos que la requieran, como el motor de paper trading (que usará datos de mercado de Binance) o el motor de ejecución de operaciones reales.

## Historia 1.4: Configuración Inicial de la Aplicación y Persistencia de Datos Fundamentales

Como usuario de UltiBotInversiones,
quiero que el sistema cargue una configuración básica al arrancar y pueda guardar de forma segura y persistente (en la base de datos Supabase/PostgreSQL) cualquier ajuste esencial, como las preferencias iniciales o la ubicación de las credenciales encriptadas,
para asegurar que la aplicación inicie correctamente y recuerde mis ajustes importantes entre sesiones.
Para que esta historia se considere "terminada" y cumpla su propósito, he preparado los siguientes Criterios de Aceptación (ACs). Estos son los cheques que nos dirán que la funcionalidad está completa y correcta:

### Criterios de Aceptación para la Historia 1.4:

AC1 (Carga de Configuración Existente): Al iniciar "UltiBotInversiones", el sistema debe intentar cargar cualquier configuración de aplicación previamente guardada desde la base de datos Supabase/PostgreSQL.

AC2 (Aplicación de Valores por Defecto): Si no se encuentra una configuración guardada, o si faltan parámetros específicos en la configuración cargada, el sistema debe aplicar valores por defecto para los ajustes esenciales que permitan un inicio y funcionamiento básico (ej. tema oscuro por defecto, idioma de la interfaz, configuraciones de conexión a base de datos si son dinámicas).

AC3 (Persistencia de Nuevos Ajustes y Cambios): El sistema debe proveer un mecanismo interno (que será utilizado por futuras funcionalidades de UI de configuración) para guardar de forma persistente en la base de datos Supabase/PostgreSQL cualquier nuevo ajuste o cambio en las configuraciones esenciales de la aplicación.

AC4 (Estructura de Configuración Segura para Datos Sensibles): La forma en que se almacenan las configuraciones debe estar diseñada para manejar de forma segura las referencias a datos sensibles (por ejemplo, la ubicación o el método de acceso al almacén de claves API encriptadas que se gestionará en la Historia 1.1), sin guardar directamente información crítica sin la protección adecuada.

AC5 (Arranque Exitoso con Configuraciones Guardadas): Después de un reinicio de la aplicación, "UltiBotInversiones" debe arrancar y operar utilizando las últimas configuraciones que fueron guardadas por el usuario, o los valores por defecto si no existían configuraciones previas.

AC6 (Manejo de Errores en Carga/Guardado de Configuración): Si se produce un error crítico durante la carga o el guardado de la configuración que impida el funcionamiento esencial, el sistema debe informar al usuario de manera clara (por ejemplo, un mensaje en la UI o en los logs iniciales si la UI aún no es completamente funcional) y, si es posible, intentar arrancar con una configuración mínima segura por defecto.

# Historias de Usuario Propuestas para la Épica 2:

Orden Sugerido:

- Historia 2.1: Diseño e Implementación del Layout Principal del Dashboard (PyQt5)

Como usuario de UltiBotInversiones, quiero un layout de dashboard principal claro, profesional y con tema oscuro (implementado con PyQt5 y QDarkStyleSheet), que defina áreas designadas para diferentes tipos de información como mercado, portafolio, gráficos y notificaciones, para tener una vista organizada desde la cual pueda acceder fácilmente a todas las funciones clave del sistema.

- Historia 2.2: Visualización de Datos de Mercado de Binance en Tiempo Real en el Dashboard

Como usuario de UltiBotInversiones, quiero poder configurar una lista de mis pares de criptomonedas favoritos en Binance y ver en una sección del dashboard sus datos de mercado en tiempo real (como precio actual, cambio en 24h y volumen en 24h), para poder monitorear rápidamente y de un vistazo el estado general del mercado que me interesa.

- Historia 2.3: Visualización de Gráficos Financieros Esenciales (mplfinance)

Como usuario de UltiBotInversiones, quiero poder seleccionar un par de criptomonedas de mi lista de seguimiento en el dashboard y visualizar un gráfico financiero básico (velas japonesas y volumen, utilizando mplfinance) con la capacidad de cambiar entre diferentes temporalidades (ej. 1m, 5m, 15m, 1H, 4H, 1D), para poder realizar un análisis técnico visual rápido y contextualizado.
Historia 2.4: Visualización del Estado del Portafolio (Paper y Real Limitado)

Como usuario de UltiBotInversiones, quiero ver en una sección dedicada del dashboard un resumen claro y actualizado del estado de mi portafolio, que diferencie visiblemente entre el saldo de paper trading y mi saldo real en Binance (enfocándose en USDT), así como el valor total estimado de mis activos, para conocer mi situación financiera actual dentro de la plataforma en todo momento.

- Historia 2.5: Presentación Integrada de Notificaciones del Sistema en la UI

Como usuario de UltiBotInversiones, quiero ver todas las notificaciones importantes generadas por el sistema (como alertas de trading de alta confianza, confirmaciones de operaciones simuladas/reales, errores de conexión, etc.) directamente en un área designada y visible de la interfaz de usuario, para estar siempre informado de los eventos relevantes sin depender exclusivamente de las notificaciones de Telegram.
Justificación del Orden Propuesto:

Comenzamos con el Layout Principal (2.1) porque es el esqueleto sobre el cual se construirán todas las demás vistas y componentes de la interfaz.
Una vez que tenemos la estructura, poblamos una sección con Datos de Mercado en Tiempo Real (2.2). Esto no solo proporciona valor inmediato al usuario, sino que también nos permite probar la ingesta y visualización de datos dinámicos.
Con los datos de mercado fluyendo, la Visualización de Gráficos (2.3) es el siguiente paso lógico, ofreciendo una herramienta de análisis visual.
Paralelamente o a continuación, la Visualización del Estado del Portafolio (2.4) es crucial para que conozcas tu situación financiera dentro de la aplicación.

Finalmente, integrar la Presentación de Notificaciones en la UI (2.5) asegura que tengas toda la información relevante centralizada.

## Historia 2.1: Diseño e Implementación del Layout Principal del Dashboard (PyQt5)

Como usuario de UltiBotInversiones,
quiero un layout de dashboard principal claro, profesional y con tema oscuro (implementado con PyQt5 y QDarkStyleSheet), que defina áreas designadas para diferentes tipos de información como mercado, portafolio, gráficos y notificaciones,
para tener una vista organizada desde la cual pueda acceder fácilmente a todas las funciones clave del sistema.
Para esta historia, que sentará las bases visuales y estructurales de tu interacción con "UltiBotInversiones", te propongo los siguientes Criterios de Aceptación (ACs):

### Criterios de Aceptación para la Historia 2.1:

AC1 (Ventana Principal Establecida): Al iniciar "UltiBotInversiones", el sistema debe presentar una ventana principal de aplicación, desarrollada utilizando el framework PyQt5.

AC2 (Aplicación Consistente de Tema Oscuro Profesional): La totalidad de la interfaz de usuario, comenzando por este layout principal del dashboard, debe aplicar de manera consistente un tema oscuro de calidad profesional (por ejemplo, utilizando QDarkStyleSheet  o una solución equivalente) para asegurar una buena legibilidad, reducir la fatiga visual y alinearse con la estética de las aplicaciones de trading.

AC3 (Definición Clara de Áreas Funcionales): El layout principal del dashboard debe estar visiblemente estructurado con secciones o paneles claramente designados y diferenciados para albergar, como mínimo, las siguientes áreas funcionales:
Un área para el "Resumen de Datos de Mercado".
Un área para el "Estado del Portafolio".
Un área principal destinada a la "Visualización de Gráficos Financieros".
Un área para el "Centro de Notificaciones del Sistema".

AC4 (Flexibilidad de Paneles: Acoplables/Redimensionables): Los diferentes paneles o secciones dentro del dashboard deben ser, como mínimo, individualmente redimensionables por el usuario. Siguiendo la visión de un "dashboard modular con paneles acoplables", se buscará que estos paneles también permitan ser desacoplados, movidos y reacoplados en diferentes posiciones por el usuario para una personalización avanzada del espacio de trabajo. Considerando tu objetivo de velocidad para la v1.0, si la implementación completa de paneles acoplables resultara muy compleja inicialmente, priorizaríamos que sean claramente definidos y redimensionables, dejando el acoplamiento avanzado como una mejora inmediata post-v1.0. ¿Cómo ves esta priorización para la v1.0?

AC5 (Adaptabilidad del Layout al Tamaño de la Ventana): El layout general del dashboard y sus paneles internos deben ajustarse de manera fluida y lógica cuando el usuario redimensiona la ventana principal de la aplicación. La información debe permanecer legible y los controles accesibles, sin que los elementos se superpongan o queden cortados, dentro de los límites prácticos de una aplicación de escritorio.

AC6 (Elementos Estructurales Básicos): El layout principal debe contemplar la inclusión de elementos estructurales básicos como una barra de menú (si se considera necesaria para futuras funcionalidades) y/o una barra de estado en la parte inferior para mostrar información concisa del sistema (por ejemplo, el estado de conexión a Binance, la hora del sistema/mercado, o el estado del motor de IA).

## Historia 2.2: Visualización de Datos de Mercado de Binance en Tiempo Real en el Dashboard

Como usuario de UltiBotInversiones,
quiero ver en el dashboard los datos de mercado en tiempo real (precio actual, cambio 24h, volumen 24h) para una lista configurable de mis pares de criptomonedas favoritos en Binance,
para poder monitorear rápidamente el estado del mercado.
Para esta funcionalidad, que es clave para que tengas una visión actualizada del mercado, te propongo los siguientes Criterios de Aceptación (ACs):

### Criterios de Aceptación para la Historia 2.2:

AC1 (Configuración de Lista de Pares de Seguimiento): El sistema debe ofrecer un mecanismo dentro de la interfaz de usuario (por ejemplo, en una sección de configuración del dashboard o directamente en el panel de datos de mercado) que te permita buscar, seleccionar y guardar una lista de los pares de trading de Binance (ej. BTC/USDT, ETH/USDT, etc.) que deseas monitorear activamente. Tu selección de pares debe persistir entre sesiones de la aplicación (utilizando la capacidad de persistencia definida en la Historia 1.4).

AC2 (Presentación Clara de Pares en el Dashboard): En el área designada del dashboard para el "Resumen de Datos de Mercado" (establecida en la Historia 2.1), el sistema debe mostrar los pares de criptomonedas que has seleccionado en un formato tabular o de lista que sea ordenado y fácil de leer.

AC3 (Información Esencial por Par): Para cada par de criptomonedas que figure en tu lista de seguimiento, la interfaz de usuario debe mostrar, como mínimo, la siguiente información de mercado:
Símbolo del Par (ej. "BTC/USDT").
Último Precio Operado (Precio Actual).
Cambio Porcentual del Precio en las últimas 24 horas.
Volumen de Negociación en las últimas 24 horas (expresado en la moneda de cotización, por ejemplo, USDT para BTC/USDT, o en la moneda base, según se defina como más útil).

AC4 (Actualización Dinámica de Datos): La información de mercado (precio, cambio, volumen) para los pares mostrados en el dashboard debe actualizarse dinámicamente en la interfaz de usuario. Estos datos se obtendrán a través de la conexión con Binance (establecida en la Épica 1). Para el precio actual, se priorizará el uso de WebSockets para una actualización en tiempo real si es factible para los pares seleccionados; para otros datos como el cambio 24h y volumen 24h, se podrán usar llamadas API REST con una frecuencia de actualización razonable y configurable (ej. cada 5-15 segundos) para optimizar el uso de la API.

AC5 (Legibilidad y Diseño Visual): La presentación de todos los datos de mercado debe ser clara, concisa y fácil de interpretar de un solo vistazo, utilizando consistentemente el tema oscuro de la aplicación para asegurar una buena legibilidad y una experiencia visual agradable. Se podrían usar indicadores visuales sutiles (ej. colores para movimientos de precio positivos/negativos).

AC6 (Manejo de Errores en la Obtención de Datos de Mercado): Si por alguna razón no se puede obtener la información para un par específico de tu lista (ej. un par temporalmente no disponible en el exchange, un error puntual de la API de Binance para ese dato), la interfaz debe indicarlo de forma no intrusiva para ese par en particular (ej. mostrando "N/A", "--", o un pequeño ícono de advertencia junto al dato faltante), sin que esto interrumpa la visualización y actualización de los datos de los demás pares.

## Historia 2.3: Visualización de Gráficos Financieros Esenciales (mplfinance)

Como usuario de UltiBotInversiones,
quiero poder seleccionar un par de mi lista de seguimiento y ver un gráfico financiero básico (velas japonesas, volumen) con diferentes temporalidades (ej. 1m, 5m, 15m, 1H, 4H, 1D),
para realizar un análisis técnico visual rápido.
Para esta funcionalidad, que es fundamental para cualquier trader, te propongo los siguientes Criterios de Aceptación (ACs):

### Criterios de Aceptación para la Historia 2.3:

AC1 (Selección del Par a Graficar desde el Dashboard): El usuario debe poder seleccionar un par de criptomonedas directamente desde su lista de seguimiento (definida en la Historia 2.2) para que su gráfico financiero correspondiente se muestre en el área designada del dashboard (establecida en la Historia 2.1).

AC2 (Presentación del Gráfico de Velas Japonesas y Volumen): Una vez seleccionado un par, el sistema debe renderizar un gráfico financiero utilizando la librería mplfinance. Este gráfico debe incluir de forma estándar:
Una representación del precio en formato de velas japonesas (mostrando Apertura, Máximo, Mínimo y Cierre - OHLC).
Un subgráfico de volumen de trading que corresponda temporalmente con las velas de precio mostradas.

AC3 (Funcionalidad de Selección de Temporalidad): La interfaz de usuario debe ofrecer controles claros y accesibles (ej. una lista desplegable, botones) que permitan al usuario cambiar la temporalidad (timeframe) del gráfico del par activo. Como mínimo, se deben incluir las siguientes opciones de temporalidad estándar de Binance: 1 minuto (1m), 5 minutos (5m), 15 minutos (15m), 1 hora (1H), 4 horas (4H), y 1 día (1D).

AC4 (Carga y Visualización de Datos Históricos del Gráfico): Al seleccionar un par y una temporalidad, el sistema debe ser capaz de obtener los datos históricos de velas (OHLCV - Open, High, Low, Close, Volume) necesarios desde la API de Binance para construir y mostrar el gráfico. Se deberá mostrar una cantidad razonable de periodos históricos (ej. las últimas 100 a 200 velas para la temporalidad seleccionada) para dar contexto.

AC5 (Actualización Dinámica del Gráfico con Nuevos Datos): El gráfico del par y la temporalidad actualmente seleccionados debe actualizarse dinámicamente en la UI para reflejar las nuevas velas a medida que se completan. Si la temporalidad es corta (ej. 1m, 5m), se intentará actualizar la última vela en formación en tiempo real con los nuevos datos de precios/ticks, si la librería y la API lo permiten de forma eficiente.

AC6 (Claridad, Legibilidad y Usabilidad Básica del Gráfico): El gráfico financiero resultante debe ser claro, legible y permitir una interpretación visual intuitiva de la acción del precio y el volumen. Deberá integrarse correctamente con el tema oscuro general de la aplicación. Sería deseable contar con funcionalidades básicas de interacción con el gráfico, como zoom y desplazamiento (paneo), si mplfinance lo facilita dentro del entorno PyQt5.

AC7 (Manejo de Errores en la Carga de Datos del Gráfico): En caso de que el sistema no pueda obtener o procesar los datos necesarios para generar el gráfico de un par y temporalidad seleccionados (debido a errores de la API de Binance, datos históricos insuficientes para esa temporalidad, etc.), debe mostrar un mensaje informativo y claro en el área del gráfico, en lugar de un gráfico vacío, corrupto o un error no controlado de la aplicación.

## Historia 2.4: Visualización del Estado del Portafolio (Paper y Real Limitado)

Como usuario de UltiBotInversiones,
quiero ver en el dashboard un resumen claro del estado de mi portafolio, diferenciando entre el saldo de paper trading y mi saldo real en Binance (enfocado en USDT), así como el valor total estimado de mis activos,
para conocer mi situación financiera actual dentro de la plataforma.
Para esta funcionalidad, que te dará una visión clara de tus fondos y el rendimiento de tus simulaciones y operaciones reales (limitadas en v1.0), te propongo los siguientes Criterios de Aceptación (ACs):

### Criterios de Aceptación para la Historia 2.4:

AC1 (Visualización del Saldo Real de Binance): En el área del dashboard designada para el "Estado del Portafolio" (establecida en la Historia 2.1), el sistema debe mostrar de manera prominente y clara el saldo actual de USDT disponible en tu cuenta real de Binance. Esta información se obtendrá y actualizará utilizando la conexión verificada en la Historia 1.3.

AC2 (Visualización del Saldo del Modo Paper Trading): El sistema debe mostrar el saldo actual del capital virtual asignado al modo Paper Trading. Este saldo se inicializará con un valor configurable por ti (por ejemplo, un monto equivalente a tu capital real, como 500 USDT virtuales, o cualquier otro valor que decidas para tus simulaciones) y se ajustará dinámicamente según las ganancias o pérdidas de las operaciones simuladas.

AC3 (Diferenciación Visual Clara entre Modos): La interfaz de usuario debe diferenciar de forma inequívoca la información y los saldos pertenecientes al portafolio de Paper Trading de aquellos correspondientes al portafolio Real de Binance, para evitar cualquier posible confusión. Esto podría ser mediante etiquetas claras, secciones separadas o indicadores visuales distintos.

AC4 (Listado y Valoración de Activos en Paper Trading): Para el portafolio de Paper Trading, el sistema debe mostrar una lista de todos los activos (criptomonedas) que se "poseen" actualmente como resultado de operaciones simuladas. Para cada activo, se deberá indicar la cantidad y su valor estimado al precio actual de mercado.

AC5 (Listado y Valoración de Activos Reales - v1.0): Para el portafolio Real, además del saldo principal en USDT, si se ejecuta alguna de las (hasta 5) operaciones con dinero real permitidas en la v1.0 que resulten en la adquisición de otros criptoactivos, el sistema debe mostrar la cantidad de dichos activos y su valor de mercado estimado actual.

AC6 (Cálculo y Presentación del Valor Total Estimado del Portafolio): El sistema debe calcular y mostrar el valor total estimado para cada modo de portafolio:
Para Paper Trading: La suma del capital virtual no invertido más el valor de mercado actual de los activos simulados que se posean.

Para el Portafolio Real: La suma del saldo en USDT más el valor de mercado actual de cualquier otro criptoactivo real que se posea.

AC7 (Actualización Dinámica de la Información del Portafolio): Toda la información del estado del portafolio (saldos, lista de activos poseídos, valor total estimado) debe actualizarse dinámicamente en la interfaz de usuario. Esta actualización ocurrirá después de cada operación cerrada (tanto simulada como real) y también periódicamente para reflejar los cambios en el valor de mercado de los activos que se tengan en cartera.

AC8 (Manejo de Errores en la Valoración del Portafolio): Si se presentan problemas para obtener los precios de mercado necesarios para valorar alguno de los activos en el portafolio (ej. un activo con un mercado temporalmente ilíquido o un error de la API de precios), la UI debe indicarlo claramente para ese activo específico (ej. mostrando "Valor no disponible" o un símbolo de advertencia) sin que esto impida la visualización del resto de la información del portafolio.

## Historia 2.5: Presentación Integrada de Notificaciones del Sistema en la UI

Como usuario de UltiBotInversiones,
quiero ver las notificaciones importantes generadas por el sistema (alertas de trading, confirmaciones, errores de conexión, etc.) directamente en un área designada de la interfaz de usuario,
para estar informado de los eventos relevantes sin depender exclusivamente de Telegram y tener un registro centralizado en la aplicación.
Para asegurar que este centro de notificaciones en la UI sea efectivo y útil, te propongo los siguientes Criterios de Aceptación (ACs):

### Criterios de Aceptación para la Historia 2.5:

AC1 (Panel de Notificaciones Designado en la UI): Dentro del layout principal del dashboard (establecido en la Historia 2.1), debe existir un panel o un área específica, claramente identificable y accesible, dedicada exclusivamente a mostrar las notificaciones del sistema.

AC2 (Recepción y Visualización de Notificaciones del Sistema): Todas las notificaciones importantes que el sistema "UltiBotInversiones" genere internamente (y que ya hemos acordado que se enviarán también a Telegram, como se definió en FR1.4 y la Historia 1.2 – por ejemplo: oportunidades de trading con alta confianza, confirmaciones de operaciones simuladas o reales, errores de conexión con APIs externas, alertas de riesgo, ejecución de Trailing Stop Loss o Take Profit, etc.) deben también mostrarse de forma clara y oportuna en este panel de notificaciones de la UI.

AC3 (Clasificación Visual de Notificaciones por Severidad/Tipo): Las notificaciones presentadas en la UI deben indicar visualmente su nivel de severidad o el tipo de evento al que corresponden (ej. "Información", "Éxito de Operación", "Advertencia de Conexión", "Error Crítico"). Esto se puede lograr mediante el uso de íconos distintivos, códigos de color o etiquetas textuales para facilitar su rápida interpretación.

AC4 (Información Clara y Concisa en Cada Notificación): Cada notificación individual mostrada en la UI debe contener un mensaje que sea claro, conciso y fácil de entender, describiendo el evento que ha ocurrido. Es importante que cada notificación incluya una marca de tiempo (timestamp) que indique cuándo se generó.

AC5 (Acceso a un Historial Reciente de Notificaciones): El panel de notificaciones debe permitir al usuario visualizar un historial de las notificaciones más recientes (por ejemplo, las últimas 20, 50 o un número configurable de notificaciones). Las notificaciones más nuevas deberían aparecer en la parte superior de la lista o destacarse de alguna manera.

AC6 (Gestión de Notificaciones por el Usuario): El usuario debe tener la capacidad de interactuar con las notificaciones, como mínimo, mediante una opción para descartar notificaciones individuales que ya ha revisado o para marcar todas las notificaciones como leídas. Las notificaciones descartadas o leídas podrían ocultarse, atenuarse visualmente o moverse a una sección de archivo.

AC7 (Actualización en Tiempo Real del Panel de Notificaciones): Las nuevas notificaciones generadas por el sistema deben aparecer en el panel de notificaciones de la UI en tiempo real o con un retraso mínimo desde el momento en que son generadas, asegurando que el usuario siempre tenga la información más actualizada.

## Épica 3: Implementación del Ciclo Completo de Paper Trading con Asistencia de IA

Objetivo de la Épica: Permitir al usuario simular un ciclo completo de trading (detección de oportunidad, análisis IA, ejecución simulada, gestión automatizada de Trailing Stop Loss y Take Profit, y visualización de resultados) en modo paper trading, con el apoyo de Gemini y los MCPs externos.

# Historias de Usuario Propuestas para la Épica 3 (en secuencia sugerida):

1. ## Historia 3.1: Activación y Configuración del Modo Paper Trading

Como usuario de UltiBotInversiones,
quiero poder activar el modo Paper Trading y configurar mi capital virtual inicial,
para poder empezar a simular operaciones de forma segura sin arriesgar dinero real y familiarizarme con el sistema.

### Criterios de Aceptación (ACs):

AC1: La interfaz de usuario (UI) debe presentar una opción clara y accesible (ej. un interruptor o botón en una sección de configuración o en el dashboard principal) para activar o desactivar el modo Paper Trading.

AC2: Al activar el modo Paper Trading por primera vez, o si no existe una configuración previa, el sistema debe solicitar al usuario que defina un capital virtual inicial (ej. 1000, 5000 USDT virtuales) o debe asignar un valor por defecto configurable (ej. el equivalente a los 500 USDT del capital real).

AC3: El capital virtual configurado para Paper Trading y el estado de activación de este modo deben persistir entre sesiones de la aplicación (utilizando la funcionalidad de la Historia 1.4).

AC4: La UI debe indicar de manera prominente y clara en todo momento cuando el sistema está operando en modo Paper Trading (ej. un banner, un cambio de color en ciertos elementos, una etiqueta visible).

AC5: Cuando el modo Paper Trading está activo, todas las "ejecuciones" de órdenes deben ser simuladas internamente y NO deben interactuar de ninguna manera con la API de ejecución de órdenes reales de Binance.

2. ## Historia 3.2: Integración del Flujo de Detección de Oportunidades (MCPs) para Paper Trading

Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que el sistema utilice activamente los servidores MCP externos que he configurado para identificar "trending coins" o "winner coins",
para que estas potenciales oportunidades de trading puedan ser subsecuentemente analizadas por la IA de Gemini dentro del entorno de simulación.

### Criterios de Aceptación (ACs):

AC1: Cuando el modo Paper Trading está activo, el sistema debe conectarse a la lista configurable de servidores MCP externos (según lo definido en FR2.1).

AC2: El sistema debe ser capaz de recibir, interpretar y procesar las señales o datos provenientes de estos MCPs que indiquen potenciales oportunidades de trading (como "trending coins" o "winner coins").

AC3: Las oportunidades identificadas y pre-procesadas deben ser encoladas o dirigidas de manera ordenada hacia el módulo de análisis de IA (Gemini) para su evaluación en el contexto del Paper Trading.

AC4: El sistema debe registrar (internamente o en logs de simulación) las oportunidades crudas recibidas de los MCPs para fines de trazabilidad y análisis del embudo de decisión.

3. ## Historia 3.3: Análisis de Oportunidades con Gemini y Verificación de Datos para Paper Trading

Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que las oportunidades identificadas por los MCPs sean analizadas en detalle por Gemini (utilizando los prompts de estrategias refinadas) y que los datos clave de los activos sean verificados (vía Mobula/Binance REST API), para obtener una evaluación de confianza robusta por parte de la IA antes de proceder a simular cualquier operación.

### Criterios de Aceptación (ACs):

AC1: Para cada oportunidad de trading recibida de los MCPs (Historia 3.2), el sistema debe enviar los datos relevantes a Gemini para un análisis profundo, utilizando los prompts de estrategias de búsqueda definidos (según FR4.2, con la colaboración del equipo BMAD).

AC2: El sistema debe recibir de Gemini un análisis de la oportunidad que incluya, como mínimo, una dirección sugerida (compra/venta) y un nivel de confianza numérico.

AC3: Si el nivel de confianza devuelto por Gemini es superior al umbral definido para Paper Trading (ej. >80%, según FR4.3), el sistema debe proceder con el paso de verificación de datos utilizando Mobula y/o Binance REST API para los activos involucrados (según FR2.4, limitado a 10-20 activos si es una preselección).

AC4: Solo si la verificación de datos es exitosa (sin encontrar discrepancias mayores que invaliden la oportunidad), la oportunidad, junto con el análisis completo de Gemini y su nivel de confianza, se considerará validada y lista para una posible simulación de operación.

AC5: El usuario debe ser notificado (a través de la UI y Telegram, según FR1.4) sobre estas oportunidades validadas de alta confianza (>80%) que han sido identificadas y están listas para ser consideradas en el modo Paper Trading.

4. ## Historia 3.4: Simulación de Ejecución de Órdenes de Entrada en Paper Trading

Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que el sistema simule la ejecución de órdenes de entrada (compra/venta) para las oportunidades que han sido validadas por la IA con una confianza superior al 80%,
para poder observar cómo se habrían comportado estas decisiones en el mercado y comenzar a construir un historial de operaciones simuladas.

### Criterios de Aceptación (ACs):

AC1: Para cada oportunidad de trading validada con una confianza de IA >80% (proveniente de la Historia 3.3), el sistema debe simular automáticamente la apertura de una nueva posición en el portafolio de Paper Trading.

AC2: La simulación de la ejecución de la orden de entrada debe utilizar un precio de mercado realista en el momento de la señal (ej. el último precio conocido del activo en Binance, con la opción de configurar un pequeño slippage simulado para mayor realismo).

AC3: La cantidad o tamaño de la posición simulada debe calcularse basándose en las reglas de gestión de capital definidas por el usuario (FR3.1 - no más del 50% del capital diario, FR3.2 - ajuste dinámico al 25%) aplicadas sobre el capital virtual disponible en el modo Paper Trading.

AC4: La apertura de esta posición simulada (con su precio de entrada, cantidad, dirección) debe reflejarse inmediatamente en la sección de portafolio de Paper Trading de la UI (Historia 2.4).

AC5: El usuario debe recibir una notificación (UI y Telegram) confirmando la apertura de la operación simulada, incluyendo los detalles clave de la misma.

5. ## Historia 3.5: Gestión Automatizada de Trailing Stop Loss y Take Profit en Paper Trading

Como usuario de UltiBotInversiones operando en modo Paper Trading,
quiero que una vez abierta una posición simulada, el sistema calcule, coloque (simuladamente) y gestione automáticamente las correspondientes órdenes de Trailing Stop Loss (TSL) y Take Profit (TP),
para simular una gestión completa del ciclo de vida de la operación y evaluar la efectividad de las estrategias de salida diseñadas por el equipo BMAD.

### Criterios de Aceptación (ACs):

AC1: Inmediatamente después de simular la apertura de una posición (Historia 3.4), el sistema debe calcular automáticamente los niveles iniciales para el Trailing Stop Loss y el Take Profit, utilizando los algoritmos y la lógica diseñados por el equipo BMAD (según FRX.1 y FRX.2).

AC2: Estos niveles calculados de TSL y TP deben registrarse internamente asociados a la posición simulada.

AC3: El sistema debe simular el seguimiento del Trailing Stop Loss, ajustando su nivel si el precio del activo se mueve favorablemente, de acuerdo con las reglas del algoritmo de TSL implementado. Estos ajustes deben basarse en los datos de mercado en tiempo real de Binance.

AC4: El sistema debe simular el cierre de la posición si el precio de mercado alcanza el nivel actual del Trailing Stop Loss o el nivel del Take Profit.

AC5: La interfaz de usuario (en la vista de operaciones abiertas o en el gráfico) debe mostrar los niveles activos de TSL y TP para cada posición simulada abierta.

AC6: El usuario debe recibir una notificación (UI y Telegram) cuando un Trailing Stop Loss o un Take Profit simulado se ejecute y, por lo tanto, se cierre la posición simulada, indicando el resultado de la operación.

6. ## Historia 3.6: Visualización de Resultados y Rendimiento del Paper Trading

Como usuario de UltiBotInversiones,
quiero poder revisar de forma clara los resultados históricos de todas mis operaciones de paper trading, incluyendo el Profit & Loss (P&L) por operación y un resumen del rendimiento general de mi portafolio virtual,
para poder evaluar la efectividad de las estrategias implementadas, el análisis de la IA, y mi propia curva de aprendizaje con el sistema.

### Criterios de Aceptación (ACs):

AC1: La interfaz de usuario debe presentar una sección o vista donde se listen todas las operaciones de Paper Trading que han sido cerradas, mostrando como mínimo: el par, la dirección (compra/venta), el precio de entrada, el precio de salida, la cantidad, y el P&L (Profit & Loss) individual de cada operación.

AC2: El impacto acumulado de las operaciones de Paper Trading (ganancias y pérdidas) debe reflejarse correctamente en la actualización del saldo del capital virtual del modo Paper Trading (visualizado según la Historia 2.4).

AC3: El sistema debe calcular y mostrar en la UI métricas básicas de rendimiento consolidadas para el modo Paper Trading, tales como: P&L total, Win Rate (porcentaje de operaciones ganadoras), número total de operaciones, y el P&L promedio por operación.

AC4: El usuario debería poder aplicar filtros básicos a la lista de operaciones cerradas (ej. por par, por fecha).

# Historias de Usuario Propuestas para la Épica 4 (en secuencia sugerida):

1. ## Historia 4.1: Configuración y Activación del Modo de "Operativa Real Limitada"

Como usuario de UltiBotInversiones,
quiero poder configurar y activar un modo específico de "Operativa Real Limitada" que me permita realizar hasta un máximo de 5 operaciones con mi dinero real en Binance,
para comenzar a probar el sistema en el mercado real de una forma controlada, con bajo riesgo inicial y total transparencia sobre cuándo se está usando capital real.

### Criterios de Aceptación (ACs):

AC1: La UI debe ofrecer una opción clara, explícita y separada (ej. un interruptor o una sección de configuración dedicada) para activar o desactivar el modo de "Operativa Real Limitada".

AC2: Al intentar activar este modo, el sistema debe verificar que la conexión con Binance (establecida en Historia 1.3) es funcional y que existe un saldo real de USDT disponible.

AC3: El sistema debe mantener un conteo persistente (guardado en la base de datos Supabase) de cuántas de las 5 operaciones con dinero real permitidas para la v1.0 ya han sido ejecutadas o intentadas.

AC4: La UI debe mostrar claramente al usuario cuántas de estas 5 operaciones con dinero real aún tiene disponibles.

AC5: Una vez que se hayan ejecutado las 5 operaciones con dinero real, el modo de "Operativa Real Limitada" debe impedir automáticamente la iniciación de nuevas operaciones reales, aunque sí debe permitir la gestión (ej. cierre, TSL/TP) de las que ya estén abiertas.

AC6: Al activar el modo de "Operativa Real Limitada", la UI debe presentar una advertencia prominente e inequívoca al usuario, informándole que las próximas operaciones (que cumplan los criterios) utilizarán dinero real de su cuenta de Binance, y podría requerir una confirmación adicional para aceptar este modo.

2. ## Historia 4.2: Identificación y Presentación de Oportunidades de Muy Alta Confianza para Operativa Real

Como usuario de UltiBotInversiones operando en el modo de "Operativa Real Limitada",
quiero que el sistema me presente únicamente aquellas oportunidades de trading que la IA (Gemini) haya evaluado con un nivel de confianza superior al 95%,
para asegurar que solo se consideren las probabilidades de éxito más altas para mis escasas y valiosas operaciones con dinero real.

### Criterios de Aceptación (ACs):

AC1: El flujo completo de detección de oportunidades (MCPs externos ➡️ análisis Gemini ➡️ verificación de datos con Mobula/Binance REST API), tal como se definió para el paper trading en la Épica 3, debe operar cuando el modo de "Operativa Real Limitada" está activo.

AC2: Únicamente las oportunidades de trading que reciban un nivel de confianza por parte de Gemini estrictamente superior al 95% (según FR4.3 ajustado) serán consideradas como candidatas válidas para una posible operación con dinero real.

AC3: Estas oportunidades de muy alta confianza (>95%) deben ser presentadas al usuario en la UI de forma destacada y claramente diferenciada de las señales de menor confianza que se manejan en el paper trading.

AC4: La presentación de una oportunidad candidata para operación real debe incluir toda la información relevante: el par de criptomonedas, la dirección sugerida (compra/venta), un resumen del análisis de Gemini y el nivel de confianza exacto.

AC5: El usuario debe recibir una notificación prioritaria y distintiva (en la UI y obligatoriamente por Telegram) cuando se identifique una oportunidad de este calibre (>95% de confianza) y aún queden operaciones reales disponibles.

3. ## Historia 4.3: Confirmación Explícita del Usuario y Ejecución de Órdenes Reales en Binance

Como usuario de UltiBotInversiones,
quiero, ante una oportunidad de muy alta confianza (>95%) que se me presente para operativa real, tener que confirmar explícitamente dicha operación en la UI antes de que cualquier orden se envíe al exchange de Binance,
para mantener el control final y absoluto sobre las decisiones que involucran mi dinero real.

### Criterios de Aceptación (ACs):

AC1: Cuando se presenta una oportunidad con confianza >95% (Historia 4.2) y el modo de "Operativa Real Limitada" está activo con cupos disponibles (Historia 4.1), la UI debe solicitar una confirmación explícita e inequívoca del usuario antes de proceder (ej. un botón claramente etiquetado como "Confirmar y Ejecutar Operación REAL").

AC2: La solicitud de confirmación debe mostrar claramente todos los detalles de la operación propuesta: par, dirección (compra/venta), la cantidad a operar (calculada según las reglas de gestión de capital sobre el saldo real), y el precio estimado de entrada.

AC3: Solo si el usuario proporciona la confirmación explícita, el sistema debe proceder a enviar la orden real al exchange de Binance, utilizando las credenciales y la conexión previamente establecidas y verificadas (Historias 1.1 y 1.3).

AC4: Si el usuario no confirma la operación o la cancela, la orden no se ejecutará con dinero real. El sistema podría ofrecer la opción de registrarla como una operación de paper trading para seguimiento.

AC5: Después de enviar la orden a Binance, la UI debe reflejar el estado de la orden (ej. "enviada", "parcialmente ejecutada", "ejecutada completamente", "error al enviar").

AC6: Una vez que la orden real ha sido enviada (independientemente de si se llena total o parcialmente de inmediato), el contador de operaciones reales disponibles (de las 5 para v1.0) debe decrementarse.

4. ## Historia 4.4: Aplicación de Reglas de Gestión de Capital y Salidas Automatizadas a Operaciones Reales

Como usuario de UltiBotInversiones,
quiero que cuando se ejecute una operación con dinero real, el sistema aplique automáticamente mis reglas de gestión de capital (límite de inversión diaria del 50% y ajuste dinámico al 25% basado en riesgo) y también la gestión automatizada de Trailing Stop Loss y Take Profit,
para proteger mi capital real y asegurar una operativa disciplinada y consistente con mi estrategia.

### Criterios de Aceptación (ACs):

AC1: Antes de presentar la propuesta de operación real para confirmación del usuario (Historia 4.3), el sistema debe haber calculado el tamaño de la posición basándose en las reglas de gestión de capital definidas (FR3.1 y FR3.2), aplicadas sobre el capital real disponible en la cuenta de Binance.

AC2: Inmediatamente después de que una operación real sea confirmada por el usuario y la orden de entrada sea aceptada por Binance, el sistema debe calcular y colocar automáticamente en Binance las órdenes correspondientes de Trailing Stop Loss y Take Profit, utilizando la misma lógica y algoritmos diseñados por el equipo BMAD para el paper trading (FRX.1, FRX.2).

AC3: El estado de estas órdenes de TSL y TP reales debe ser visible en la interfaz de usuario, asociado a la posición real abierta.

AC4: La ejecución de un TSL o TP en una operación real debe ser notificada al usuario (UI y Telegram) y debe cerrar la posición correspondiente en Binance.

AC5: El sistema debe monitorear y respetar la regla de no exceder el 50% del capital total disponible para inversión diaria, considerando el capital comprometido en estas operaciones reales.

5. ## Historia 4.5: Visualización y Seguimiento Diferenciado de Operaciones y Portafolio Real

Como usuario de UltiBotInversiones,
quiero que la sección de portafolio en la UI muestre de forma clara y separada mis operaciones, saldos y rendimiento con dinero real en Binance, distinguiéndolos de los datos de paper trading,
para poder hacer un seguimiento preciso y sin confusiones de mi rendimiento y situación financiera real.

### Criterios de Aceptación (ACs):

AC1: La sección de "Estado del Portafolio" en la UI (Historia 2.4) debe tener una subsección claramente diferenciada o un método visual inequívoco para mostrar las posiciones abiertas con dinero real y el saldo de capital real.

AC2: Se debe mostrar el P&L realizado (para operaciones reales cerradas) y el P&L no realizado (para operaciones reales abiertas) de forma separada para el componente real del portafolio.

AC3: El saldo de USDT real en Binance, así como las cantidades de otros criptoactivos adquiridos mediante las operaciones reales, deben actualizarse con precisión para reflejar las operaciones ejecutadas y cerradas.

AC4: El historial de operaciones (si se implementa una vista de historial) debe permitir filtrar o distinguir claramente entre las operaciones realizadas en modo Paper Trading y las operaciones ejecutadas con dinero real.

# Historias de Usuario Propuestas para la Épica 5:

Orden Sugerido:

## Historia 5.1: Definición y Configuración Modular de Estrategias de Trading

Como usuario de UltiBotInversiones,
quiero que el sistema permita la definición modular de diferentes estrategias de trading (inicialmente Scalping, Day Trading, Arbitraje Simple), incluyendo sus parámetros configurables específicos,
para que puedan ser gestionadas y ejecutadas de forma independiente.

### Criterios de Aceptación (ACs) para la Historia 5.1:

AC1: El sistema debe contar con una estructura interna (ej. clases base, interfaces) que permita definir nuevas estrategias de trading de forma modular, especificando su lógica de entrada, salida y gestión de riesgos básicos.

AC2: Para cada una de las estrategias base (Scalping, Day Trading, Arbitraje Simple), se deben identificar y definir sus parámetros configurables clave (ej. para Scalping: % de ganancia objetivo por operación, % de stop-loss; para Day Trading: indicadores técnicos y umbrales; para Arbitraje: umbral de diferencia de precios).

AC3: El sistema debe permitir persistir la configuración de los parámetros para cada estrategia definida (utilizando la base de la Historia 1.4: Configuración Inicial de la Aplicación y Persistencia de Datos Fundamentales).

AC4: La lógica de cada estrategia debe ser encapsulada de manera que pueda ser invocada por el motor de trading del sistema.

AC5: La documentación interna (a nivel de código y diseño) debe describir claramente cómo añadir nuevas estrategias modulares al sistema en el futuro.

## Historia 5.2: Integración de Estrategias con el Motor de Análisis IA (Gemini)

Como usuario de UltiBotInversiones,
quiero que cada estrategia de trading definida pueda interactuar con el motor de análisis de IA (Gemini) para refinar sus señales de entrada o validar oportunidades según su lógica particular,
para mejorar la toma de decisiones y la efectividad de las estrategias.

### Criterios de Aceptación (ACs) para la Historia 5.2:

AC1: Se debe poder configurar, para cada estrategia individualmente, si esta requiere o utiliza el análisis de IA (Gemini) y de qué manera (ej. para confirmación de tendencia, análisis de sentimiento de noticias relacionado con el activo, validación de patrones de la estrategia).

AC2: Los prompts enviados a Gemini deben poder ser adaptados o extendidos dinámicamente con información o contexto específico proveniente de la estrategia activa que está evaluando una señal u oportunidad.

AC3: El resultado del análisis de Gemini (ej. nivel de confianza, sugerencias, datos adicionales) debe ser devuelto y procesado por la lógica de la estrategia correspondiente para la toma de decisión final sobre ejecutar o no una operación.

AC4: Si una estrategia está configurada para no utilizar IA, debe poder operar de forma autónoma basándose únicamente en sus reglas predefinidas y los datos de mercado disponibles.

AC5: El sistema debe registrar de forma clara (en logs y en los detalles de la operación) si una operación fue influenciada, confirmada o generada con la asistencia de la IA y bajo qué estrategia específica.

## Historia 5.3: Panel de Control para Selección y Activación de Estrategias en la UI

Como usuario de UltiBotInversiones,
quiero un panel de control en la interfaz de usuario (Dashboard) donde pueda ver las estrategias de trading disponibles (Scalping, Day Trading, Arbitraje Simple), configurar sus parámetros específicos, y activarlas o desactivarlas individualmente tanto para el modo Paper Trading como para la Operativa Real Limitada,
para tener control granular y flexible sobre las operaciones que el bot realiza en mi nombre.

### Criterios de Aceptación (ACs) para la Historia 5.3:

AC1: La interfaz de usuario (desarrollada en la Épica 2) debe incluir una nueva sección o panel claramente identificable para la "Gestión de Estrategias".

AC2: En este panel, se deben listar todas las estrategias de trading definidas y disponibles en el sistema (inicialmente Scalping, Day Trading, Arbitraje Simple).

AC3: Para cada estrategia listada, el usuario debe poder acceder a una interfaz donde pueda visualizar y modificar sus parámetros configurables (definidos en la Historia 5.1). Todos los cambios realizados deben persistirse de forma segura.

AC4: El usuario debe poder activar o desactivar cada estrategia de forma independiente. Esta activación/desactivación debe poder realizarse por separado para el modo Paper Trading y para el modo de Operativa Real Limitada.

AC5: La interfaz de usuario debe mostrar de forma clara e inequívoca el estado actual (activo/inactivo) de cada estrategia para cada uno de los modos de operación (Paper y Real).

AC6: El sistema debe asegurar que solamente las estrategias que estén activadas para un modo de operación específico (Paper Trading o Real Limitada) puedan generar señales o ejecutar operaciones dentro de ese modo.

## Historia 5.4: Ejecución de Operaciones Basada en Estrategias Activas y Configuradas

Como usuario de UltiBotInversiones,
quiero que el motor de trading del sistema solo considere y ejecute operaciones (simuladas en Paper Trading o propuestas para confirmación en Operativa Real Limitada) basadas en las señales generadas por las estrategias que yo he activado y configurado explícitamente,
para asegurar que el bot opera estrictamente de acuerdo a mis preferencias y estrategias seleccionadas.

### Criterios de Aceptación (ACs) para la Historia 5.4:

AC1: El motor de trading debe consultar en tiempo real el estado (activo/inactivo) y la configuración actual de todas las estrategias (gestionado a través de la Historia 5.3) antes de procesar cualquier señal de mercado potencial o oportunidad identificada por los MCPs.

AC2: Cuando una oportunidad de trading es detectada (sea por MCPs externos o por un análisis interno del sistema), el sistema debe filtrar y determinar qué estrategias activas son aplicables a dicha oportunidad (basado en el par de monedas, condiciones de mercado, etc., según la lógica de cada estrategia).

AC3: Las señales o datos de la oportunidad deben ser procesados por la lógica interna de la(s) estrategia(s) activa(s) que sean aplicables, incluyendo cualquier interacción con el motor de IA (Gemini) si así está configurado para dicha estrategia (según Historia 5.2).

AC4: Solo se procederá a simular una operación (en modo Paper Trading, como se definió en la Épica 3) o a proponerla para ejecución real (en modo Operativa Real Limitada, como se definió en la Épica 4) si una estrategia activa y correctamente configurada así lo determina y alcanza el umbral de confianza requerido.

AC5: Cada operación ejecutada (simulada o real) debe ser asociada y registrada de forma persistente con la estrategia específica que la originó, para fines de seguimiento y análisis de desempeño.

## Historia 5.5: Monitoreo Básico del Desempeño por Estrategia en la UI

Como usuario de UltiBotInversiones,
quiero poder ver en el dashboard un resumen básico del desempeño de cada una de mis estrategias activadas (ej. número de operaciones realizadas, Profit & Loss total generado, y tasa de acierto), diferenciado por modo de operación (Paper Trading y Real),
para poder evaluar de manera sencilla la efectividad de cada estrategia y tomar decisiones informadas sobre su futura configuración o activación.

### Criterios de Aceptación (ACs) para la Historia 5.5:

AC1: La sección de "Estado del Portafolio" (definida en la Historia 2.4) o, si es más apropiado, una nueva sección dedicada en el dashboard, debe incluir un apartado para el "Desempeño por Estrategia".

AC2: Para cada estrategia que haya ejecutado al menos una operación (tanto en modo Paper Trading como en modo Real), el sistema debe mostrar como mínimo la siguiente información:
Nombre de la Estrategia.
Modo de Operación (Paper Trading / Operativa Real Limitada).
Número total de operaciones ejecutadas por esa estrategia en ese modo.
Profit & Loss (P&L) total generado por esa estrategia en ese modo.
Win Rate (porcentaje de operaciones ganadoras sobre el total de operaciones cerradas) para esa estrategia en ese modo.

AC3: Esta información de desempeño por estrategia debe actualizarse dinámicamente en la interfaz de usuario, idealmente después de que cada operación cerrada por dicha estrategia sea registrada.

AC4: Los datos de desempeño deben ser claramente diferenciados y presentados por separado para el modo Paper Trading y para el modo de Operativa Real Limitada.

AC5: El usuario debería poder ver esta información de forma consolidada (sumando todos los modos si tuviera sentido) o tener la opción de filtrar por un modo de operación específico para analizar el desempeño de las estrategias en dicho contexto.

## Justificación del Orden Propuesto para la Épica 5:

Este orden sigue una progresión lógica para construir la funcionalidad de gestión de estrategias:

Primero (5.1), es crucial establecer la definición y configuración modular de las estrategias. Esto sienta las bases técnicas para que el sistema entienda qué es una estrategia y cómo se parametriza.
Luego (5.2), se define la integración de estas estrategias con el motor de IA (Gemini), un componente central de UltiBotInversiones, permitiendo que las estrategias se beneficien del análisis inteligente.
Con las estrategias definidas y potencialmente potenciadas por IA, el siguiente paso es darle al usuario el control sobre ellas a través de un panel en la UI (5.3). Esto incluye la configuración de parámetros y la activación/desactivación para los diferentes modos de trading.
Una vez que el usuario puede gestionar las estrategias, es necesario asegurar que el motor de trading las utilice correctamente para la ejecución de operaciones (5.4), respetando las configuraciones y el estado de activación.
Finalmente (5.5), para cerrar el ciclo y permitir la toma de decisiones informadas, se implementa el monitoreo básico del desempeño de cada estrategia directamente en la UI.