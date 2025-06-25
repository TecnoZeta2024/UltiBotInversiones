# Librería de Componentes de UI - UltiBot

Este documento sirve como una guía de estilo y referencia técnica para los componentes de la interfaz de usuario (UI) de UltiBot. El objetivo es mantener la consistencia, promover la reutilización y acelerar el desarrollo.

---

## 1. Componentes de Navegación y Estado

### 1.1. TradingModeSelector

**Archivo:** `src/ultibot_ui/widgets/trading_mode_selector.py`

#### **Descripción**
El `TradingModeSelector` es un widget compuesto que proporciona un control visual para que el usuario pueda cambiar entre los modos de trading de la aplicación (ej. `Paper Trading` y `Real Trading`). Está diseñado para ser flexible y puede presentarse en varios estilos visuales.

#### **API del Widget**

**Propiedades (al inicializar)**

| Propiedad | Tipo  | Por Defecto | Descripción                                                                 |
|-----------|-------|-------------|-----------------------------------------------------------------------------|
| `style`   | `str` | `"toggle"`  | Define el estilo visual del widget. Opciones: `"toggle"`, `"dropdown"`, `"radio"`. |
| `parent`  | `QWidget` | `None`      | El widget padre en la jerarquía de Qt.                                      |

**Señales (Eventos que emite)**

| Señal          | Argumentos | Descripción                                                              |
|----------------|------------|--------------------------------------------------------------------------|
| `mode_changed` | `str`      | Se emite cuando el modo de trading cambia, pasando el nuevo modo como `str`. |

**Slots / Métodos Públicos (Acciones que puede realizar)**

| Método                | Argumentos      | Devuelve | Descripción                                                                                             |
|-----------------------|-----------------|----------|---------------------------------------------------------------------------------------------------------|
| `set_enabled_modes`   | `modes: list`   | `None`   | Habilita o deshabilita modos de trading específicos. Ej: `['paper']` deshabilita la opción `real`.      |
| `get_current_mode`    | `None`          | `str`    | Devuelve el modo de trading actualmente activo (ej. `"paper"` o `"real"`).                               |

#### **Estados Visuales**

1.  **Estado de Modo (`paper` vs. `real`):**
    *   El color del indicador de estado, el texto y los iconos cambian para reflejar el modo activo.
    *   **Paper:** Generalmente asociado con un color verde o azul para indicar seguridad.
    *   **Real:** Generalmente asociado con un color naranja o rojo para indicar precaución.

2.  **Estado de Estilo (`toggle`, `dropdown`, `radio`):**
    *   La estructura fundamental del widget cambia según el estilo seleccionado en el constructor.

3.  **Estado de Interacción (`hover`, `pressed`):**
    *   El widget proporciona retroalimentación visual cuando el usuario interactúa con él, como cambios de color en los bordes o el fondo.

4.  **Estado Habilitado/Deshabilitado:**
    *   El widget puede ser deshabilitado (parcial o totalmente) a través del método `set_enabled_modes`. Por ejemplo, si solo el modo `paper` está habilitado, el botón de tipo `toggle` se desactivará.

#### **Uso Recomendado**
-   Colocar en la cabecera principal de la aplicación o en una barra de navegación superior para un acceso rápido y visible.
-   Utilizar el estilo `"toggle"` para un cambio rápido entre dos modos.
-   Utilizar el estilo `"dropdown"` si se planea añadir más de dos modos en el futuro.

---

### 1.2. TradingModeStatusBar

**Archivo:** `src/ultibot_ui/widgets/trading_mode_selector.py`

#### **Descripción**
Un widget de solo lectura, simple y compacto, diseñado para mostrar el modo de trading actual. Es ideal para barras de estado o pies de página donde el espacio es limitado y no se requiere interacción directa.

#### **API del Widget**
Este componente no tiene una API pública significativa. Su única función es escuchar los cambios del `TradingModeStateManager` y actualizar su propia apariencia.

#### **Estados Visuales**
-   El color de fondo y el texto del widget cambian para coincidir con el modo de trading activo, de forma similar al `TradingModeSelector`.

#### **Uso Recomendado**
-   Incrustar en la barra de estado principal de la aplicación (`QStatusBar`) para proporcionar información contextual persistente al usuario.

---

## 2. Componentes de Navegación

### 2.1. SidebarNavigationWidget

**Archivo:** `src/ultibot_ui/widgets/sidebar_navigation_widget.py`

#### **Descripción**
El `SidebarNavigationWidget` es un panel de navegación vertical que contiene los puntos de acceso principales a las diferentes vistas de la aplicación (Dashboard, Terminal, Estrategias, etc.). Gestiona el estado de la vista activa y notifica al resto de la aplicación cuando el usuario solicita un cambio de vista.

#### **API del Widget**

**Propiedades (al inicializar)**
Este widget no tiene propiedades de inicialización personalizables.

