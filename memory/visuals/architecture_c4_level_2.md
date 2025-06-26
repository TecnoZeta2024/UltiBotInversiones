# Diagrama de Contenedores (C4 - Nivel 2): UltiBotInversiones

## 1. Propósito y Alcance
Este diagrama descompone el sistema `UltiBotInversiones` en sus principales contenedores. Un "contenedor" representa una aplicación o un almacén de datos ejecutable de forma independiente. El objetivo es mostrar la arquitectura de alto nivel del sistema y cómo se distribuyen las responsabilidades entre sus partes principales.

## 2. Cómo Interpretar este Diagrama
- **Persona/Sistema Externo:** Actores que interactúan con los contenedores.
- **Contenedor:** Un bloque de construcción principal del sistema.
- **Flechas:** Indican las interacciones y el flujo de datos entre contenedores y sistemas externos, especificando la tecnología utilizada (ej. `API REST (HTTPS)`).

## 3. Diagrama

```mermaid
graph TD
    actor "Trader" as Trader

    subgraph "Sistema UltiBotInversiones"
        direction TB
        
        rectangle "UI Application" as UI [
            <b>UI Application</b>
            <br/>
            (PySide6 Desktop App)
            <br/>
            <i>Proporciona la interfaz gráfica para el trading.</i>
        ]

        rectangle "API Server" as Backend [
            <b>API Server</b>
            <br/>
            (Python FastAPI)
            <br/>
            <i>Ejecuta la lógica de negocio, gestiona estrategias y se conecta a servicios externos.</i>
        ]

        database "Database" as DB [
            <b>Database</b>
            <br/>
            (SQLite)
            <br/>
            <i>Almacena configuraciones, estrategias, órdenes y reportes.</i>
        ]
        
        database "Cache" as Cache [
            <b>Cache</b>
            <br/>
            (Redis)
            <br/>
            <i>Almacena temporalmente datos de mercado para un acceso rápido.</i>
        ]

    end

    subgraph "Sistemas Externos"
        direction RL
        rectangle "Binance"
        rectangle "Mobula API"
        rectangle "AI Language Model"
        rectangle "Telegram"
    end

    Trader -- "Interactúa con" --> UI
    UI -- "Realiza peticiones API" --> Backend
    Backend -- "Lee/Escribe" --> DB
    Backend -- "Lee/Escribe" --> Cache
    
    Backend -- "API Calls" --> Binance
    Backend -- "API Calls" --> Mobula
    Backend -- "API Calls" --> "AI Language Model"
    Backend -- "Notifica vía" --> Telegram

    style UI fill:#00aaff,stroke:#333,stroke-width:2px
    style Backend fill:#1168bd,stroke:#333,stroke-width:2px,color:#fff
    style DB fill:#e65100,stroke:#333,stroke-width:2px,color:#fff
    style Cache fill:#d50000,stroke:#333,stroke-width:2px,color:#fff
```

## 4. Observaciones y Análisis del Oráculo
- La arquitectura sigue un patrón cliente-servidor clásico, con una clara separación entre la interfaz de usuario (`ultibot_ui`) y la lógica de negocio (`ultibot_backend`).
- El `API Server` actúa como el cerebro del sistema, orquestando todas las operaciones y la comunicación con el exterior.
- El uso de `SQLite` refuerza la directiva de un sistema "Local-First", fácil de desplegar y sin costos de base de datos externa.
- La inclusión de `Redis` indica un diseño consciente del rendimiento, especialmente para el manejo de datos de mercado que cambian rápidamente.

## 5. Siguientes Pasos Sugeridos
- Para profundizar en la arquitectura, el siguiente paso es seleccionar uno de los contenedores (probablemente el `API Server`) y explorar su **Diagrama de Componentes (Nivel 3)**.
