# Guía de Componentes de Front-End (PyQt5)

Este documento sirve como una guía para los componentes de interfaz de usuario (UI) reutilizables y los elementos de diseño atómico que se utilizarán en la aplicación "UltiBotInversiones". El objetivo es promover la consistencia, la reutilización y la eficiencia en el desarrollo del frontend con PyQt5.

## 1. Filosofía de Componentes

-   **Modularidad:** Diseñar componentes que sean autocontenidos y tengan una única responsabilidad bien definida.
-   **Reutilización:** Crear componentes genéricos que puedan ser utilizados en múltiples partes de la aplicación con mínima o ninguna modificación.
-   **Consistencia:** Asegurar que todos los componentes sigan la guía de estilo visual (`docs/front-end-style-guide.md`) y los estándares de codificación (`docs/front-end-coding-standards.md`).
-   **Personalización:** Permitir la personalización de componentes a través de parámetros o propiedades cuando sea necesario, sin romper su encapsulación.

## 2. Componentes Atómicos / Primitivos

Estos son los bloques de construcción básicos, a menudo wrappers o estilizaciones de widgets estándar de PyQt5.

-   **Botones (`ActionButton`, `IconButton`):**
    -   `ActionButton(QPushButton)`: Botón estándar para acciones primarias y secundarias.
        -   Propiedades: texto, icono (opcional), tipo (primario, secundario, peligro), estado (habilitado, deshabilitado).
        -   Estilo: Conforme a la paleta de colores y tipografía.
    -   `IconButton(QPushButton)`: Botón que solo contiene un icono.
        -   Propiedades: icono, tooltip.
-   **Campos de Entrada (`InputField`, `PasswordField`, `SearchField`):**
    -   `InputField(QLineEdit)`: Para entrada de texto general.
        -   Propiedades: placeholder, validación (opcional), icono (opcional).
    -   `PasswordField(QLineEdit)`: Para entrada de contraseñas (oculta el texto).
    -   `SearchField(QLineEdit)`: Campo de entrada con un icono de búsqueda y funcionalidad de borrado.
-   **Etiquetas (`Label`, `StatusLabel`):**
    -   `Label(QLabel)`: Para mostrar texto estático.
        -   Propiedades: texto, alineación, peso de fuente.
    -   `StatusLabel(QLabel)`: Etiqueta que puede cambiar de color según el estado (ej. éxito, error, advertencia).
-   **Selectores (`ComboBox`, `RadioButtonGroup`, `CheckBox`):**
    -   `ComboBox(QComboBox)`: Para seleccionar una opción de una lista desplegable.
    -   `RadioButtonGroup`: Un grupo de `QRadioButton` para selección única.
    -   `CheckBox(QCheckBox)`: Para opciones binarias (activado/desactivado).
-   **Indicadores de Progreso (`ProgressBar`):**
    -   `ProgressBar(QProgressBar)`: Para mostrar el progreso de una tarea.

## 3. Componentes Compuestos

Estos componentes combinan varios elementos atómicos o widgets estándar para crear funcionalidades más complejas.

-   **`SectionTitleWidget(QWidget)`:**
    -   Descripción: Un widget para mostrar un título de sección con una línea divisoria opcional.
    -   Contiene: `QLabel` para el título, `QFrame` para la línea.
-   **`FormFieldWidget(QWidget)`:**
    -   Descripción: Un widget que agrupa una etiqueta (`QLabel`) y un campo de entrada (`QLineEdit`, `QComboBox`, etc.) para formularios.
    -   Contiene: `QLabel`, widget de entrada.
    -   Puede incluir espacio para mensajes de validación.
-   **`StatusIndicatorWidget(QWidget)`:**
    -   Descripción: Muestra un icono y/o texto para indicar un estado (ej. Conectado ✅, Desconectado ❌, Verificando...).
    -   Contiene: `QLabel` (para icono), `QLabel` (para texto).
    -   Referencia: `docs/Front-end-spec.md` (Bloque A.3 en Gestión de Credenciales).
-   **`CredentialCardWidget(QWidget)`:**
    -   Descripción: Un widget para mostrar la información de una credencial de API en la lista de "Servicios Conectables".
    -   Contiene: Icono del servicio, nombre del servicio, estado, etiqueta de credencial.
    -   Referencia: `docs/Front-end-spec.md` (Panel Izquierdo en Gestión de Credenciales).
-   **`NotificationItemWidget(QWidget)`:**
    -   Descripción: Representa una notificación individual en la lista de notificaciones.
    -   Contiene: Icono de tipo/prioridad, timestamp, mensaje corto.
    -   Estilo: Fondo con color según prioridad.
    -   Referencia: `docs/Front-end-spec.md` (Bloque 4.1.2 en Dashboard).
-   **`StrategyCardWidget(QWidget)`:**
    -   Descripción: Muestra información resumida de una configuración de estrategia en el panel de gestión.
    -   Contiene: Nombre de la estrategia, tipo, estado (Paper/Real), última modificación, pares aplicables, botones de acción (editar, duplicar, eliminar, activar/desactivar).
    -   Referencia: `docs/Front-end-spec.md` (Panel de Gestión de Estrategias).
