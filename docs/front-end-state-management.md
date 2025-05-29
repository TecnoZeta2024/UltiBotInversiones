# Gestión de Estado en el Front-End (PyQt5)

Este documento describe la estrategia y los patrones para la gestión del estado de la aplicación dentro de la interfaz de usuario (UI) de "UltiBotInversiones", desarrollada con PyQt5. Una gestión de estado eficaz es crucial para mantener la UI consistente, responsiva y fácil de mantener.

## 1. Principios Generales

-   **Fuente Única de Verdad (Single Source of Truth - SSOT):** Para datos críticos de la aplicación (ej. estado del portafolio, configuración del usuario, estado de las estrategias), se intentará mantener una fuente única de verdad. Idealmente, el backend es la fuente autoritativa, y la UI refleja este estado.
-   **Flujo de Datos Unidireccional (Preferido):** Siempre que sea posible, se favorecerá un flujo de datos unidireccional: las acciones del usuario en la UI desencadenan llamadas a la API del backend, el backend procesa la lógica y actualiza su estado, y luego la UI se actualiza para reflejar el nuevo estado (ya sea mediante una nueva solicitud GET o a través de notificaciones/WebSockets).
-   **Estado Local de la UI:** Los widgets individuales y las vistas pueden mantener su propio estado local para aspectos puramente de presentación que no necesitan ser compartidos globalmente (ej. estado de un botón, texto en un campo de entrada antes de ser enviado).

## 2. Estrategias de Gestión de Estado

Dada la naturaleza de una aplicación de escritorio con PyQt5 y un backend FastAPI, se pueden combinar varias estrategias:

### 2.1. Estado Gestionado por el Backend y Sincronización API

-   **Descripción:** La mayoría del estado de la aplicación (configuración del usuario, credenciales, estado del portafolio, historial de trades, configuraciones de estrategias) reside en el backend y se persiste en la base de datos. La UI obtiene y actualiza este estado a través de llamadas a la API interna.
-   **Mecanismo:**
    -   La UI realiza solicitudes GET para obtener el estado actual cuando una vista se carga o necesita refrescarse.
    -   Las acciones del usuario que modifican el estado (ej. guardar configuración, activar una estrategia) resultan en solicitudes POST/PUT/PATCH/DELETE al backend.
    -   El backend valida y procesa la solicitud, actualiza la base de datos y devuelve una respuesta.
    -   La UI actualiza su visualización basándose en la respuesta o re-solicitando los datos.
-   **Pros:**
    -   Consistencia de datos centralizada en el backend.
    -   Lógica de negocio compleja permanece en el backend.
-   **Contras:**
    -   Puede requerir múltiples llamadas API para mantener la UI sincronizada si no se usan mecanismos de actualización en tiempo real.

### 2.2. Señales y Slots de Qt para Comunicación entre Componentes de UI

-   **Descripción:** El mecanismo incorporado de señales y slots de Qt se utilizará extensivamente para la comunicación y la propagación de cambios de estado entre diferentes componentes de la UI (widgets, vistas).
-   **Mecanismo:**
    -   Un componente emite una señal cuando su estado cambia o ocurre un evento relevante.
    -   Otros componentes interesados se conectan (slots) a estas señales para reaccionar y actualizar su propio estado o visualización.
    -   Ejemplo: `SidebarNavigationWidget` emite `view_selected_signal`, `MainWindow` tiene un slot que cambia la vista en `QStackedWidget`. Un `ApiWorker` (QThread) emite `result_ready` o `error_occurred`.
-   **Pros:**
    -   Mecanismo nativo de Qt, bien integrado y eficiente.
    -   Permite una comunicación desacoplada entre componentes.
-   **Contras:**
    -   Para estados globales complejos, puede llevar a una red intrincada de conexiones de señales/slots ("callback hell" si no se gestiona bien).

### 2.3. Modelos de Datos de Qt (QAbstractItemModel y subclases)

-   **Descripción:** Para widgets que muestran colecciones de datos (ej. `QTableView`, `QListView`, `QTreeView`), se utilizarán los modelos de datos de Qt (`QAbstractListModel`, `QAbstractTableModel`).
-   **Mecanismo:**
    -   Se crea una subclase del modelo apropiado que encapsula los datos y la lógica para acceder a ellos y modificarlos.
    -   La vista (ej. `QTableView`) se conecta al modelo.
    -   Cuando los datos en el modelo cambian, el modelo emite señales (`dataChanged`, `rowsInserted`, etc.) y la vista se actualiza automáticamente.
    -   Los datos para el modelo pueden provenir de una caché local o ser actualizados desde el backend.