**Señales (Eventos que emite)**

| Señal                  | Argumentos | Descripción                                                                 |
|------------------------|------------|-----------------------------------------------------------------------------|
| `navigation_requested` | `str`      | Se emite cuando se hace clic en un botón, pasando el nombre de la vista solicitada. |

**Slots / Métodos Públicos (Acciones que puede realizar)**

| Método          | Argumentos | Devuelve | Descripción                                                                                             |
|-----------------|------------|----------|---------------------------------------------------------------------------------------------------------|
| `select_view`   | `name: str`| `None`   | Permite cambiar la vista de forma programática, simulando el clic en el botón de navegación correspondiente. |

#### **Estados Visuales**

1.  **Estado Activo/Seleccionado (`checked`):**
    *   El botón correspondiente a la vista actualmente visible se resalta con un color de fondo y texto distintivos para indicar la ubicación del usuario en la aplicación.
    *   El widget asegura que solo un botón pueda estar en estado `checked` a la vez.

2.  **Estado de Interacción (`hover`):**
    *   Proporciona retroalimentación visual cuando el cursor del ratón se sitúa sobre un botón de navegación, típicamente cambiando su color de fondo para indicar que es un elemento interactivo.

#### **Uso Recomendado**
-   Utilizar como el componente principal de navegación en un diseño de `QMainWindow` o similar, anclado al lado izquierdo de la ventana.
-   Conectar la señal `navigation_requested` a un `QStackedWidget` o un mecanismo similar para cambiar la vista central que se muestra al usuario.

---

## 3. Componentes de Visualización de Datos

### 3.1. ChartWidget

**Archivo:** `src/ultibot_ui/widgets/chart_widget.py`

#### **Descripción**
El `ChartWidget` es el componente principal para la visualización de datos de mercado. Renderiza gráficos de velas (candlestick) interactivos utilizando `mplfinance`. Incluye controles para cambiar el símbolo del activo y la temporalidad del gráfico. La obtención de datos se realiza de forma asíncrona para no bloquear la UI.

#### **API del Widget**

**Propiedades (al inicializar)**

| Propiedad     | Tipo              | Descripción                                                              |
|---------------|-------------------|--------------------------------------------------------------------------|
| `api_client`  | `UltiBotAPIClient`| Una instancia del cliente API para realizar las solicitudes de datos de mercado. |
| `main_window` | `BaseMainWindow`  | Una referencia a la ventana principal para la gestión de hilos (`QThread`). |
| `parent`      | `QWidget`         | El widget padre en la jerarquía de Qt.                                   |

**Señales (Eventos que emite)**

| Señal                      | Argumentos      | Descripción                                                              |
|----------------------------|-----------------|--------------------------------------------------------------------------|
| `symbol_selected`          | `str`           | Se emite cuando el usuario selecciona un nuevo símbolo.                    |
| `interval_selected`        | `str`           | Se emite cuando el usuario selecciona una nueva temporalidad.              |
| `candlestick_data_fetched` | `list[Kline]`   | Se emite cuando los datos de velas han sido obtenidos exitosamente.      |
| `api_error_occurred`       | `str`           | Se emite si ocurre un error durante la comunicación con la API.          |

**Slots / Métodos Públicos (Acciones que puede realizar)**

| Método              | Argumentos        | Devuelve | Descripción                                                              |
|---------------------|-------------------|----------|--------------------------------------------------------------------------|
| `load_chart_data`   | `None`            | `None`   | Inicia el proceso de carga asíncrona de los datos para el símbolo y temporalidad actuales. |
| `set_candlestick_data`| `data: list[Kline]`| `None`   | Establece los datos del gráfico y dispara una actualización visual.      |
| `start_updates`     | `None`            | `None`   | Inicia la carga inicial de datos.                                        |
| `stop_updates`      | `None`            | `None`   | Detiene cualquier proceso de actualización en curso (actualmente no implementado). |

#### **Estados Visuales**

1.  **Estado de Carga:**
    *   Muestra un texto "Cargando datos..." mientras el `ApiWorker` está obteniendo la información del mercado.

2.  **Estado de Datos Recibidos:**
    *   Renderiza el gráfico de `mplfinance` una vez que los datos están disponibles. El `QLabel` de carga es reemplazado por el `FigureCanvas`.

3.  **Estado de Error:**
    *   Si la llamada a la API falla o no se reciben datos, muestra un mensaje de error claro en el área del gráfico.

4.  **Estado Vacío:**
    *   Si no hay datos disponibles para el símbolo/temporalidad seleccionados, muestra el mensaje "No hay datos disponibles...".

#### **Uso Recomendado**
-   Como el widget central en una vista de "Terminal de Trading" o "Análisis de Mercado".
-   La gestión de hilos a través de `main_window.add_thread` es crucial para asegurar que los `ApiWorker` se gestionen correctamente y no queden hilos huérfanos.
