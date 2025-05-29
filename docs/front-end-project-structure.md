# Estructura del Proyecto Front-End (PyQt5)

Este documento detalla la estructura organizativa para el código fuente del frontend de "UltiBotInversiones", desarrollado con PyQt5. También incluye la estructura de navegación de la aplicación como se define en la especificación UI/UX.

## 1. Estructura de Directorios del Código Fuente (`src/ultibot_ui/`)

La interfaz de usuario de PyQt5 residirá dentro del directorio `src/ultibot_ui/` del monorepo, como se especifica en `docs/Architecture.md` (sección "Project Structure"). La estructura interna propuesta para `src/ultibot_ui/` es la siguiente:

```
src/
└── ultibot_ui/                 # Módulo principal de la interfaz de usuario con PyQt5
    ├── __init__.py             # Hace de ultibot_ui un paquete Python
    ├── main.py                 # Punto de entrada de la aplicación PyQt5 (inicializa QApplication, MainWindow)
    ├── main_window.py          # Define la clase MainWindow principal de la aplicación
    │
    ├── assets/                 # Recursos estáticos de la UI
    │   ├── icons/              # Iconos (SVG, PNG)
    │   ├── images/             # Imágenes generales (si las hubiera)
    │   └── stylesheets/        # Hojas de estilo (ej. qdarkstyle.qss, custom.qss)
    │
    ├── components/             # Componentes de UI reutilizables (ver docs/front-end-component-guide.md)
    │   ├── __init__.py
    │   ├── atomic/             # Componentes atómicos/primitivos
    │   │   ├── __init__.py
    │   │   ├── action_button.py
    │   │   └── input_field.py
    │   │   └── ... (otros componentes atómicos)
    │   └── composite/          # Componentes compuestos
    │       ├── __init__.py
    │       ├── credential_card_widget.py
    │       ├── notification_item_widget.py
    │       └── ... (otros componentes compuestos)
    │
    ├── views/                  # Widgets que representan las vistas/pantallas principales
    │   ├── __init__.py
    │   ├── dashboard_view.py
    │   ├── settings_view.py
    │   ├── credential_management_view.py
    │   ├── strategy_management_view.py
    │   ├── trade_history_view.py
    │   └── opportunities_view.py
    │
    ├── dialogs/                # Diálogos personalizados
    │   ├── __init__.py
    │   ├── confirm_dialog.py
    │   └── error_dialog.py
    │
    ├── models/                 # Modelos de datos específicos para la UI (ej. QAbstractTableModel)
    │   ├── __init__.py
    │   └── trade_history_model.py
    │
    ├── services/               # Lógica para interactuar con el backend o servicios de UI
    │   ├── __init__.py
    │   ├── api_client.py       # Cliente HTTP para la API del backend (usando httpx)
    │   └── notification_handler_ui.py # Manejo de notificaciones en la UI
    │
    ├── utils/                  # Utilidades específicas del frontend
    │   ├── __init__.py
    │   └── helpers.py
    │
    └── resources/              # Archivos de recursos de Qt (si se usan .qrc)
        └── resources.qrc
        └── resources_rc.py     # Generado por pyrcc5
```

**Descripción de Directorios Clave:**

-   **`main.py`**: Punto de entrada que inicia la `QApplication` y muestra la `MainWindow`.
-   **`main_window.py`**: Define la `QMainWindow` principal, que contendrá la barra lateral de navegación y el `QStackedWidget` para las diferentes vistas.
-   **`assets/`**: Almacena recursos estáticos como iconos, imágenes y hojas de estilo (ej. `qdarkstyle.qss` o una hoja de estilo personalizada).
-   **`components/`**: Contiene los widgets personalizados reutilizables, divididos en `atomic` (botones, campos de entrada básicos) y `composite` (combinaciones más complejas como `CredentialCardWidget`). Esto se alinea con la `docs/front-end-component-guide.md`.
-   **`views/`**: Cada archivo aquí representa una pantalla o sección principal de la aplicación (ej. `DashboardView`, `SettingsView`). Estos son los widgets que se cargarán en el `QStackedWidget` de la `MainWindow`.
-   **`dialogs/`**: Para diálogos personalizados reutilizables (ej. confirmación, error, entrada de datos específicos).
-   **`models/`**: Si se utilizan modelos de datos de Qt (como `QAbstractTableModel`) para poblar vistas como `QTableView`, se definirán aquí.
-   **`services/`**: Clases que manejan la lógica de comunicación con el backend (`api_client.py`) o servicios específicos de la UI (ej. un manejador central para las notificaciones que se muestran en la UI).
-   **`utils/`**: Funciones de ayuda o utilidades misceláneas específicas para el frontend.
-   **`resources/`**: Para el sistema de recursos de Qt si se compilan recursos en la aplicación (opcional para v1.0 si los assets se cargan directamente).

## 2. Estructura de Navegación de la Aplicación

La navegación se basa en una barra lateral y un área de contenido principal, como se describe en `docs/Front-end-spec.md`.

### 2.1. Barra Lateral de Navegación (Sidebar)

-   Un panel vertical a la izquierda de la pantalla que lista las secciones principales.
-   Ítems de la Barra Lateral (basado en `docs/Front-end-spec.md` y `docs/front-end-component-guide.md`):
    -   `<Icono> Dashboard`
    -   `<Icono> Oportunidades` (Vista para oportunidades detectadas)
    -   `<Icono> Estrategias` (Panel de Gestión de Estrategias)
    -   `<Icono> Historial` (Historial y Detalles de Operaciones)
    -   `<Icono> Configuración` (Configuración del Sistema: Credenciales, General)
-   **Iconografía**: Se utilizarán iconos representativos para cada ítem.
-   **Estado Activo**: El ítem de la sección activa en la barra lateral estará claramente resaltado.

### 2.2. Mecanismo de Enrutamiento

-   Se utilizará un `QStackedWidget` en la `MainWindow` para gestionar el cambio entre las diferentes vistas principales.
-   La selección de un ítem en la `SidebarNavigationWidget` cambiará la vista actual en el `QStackedWidget`.
-   Más detalles en `docs/front-end-routing-strategy.md`.

Esta estructura de proyecto y navegación busca proporcionar una base organizada y escalable para el desarrollo del frontend de "UltiBotInversiones".
