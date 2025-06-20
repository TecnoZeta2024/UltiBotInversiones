graph TD
    subgraph "Usuario"
        U[👤 Usuario]
    end

    subgraph "Frontend (UI)"
        UI[🖥️ UltiBot UI<br/>PyQt/FastAPI Frontend]
    end

    subgraph "Backend (API)"
        B[⚙️ UltiBot Backend<br/>FastAPI]
    end

    subgraph "Servicios Externos"
        BINANCE[📈 Binance API]
        GEMINI[🧠 Gemini AI]
    end

    subgraph "Supabase (BaaS)"
        DB[🗄️ PostgreSQL Database]
        AUTH[🔑 Authentication]
        STORAGE[☁️ Storage]
        EDGE[⚡ Edge Functions]
    end

    U --> UI
    UI --> B
    B --> BINANCE
    B --> GEMINI
    B --> DB
    B --> AUTH
    B --> STORAGE
    B --> EDGE

    style U fill:#bbdefb,stroke:#3f51b5,stroke-width:2px
    style UI fill:#c8e6c9,stroke:#4caf50,stroke-width:2px
    style B fill:#ffccbc,stroke:#ff5722,stroke-width:2px
    style BINANCE fill:#e0f2f7,stroke:#00bcd4,stroke-width:2px
    style GEMINI fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style DB fill:#e1f5fe,stroke:#2196f3,stroke-width:2px
    style AUTH fill:#e1f5fe,stroke:#2196f3,stroke-width:2px
    style STORAGE fill:#e1f5fe,stroke:#2196f3,stroke-width:2px
    style EDGE fill:#e1f5fe,stroke:#2196f3,stroke-width:2px
