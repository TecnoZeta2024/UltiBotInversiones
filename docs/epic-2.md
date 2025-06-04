# Épica 2: Interfaz de Usuario (UI) Principal y Visualización de Datos

**Objetivo de la Épica:** Diseñar e implementar la interfaz de usuario principal (Dashboard) de "UltiBotInversiones" utilizando PyQt5, permitiendo la visualización de datos de mercado en tiempo real, gráficos financieros, el estado del portafolio (paper y real limitado), y un sistema de notificaciones integrado.

## Historias de Usuario Propuestas para la Épica 2:

### Historia 2.1: Diseño e Implementación del Layout Principal del Dashboard (PyQt5)
Como usuario de UltiBotInversiones,
quiero un layout de dashboard principal claro, profesional y con tema oscuro (implementado con PyQt5 y QDarkStyleSheet), que defina áreas designadas para diferentes tipos de información como mercado, portafolio, gráficos y notificaciones,
para tener una vista organizada desde la cual pueda acceder fácilmente a todas las funciones clave del sistema.

##### Criterios de Aceptación:
*   AC1 (Ventana Principal Establecida): Al iniciar "UltiBotInversiones", el sistema debe presentar una ventana principal de aplicación, desarrollada utilizando el framework PyQt5.
*   AC2 (Aplicación Consistente de Tema Oscuro Profesional): La totalidad de la interfaz de usuario debe aplicar de manera consistente un tema oscuro de calidad profesional.
*   AC3 (Definición Clara de Áreas Funcionales): El layout principal del dashboard debe estar visiblemente estructurado con secciones para "Resumen de Datos de Mercado", "Estado del Portafolio", "Visualización de Gráficos Financieros", y "Centro de Notificaciones del Sistema".
*   AC4 (Flexibilidad de Paneles: Acoplables/Redimensionables): Los paneles deben ser redimensionables. Se buscará que sean acoplables/desacoplables.
*   AC5 (Adaptabilidad del Layout al Tamaño de la Ventana): El layout debe ajustarse fluidamente al redimensionar la ventana principal.
*   AC6 (Elementos Estructurales Básicos): El layout debe contemplar una barra de menú (opcional) y/o una barra de estado.

### Historia 2.2: Visualización de Datos de Mercado de Binance en Tiempo Real en el Dashboard
Como usuario de UltiBotInversiones,
quiero ver en el dashboard los datos de mercado en tiempo real (precio actual, cambio 24h, volumen 24h) para una lista configurable de mis pares de criptomonedas favoritos en Binance,
para poder monitorear rápidamente el estado del mercado.

##### Criterios de Aceptación:
*   AC1 (Configuración de Lista de Pares de Seguimiento): El sistema debe permitir al usuario buscar, seleccionar y guardar una lista de pares de Binance a monitorear, persistiendo la selección.
*   AC2 (Presentación Clara de Pares en el Dashboard): Los pares seleccionados deben mostrarse en un formato tabular o de lista ordenado y fácil de leer.
*   AC3 (Información Esencial por Par): Para cada par, mostrar: Símbolo, Último Precio, Cambio % 24h, Volumen 24h.
*   AC4 (Actualización Dinámica de Datos): La información debe actualizarse dinámicamente (WebSockets para precio si es factible, API REST para otros datos con frecuencia configurable).
*   AC5 (Legibilidad y Diseño Visual): Presentación clara, concisa, con tema oscuro consistente. Indicadores visuales sutiles para movimientos de precio.
*   AC6 (Manejo de Errores en la Obtención de Datos de Mercado): Si no se puede obtener información para un par, indicarlo de forma no intrusiva sin interrumpir los demás.

### Historia 2.3: Visualización de Gráficos Financieros Esenciales (mplfinance)
Como usuario de UltiBotInversiones,
quiero poder seleccionar un par de mi lista de seguimiento y ver un gráfico financiero básico (velas japonesas, volumen) con diferentes temporalidades (ej. 1m, 5m, 15m, 1H, 4H, 1D),
para realizar un análisis técnico visual rápido.

