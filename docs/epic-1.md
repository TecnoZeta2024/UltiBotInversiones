# Épica 1: Configuración Fundacional y Conectividad Segura

**Objetivo de la Épica:** Establecer la configuración base del sistema "UltiBotInversiones", asegurar la conectividad con Binance y servicios de notificación (Telegram), y permitir la gestión segura de credenciales.

## Historias de Usuario Propuestas para la Épica 1:

### Bloque Fundacional Técnico (Ejecutar Primero):

#### Historia 1.0.1: Configuración del Repositorio y Estructura Inicial del Proyecto (Monorepo)
Como: Equipo de Desarrollo,
Quiero: Configurar el repositorio Git (Monorepo) y establecer la estructura de directorios inicial del proyecto "UltiBotInversiones",
Para que: Podamos asegurar una base organizada y coherente para todo el desarrollo futuro y facilitar la gestión de dependencias.

##### Criterios de Aceptación:
*   Se crea un nuevo repositorio Git para el proyecto "UltiBotInversiones".
*   Se define y aplica la estructura de directorios raíz para el Monorepo (ej. src/, docs/, tests/, scripts/, infra/) según la decisión de "Monorepo" y "Monolito Modular" documentada en la sección "Suposiciones Técnicas" del PRD.
*   Se incluye un archivo README.md inicial en la raíz del proyecto con el nombre del proyecto y una breve descripción placeholder.
*   Se configura un archivo .gitignore base para excluir archivos y directorios comúnmente innecesarios en el control de versiones (ej. __pycache__/, *.pyc, venv/, build/, dist/, *.env, secrets/).
*   La estructura inicial dentro de src/ refleja la arquitectura de "Monolito Modular" (ej. se crean directorios placeholder como src/core_logic/, src/data_management/, src/interfaces/, src/app_ui/ si aplica, etc.).

#### Historia 1.0.2: Configuración del Entorno de Desarrollo Base (Docker y Dependencias)
Como: Equipo de Desarrollo,
Quiero: Configurar el entorno de desarrollo base utilizando Docker y Poetry (para la gestión de dependencias de Python),
Para que: Podamos asegurar un entorno de desarrollo consistente, reproducible y aislado para todos los miembros del equipo y para los futuros procesos de Integración Continua/Despliegue Continuo (CI/CD).

##### Criterios de Aceptación:
*   Se crea un Dockerfile (o un docker-compose.yml si se prefiere para gestionar múltiples servicios localmente) que define el entorno de ejecución principal basado en Python 3.11+.
*   Se inicializa Poetry en el proyecto, generando un archivo pyproject.toml para la gestión de dependencias de Python.
*   Se añaden las dependencias iniciales del stack tecnológico confirmado (ej. FastAPI, PyQt5, google-generativeai) al pyproject.toml.
*   Se incluyen scripts básicos (ej. en una carpeta scripts/) para construir la imagen de Docker y para ejecutar un contenedor en modo de desarrollo (ej. montando el código fuente local).
*   El entorno de desarrollo permite la instalación exitosa de las dependencias y la ejecución de una aplicación Python básica dentro del contenedor Docker.

#### Historia 1.0.3: Andamiaje Inicial para el Monolito Modular
Como: Equipo de Desarrollo,
Quiero: Implementar el andamiaje básico para la arquitectura de "Monolito Modular" dentro del directorio src/, definiendo los directorios para los módulos principales (ej. para la lógica del núcleo, acceso a datos, interfaces/adaptadores, UI si es parte del monolito),
Para que: Se establezca una estructura de código clara desde el principio, que facilite el desarrollo organizado, la separación de responsabilidades y la futura evolución del sistema.

##### Criterios de Aceptación:
*   Dentro de src/, se crean los directorios que representarán los principales módulos del Monolito Modular (ej. src/core_logic/, src/data_access/, src/api_services/, src/ui_layer/ si aplica), según se alinee con la visión arquitectónica.
*   Cada directorio de módulo principal contiene un archivo __init__.py (si es Python) y un README.md placeholder que describe brevemente la responsabilidad futura de ese módulo.
*   Se define conceptualmente (ej. en los READMEs de los módulos) cómo estos módulos principales interactuarán, preparando el terreno para interfaces bien definidas.

#### Historia 1.0.4: Puesta en Marcha del Framework de Pruebas Unitarias
Como: Equipo de Desarrollo,
Quiero: Configurar e integrar un framework de pruebas unitarias (ej. PyTest para Python) en el proyecto,
Para que: Podamos escribir y ejecutar pruebas unitarias desde el inicio del desarrollo, asegurando la calidad del código, facilitando la refactorización y promoviendo buenas prácticas de desarrollo.

