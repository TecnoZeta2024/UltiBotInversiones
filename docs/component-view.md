## Architectural / Design Patterns Adopted

A continuación, se listan los patrones arquitectónicos y de diseño fundamentales que se adoptarán para "UltiBotInversiones":

* **Monolito Modular (Modular Monolith):**
    * _Rationale/Referencia:_ Es el estilo arquitectónico principal para la v1.0, como se decidió en el PRD. Favorece la velocidad de desarrollo inicial para el MVP, manteniendo una clara separación de responsabilidades a través de módulos bien definidos (ej. UI, núcleo de trading, gestión de datos, servicios de IA, notificaciones). Esta modularidad interna facilitará una posible evolución futura.

* **Monorepo:**
    * _Rationale/Referencia:_ La estructura del repositorio será un Monorepo, según la decisión del PRD para la v1.0. Esto simplificará la gestión de dependencias, la configuración del entorno de desarrollo y los procesos de CI/CD iniciales, además de facilitar la coherencia y refactorización en las primeras etapas.

* **Agente-Herramientas (Agent-Tool) con LangChain (Python):**
    * _Rationale/Referencia:_ Para la interacción con la IA (Gemini), se utilizará el patrón Agente-Herramientas facilitado por LangChain (Python). El agente (impulsado por Gemini) podrá decidir dinámicamente qué "herramienta" (wrappers para APIs de Binance, Servidores MCP, Mobula API, etc.) utilizar para recopilar información o ejecutar acciones, permitiendo un análisis y toma de decisiones más flexibles y potentes.

* **Procesamiento Asíncrono:**
    * _Rationale/Referencia:_ Se empleará extensivamente el procesamiento asíncrono (`async/await` en Python con bibliotecas como `httpx`, `websockets`, y las `BackgroundTasks` de FastAPI) para cumplir con el requisito de baja latencia (<500ms) y para manejar operaciones de I/O intensivas (llamadas a APIs externas, streams de datos) y tareas de larga duración (análisis de IA) sin bloquear el flujo principal de la aplicación.

* **Diseño Orientado al Dominio (Domain-Driven Design - DDD) - (Principio Guía):**
    * _Rationale/Referencia:_ El PRD valora los principios de DDD. Si bien no es un patrón estructural per se para el monolito, DDD guiará el diseño de los módulos internos, el modelado de entidades y la lógica de negocio, buscando alinear el software estrechamente con el dominio del trading y las inversiones para gestionar la complejidad.

* **Arquitectura Orientada a Eventos (Event-Driven Architecture - EDA) - (Consideración para Evolución Futura):**
    * _Rationale/Referencia:_ El PRD menciona la visión de evolucionar hacia una "Arquitectura Orientada a Eventos con Microservicios Opcionales" post-v1.0. El diseño modular actual del monolito deberá considerar interfaces y flujos de datos que puedan facilitar una futura transición hacia una EDA si el sistema escala y lo requiere, por ejemplo, para desacoplar servicios o manejar flujos de datos complejos de manera más reactiva.

* **Command Query Responsibility Segregation (CQRS) - (Consideración para Evolución Futura):**
    * _Rationale/Referencia:_ El PRD también valora CQRS como principio. Aunque probablemente no se implementará completamente en la v1.0 del monolito, el diseño de los módulos de datos y servicios podría considerar una separación conceptual de los modelos y rutas para comandos (escrituras) y consultas (lecturas) si esto simplifica la lógica o prepara el camino para futuras optimizaciones de rendimiento y escalabilidad.


## Diagrama de Componentes Principales (Mermaid C4 Model - Nivel 2):

```mermaid
graph TD
    UserInterface["Interfaz de Usuario (PyQt5)"]

    subgraph "UltiBotInversiones - Componentes del Monolito Modular"
        TradingEngine["Motor de Trading"]
        MarketDataMgr["Gestor de Datos de Mercado"]
        AI_Orchestrator["Orquestador de Análisis IA\n(LangChain + Gemini + Herramientas)"]
        OrderExecutor["Ejecutor de Órdenes"]
        PortfolioManager["Gestor de Portafolio"]
        StrategyManager["Gestor de Estrategias"]
        NotificationService["Servicio de Notificaciones"]
        CredentialManager["Gestor de Credenciales"]
        ConfigManager["Gestor de Configuración"]
        DataPersistenceService["Servicio de Persistencia de Datos\n(Supabase/PostgreSQL)"]
    end

    subgraph "Servicios Externos"
        BinanceAPI[("API de Binance")]
        TelegramAPI[("API de Telegram")]
        GeminiModelAPI[("API del Modelo Gemini")]
        MCPServers[("Servidores MCP")]
        MobulaAPI[("API de Mobula")]
    end

    %% Interacciones de la UI
    UserInterface --> TradingEngine
    UserInterface --> PortfolioManager
    UserInterface --> StrategyManager
    UserInterface --> ConfigManager
    UserInterface -.-> NotificationService %% UI puede leer notificaciones o disparar tests

    %% Interacciones del Motor de Trading
    TradingEngine --> MarketDataMgr
    TradingEngine --> AI_Orchestrator
    TradingEngine --> OrderExecutor
    TradingEngine --> PortfolioManager
    TradingEngine --> StrategyManager
    TradingEngine -.-> ConfigManager %% Para leer configuraciones de gestión de capital, etc.
    TradingEngine -.-> DataPersistenceService %% Para registrar histórico de trades, etc.

    %% Interacciones del Orquestador de IA
    AI_Orchestrator -.-> MarketDataMgr %% Como herramienta/fuente de datos
    AI_Orchestrator -.-> CredentialManager %% Para obtener claves de sus herramientas
    AI_Orchestrator -->|Consulta Motor IA| GeminiModelAPI
    AI_Orchestrator -->|Utiliza Herramienta| MCPServers
    AI_Orchestrator -->|Utiliza Herramienta| MobulaAPI
    AI_Orchestrator -->|Puede usar Herramienta| BinanceAPI %% Para datos adicionales

    %% Interacciones de los Gestores de Datos y Configuración
    CredentialManager --> DataPersistenceService
    ConfigManager --> DataPersistenceService
    PortfolioManager --> DataPersistenceService
    PortfolioManager -.-> MarketDataMgr %% Para precios actuales y valoración
    StrategyManager --> DataPersistenceService

    %% Interacciones con APIs Externas (directas)
    MarketDataMgr -->|Datos de Mercado| BinanceAPI
    OrderExecutor -->|Ejecución de Órdenes| BinanceAPI
    NotificationService -->|Envío de Mensajes| TelegramAPI
    
    %% Componentes que necesitan credenciales
    MarketDataMgr -.-> CredentialManager
    OrderExecutor -.-> CredentialManager
    NotificationService -.-> CredentialManager
    %% AI_Orchestrator ya tiene su línea a CredentialManager
