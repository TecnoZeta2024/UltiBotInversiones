# Arquitectura Frontend - UltiBot Inversiones Web

Este documento describe la arquitectura de alto nivel para la nueva interfaz de usuario web de UltiBot Inversiones, construida con React, Zustand y Magic UI.

## 1. Estructura de Directorios

La estructura de directorios está diseñada para ser modular, escalable y fácil de navegar.

```
src/ultibot_frontend/
├── components/
│   ├── base/         # Componentes atómicos y reutilizables (Button, Input, Card)
│   └── shared/       # Componentes complejos compuestos (organisms) (StrategyForm, MarketChart)
├── hooks/            # Hooks personalizados de React (useWebSocket, useApi)
├── lib/              # Funciones de utilidad, clientes de API y lógica no relacionada con React
├── store/            # Slices y configuración del store de Zustand
├── views/            # Componentes de página completa que corresponden a rutas (Dashboard, Portfolio)
└── App.tsx           # Componente raíz de la aplicación y configuración de rutas
```

### Convenciones de Nombrado

-   **Componentes:** `PascalCase` (ej. `MarketChart.tsx`).
-   **Hooks:** `camelCase` con el prefijo `use` (ej. `useMarketData.ts`).
-   **Archivos de Estilo:** (Si se usan) `kebab-case` (ej. `market-chart.css`).

## 2. Flujo de Datos y Gestión de Estado

### 2.1. Flujo de Datos en Tiempo Real

El sistema utilizará **WebSockets** para la comunicación en tiempo real desde el backend.

1.  **Conexión:** Un hook `useWebSocket` establecerá y gestionará la conexión WebSocket al iniciar la aplicación.
2.  **Recepción de Datos:** El hook recibirá mensajes del backend (ej. actualizaciones de precios, ejecución de órdenes).
3.  **Actualización de Estado:** Al recibir un mensaje, el hook `useWebSocket` invocará la acción correspondiente en el store de Zustand para actualizar el estado global. Por ejemplo, un nuevo precio de un activo llamará a una acción en `marketDataSlice`.

### 2.2. Gestión de Estado con Zustand

Zustand se utilizará para la gestión de estado global por su simplicidad y rendimiento. El store se dividirá en "slices" lógicos para mantener la organización.

#### Slices de Zustand (`src/ultibot_frontend/store/`)

-   **`marketDataSlice.ts`**:
    -   **Responsabilidad:** Gestionar los datos de mercado en tiempo real, como precios de activos, tickers y datos históricos para gráficos.
    -   **Estado:** `{ prices: {}, historicalData: {} }`
    -   **Acciones:** `updatePrice()`, `setHistoricalData()`

-   **`ordersSlice.ts`**:
    -   **Responsabilidad:** Mantener el estado de las órdenes de trading (activas, ejecutadas, canceladas).
    -   **Estado:** `{ activeOrders: [], orderHistory: [] }`
    -   **Acciones:** `addOrder()`, `updateOrderStatus()`

-   **`opportunitiesSlice.ts`**:
    -   **Responsabilidad:** Almacenar y gestionar las oportunidades de trading identificadas por el backend.
    -   **Estado:** `{ opportunities: [] }`
    -   **Acciones:** `setOpportunities()`, `addOpportunity()`

-   **`userInterfaceSlice.ts`**:
    -   **Responsabilidad:** Gestionar el estado de la UI, como la visibilidad de modales, notificaciones, tema actual (claro/oscuro) y estado de carga global.
    -   **Estado:** `{ isLoading: false, notifications: [], activeModal: null }`
    -   **Acciones:** `setLoading()`, `showNotification()`, `openModal()`