##### Criterios de Aceptación:
*   El framework de pruebas unitarias (ej. PyTest) y cualquier librería de apoyo necesaria (ej. pytest-cov para cobertura) se añaden como dependencias de desarrollo en pyproject.toml.
*   Se establece la estructura de directorios para las pruebas unitarias (ej. tests/unit/) según las convenciones del PRD y futuro Documento de Arquitectura.
*   Se crea una prueba unitaria de ejemplo simple (ej. para una función de utilidad básica) dentro de la estructura de pruebas, y esta prueba se ejecuta exitosamente.
*   Se añaden o configuran scripts (ej. en scripts/ o mediante comandos de Poetry en pyproject.toml) para ejecutar fácilmente todas las pruebas unitarias.
*   Se documenta brevemente en el README.md principal o en docs/operational-guidelines.md (si ya existe) cómo ejecutar las pruebas.

#### Historia 1.0.5: Configuración Inicial de la Infraestructura en Supabase (Base de Datos)
Como: Equipo de Desarrollo,
Quiero: Realizar la configuración inicial del proyecto en Supabase, incluyendo la creación de la instancia de base de datos PostgreSQL y la obtención segura de las credenciales de conexión,
Para que: El sistema "UltiBotInversiones" pueda conectarse a una base de datos persistente para almacenar y recuperar datos esenciales de la aplicación desde las primeras etapas de desarrollo.

##### Criterios de Aceptación:
*   Se crea un nuevo proyecto en la plataforma Supabase para "UltiBotInversiones".
*   Se obtienen las credenciales de conexión a la base de datos PostgreSQL proporcionadas por Supabase (como la URL de conexión, la clave de API de servicio (service_role key)).
*   Se establece un método seguro para que el equipo de desarrollo acceda a estas credenciales para el entorno local (ej. mediante un archivo .env que NO se commitea al repositorio, con un .env.example como plantilla).
*   Se realiza una conexión de prueba exitosa a la base de datos Supabase desde el entorno de desarrollo local utilizando las credenciales obtenidas y una librería de Python para PostgreSQL (ej. psycopg2-binary o asyncpg si se planea asincronismo).

### Historias de Usuario Funcionales (Post-Bloque Técnico):

#### Historia 1.1: Configuración y Almacenamiento Seguro de Credenciales del Sistema
Como usuario de UltiBotInversiones,
quiero poder ingresar y que el sistema almacene de forma segura y encriptada todas mis claves API necesarias (Binance, Gemini, Telegram, Mobula, y para los servidores MCP que configure),
para que "UltiBotInversiones" pueda operar en mi nombre e interactuar con estos servicios externos sin exponer mis credenciales sensibles.

##### Criterios de Aceptación:
*   AC1 (Interfaz de Gestión de Credenciales - Backend): El sistema deberá tener la capacidad interna de recibir, actualizar y eliminar de forma segura las claves API para cada servicio externo requerido (Binance, Gemini, Telegram, Mobula). También deberá permitir un mecanismo para agregar y gestionar credenciales para múltiples servidores MCP. Nota: La interfaz de usuario (UI) específica para esta gestión se detallará en una historia de la Épica de UI, pero el backend debe estar preparado.
*   AC2 (Encriptación Fuerte en Reposo): Todas las claves API que el usuario ingrese deberán ser encriptadas utilizando un algoritmo de encriptación robusto y estándar (por ejemplo, AES-256 o Fernet) antes de ser almacenadas de forma persistente en la base de datos Supabase/PostgreSQL.
*   AC3 (Desencriptación Segura y Oportuna): El sistema deberá implementar un mecanismo seguro para desencriptar las claves API necesarias únicamente en el momento de la ejecución, cuando se necesite interactuar con el servicio externo correspondiente. Se debe minimizar el tiempo que las claves permanezcan desencriptadas en la memoria de la aplicación.
*   AC4 (Prohibición de Almacenamiento en Texto Plano): Bajo ninguna circunstancia las claves API deberán ser almacenadas o registradas (logueadas) en texto plano en ningún componente del sistema.
*   AC5 (Verificación Opcional de Validez de Claves): Al momento de ingresar o actualizar las claves API para servicios críticos (Binance, Gemini, Telegram), el sistema deberá intentar realizar una conexión de prueba básica para verificar la validez y ofrecer retroalimentación.
*   AC6 (Indicación del Estado de Configuración): La UI deberá indicar qué credenciales han sido configuradas y su estado de verificación, sin mostrar las claves.

