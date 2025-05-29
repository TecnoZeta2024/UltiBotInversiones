# Guía de Estilo de Front-End y Branding para UltiBotInversiones

Este documento define la guía de estilo visual y los elementos de branding que se utilizarán en la interfaz de usuario (UI) de "UltiBotInversiones". El objetivo es asegurar una experiencia de usuario coherente, profesional y estéticamente agradable, alineada con los principios de diseño del proyecto.

## 1. Paleta de Colores (Color Palette)

-   **Tema Principal:** Oscuro.
    -   **Fondos Principales:**
        -   `#252526` (Gris oscuro profundo para el fondo más general).
        -   `#1E1E1E` (Gris aún más oscuro para áreas secundarias/contenedores).
        -   `#2D2D2D` (Gris oscuro ligeramente más claro para barras laterales, cabeceras, modales).
    -   **Texto Principal y Secundario:**
        -   `#E0E0E0` (Blanco hueso/Gris muy claro para texto principal).
        -   `#A0A0A0` (Gris medio para texto secundario/etiquetas).
-   **Color Primario/Acento Principal (Azul Oscuro Tecnológico):**
    -   Optaremos por: `#0D6EFD` (Un azul moderno y enérgico que ofrecerá buen contraste y es ampliamente reconocido por su claridad).
-   **Colores de Feedback/Semántica:**
    -   **Éxito:** `#28A745` (Verde).
    -   **Error/Alerta Crítica:** `#DC3545` (Rojo).
    -   **Advertencia:** `#FFC107` (Amarillo ámbar).
    -   **Información:** `#0DCAF0` (Un cian claro y limpio, que complementa bien el azul de acento principal).
-   **Colores para Gráficos:**
    -   Líneas/Velas Ascendentes: `#28A745` (Éxito) o una variante más clara del acento como `#589BFF`.
    -   Líneas/Velas Descendentes: `#DC3545` (Error) o un naranja como `#FD7E14`.
    -   Indicadores (Medias Móviles, etc.): Se utilizará una paleta secundaria que contraste bien, como: `#6F42C1` (Violeta), `#20C997` (Turquesa), `#E83E8C` (Magenta Rosado).
-   **Bordes y Separadores:**
    -   `#444444` (Un gris medio oscuro para sutiles separaciones).

## 2. Tipografía (Typography)

-   **Familia Principal:** Optaremos por una fuente Sans-Serif moderna, limpia y altamente legible, ideal para interfaces de usuario y visualización de datos.
    -   **Sugerencia:** "Roboto" o "Open Sans". Estas fuentes son estándar, ofrecen una amplia variedad de pesos y están diseñadas para la legibilidad en pantalla. Para PyQt5, aseguraríamos que la fuente seleccionada esté disponible o se empaquete con la aplicación. Si no, nos basaremos en fuentes Sans-Serif genéricas de alta calidad que Qt pueda renderizar bien (como "Noto Sans" o "DejaVu Sans" que suelen estar disponibles en muchos sistemas).
    -   **Fallback:** `Arial`, `Helvetica`, `sans-serif`.
-   **Tamaños y Pesos:**
    -   **Títulos Principales (H1):** 24px - Peso: Bold (700)
    -   **Subtítulos (H2):** 20px - Peso: Semibold (600)
    -   **Títulos de Sección (H3):** 18px - Peso: Medium (500)
    -   **Texto del Cuerpo Principal:** 14px - Peso: Regular (400)
    -   **Texto Secundario/Etiquetas:** 12px - Peso: Regular (400)
    -   **Botones:** 14px - Peso: Medium (500)
    -   _(Los tamaños en `px` son una referencia para el diseño; PyQt5 maneja los tamaños de fuente de manera que puede ser ligeramente diferente, pero la jerarquía y pesos relativos son la clave)._

## 3. Iconografía (Iconography)

-   **Estilo:** Iconos limpios, modernos y fácilmente reconocibles, consistentes con el tema oscuro. Se preferirán iconos de estilo "outline" o "filled" sutiles.
-   **Biblioteca Sugerida:**
    -   **FontAwesome:** Es una biblioteca muy completa y ampliamente utilizada. Existen integraciones o formas de usar sus iconos en aplicaciones Qt.
    -   **Material Design Icons:** Otra excelente opción, con una gran variedad y un estilo que se adapta bien.
    -   **SVG Personalizados:** Para iconos muy específicos, se pueden crear SVGs. PyQt5 tiene buen soporte para SVG.
-   **Uso:** Los iconos se usarán para mejorar la comprensión visual en botones, elementos de navegación, indicadores de estado y junto a etiquetas informativas. Deben tener un color que contraste bien con el fondo, usualmente el color del texto o el color de acento para acciones.
-   **Iconos Específicos (Ejemplos de la Barra Lateral):**
    -   Dashboard: Un icono que represente un panel de control o vista general (ej. un gráfico de barras, un velocímetro).
    -   Oportunidades: Un icono que sugiera descubrimiento o ideas (ej. una bombilla, una lupa).
    -   Estrategias: Un icono que represente planificación o reglas (ej. un diagrama de flujo, un engranaje).
    -   Historial: Un icono que indique tiempo o registros pasados (ej. un reloj, un libro abierto).
    -   Configuración: Un icono universal de ajustes (ej. un engranaje, una llave inglesa).

## 4. Espaciado y Cuadrícula (Spacing & Grid)

-   **Unidad Base de Espaciado:** Se recomienda un sistema de espaciado basado en múltiplos de una unidad base (ej. 8px). Esto significa que los márgenes, paddings y el espacio entre elementos serían 8px, 16px, 24px, 32px, etc. Esto ayuda a mantener la consistencia visual.
-   **Cuadrícula (Grid):** Aunque una cuadrícula estricta de 12 columnas como en la web puede no aplicarse directamente de la misma manera en PyQt5, el principio de alinear elementos de forma coherente y mantener un ritmo visual es importante.
    -   Los layouts se diseñarán con una alineación lógica y consistente.
    -   Se utilizarán `QSplitter` y layouts de Qt (`QVBoxLayout`, `QHBoxLayout`, `QGridLayout`) para organizar los elementos de manera flexible y adaptable.
-   **Márgenes y Paddings Generales:**
    -   Contenedores principales: Padding generoso (ej. 16px o 24px).
    -   Espacio entre elementos agrupados: Espacio moderado (ej. 8px o 12px).
    -   Espacio entre texto y borde de botón: Consistente (ej. 8px vertical, 12px horizontal).

## 5. Aplicación del Estilo

-   Se utilizará una hoja de estilo global (ej. `qdarkstyle.qss` o una personalizada basada en ella) para aplicar el tema oscuro y los estilos base a la aplicación.
-   Los estilos específicos de componentes que no puedan ser cubiertos por la hoja de estilo global se definirán dentro de los propios componentes personalizados, pero siempre buscando la coherencia con esta guía.
-   Se debe hacer referencia a esta guía al desarrollar nuevos componentes o vistas para asegurar la consistencia visual en toda la aplicación.
