# Diagrama de Componentes (C4 - Nivel 3): API Server

## 1. Propósito y Alcance
Este diagrama muestra los componentes principales dentro del contenedor `API Server (ultibot_backend)`. Un "componente" es un grupo de código relacionado (ej. un módulo o un conjunto de clases) que cumple una función específica. El objetivo es entender cómo está estructurada internamente la lógica de negocio del backend.

## 2. Cómo Interpretar este Diagrama
- **Contenedor Externo:** Un contenedor con el que el `API Server` interactúa.
- **Componente:** Un bloque lógico dentro del `API Server`.
- **Flechas:** Indican las llamadas a funciones o el flujo de datos entre componentes.

## 3. Diagrama

```mermaid
graph TD
    subgraph "Contenedor: API Server (ultibot_backend)"
        direction TB

        rectangle "API Routers" as Routers [
            <b>API Routers</b>
            <br/>
            (FastAPI)
            <br/>
            <i>Expone los endpoints HTTP. Punto de entrada para la UI.</i>
        ]

        rectangle "Strategy Service" as StrategyService [
            <b>Strategy Service</b>
            <br/>
            <i>Gestiona la lógica de creación, análisis y ciclo de vida de las estrategias.</i>
        ]

        rectangle "Market Data Service" as MarketDataService [
            <b>Market Data Service</b>
            <br/>
            <i>Provee datos de mercado, interactuando con la caché y adaptadores externos.</i>
        ]

        rectangle "Order Execution Service" as OrderService [
            <b>Order Execution Service</b>
            <br/>
            <i>Maneja la creación y envío de órdenes al exchange.</i>
        ]
        
        rectangle "AI Orchestrator Service" as AIService [
            <b>AI Orchestrator Service</b>
            <br/>
            <i>Orquesta las solicitudes al modelo de IA para análisis.</i>
        ]

        rectangle "Persistence Service" as Persistence [
            <b>Persistence Service</b>
            <br/>
            (Adapter)
            <br/>
            <i>Abstrae el acceso a la base de datos (SQLite).</i>
        ]

        rectangle "External API Adapters" as Adapters [
            <b>External API Adapters</b>
            <br/>
            <i>Clientes para Binance, Mobula, Telegram, etc.</i>
        ]

        Routers --> StrategyService
        Routers --> MarketDataService
        Routers --> OrderService
        
        StrategyService -- "Usa" --> MarketDataService
        StrategyService -- "Usa" --> AIService
        StrategyService -- "Guarda/Carga" --> Persistence
        StrategyService -- "Ejecuta órdenes vía" --> OrderService

        MarketDataService -- "Usa" --> Adapters
        MarketDataService -- "Usa caché" --> Cache[(Cache<br/>Redis)]
        
        OrderService -- "Usa" --> Adapters
        AIService -- "Usa" --> Adapters
        
    end

    UI_App[UI Application] -- "API REST" --> Routers
    Persistence -- "SQL" --> DB[(Database<br/>SQLite)]
    
    style Routers fill:#0277bd,stroke:#333,stroke-width:2px,color:#fff
    style StrategyService fill:#0288d1,stroke:#333,stroke-width:2px,color:#fff
    style MarketDataService fill:#0288d1,stroke:#333,stroke-width:2px,color:#fff
    style OrderService fill:#0288d1,stroke:#333,stroke-width:2px,color:#fff
    style AIService fill:#0288d1,stroke:#333,stroke-width:2px,color:#fff
    style Persistence fill:#039be5,stroke:#333,stroke-width:2px,color:#fff
    style Adapters fill:#039be5,stroke:#333,stroke-width:2px,color:#fff
```

## 4. Observaciones y Análisis del Oráculo
- La arquitectura interna está bien estructurada alrededor de servicios con responsabilidades claras, siguiendo el **Principio de Responsabilidad Única (SRP)**.
- Los `API Routers` actúan como una fachada delgada, delegando la lógica de negocio a los servicios correspondientes.
- El `Strategy Service` es el componente central, orquestando a otros servicios para cumplir con sus funciones.
- El uso de `Adapters` (tanto para persistencia como para APIs externas) demuestra una buena aplicación del **Principio de Inversión de Dependencias (DIP)**, aislando la lógica de negocio de los detalles de implementación externos.

## 5. Siguientes Pasos Sugeridos
- Analizar el flujo de una transacción específica (ej. "crear una nueva estrategia") a través de estos componentes usando el **Protocolo de Rastreo de Flujo Transaccional (PRFT)**.
- Auditar los contratos de datos (modelos Pydantic) que se pasan entre estos componentes y a través de los `API Routers`.
