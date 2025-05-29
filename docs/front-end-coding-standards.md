# Estándares de Codificación de Front-End (PyQt5)

Este documento establece los estándares de codificación específicos para el desarrollo de la interfaz de usuario (UI) de UltiBotInversiones, que se implementará con PyQt5. Estos estándares complementan las directrices generales de Python definidas en `docs/Architecture.md` (sección "Coding Standards").

## 1. Referencia a Estándares Generales

Todos los estándares de codificación de Python definidos en `docs/Architecture.md` (incluyendo el uso de `Ruff` para linting y formateo, convenciones de nomenclatura, manejo de type hints, docstrings estilo Google, etc.) aplican también al código del frontend. Esta sección se enfoca en convenciones adicionales o específicas para PyQt5.

## 2. Nomenclatura Específica de PyQt5

-   **Nombres de Clases de Widgets:**
    -   Seguirán `PascalCase` como las clases de Python (ej. `MainWindow`, `PortfolioViewWidget`).
    -   Si un widget personalizado hereda de un widget Qt específico, es útil (pero no obligatorio) incluir el tipo base en el nombre si aporta claridad (ej. `OrderFormDialog(QDialog)`).
-   **Nombres de Instancias de Widgets (Variables):**
    -   Utilizar `snake_case` seguido de un sufijo que indique el tipo de widget de forma abreviada y consistente. Esto mejora la legibilidad al revisar el código de la UI.
    -   Ejemplos de sufijos comunes:
        -   `QPushButton`: `_btn` (ej. `submit_order_btn`)
        -   `QLabel`: `_lbl` (ej. `status_message_lbl`)
        -   `QLineEdit`: `_le` (ej. `api_key_le`)
        -   `QComboBox`: `_combo` (ej. `pair_selector_combo`)
        -   `QTableView` / `QTableWidget`: `_tbl` (ej. `trades_history_tbl`)
        -   `QListWidget`: `_lw` (ej. `notifications_lw`)
        -   `QCheckBox`: `_chk` (ej. `enable_paper_mode_chk`)
        -   `QRadioButton`: `_rb` (ej. `theme_dark_rb`)
        -   `QGroupBox`: `_gb` (ej. `market_data_gb`)
        -   `QTabWidget`: `_tab_widget` (ej. `main_view_tab_widget`)
        -   `QMainWindow`: `_main_window` (o `_window`)
        -   `QDialog`: `_dialog`
        -   Layouts (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`): `_layout` (ej. `main_v_layout`, `buttons_h_layout`)
    -   Ejemplo de uso: `self.confirm_button_btn = QPushButton("Confirmar")`
-   **Nombres de Slots (Métodos Conectados a Señales):**
    -   Utilizar `snake_case`.
    -   El nombre debe ser descriptivo de la acción que realiza o del evento que maneja.
    -   Es una buena práctica prefijarlos con `on_` seguido del nombre del widget y la señal (si es específico), o una descripción de la acción.
    -   Ejemplos:
        -   `def on_submit_button_btn_clicked(self): ...`
        -   `def handle_portfolio_update_signal(self, portfolio_data): ...`
        -   `def update_market_data_display(self): ...`
-   **Nombres de Señales Personalizadas:**
    -   Utilizar `camelCase` (convención común en Qt/C++ de donde provienen las señales/slots) o `snake_case` si se prefiere mantener consistencia con el resto de Python. **Para este proyecto, se optará por `snake_case` para las señales personalizadas para mantener la coherencia con el código Python general.**
    -   El nombre debe ser descriptivo del evento que la señal representa.
    -   Ejemplo: `portfolio_updated_signal = pyqtSignal(dict)`

## 3. Estructura de Archivos y Clases de UI

-   **Separación de Lógica y Presentación:**
    -   Evitar incluir lógica de negocio compleja directamente en las clases de los widgets.
    -   La lógica de la UI (manejo de eventos, actualización de widgets) debe estar en las clases de los widgets.
    -   La lógica de negocio o la interacción con el backend debe delegarse a clases de servicio o controladores separados, si la complejidad lo justifica, o manejarse a través de la capa de interacción API (ver `docs/front-end-api-interaction.md`).
-   **Archivos `.ui` (Qt Designer):**
    -   Si se utiliza Qt Designer para diseñar layouts, los archivos `.ui` deben almacenarse en un subdirectorio `ui/` dentro del directorio del widget o ventana correspondiente (ej. `src/ultibot_ui/windows/main_window/main_window.ui`).
    -   Las clases Python que cargan estos archivos `.ui` (usando `uic.loadUi()`) deben estar claramente asociadas.
-   **Clases de Widgets Personalizados:**
    -   Cada widget personalizado complejo debe residir en su propio archivo Python.
    -   Si un widget es muy simple y solo se usa en un contexto, puede definirse en el mismo archivo que su contenedor.

## 4. Uso de Señales y Slots

-   Es el mecanismo fundamental para la comunicación entre objetos en PyQt5.
-   **Conexiones:**
    -   Realizar las conexiones de señales a slots en el método `__init__` de la clase o en un método dedicado a la configuración de la UI (ej. `_init_ui` o `_connect_signals`).
    -   Preferir el nuevo estilo de conexión de señales: `widget.signal_name.connect(self.slot_name)`.
-   **Señales Personalizadas:**
    -   Definir señales personalizadas (`pyqtSignal`) en las clases para comunicar eventos o cambios de estado a otros componentes de forma desacoplada.

## 5. Gestión de Layouts

-   Utilizar los gestores de layout de Qt (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, `QFormLayout`, `QStackedLayout`) para organizar los widgets.
-   Evitar el posicionamiento absoluto de widgets (`widget.move(x, y)`) a menos que sea estrictamente necesario para un efecto muy específico, ya que dificulta la responsividad y el mantenimiento.
-   Utilizar `QSizePolicy` y `stretch factors` en los layouts para controlar cómo los widgets se redimensionan y ocupan el espacio.

## 6. Estilo y Tema

-   Como se define en `docs/Front-end-spec.md` y `docs/front-end-style-guide.md`, se utilizará un tema oscuro (ej. QDarkStyleSheet).
-   Evitar aplicar estilos directamente en el código Python mediante `widget.setStyleSheet("...")` para propiedades individuales si estas pueden ser cubiertas por la hoja de estilo global.
-   Si se necesitan estilos específicos para un widget personalizado que no pueden ser manejados por la hoja de estilo global, encapsularlos dentro de la clase del widget.

## 7. Internacionalización (i18n) y Localización (l10n)

-   Para la v1.0, el idioma principal es el español.
-   Todo el texto visible para el usuario en la UI (etiquetas, botones, mensajes) debe ser fácilmente extraíble para una futura internacionalización.
-   Considerar el uso de `QCoreApplication.translate()` o `self.tr()` (si la clase hereda de `QObject`) para marcar cadenas traducibles, aunque la implementación completa de i18n puede ser post-v1.0.
    ```python
    # Ejemplo
    # self.my_button_btn.setText(self.tr("Confirmar"))
    ```

## 8. Comentarios y Documentación Específicos de UI

-   Además de los docstrings para clases y métodos, añadir comentarios para explicar lógica compleja de la UI, manejo de eventos particular, o el propósito de ciertos widgets si no es obvio por su nombre.
-   Si se usan archivos `.ui`, asegurarse de que los nombres de los objetos en Qt Designer sean descriptivos.

## 9. Manejo de Recursos

-   Los recursos como iconos, imágenes, etc., deben gestionarse utilizando el sistema de recursos de Qt (`.qrc` files) si la cantidad de recursos crece.
-   Para la v1.0, pueden almacenarse en un directorio `assets/` (como se define en `docs/Architecture.md` sección "Project Structure") y cargarse directamente, pero se debe planificar la migración a `.qrc` si es necesario.

## 10. Consideraciones de Rendimiento en la UI

-   Evitar operaciones de larga duración en el hilo principal de la UI. Utilizar `QThread` o la integración `asyncio` (ver `docs/front-end-api-interaction.md`) para tareas en segundo plano (ej. llamadas API, cálculos complejos).
-   Optimizar la actualización de widgets. Si se actualizan grandes cantidades de datos (ej. en una tabla), considerar el uso de modelos de datos (`QAbstractTableModel`) que solo actualicen las celdas modificadas.
-   Ser consciente del número de widgets creados. Demasiados widgets pueden impactar el rendimiento.

Siguiendo estos estándares específicos para PyQt5, junto con los estándares generales de Python, se busca crear un frontend robusto, mantenible y de alta calidad para UltiBotInversiones.
