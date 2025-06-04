## Core Workflow / Sequence Diagrams

```mermaid
sequenceDiagram
    participant User as Usuario (via UI)
    participant UI as Interfaz de Usuario (PyQt5)
    participant MarketDataMgr as Gestor de Datos de Mercado (Binance WS)
    participant TradingEngine as Motor de Trading
    participant ConfigManager as Gestor de Configuración
    participant DataPersistenceService as Servicio de Persistencia (Supabase)
    participant AI_Orchestrator as Orquestador IA (LangChain + Gemini)
    participant CredentialManager as Gestor de Credenciales
    participant BinanceAPI as API de Binance (REST)
    participant MobulaAPI as API de Mobula (Ej. Herramienta IA)
    participant NotificationService as Servicio de Notificaciones
    participant TelegramAPI as API de Telegram

    Note over MarketDataMgr, TradingEngine: Fase 1: Detección y Registro de Oportunidad (Flujo Iniciado por Datos de Mercado)
    MarketDataMgr->>TradingEngine: Notifica evento de mercado relevante (ej. datos de klines, ticker)
    TradingEngine->>TradingEngine: Evalúa evento con estrategias activas
    alt Oportunidad Potencial Detectada por Estrategia Interna
        TradingEngine->>DataPersistenceService: Crea/Actualiza registro de Oportunidad (O_ID, datos_iniciales, estado: nueva/actualizada)
        DataPersistenceService-->>TradingEngine: Oportunidad Creada/Actualizada (O_ID)
        TradingEngine->>AI_Orchestrator: Solicita análisis para Oportunidad (O_ID)
    end

    Note over AI_Orchestrator, DataPersistenceService, GeminiAPI, BinanceAPI, MobulaAPI: Fase 2: Análisis y Enriquecimiento por IA
    AI_Orchestrator->>DataPersistenceService: Obtiene datos de Oportunidad (O_ID)
    DataPersistenceService-->>AI_Orchestrator: Datos de Oportunidad
    AI_Orchestrator->>AI_Orchestrator: Prepara prompt inicial con datos y herramientas disponibles

    loop Ciclo de Invocación de Herramientas (LangChain)
        AI_Orchestrator->>GeminiAPI: Envía prompt/solicitud de siguiente paso
        GeminiAPI-->>AI_Orchestrator: Decide (ej: usar Herramienta_Binance_MarketData)
        alt Usar Herramienta Binance (REST)
            AI_Orchestrator->>CredentialManager: Solicita credenciales para herramienta Binance (si aplica y no cacheadas)
            CredentialManager-->>AI_Orchestrator: Credenciales
            AI_Orchestrator->>BinanceAPI: Obtiene datos de mercado adicionales (REST)
            BinanceAPI-->>AI_Orchestrator: Datos de mercado
            AI_Orchestrator->>GeminiAPI: Devuelve resultado de Herramienta_Binance
        else Usar Herramienta Mobula (ejemplo)
            AI_Orchestrator->>CredentialManager: Solicita credenciales para herramienta Mobula
            CredentialManager-->>AI_Orchestrator: Credenciales
            AI_Orchestrator->>MobulaAPI: Verifica/enriquece datos del activo
            MobulaAPI-->>AI_Orchestrator: Datos del activo
            AI_Orchestrator->>GeminiAPI: Devuelve resultado de Herramienta_Mobula
        else Otras Herramientas o Análisis Final
            GeminiAPI-->>AI_Orchestrator: Resultado final del análisis (confianza, parámetros, lógica)
        end
    end
    AI_Orchestrator->>DataPersistenceService: Actualiza Oportunidad (O_ID, análisis_IA, estado: analizada)
    DataPersistenceService-->>AI_Orchestrator: Confirmación de actualización
    AI_Orchestrator-->>TradingEngine: Devuelve resumen del análisis (O_ID, confianza, parámetros)

    Note over TradingEngine, ConfigManager, UI, User: Fase 3: Presentación y Confirmación (si es necesaria)
    TradingEngine->>DataPersistenceService: Obtiene Oportunidad analizada (O_ID)
    DataPersistenceService-->>TradingEngine: Datos completos de Oportunidad
    TradingEngine->>ConfigManager: Consulta configuración de usuario (ej. umbral realTrading, confirmación manual)
    ConfigManager-->>TradingEngine: Preferencias del usuario
    alt Requiere Confirmación del Usuario y Alta Confianza
        TradingEngine->>UI: Presenta oportunidad de alta confianza al usuario (O_ID, detalles)
        UI->>User: Muestra detalles y solicita confirmación para operación real
        User->>UI: Confirma ejecución de la operación (O_ID)
        UI->>TradingEngine: Envía confirmación del usuario para ejecutar (O_ID)
    else Decisión Automatizada (No mostrado en este flujo de "orden real con confirmación")
        TradingEngine->>TradingEngine: Procede basado en reglas (ej. paper trading o real si configurado)
    end

    Note over TradingEngine, CredentialManager, BinanceAPI, DataPersistenceService: Fase 4: Ejecución de Orden Real
    TradingEngine->>CredentialManager: Solicita credenciales de Binance (API Key Real)
    CredentialManager-->>TradingEngine: Credenciales de Binance
    TradingEngine->>BinanceAPI: Coloca orden de compra/venta (parámetros de O_ID, credenciales)
    BinanceAPI-->>TradingEngine: Respuesta de la orden (ID_Orden_Exchange, estado_orden)
    TradingEngine->>DataPersistenceService: Crea registro de Trade (basado en O_ID, ID_Orden_Exchange, detalles)
    DataPersistenceService-->>TradingEngine: Trade Creado
    TradingEngine->>DataPersistenceService: Actualiza Oportunidad (O_ID, estado: convertida_a_trade_real, Trade_ID)
    DataPersistenceService-->>TradingEngine: Confirmación
    TradingEngine->>TradingEngine: Llama a PortfolioManager para actualizar estado (no detallado aquí)

    Note over TradingEngine, NotificationService, UI, TelegramAPI: Fase 5: Gestión Post-Ejecución y Notificación
    TradingEngine->>NotificationService: Notifica ejecución de la operación (detalles del Trade)
    NotificationService->>DataPersistenceService: Guarda Notificación (opcional, para historial)
    DataPersistenceService-->>NotificationService: Confirmación
    NotificationService->>UI: Envía notificación a la UI (si está activa)
    NotificationService->>TelegramAPI: Envía notificación a Telegram (si configurado)
    TelegramAPI-->>NotificationService: Confirmación de envío (opcional)
    UI->>User: Muestra notificación