#### Historia 1.2: Inicialización y Verificación del Bot de Notificaciones de Telegram
Como usuario de UltiBotInversiones,
quiero que el sistema utilice mis credenciales de Telegram para conectarse a mi bot personal y enviar un mensaje de prueba,
para confirmar que puedo recibir notificaciones importantes sobre la actividad del sistema y las operaciones directamente en Telegram.

##### Criterios de Aceptación:
*   AC1 (Acceso Seguro a Credenciales de Telegram): El sistema debe poder recuperar de manera segura el Token del Bot de Telegram y el Chat ID del usuario desde el almacén de credenciales encriptadas.
*   AC2 (Conexión y Envío de Mensaje de Prueba Inicial): Al iniciar o actualizar credenciales de Telegram, el sistema debe enviar un mensaje de prueba predefinido al Chat ID.
*   AC3 (Indicación de Conexión Exitosa en la UI): Si el mensaje de prueba se envía con éxito, la UI debe reflejar que la conexión con Telegram está activa.
*   AC4 (Gestión Clara de Errores de Conexión a Telegram): En caso de fallo, notificar al usuario en la UI sobre la naturaleza del error y sugerir causas.
*   AC5 (Opción de Re-Verificar Conexión Manualmente): El usuario debe poder solicitar manualmente un reintento de conexión y envío de mensaje de prueba.
*   AC6 (Preparación del Módulo de Notificaciones): Una vez verificada la conexión, el módulo de notificaciones debe estar listo para usarla.

#### Historia 1.3: Verificación de Conectividad y Estado Básico de la Cuenta de Binance
Como usuario de UltiBotInversiones,
quiero que el sistema verifique la conectividad con mi cuenta de Binance y muestre el estado básico de mis balances (específicamente USDT),
para asegurar que "UltiBotInversiones" está correctamente enlazado y listo para futuras operaciones (simuladas o reales).

##### Criterios de Aceptación:
*   AC1 (Acceso Seguro a Credenciales de Binance): El sistema debe ser capaz de recuperar de forma segura la API Key y el Secret Key de Binance del almacén de credenciales encriptadas.
*   AC2 (Prueba de Conexión y Obtención de Información de Cuenta): Al iniciar/actualizar credenciales de Binance, o por acción del usuario, el sistema debe usar las claves para confirmar validez y obtener información básica de la cuenta (balances).
*   AC3 (Visualización Específica del Saldo de USDT en la UI): Si la conexión es exitosa, la UI debe mostrar el saldo disponible de USDT en la cuenta Spot de Binance.
*   AC4 (Indicación Clara de Conexión Exitosa en la UI): La UI debe indicar visualmente que la conexión con Binance está activa y las credenciales son válidas.
*   AC5 (Manejo Detallado de Errores de Conexión o Autenticación con Binance): En caso de fallo, notificar al usuario de manera precisa en la UI sobre el tipo de error y posibles soluciones.
*   AC6 (Opción de Reintentar la Verificación de Conexión a Binance): El usuario debe poder solicitar manualmente un reintento de conexión y verificación de balances.
*   AC7 (Disponibilidad de Conexión para Módulos Posteriores): Una vez verificada, la conexión debe estar disponible para otros módulos (paper trading, ejecución real).

#### Historia 1.4: Configuración Inicial de la Aplicación y Persistencia de Datos Fundamentales
Como usuario de UltiBotInversiones,
quiero que el sistema cargue una configuración básica al arrancar y pueda guardar de forma segura y persistente (en la base de datos Supabase/PostgreSQL) cualquier ajuste esencial, como las preferencias iniciales o la ubicación de las credenciales encriptadas,
para asegurar que la aplicación inicie correctamente y recuerde mis ajustes importantes entre sesiones.

##### Criterios de Aceptación:
*   AC1 (Carga de Configuración Existente): Al iniciar, el sistema debe intentar cargar configuraciones guardadas desde Supabase/PostgreSQL.
*   AC2 (Aplicación de Valores por Defecto): Si no hay configuración o faltan parámetros, aplicar valores por defecto para ajustes esenciales.
*   AC3 (Persistencia de Nuevos Ajustes y Cambios): El sistema debe permitir guardar de forma persistente nuevos ajustes o cambios en configuraciones esenciales.
*   AC4 (Estructura de Configuración Segura para Datos Sensibles): La configuración debe manejar de forma segura referencias a datos sensibles (ej. acceso al almacén de claves API encriptadas).
*   AC5 (Arranque Exitoso con Configuraciones Guardadas): Tras un reinicio, la aplicación debe usar las últimas configuraciones guardadas o los valores por defecto.
*   AC6 (Manejo de Errores en Carga/Guardado de Configuración): Si hay un error crítico, informar al usuario y, si es posible, arrancar con una configuración mínima segura.
