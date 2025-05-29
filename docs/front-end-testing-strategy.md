# Estrategia de Pruebas del Front-End (PyQt5)

Este documento describe el enfoque y las estrategias para probar la interfaz de usuario (UI) de "UltiBotInversiones", desarrollada con PyQt5. El objetivo es asegurar que la UI sea funcional, usable, robusta y cumpla con los requisitos definidos.

## 1. Referencia a la Estrategia General de Pruebas

Esta estrategia de pruebas del frontend es un complemento a la "Overall Testing Strategy" definida en `docs/Architecture.md` (sección "Overall Testing Strategy"). Se enfoca en los aspectos específicos de la UI con PyQt5.

## 2. Tipos de Pruebas para el Frontend

### 2.1. Pruebas Unitarias de Lógica de UI (Opcional para v1.0, Enfocarse si hay Lógica Compleja)

-   **Alcance:** Probar la lógica interna de los widgets personalizados o vistas que no dependa directamente de la renderización visual o interacciones complejas de Qt. Esto podría incluir:
    -   Formateo de datos para visualización.
    -   Lógica de validación simple en campos de entrada (aunque la validación autoritativa está en el backend).
    -   Manejo de estado interno simple de un widget.
-   **Herramientas:** `pytest` y `unittest.mock`.
-   **Consideración para v1.0:** Para mantener la agilidad, las pruebas unitarias exhaustivas de la lógica de UI pueden ser limitadas. Se priorizarán si un widget contiene una lógica no trivial que pueda ser probada sin instanciar completamente el entorno gráfico.

### 2.2. Pruebas de Integración de Componentes (Limitadas para v1.0)

-   **Alcance:** Probar la interacción entre varios widgets personalizados o la correcta conexión de señales y slots dentro de una vista compuesta.
-   **Herramientas:** `pytest-qt`. Esta biblioteca proporciona utilidades para interactuar con widgets Qt en un entorno de prueba, simular eventos de usuario (clics, entrada de texto) y verificar el estado de los widgets.
    -   `qtbot`: Un fixture de `pytest-qt` que permite controlar y consultar widgets.
-   **Ejemplos:**
    -   Verificar que al hacer clic en un botón en `SidebarNavigationWidget` se emita la señal correcta.
    -   Verificar que al cambiar el texto en un `QLineEdit`, un `QLabel` asociado se actualice correctamente si están conectados.
-   **Consideración para v1.0:** Se pueden implementar algunas pruebas de integración para los flujos de interacción más críticos o complejos dentro de las vistas. Sin embargo, una cobertura exhaustiva podría ser post-v1.0.

### 2.3. Pruebas de Interfaz de Usuario (UI Testing) / Pruebas Funcionales (Principalmente Manuales para v1.0)

-   **Alcance:** Verificar que la aplicación completa, desde la perspectiva del usuario, se comporta como se espera. Esto incluye:
    -   Navegación entre vistas.
    -   Correcta visualización de datos obtenidos del backend.
    -   Respuesta a interacciones del usuario (clics, entrada de formularios, etc.).
    -   Manejo de errores y presentación de mensajes al usuario.
    -   Cumplimiento de los flujos de usuario definidos en `docs/Front-end-spec.md`.
-   **Enfoque para v1.0:** **Principalmente Pruebas Manuales Exhaustivas.**
    -   Se crearán casos de prueba basados en las historias de usuario y los criterios de aceptación de las Épicas 1 a 5.
    -   El equipo (incluyéndote a ti, Carlos, como usuario principal) ejecutará estos casos de prueba manualmente en la aplicación.
    -   Se documentarán los resultados, y cualquier error o desviación se registrará como un bug.
-   **Automatización (Post-v1.0):**
    -   Para futuras versiones, se podría considerar la automatización de pruebas de UI utilizando herramientas como:
        -   `pytest-qt` para escenarios más complejos.
        -   Herramientas de automatización de GUI de propósito general si fuera necesario (aunque pueden ser más frágiles).
    -   La inversión en automatización de UI se evaluará según el ROI y la estabilidad de la interfaz.

### 2.4. Pruebas de Usabilidad (Manuales)

-   **Alcance:** Evaluar la facilidad de uso, la intuitividad y la satisfacción general del usuario con la interfaz.
-   **Enfoque:**
    -   Revisiones heurísticas basadas en principios de usabilidad.
    -   Pruebas informales "pensando en voz alta" realizadas por ti, Carlos, mientras usas la aplicación, para identificar puntos de fricción o confusión.
    -   Feedback continuo durante el desarrollo.

## 3. Entorno de Pruebas

-   Las pruebas unitarias y de integración (si se automatizan) se ejecutarán en un entorno local de desarrollo.
-   Las pruebas manuales se realizarán directamente sobre la aplicación en ejecución en el entorno de desarrollo.

## 4. Cobertura de Pruebas

-   Para la v1.0, el énfasis estará en la **cobertura funcional a través de pruebas manuales exhaustivas** de los flujos críticos.
-   La cobertura de código por pruebas unitarias/integración automatizadas para la UI será secundaria en v1.0, enfocándose en lógica compleja si la hubiera.

## 5. Responsabilidades

-   **Desarrollador (Karen, como Design Architect y potencialmente guiando a un agente desarrollador de UI):**
    -   Asegurar que los componentes de la UI estén diseñados para ser testeables.
    -   Implementar pruebas unitarias/integración para lógica de UI crítica o compleja (si se decide).
    -   Colaborar en la definición de casos de prueba manuales.
-   **Usuario Principal (Carlos):**
    -   Participación activa en pruebas manuales de usabilidad y funcionales.
    -   Proporcionar feedback continuo sobre la UI.

## 6. Herramientas Específicas para Pruebas de UI con PyQt5

-   **`pytest-qt`:**
    -   Proporciona el fixture `qtbot`.
    -   `qtbot.addWidget(widget)`: Registra un widget para limpieza automática.
    -   `qtbot.mouseClick(widget, Qt.LeftButton)`: Simula clics.
    -   `qtbot.keyClicks(widget, "texto")`: Simula entrada de teclado.
    -   `qtbot.waitUntil(callback, timeout)`: Espera hasta que una condición se cumpla.
    -   Permite verificar señales emitidas y el estado de los widgets.

```python
# Ejemplo conceptual de una prueba de integración con pytest-qt
# (Asumiendo un widget LoginDialog con campos username_le, password_le y login_btn)

# def test_login_dialog_successful_login_emits_signal(qtbot):
#     dialog = LoginDialog()
#     qtbot.addWidget(dialog)

#     # Simular entrada de usuario
#     qtbot.keyClicks(dialog.username_le, "testuser")
#     qtbot.keyClicks(dialog.password_le, "password")

#     # Conectar a una señal que el diálogo debería emitir en login exitoso
#     with qtbot.waitSignal(dialog.login_successful_signal, timeout=1000) as blocker:
#         qtbot.mouseClick(dialog.login_button_btn, Qt.LeftButton)
    
#     assert blocker.args == ["testuser"] # Verificar argumentos de la señal
```

Esta estrategia busca asegurar una UI de calidad para "UltiBotInversiones" v1.0, balanceando la necesidad de robustez con la agilidad requerida para el desarrollo inicial.
