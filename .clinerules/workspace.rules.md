- El sistema se basa en arquitectura modular y procesamiento paralelo.
- Usar `PyQt5` con `QDarkStyleSheet` como base de UI para el dashboard.
- siempre se debe asegurar el correcto funcionamiento del frontend con el backend
- Las operaciones reales deben confirmarse explícitamente por el usuario antes de ejecutarse.
- Toda funcionalidad debe estar alineada al PRD y respetar los NFRs definidos (latencia < 500ms, win rate > 75%, etc.).
- Todo análisis y decisión de trading debe tener trazabilidad, ya sea en logs o en la UI.

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

#### 🐞 Depuración Metódica

* Replica cada problema en escenarios mínimos.
* Análisis exhaustivo de logs y trazas.
* Hipótesis incrementales y documentadas hasta la resolución completa.

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