-   **`MarketDataRowWidget(QWidget)` o `MarketDataView (QTableView con modelo personalizado)`:**
    -   Descripción: Muestra los datos de un par de mercado en la lista de seguimiento.
    -   Columnas: Símbolo, Último Precio, Cambio 24h (%), Volumen 24h.
    -   Referencia: `docs/Front-end-spec.md` (Bloque 3.2.1 en Dashboard).
-   **`PortfolioAssetRowWidget(QWidget)` o `PortfolioAssetView (QTableView con modelo personalizado)`:**
    -   Descripción: Muestra los detalles de un activo en el desglose del portafolio.
    -   Columnas: Símbolo, Cantidad, Precio Prom. Compra, Precio Actual, Valor Actual, P&L No Realizado, % Portafolio.
    -   Referencia: `docs/Front-end-spec.md` (Bloque 2.3 en Dashboard).
-   **`StrategyPerformanceTableView(QWidget)`:**
    -   Archivo: `src/ultibot_ui/widgets/strategy_performance_table_view.py`
    -   Clase Principal: `StrategyPerformanceTableView`
    -   Modelo de Datos Asociado: `StrategyPerformanceTableModel` (definido en el mismo archivo).
    -   Propósito: Mostrar una tabla con el resumen del desempeño de las estrategias de trading. La tabla incluye columnas como Nombre de la Estrategia, Modo de Operación, Número de Operaciones, P&L Total y Win Rate.
    -   Dependencias Clave: `PyQt5.QtWidgets.QWidget`, `QTableView`, `QAbstractTableModel`.
    -   Métodos Públicos Clave:
        -   `set_data(data: List[Dict[str, Any]])`: Actualiza los datos que se muestran en la tabla. Los datos son una lista de diccionarios, donde cada diccionario representa el desempeño de una estrategia.
    -   Interacción y Características:
        -   Recibe los datos de desempeño desde `DashboardView`.
        -   Utiliza `StrategyPerformanceTableModel` para manejar la lógica de presentación de datos, incluyendo el formato de números y la alineación del texto.
        -   Implementa un coloreado de fondo para las filas basado en el modo de operación ("paper" o "real") para mejorar la diferenciación visual cuando se muestran datos de múltiples modos.
    -   Uso en la Aplicación: Se integra en `DashboardView` como una pestaña, permitiendo al usuario consultar y analizar el desempeño de sus estrategias de trading. Se puede filtrar por modo de operación (Todos, Paper, Real) mediante un `QComboBox` gestionado en `DashboardView`.

## 4. Vistas Principales / Contenedores de Layout

Estos son los componentes de más alto nivel que organizan las secciones principales de la aplicación.

-   **`MainWindow(QMainWindow)`:**
    -   La ventana principal de la aplicación.
    -   Contendrá la barra lateral de navegación y el área de contenido principal (`QStackedWidget` o similar).
-   **`SidebarNavigationWidget(QWidget)`:**
    -   El panel de navegación lateral con iconos y etiquetas para Dashboard, Oportunidades, Estrategias, Historial, Configuración.
    -   Referencia: `docs/Front-end-spec.md` (Barra Lateral de Navegación Actualizada).
-   **`DashboardView(QWidget)`:**
    -   El widget principal para la vista del Dashboard.
    -   Organizará las Zonas 1, 2, 3 y 4 utilizando `QSplitter` y otros layouts.
    -   Contendrá instancias de `MarketDataView`, `PortfolioAssetView`, el widget de gráficos, y el panel de notificaciones.
    -   Referencia: `docs/Front-end-spec.md` (Esquema de Bloques del Dashboard Principal).
-   **`SettingsView(QWidget)`:**
    -   Vista principal para la configuración del sistema.
    -   Podría usar un `QTabWidget` o similar para sub-secciones como "Gestión de Credenciales" y "Configuración General".
-   **`CredentialManagementView(QWidget)`:**
    -   La vista para gestionar las credenciales de API.
    -   Layout de dos paneles (lista de servicios y formulario/detalle).
    -   Referencia: `docs/Front-end-spec.md` (Gestión de Conexiones y Credenciales).
-   **`StrategyManagementView(QWidget)`:**
    -   La vista para gestionar las estrategias de trading.
    -   Contendrá la lista de `StrategyCardWidget` y formularios para crear/editar estrategias.
    -   Referencia: `docs/Front-end-spec.md` (Gestión de Estrategias de Trading).
-   **`TradeHistoryView(QWidget)`:**
    -   Vista para mostrar el historial de operaciones.
    -   Probablemente una `QTableView` con un modelo de datos personalizado.

## 5. Desarrollo y Documentación de Componentes

-   **Ubicación:** Los componentes reutilizables se ubicarán en `src/ultibot_ui/widgets/`. Las vistas principales en `src/ultibot_ui/windows/` o un directorio similar.
-   **Docstrings:** Cada clase de componente debe tener un docstring claro explicando su propósito, parámetros principales (si los tiene al instanciar) y señales/slots importantes.
-   **Ejemplos (Opcional):** Para componentes muy complejos o reutilizables, se podría considerar crear pequeños ejemplos de uso (posiblemente en un directorio de pruebas o ejemplos separado).

Esta guía evolucionará a medida que se desarrollen los componentes. El objetivo es tener una referencia clara para mantener la coherencia y facilitar el desarrollo del frontend.
