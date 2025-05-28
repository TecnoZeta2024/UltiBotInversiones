John, estamos trabajando en el PRD de UltiBotInversiones. Ya hemos definido y aprobado las Épicas 1, 2, 3 y 4, incluyendo todas sus Historias de Usuario y Criterios de Aceptación. La última Épica que aprobaste fue la Épica 4: 'Habilitación de Operativa Real Limitada y Gestión de Capital'. Estábamos listos para pasar a la siguiente Épica o sección del PRD

Basándome en la información de las fuentes, puedo describir un flujo de trabajo secuencial hipotético en Visual Studio Code (o un IDE similar) para un nuevo proyecto utilizando el método BMAD V3, así como las carpetas y archivos necesarios.

El método BMAD ha evolucionado significativamente para pasar de la "vibe coding" (codificación por intuición) no estructurada, que a menudo lleva a que los agentes "se salgan del carril" y desperdicien recursos, a un enfoque ágil impulsado por IA más planificado y optimizado. La versión 3 introduce un **Agente Orquestador BMAD** y una mayor personalización, con roles, tareas, checklists y plantillas separados.

El flujo de trabajo generalmente comienza en una interfaz web (como Gemini Gems o ChatGPT custom GPTs) con el Agente BMAD principal, donde se realiza la **planificación inicial**: ideación, brainstorming, investigación, definición del Product Requirements Document (PRD), arquitectura y especificaciones de diseño UI/UX. Una vez que estos artefactos de planificación están listos, el proceso pasa al entorno del IDE para la **ejecución y desarrollo**.

Para un rendimiento óptimo del sistema BMAD en Visual Studio Code, **necesitarás tener la siguiente estructura de carpetas y archivos en la raíz de tu proyecto**:

*   **Carpeta `bmad-agent`**: Debes copiar esta carpeta desde el repositorio de GitHub del método BMAD a la raíz de tu proyecto. Esta carpeta contiene todos los activos que los agentes locales del IDE necesitarán para funcionar. Dentro de `bmad-agent`, encontrarás subcarpetas para:
    *   `checklists`: Contiene las checklists detalladas que los agentes usan para validar su trabajo, como la checklist de Definición de "Done" para historias, la checklist maestra del Product Owner o la checklist de arquitectura.
    *   `data`: Puede contener archivos de datos auxiliares.
    *   `personas`: Define los diferentes roles o "personalidades" que los agentes pueden adoptar. Aquí encontrarás los archivos específicos para los agentes del IDE como `sm.ide.md` (Scrum Master) y `dev.ide.md` (Developer), que están ajustados para trabajar con la estructura de carpetas del método BMAD.
    *   `tasks`: Contiene conjuntos de instrucciones autónomos para tareas específicas, como ejecutar checklists, crear historias, "shardear" documentos (dividirlos en partes más pequeñas y detalladas), indexar bibliotecas, etc.. Estas tareas reducen la necesidad de que los agentes principales tengan todas las instrucciones cargadas al mismo tiempo y permiten que cualquier agente capaz ejecute una tarea si se le proporciona el contenido del archivo de tarea.
    *   `templates`: Define las estructuras para documentos clave como el PRD o las historias de usuario.

*   **Carpeta `docs`**: Esta carpeta debe crearse en la raíz de tu proyecto. Aquí es donde almacenarás los artefactos generados durante la fase de planificación (generalmente realizada en la web) y los documentos "shardeados" y las historias generadas por los agentes del IDE. Dentro de `docs`, tendrás:
    *   Los archivos iniciales de planificación: PRD, arquitectura, especificación UI/UX, etc..
    *   Los archivos generados por la tarea de "sharding": Archivos EPIC, referencia de API, vista de componentes, modelos de datos, estructura del proyecto.
    *   Una subcarpeta `stories`: Aquí se generarán y almacenarán las historias de usuario detalladas para el desarrollo.

**Hipotético Flujo de Trabajo Secuencial en Visual Studio Code (Post-Planificación Web):**

