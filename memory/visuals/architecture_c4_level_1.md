# Diagrama de Contexto del Sistema (C4 - Nivel 1): UltiBotInversiones

## 1. Propósito y Alcance
Este diagrama ofrece una visión de alto nivel del ecosistema de `UltiBotInversiones`. Muestra los principales usuarios y los sistemas de software externos con los que interactúa. El propósito es entender el alcance del sistema y sus dependencias clave sin entrar en detalles de implementación interna.

## 2. Cómo Interpretar este Diagrama
- **Persona:** Representa a un usuario humano que interactúa con el sistema.
- **Sistema de Software:** Representa el sistema `UltiBotInversiones` en su totalidad.
- **Sistema Externo:** Representa un sistema de software de terceros del que `UltiBotInversiones` depende.
- **Flechas:** Indican el flujo de datos o la interacción entre los elementos.

## 3. Diagrama

```mermaid
graph TD
    subgraph "Ecosistema UltiBotInversiones"
        direction LR

        actor "Trader" as Trader
        
        rectangle "UltiBotInversiones" as System [
            <b>UltiBotInversiones</b>
            <br/>
            Sistema de trading algorítmico personal
        ]

        Trader -- "Gestiona estrategias y opera" --> System
    end

    subgraph "Sistemas Externos"
        direction RL

        rectangle "Binance Exchange" as Binance [
            <b>Binance Exchange</b>
            <br/>
            Proveedor de datos de mercado y ejecución de órdenes
        ]

        rectangle "Mobula API" as Mobula [
            <b>Mobula API</b>
            <br/>
            Proveedor de datos de mercado suplementarios
        ]

        rectangle "AI Language Model" as AI [
            <b>AI Language Model</b>
            <br/>
            Servicio de IA para análisis y generación de estrategias
        ]

        rectangle "Telegram" as Telegram [
            <b>Telegram</b>
            <br/>
            Servicio de notificaciones
        ]
    end

    System -- "Obtiene datos de mercado y ejecuta órdenes" --> Binance
    System -- "Obtiene datos de activos" --> Mobula
    System -- "Solicita análisis y estrategias" --> AI
    System -- "Envía notificaciones" --> Telegram

    style Trader fill:#00aaff,stroke:#333,stroke-width:2px
    style System fill:#1168bd,stroke:#333,stroke-width:2px,color:#fff
    style Binance fill:#f0b90b,stroke:#333,stroke-width:2px
    style Mobula fill:#9c27b0,stroke:#333,stroke-width:2px,color:#fff
    style AI fill:#4caf50,stroke:#333,stroke-width:2px,color:#fff
    style Telegram fill:#229ED9,stroke:#333,stroke-width:2px,color:#fff
```

## 4. Observaciones y Análisis del Oráculo
- El sistema está diseñado para ser un centro de control para el trader, orquestando interacciones con múltiples servicios especializados.
- La dependencia de sistemas externos como `Binance` y `Mobula` es crítica para la funcionalidad principal de datos y operaciones.
- La integración con un `AI Language Model` posiciona al sistema como una herramienta de trading "inteligente", no solo de ejecución.
- El uso de `Telegram` para notificaciones sugiere un diseño que permite al usuario monitorear el sistema de forma remota.

## 5. Siguientes Pasos Sugeridos
- Para entender cómo estos sistemas se materializan dentro de la aplicación, el siguiente paso lógico es explorar el **Diagrama de Contenedores (Nivel 2)**.
- Analizar los "contratos" (datos intercambiados) entre `UltiBotInversiones` y cada sistema externo para comprender mejor las integraciones.
