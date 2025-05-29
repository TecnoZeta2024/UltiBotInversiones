# Estrategia de Enrutamiento en el Front-End (PyQt5)

Este documento detalla cómo se gestionará la navegación entre diferentes vistas o pantallas dentro de la aplicación de escritorio "UltiBotInversiones", desarrollada con PyQt5. El objetivo es tener un sistema de navegación claro, predecible y fácil de mantener.

## 1. Mecanismo Principal de Navegación: `QStackedWidget`

La navegación principal entre las diferentes secciones de la aplicación (Dashboard, Oportunidades, Estrategias, Historial, Configuración) se gestionará utilizando un `QStackedWidget`.

-   **Funcionamiento:**
    -   La ventana principal (`MainWindow`) contendrá una barra de navegación lateral (`SidebarNavigationWidget`) y un `QStackedWidget` que ocupará el área de contenido principal.
    -   Cada sección principal de la aplicación (Dashboard, Configuración, etc.) será un widget independiente (ej. `DashboardView(QWidget)`, `SettingsView(QWidget)`).
    -   Estos widgets de vista se añadirán como "páginas" al `QStackedWidget`.
    -   Cuando el usuario haga clic en un ítem de la `SidebarNavigationWidget`, se emitirá una señal. Esta señal será capturada por la `MainWindow`, que a su vez llamará al método `setCurrentIndex()` o `setCurrentWidget()` del `QStackedWidget` para mostrar la vista correspondiente.

-   **Ventajas:**
    -   **Simple y Eficaz:** Es un mecanismo estándar de Qt para manejar múltiples vistas en un solo espacio.
    -   **Gestión Centralizada:** La lógica de cambio de vista reside principalmente en la `MainWindow`.
    -   **Rendimiento:** Los widgets que no están visibles en el `QStackedWidget` no consumen recursos de renderizado significativos (aunque siguen existiendo en memoria).

## 2. Componentes Involucrados

-   **`MainWindow(QMainWindow)`:**
    -   Contiene la `SidebarNavigationWidget` y el `QStackedWidget`.
    -   Conecta las señales de la `SidebarNavigationWidget` a slots que cambian la vista activa en el `QStackedWidget`.
    -   Mantiene referencias a las instancias de las vistas principales.

-   **`SidebarNavigationWidget(QWidget)`:**
    -   Muestra los ítems de navegación (Dashboard, Oportunidades, etc.), como se define en `docs/Front-end-spec.md`.
    -   Emite una señal cuando un ítem de navegación es seleccionado, pasando un identificador o índice de la vista deseada.
        ```python
        # Ejemplo de señal en SidebarNavigationWidget
        # view_selected_signal = pyqtSignal(str) # str podría ser el nombre de la vista
        # ...
        # self.dashboard_button_btn.clicked.connect(lambda: self.view_selected_signal.emit("dashboard"))
        ```

-   **`QStackedWidget`:**
    -   Instanciado en `MainWindow`.
    -   Las vistas (`DashboardView`, `SettingsView`, etc.) se añaden a este widget.

-   **Vistas Individuales (ej. `DashboardView(QWidget)`):**
    -   Cada vista es un `QWidget` (o una subclase) que encapsula toda la UI y lógica para esa sección.
    -   No necesitan conocer directamente el mecanismo de enrutamiento; son simplemente mostradas u ocultadas por el `QStackedWidget`.

## 3. Flujo de Navegación

1.  El usuario hace clic en un ítem en la `SidebarNavigationWidget` (ej. "Estrategias").
2.  La `SidebarNavigationWidget` emite una señal (ej. `view_selected_signal.emit("strategies")`).
3.  La `MainWindow` tiene un slot conectado a esta señal.
4.  El slot en `MainWindow` identifica el widget de vista correspondiente a "strategies" (ej. `self.strategy_management_view`) y llama a `self.stacked_widget.setCurrentWidget(self.strategy_management_view)`.
5.  El `QStackedWidget` muestra la `StrategyManagementView` y oculta la vista anteriormente activa.
6.  La `SidebarNavigationWidget` actualiza su estado visual para resaltar "Estrategias" como la sección activa.

## 4. Navegación Interna dentro de las Vistas (Sub-Navegación)

Si una vista principal (ej. `SettingsView`) tiene múltiples sub-secciones (ej. "Gestión de Credenciales", "Configuración General"), esta sub-navegación puede gestionarse internamente dentro de `SettingsView` utilizando:

-   **`QTabWidget`:** Ideal para un número pequeño y fijo de sub-secciones.
-   Otro `QStackedWidget` anidado: Si las sub-secciones son complejas o numerosas.
-   Botones o una lista que cambien el contenido de un panel dentro de la vista.

La `MainWindow` no necesita estar al tanto de esta sub-navegación interna.

## 5. Consideraciones

-   **Inicialización de Vistas:**
    -   Las vistas pueden ser instanciadas todas al inicio de la aplicación y añadidas al `QStackedWidget`.
    -   Alternativamente, para optimizar el tiempo de inicio si algunas vistas son muy pesadas, se podría considerar la carga perezosa (lazy loading), donde una vista solo se instancia la primera vez que se navega a ella. Para la v1.0, la instanciación al inicio es más simple.
-   **Paso de Datos entre Vistas:**
    -   Generalmente, las vistas deben ser lo más independientes posible.
    -   Si se necesita pasar datos al activar una vista, se puede hacer a través de métodos en la vista que son llamados por `MainWindow` antes de mostrarla, o mediante un sistema de gestión de estado más centralizado si la complejidad aumenta (ver `docs/front-end-state-management.md`).
-   **Estado de Navegación:**
    -   La `SidebarNavigationWidget` debe reflejar visualmente qué vista está activa.
    -   La `MainWindow` es responsable de mantener la coherencia entre la selección de la barra lateral y la vista mostrada.

Esta estrategia de enrutamiento basada en `QStackedWidget` proporciona una solución robusta y estándar de Qt para las necesidades de navegación de "UltiBotInversiones" en su v1.0.
