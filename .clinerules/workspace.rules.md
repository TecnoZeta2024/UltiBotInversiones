### 🔧 Sistema Avanzado de Ingeniería del Software

Aplica estricta y sistemáticamente las siguientes prácticas técnicas en cada tarea:

#### 🧩 Principios Arquitectónicos

* **Separation of Concerns**: Claridad y modularidad extrema, responsabilidades delimitadas por módulos y capas.
* **Single Responsibility (SRP)**: Cada módulo y agente IA tiene una sola razón para cambiar, maximizando estabilidad.
* **Open/Closed (OCP)**: Prioriza extensibilidad usando abstracciones e inyección de dependencias.
* **Dependency Inversion (DIP)**: Alto nivel depende de abstracciones robustas y flexibles, evitando dependencias directas.

#### ✂️ Gestión del Código

* **Don't Repeat Yourself (DRY)**: Reutilización máxima mediante componentes modulares claramente documentados.
* **KISS & YAGNI**: Soluciones mínimas y efectivas, implementación solo ante necesidades concretas comprobadas.
* **Clean Code**: Código legible, funciones pequeñas, nombres descriptivos, control de flujo claro con early returns y guard clauses. Comentarios explican decisiones estratégicas (el "por qué", no el "qué").

#### ✅ Validación de Contexto Inicial y Artefactos
* **Cuando el contexto inicial de una tarea (especialmente una tarea de continuación o una que depende de un estado previo) mencione artefactos específicos (archivos, configuraciones) como existentes o con un estado particular, y estos sean relevantes para la tarea actual:
    * Considera un paso temprano de verificación (ej. `list_files` en el directorio relevante, `read_file` selectivo si el contenido es clave, o incluso `search_files` si se busca un patrón específico) para confirmar su estado real.
    * Si se detectan discrepancias significativas entre el estado esperado y el real (ej. archivos cruciales faltantes, contenido muy diferente), informa al usuario de estas discrepancias y cómo podrían afectar el plan o el resultado de la tarea. Ajusta el plan según sea necesario.
    * Si existe un `docs/project_tasks/issues_log.md`, considera registrar estas discrepancias.

#### 🐞 Depuración Metódica

* Replica cada problema en escenarios mínimos.
* Análisis exhaustivo de logs y trazas.
* Hipótesis incrementales y documentadas hasta la resolución completa.
* **Utiliza y actualiza sistemáticamente cualquier documento de seguimiento de errores o tareas (ej. archivos Markdown, issues de proyecto) para registrar el progreso, los hallazgos y los próximos pasos.**
* **Al encontrar discrepancias entre el estado esperado de los artefactos (ej. archivos faltantes o con contenido inesperado basado en información previa) y el estado real, considera esto como un punto de atención. Si existe un archivo de log de tareas designado (ej. `docs/project_tasks/issues_log.md`), intenta añadir una entrada concisa sobre la discrepancia y cómo se manejó. Informa al usuario si la discrepancia podría afectar el resultado general de la tarea.**
* **Adicionalmente, al encontrar errores significativos (fallos de herramientas, interrupciones de API) o al realizar handoffs de tareas complejas, si existe un archivo de log de tareas designado en el proyecto (ej. `docs/project_tasks/issues_log.md`), intenta añadir una entrada concisa resumiendo el problema, la solución aplicada o los próximos pasos. Esto complementa el contexto transferido mediante `new_task`.**
* **Al ejecutar scripts o comandos, especialmente aquellos que no son directamente ejecutables por el intérprete primario (e.g., `.bat` en Windows, `.sh` en Linux/macOS), verifica el método de invocación apropiado para el sistema operativo y shell del usuario. Por ejemplo, para PowerShell en Windows, los scripts en el directorio actual a menudo requieren el prefijo `.\`. Considera el tipo de archivo y el entorno antes de usar `execute_command` para minimizar errores de ejecución.**

#### 🔝 Mejora Continua y Deuda Técnica

* Sigue estrictamente la regla del Boy Scout: "deja el código y procesos mejor que como los encontraste".
* Documenta, registra y prioriza deuda técnica, abordándola proactivamente en ciclos de mejora específicos.

### 🛠 Gestión de Equipos de Agentes IA

* Define claramente objetivos y tareas específicas para cada agente IA.
* Coordina agentes con instrucciones claras y concretas sobre el cumplimiento riguroso de estas prácticas tecnológicas.
* Evalúa resultados continuamente, corrigiendo y ajustando procesos para optimizar desempeño y resultados.

### 🎯 Resultado Esperado

Cada tarea ejecutada por ti y tu equipo de agentes IA debe:

* Reflejar excelencia técnica y calidad innegociable.
* Entregar resultados altamente eficientes y efectivos.
* Mantener alineamiento constante con objetivos estratégicos personales de desarrollo digital.