##### Criterios de Aceptación:
*   AC1 (Selección del Par a Graficar desde el Dashboard): El usuario debe poder seleccionar un par de su lista de seguimiento para mostrar su gráfico.
*   AC2 (Presentación del Gráfico de Velas Japonesas y Volumen): Renderizar gráfico con mplfinance, incluyendo velas (OHLC) y subgráfico de volumen.
*   AC3 (Funcionalidad de Selección de Temporalidad): Controles para cambiar la temporalidad del gráfico (mínimo: 1m, 5m, 15m, 1H, 4H, 1D).
*   AC4 (Carga y Visualización de Datos Históricos del Gráfico): Obtener datos históricos OHLCV de Binance y mostrar una cantidad razonable de periodos.
*   AC5 (Actualización Dinámica del Gráfico con Nuevos Datos): El gráfico debe actualizarse dinámicamente con nuevas velas.
*   AC6 (Claridad, Legibilidad y Usabilidad Básica del Gráfico): Gráfico claro, legible, integrado con tema oscuro. Deseable zoom y paneo.
*   AC7 (Manejo de Errores en la Carga de Datos del Gráfico): Si hay errores, mostrar un mensaje informativo en lugar de un gráfico vacío/corrupto.

### Historia 2.4: Visualización del Estado del Portafolio (Paper y Real Limitado)
Como usuario de UltiBotInversiones,
quiero ver en el dashboard un resumen claro del estado de mi portafolio, diferenciando entre el saldo de paper trading y mi saldo real en Binance (enfocado en USDT), así como el valor total estimado de mis activos,
para conocer mi situación financiera actual dentro de la plataforma.

##### Criterios de Aceptación:
*   AC1 (Visualización del Saldo Real de Binance): Mostrar prominentemente el saldo actual de USDT disponible en la cuenta real de Binance.
*   AC2 (Visualización del Saldo del Modo Paper Trading): Mostrar el saldo actual del capital virtual asignado al modo Paper Trading, ajustable por ganancias/pérdidas simuladas.
*   AC3 (Diferenciación Visual Clara entre Modos): Diferenciar inequívocamente la información de Paper Trading y Real de Binance.
*   AC4 (Listado y Valoración de Activos en Paper Trading): Mostrar lista de activos "poseídos" en Paper Trading, con cantidad y valor estimado.
*   AC5 (Listado y Valoración de Activos Reales - v1.0): Mostrar cantidad y valor de mercado de criptoactivos reales adquiridos (hasta 5 operaciones v1.0).
*   AC6 (Cálculo y Presentación del Valor Total Estimado del Portafolio): Calcular y mostrar valor total estimado para Paper Trading y Portafolio Real.
*   AC7 (Actualización Dinámica de la Información del Portafolio): Toda la información del portafolio debe actualizarse dinámicamente.
*   AC8 (Manejo de Errores en la Valoración del Portafolio): Si hay problemas para obtener precios, indicarlo claramente para el activo afectado.

### Historia 2.5: Presentación Integrada de Notificaciones del Sistema en la UI
Como usuario de UltiBotInversiones,
quiero ver las notificaciones importantes generadas por el sistema (alertas de trading, confirmaciones, errores de conexión, etc.) directamente en un área designada de la interfaz de usuario,
para estar informado de los eventos relevantes sin depender exclusivamente de Telegram y tener un registro centralizado en la aplicación.

##### Criterios de Aceptación:
*   AC1 (Panel de Notificaciones Designado en la UI): Un panel específico y accesible para mostrar notificaciones del sistema.
*   AC2 (Recepción y Visualización de Notificaciones del Sistema): Todas las notificaciones importantes deben mostrarse en este panel.
*   AC3 (Clasificación Visual de Notificaciones por Severidad/Tipo): Indicar visualmente severidad/tipo (Información, Éxito, Advertencia, Error) con iconos, colores o etiquetas.
*   AC4 (Información Clara y Concisa en Cada Notificación): Mensaje claro, conciso, fácil de entender, con marca de tiempo.
*   AC5 (Acceso a un Historial Reciente de Notificaciones): Permitir visualizar un historial de notificaciones recientes (ej. últimas 20-50).
*   AC6 (Gestión de Notificaciones por el Usuario): Opción para descartar notificaciones individuales o marcar todas como leídas.
*   AC7 (Actualización en Tiempo Real del Panel de Notificaciones): Nuevas notificaciones deben aparecer en tiempo real o con mínimo retraso.
