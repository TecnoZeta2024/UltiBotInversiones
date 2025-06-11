## Project Structure

A continuación, se presenta la estructura de directorios propuesta para el Monorepo de "UltiBotInversiones". Esta estructura está diseñada para separar claramente las responsabilidades del backend, la interfaz de usuario de escritorio (PyQt5), y otros artefactos del proyecto.

{project-root}/
├── .github/                    # Workflows de CI/CD (ej. GitHub Actions)
│   └── workflows/
│       └── main.yml
├── .vscode/                    # Configuración específica para VSCode (opcional)
│   └── settings.json
├── docs/                       # Toda la documentación del proyecto (PRD, Arquitectura, Épicas, etc.)
│   ├── index.md                # Índice principal de la documentación
│   ├── PRD.md
│   ├── Architecture.md
│   ├── Epicas.md
│   └── ... (otros archivos .md como data-models.md, api-reference.md que crearemos)
├── infra/                      # Configuración de infraestructura (ej. Docker-compose para desarrollo, scripts de Supabase si son necesarios fuera de la app)
│   └── docker-compose.yml
├── scripts/                    # Scripts de utilidad (ej. para linters, formateadores, tareas de build o despliegue personalizadas)
│   └── run_linters.sh
├── src/                        # Código fuente principal de la aplicación
│   ├── ultibot_backend/        # Módulo principal del backend (Monolito Modular con FastAPI)
│   │   ├── __init__.py
│   │   ├── api/                # Endpoints/Routers de FastAPI (controladores)
│   │   │   ├── __init__.py
│   │   │   └── v1/             # Versión 1 de la API
│   │   │       ├── __init__.py
│   │   │       └── endpoints/  # Módulos para diferentes grupos de endpoints
│   │   ├── core/               # Lógica de negocio central, entidades y modelos de dominio (agnósticos al framework)
│   │   │   ├── __init__.py
│   │   │   └── domain_models/  # Modelos Pydantic o dataclasses para el dominio
│   │   ├── services/           # Implementaciones de nuestros componentes lógicos (TradingEngine, AI_Orchestrator, etc.)
│   │   │   ├── __init__.py
│   │   │   ├── trading_engine_service.py
│   │   │   ├── ai_orchestrator_service.py
│   │   │   ├── market_data_service.py
│   │   │   ├── order_execution_service.py
│   │   │   ├── portfolio_service.py
│   │   │   ├── strategy_service.py
│   │   │   ├── notification_service.py # Implementación del NotificationService
│   │   │   ├── credential_service.py   # Implementación del CredentialManager
│   │   │   └── config_service.py       # Implementación del ConfigManager
│   │   ├── adapters/           # Adaptadores para servicios externos y la capa de persistencia
│   │   │   ├── __init__.py
│   │   │   ├── binance_adapter.py
│   │   │   ├── telegram_adapter.py
│   │   │   ├── mobula_adapter.py
│   │   │   └── persistence_service.py # Implementación del DataPersistenceService (Supabase)
│   │   ├── main.py             # Punto de entrada de la aplicación FastAPI
│   │   └── app_config.py       # Configuración específica del backend (ej. carga de variables de entorno)
│   ├── ultibot_ui/             # Módulo principal de la interfaz de usuario con PyQt5
│   │   ├── __init__.py
│   │   ├── windows/            # Ventanas principales de la aplicación
│   │   ├── widgets/            # Widgets personalizados y reutilizables
│   │   ├── assets/             # Recursos de la UI (iconos, imágenes, archivos .ui si se usan)
│   │   ├── services/           # Lógica para interactuar con el backend (si es necesario, ej. cliente HTTP)
│   │   └── main.py             # Punto de entrada de la aplicación PyQt5
│   └── shared/                 # Código o tipos compartidos entre el backend y la UI (si aplica)
│       ├── __init__.py
│       └── data_types.py       # Ej. Definiciones Pydantic comunes si la UI las consume
├── tests/                      # Pruebas automatizadas
│   ├── backend/                # Pruebas para el backend
│   │   ├── unit/               # Pruebas unitarias (reflejando la estructura de ultibot_backend/)
│   │   └── integration/        # Pruebas de integración
│   ├── ui/                     # Pruebas para la UI de PyQt5
│   │   └── unit/
│   └── e2e/                    # Pruebas End-to-End (si aplican para el flujo completo)
├── .env.example                # Ejemplo de variables de entorno requeridas
├── .gitignore                  # Archivos y directorios a ignorar por Git
├── Dockerfile                  # Para construir la imagen Docker del backend (y potencialmente la UI si se empaqueta junta)
├── pyproject.toml              # Definición del proyecto y dependencias para Poetry
└── README.md                   # Visión general del proyecto, instrucciones de configuración y ejecución
