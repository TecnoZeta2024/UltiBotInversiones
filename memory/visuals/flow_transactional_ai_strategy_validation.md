# Flujo Transaccional: Validación de Estrategia de IA

## 1. Propósito y Alcance
Este documento visualiza el ciclo de vida completo de la validación de una oportunidad de trading mediante una estrategia de IA, desde la activación de la estrategia hasta la confirmación del usuario. El objetivo es clarificar las interacciones entre los componentes clave del sistema.

## 2. Cómo Interpretar este Diagrama
- **Participantes:** Representan los componentes del sistema (UI, API, servicios de backend).
- **Flechas:** Indican el flujo de control y las llamadas entre componentes.
- **Loop:** Muestra el proceso continuo del motor de trading que busca y procesa oportunidades.
- **Alt:** Representa la bifurcación lógica clave basada en el umbral de confianza del análisis de la IA.

## 3. Diagrama
```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API_Gateway
    participant TradingEngine
    participant AIOrchestrator
    participant Persistence

    User->>+UI: Activa Estrategia de IA
    UI->>+API_Gateway: PATCH /strategies/{id}/activate
    API_Gateway-->>-UI: 200 OK

    loop Proceso en Segundo Plano
        TradingEngine->>TradingEngine: process_opportunity()
        TradingEngine->>+AIOrchestrator: analyze_opportunity_with_strategy_context_async(opportunity)
        AIOrchestrator->>AIOrchestrator: Genera AIAnalysis
        AIOrchestrator-->>-TradingEngine: Retorna AIAnalysisResult
        
        alt Confianza >= 90%
            TradingEngine->>TradingEngine: Crea TradingDecision("execute_trade")
            TradingEngine->>+Persistence: update_opportunity_status(PENDING_USER_CONFIRMATION_REAL)
            Persistence-->>-TradingEngine: 200 OK
        else Confianza < 90%
            TradingEngine->>+Persistence: update_opportunity_status(REJECTED_BY_SYSTEM)
            Persistence-->>-TradingEngine: 200 OK
        end
    end

    User->>+UI: Abre vista de Oportunidades
    UI->>+API_Gateway: GET /opportunities/real-trading-candidates
    API_Gateway->>+Persistence: get_all(status=PENDING_USER_CONFIRMATION_REAL)
    Persistence-->>-API_Gateway: Lista de Oportunidades
    API_Gateway-->>-UI: Oportunidades de Alta Confianza
    UI-->>-User: Muestra AIAnalysis en Diálogo

    User->>+UI: Confirma Ejecución de Trade
    UI->>+API_Gateway: POST /trades/execute-from-opportunity
    API_Gateway->>+TradingEngine: execute_trade_from_confirmed_opportunity()
    TradingEngine-->>-API_Gateway: Trade Creado
    API_Gateway-->>-UI: 200 OK
```

## 4. Observaciones y Análisis del Oráculo
- El flujo es asíncrono y está impulsado por un motor de trading que opera en segundo plano.
- La decisión crítica de proceder con una oportunidad de trading real depende de un umbral de confianza preconfigurado, lo que introduce un punto de control de riesgo automatizado.
- El `AIOrchestratorService` es el componente central para la inteligencia del sistema, encapsulando la lógica de análisis.
- El usuario tiene la última palabra para ejecutar operaciones de trading real, actuando como una capa final de seguridad y control.

## 5. Siguientes Pasos Sugeridos
- Implementar un sistema de monitoreo para las decisiones del `TradingEngine` para auditar por qué ciertas oportunidades son rechazadas.
- Añadir más métricas al `AIAnalysisResult` para enriquecer la información presentada al usuario.
- Considerar la implementación de un mecanismo de re-análisis para oportunidades que caen justo por debajo del umbral de confianza.