1.  **Configuración del IDE:**
    *   Asegúrate de haber copiado la carpeta `bmad-agent` al directorio raíz de tu proyecto.
    *   Copia los artefactos de planificación generados en la fase web (PRD, arquitectura, especificación UI/UX, etc.) a la carpeta `docs`. Si usaste una plantilla de inicio para tu proyecto, es crucial que hayas informado al agente durante la planificación para que los documentos generados se alineen con esa estructura.
    *   Configura el Agente BMAD Orquestador en Visual Studio Code. Esto generalmente implica copiar el contenido del archivo `IDE BMAD orchestrator markdown file` (ubicado en el repositorio del método BMAD) en la configuración de agente personalizado de tu IDE. Esto permite que el Agente BMAD acceda y utilice las carpetas `checklists`, `data`, `personas`, `tasks` y `templates` que copiaste. También necesitarás configurar los agentes `sm.ide.md` y `dev.ide.md`.
    *   Instala las dependencias del proyecto (ej. ejecutando `npm install`).

2.  **Sharding de Documentos:**
    *   Utiliza el Agente BMAD Orquestador configurado como Product Owner o Scrum Master (o los agentes PO/SM dedicados si los configuraste) para ejecutar la tarea de "sharding" de documentos.
    *   Esta tarea leerá el PRD y la arquitectura en la carpeta `docs` y generará documentos más granulares como archivos EPIC (con historias de alto nivel), referencia de API, vista de componentes, modelos de datos y la estructura detallada del proyecto (backend/frontend). Estos documentos se almacenarán dentro de la carpeta `docs` y son vitales para **mantener a los agentes desarrolladores "en el carril"**. Las historias, aunque de alto nivel en los EPICS, se detallarán más tarde y se almacenarán en `docs/stories`.

3.  **Ciclo de Desarrollo (Historia por Historia):** El flujo de trabajo en el IDE se vuelve iterativo, manejando una historia a la vez, generalmente utilizando ventanas de chat separadas para el Scrum Master y el Developer.
    *   **Drafting de la Historia (Scrum Master):**
        *   **Abre una *nueva ventana de chat*** y selecciona tu Agente Scrum Master (sm.ide.md).
        *   Pídele al Scrum Master que "draft the next story" (elabore la siguiente historia). El SM leerá la carpeta `docs`, identificará la última historia completada, determinará la siguiente historia basándose en los archivos EPIC shardeados y recopilará toda la información necesaria de los artefactos de arquitectura shardeados (modelos de datos, estructura del proyecto, etc.).
        *   El SM creará una **historia muy detallada con tareas y subtareas** diseñada para que el agente desarrollador la implemente directamente, sin necesidad de buscar en todos los demás archivos.
        *   El SM ejecutará una checklist para asegurar que el borrador de la historia sea completo.
    *   **Implementación de la Historia (Developer):**
        *   Una vez que la historia ha sido elaborada por el SM, **abre una *nueva ventana de chat*** y selecciona tu Agente Developer (dev.ide.md).
        *   Indícale al agente desarrollador que "implement this story" (implemente esta historia). El agente leerá la historia detallada, utilizará la información de los documentos shardeados (como la estructura del proyecto que indica dónde colocar los archivos) y escribirá el código necesario.
        *   El agente desarrollador **dejará notas** dentro del archivo de la historia (progreso, notas para el siguiente SM, registro de cambios, agente utilizado).
    *   **Revisión y Marcado como "Done":** Revisa el código que el agente desarrollador ha escrito. Una vez que estés satisfecho con la implementación y las pruebas (la checklist de Definición de "Done" ayuda aquí), **marca la historia como "done"** en el archivo de la historia.

4.  **Iteración:** Regresa al paso 3a (abrir una *nueva ventana de chat* para el Scrum Master) para que el SM elabore la siguiente historia. El SM utilizará las notas dejadas por el agente desarrollador en la historia anterior para informarse y evitar repetir errores o incorporar aprendizajes. Repite este ciclo hasta que se completen todas las historias planificadas para tu MVP o fase actual del proyecto.

5.  **Corrección de Curso (Si es Necesario):** Si en medio del proyecto necesitas hacer un cambio importante o añadir una nueva funcionalidad, utiliza la tarea o agente de "Course Correction" (Corrección de Curso). Este agente te ayudará a determinar el mejor enfoque (ej. si necesitas volver a la planificación, desechar algunas historias, o si puedes pivotar desde tu estado actual) y actualizará los artefactos y las historias restantes.

Este flujo de trabajo, apoyado por la estructura de carpetas `bmad-agent` y `docs` con sus subcarpetas y los documentos shardeados, permite que los agentes se mantengan enfocados, coherentes y "en el carril" durante todo el proceso de desarrollo en el IDE. La separación de tareas, personas y checklists, y la orquestación del Agente BMAD, son innovaciones clave en V3 que hacen que este proceso sea **poderoso y personalizable**.