-   **Pros:**
    -   Separación clara de datos y presentación.
    -   Actualizaciones eficientes de la vista.
    -   Manejo integrado de selección, ordenación, filtrado (con proxies como `QSortFilterProxyModel`).
-   **Contras:**
    -   Puede ser verboso de implementar para estructuras de datos simples.

### 2.4. Gestores de Estado o Servicios Singleton (Opcional, para estado global complejo)

-   **Descripción:** Si ciertos estados necesitan ser accesibles o modificados por múltiples componentes no directamente relacionados en la jerarquía de widgets, se podría considerar un objeto singleton o una clase de servicio dedicada a gestionar ese estado específico.
-   **Mecanismo:**
    -   Se crea una clase (ej. `PortfolioStateService`, `UserPreferencesService`) que mantiene el estado y ofrece métodos para accederlo y modificarlo.
    -   Esta clase puede usar señales de Qt para notificar a los componentes de la UI sobre los cambios de estado.
    -   Los componentes de la UI obtienen una instancia de este servicio (posiblemente a través de inyección de dependencias simple o un acceso global controlado) para leer el estado o invocar cambios.
-   **Ejemplo de Estado Global Potencial:**
    -   Estado de conexión a servicios externos (Binance, Telegram).
    -   Preferencias del usuario cargadas al inicio.
    -   El modo actual de operación (Paper/Real).
-   **Pros:**
    -   Centraliza la gestión de estado global específico.
    -   Reduce el acoplamiento directo entre componentes distantes.
-   **Contras:**
    -   Debe usarse con moderación para evitar convertirlo en un "god object" o un anti-patrón de estado global masivo.

## 3. Estrategia para UltiBotInversiones v1.0

Para la v1.0, se adoptará un enfoque pragmático combinando:

1.  **Backend como Fuente de Verdad Principal:** La mayoría de los datos persistentes y la lógica de negocio residirán en el backend. La UI consultará y actualizará estos datos vía API.
2.  **Señales y Slots para Comunicación Interna de la UI:** Será el pilar para la comunicación entre widgets y la respuesta a eventos.
3.  **Modelos de Datos de Qt para Vistas de Colección:** Se usarán para `QTableView` (ej. historial de trades, lista de seguimiento, desglose de portafolio) para una presentación eficiente.
4.  **Estado Local en Widgets:** Para propiedades de UI puramente visuales o temporales.
5.  **Gestores de Estado Singleton Mínimos:** Se considerarán para estados muy globales y transversales si es estrictamente necesario, como:
    -   `AppModeManager`: Para conocer el modo actual (Paper/Real) y notificar cambios.
    -   `ConnectionStatusService`: Para rastrear y notificar el estado de conexión a Binance, Telegram, etc.

## 4. Actualizaciones en Tiempo Real

-   **WebSockets:** Si el backend expone endpoints WebSocket para actualizaciones en tiempo real (ej. precios de mercado, notificaciones de ejecución de trades), la UI deberá establecer y gestionar estas conexiones. Las bibliotecas como `QtWebSockets` o la integración de `websockets` (del stack) con el bucle de eventos de Qt serán necesarias.
-   **Polling (Alternativa):** Si los WebSockets no están disponibles para todas las actualizaciones en tiempo real necesarias, se podría recurrir a un polling periódico a ciertos endpoints API, pero esto es menos eficiente y debe usarse con precaución.

## 5. Ejemplo de Flujo de Estado (Guardar Configuración)

1.  **UI:** Usuario modifica un campo en `SettingsView`.
2.  **UI (`SettingsView`):** Al hacer clic en "Guardar", se recopilan los datos del formulario.
3.  **UI (Capa API):** Se crea un `ApiWorker` (QThread) para enviar una solicitud `PATCH /api/v1/config/` al backend con los datos modificados.
4.  **Backend:** FastAPI recibe la solicitud, valida los datos con Pydantic, actualiza la configuración en la base de datos.
5.  **Backend:** Devuelve una respuesta `200 OK` con la configuración actualizada (o solo éxito).
6.  **UI (`ApiWorker`):** Emite `result_ready` con la respuesta.
7.  **UI (`SettingsView`):** El slot conectado a `result_ready` actualiza cualquier visualización local si es necesario y muestra un mensaje de éxito al usuario.
8.  **UI (Opcional, si es estado global):** Si la configuración guardada afecta a otras partes de la UI (ej. cambio de tema), `SettingsView` o un servicio de configuración podría emitir una señal global (ej. `config_updated_signal`) que otros widgets escuchan para actualizarse.

Esta estrategia busca un equilibrio entre la simplicidad para la v1.0 y la robustez necesaria para una aplicación como UltiBotInversiones. Se revisará y refinará a medida que la aplicación evolucione.
