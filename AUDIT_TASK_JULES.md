### INFORME DE ESTADO Y PLAN DE ACCIÓN - 2025-06-10 18:15

**ESTADO ACTUAL:**
*   Iniciando FASE 2: HIPÓTESIS Y PLAN DE ACCIÓN UNIFICADO. Se ha procesado el análisis del equipo de desarrollo y se ha formulado una nueva hipótesis central que aborda los errores de concurrencia asíncrona.

**1. OBSERVACIONES (Resultados de FASE 1):**
*   El análisis del equipo de desarrollo y los logs (`frontend.log`) confirman múltiples errores de `sniffio: 'async library not found'` en varios componentes de la UI, incluyendo `PresetManagementDialog`, `NotificationWidget` y `PortfolioWidget`.
*   Se ha identificado un `RuntimeError: Task attached to a different loop` específicamente en `PortfolioWidget`, relacionado con el uso de `asyncio.gather` a través de un `ApiWorker`.
*   La causa raíz identificada es la creación incorrecta de nuevos bucles de eventos `asyncio` en hilos de trabajo (`QThread`) de la UI, en lugar de utilizar el bucle de eventos principal gestionado por `qasync`.
*   Ya se ha realizado una refactorización parcial en `PresetManagementDialog` para utilizar el bucle principal, validando la estrategia de solución.

**2. HIPÓTESIS CENTRAL (Resultados de FASE 2):**
*   La proliferación de múltiples bucles de eventos `asyncio` en la capa de la interfaz de usuario es la causa fundamental de los errores de `sniffio` y `RuntimeError`. La biblioteca `httpx`, utilizada por el `api_client`, y otras bibliotecas asíncronas, no están diseñadas para operar a través de diferentes bucles de eventos de manera segura. La solución consiste en centralizar todas las operaciones asíncronas de la UI en el único bucle de eventos `qasync` creado en `src/ultibot_ui/main.py` y pasarlo explícitamente a todos los componentes que lo necesiten.

**3. PLAN DE ACCIÓN UNIFICADO (Propuesta para FASE 3):**
| Archivo a Modificar | Descripción del Cambio | Justificación (Por qué este cambio soluciona el problema) |
| :--- | :--- | :--- |
| `src/ultibot_ui/widgets/notification_widget.py` | Modificar el constructor de `NotificationWidget` para que acepte el bucle de eventos `qasync` como argumento. Actualizar su lógica interna para utilizar este bucle al realizar llamadas a la API. | Centraliza la ejecución asíncrona en el bucle principal de la aplicación, eliminando la creación de bucles de eventos ad-hoc y resolviendo los errores `sniffio` asociados a este widget. |
| `src/ultibot_ui/windows/main_window.py` | Localizar la instanciación de `NotificationWidget` y pasarle el bucle de eventos principal (`self.loop`) como argumento en su constructor. | Proporciona al widget la instancia correcta del bucle de eventos `qasync`, permitiendo que las operaciones asíncronas se ejecuten en el contexto adecuado. |
| `src/ultibot_ui/widgets/portfolio_widget.py` y `src/ultibot_ui/workers.py` | No se realizarán cambios directos por ahora. Se observará su comportamiento durante la fase de pruebas. | La hipótesis es que el `RuntimeError` es un efecto secundario de la mala gestión de bucles en otros componentes. Al corregir los demás widgets, es probable que este error se resuelva sin modificación directa. |
| **Pruebas y Verificación** | Ejecutar `./run_frontend_with_backend.bat` y probar exhaustivamente las funcionalidades de gestión de presets, notificaciones y portafolio. | Validar que los errores `sniffio` y `RuntimeError` han sido eliminados y que la aplicación funciona de manera estable con un único bucle de eventos. |

**4. RIESGOS POTENCIALES:**
*   Medio. La refactorización de la concurrencia es delicada. Existe el riesgo de que la centralización del bucle de eventos pueda introducir cuellos de botella si las tareas asíncronas son muy pesadas y bloquean la UI. Sin embargo, el uso de `ApiWorker` en hilos separados mitiga este riesgo. El principal riesgo es que el `RuntimeError` en `PortfolioWidget` persista, lo que requeriría un análisis más profundo (post-mortem).

**5. SOLICITUD:**
*   [**PAUSA**] Espero aprobación explícita ("Procede con el plan") para ejecutar las modificaciones propuestas.
