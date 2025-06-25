# BASE DE CONOCIMIENTO DEL PROYECTO: UltiBotInversiones

Este documento proporciona un resumen conciso y altamente informativo de los aspectos clave del proyecto UltiBotInversiones. Sirve como una referencia rápida para todos los agentes y desarrolladores, asegurando una comprensión compartida de la arquitectura, los modelos de datos y las directrices operativas.

---

## 1. Visión General y Arquitectura

UltiBotInversiones es una plataforma de trading personal avanzada, implementada como un **Monolito Modular** dentro de un **Monorepo**. Su objetivo es la ejecución de estrategias de trading de baja latencia, potenciadas por **Inteligencia Artificial (Gemini)** y orquestadas por **LangChain (Python)**.

### 1.1. Arquitectura del Sistema Principal (`Architecture.md`)
*   **Estilo Arquitectónico:** Monolito Modular (v1.0), con visión a Arquitectura Orientada a Eventos y Microservicios.
*   **Estructura del Repositorio:** Monorepo.
*   **Flujo de Datos:** Unidireccional (captura de datos -> análisis IA -> ejecución -> notificación).
*   **Patrones Clave:** Agente-Herramientas (LangChain), Procesamiento Asíncrono, Diseño Orientado al Dominio (DDD).
*   **Componentes Principales:** UI (PyQt5), Núcleo de Trading, Orquestador IA, Gestión de Datos (Supabase/PostgreSQL), Sistema de Notificaciones.
*   **Servicios Externos:** Binance API (datos y ejecución), Telegram Bot API (notificaciones), Mobula API (verificación de datos), Google Gemini API (motor IA).

### 1.2. Arquitectura del Sistema de Agentes de IA (`agent-system-architecture.md`)
El sistema de agentes se basa en `bmad-agent` y orquesta tareas complejas.
*   **Orquestador (Orchestrator):** Núcleo del sistema, gestiona el estado, procesa comandos y dirige el flujo de agentes.
*   **Cargadores:** Config Loader, Persona Loader.
*   **Ejecutor de Tareas (Task Executor):** Localiza y ejecuta tareas, resuelve rutas a recursos.
*   **Interfaz del Espacio de Trabajo (Workspace Interface):** Abstracción para interactuar con el proyecto (leer/escribir archivos, ejecutar comandos).

---

## 2. Modelos de Datos Clave (`data-models.md`)

Las entidades principales del sistema, persistidas en PostgreSQL (vía Supabase), incluyen:

*   **`UserConfiguration`**: Preferencias del usuario (notificaciones, trading, IA, UI).
*   **`APICredential`**: Almacenamiento seguro y encriptado de claves API externas (Binance, Telegram, Gemini, Mobula).
*   **`Notification`**: Registros de notificaciones del sistema (eventos, canales, prioridad).
*   **`Trade`**: Detalles de operaciones de trading (paper, real, backtest), incluyendo órdenes de entrada/salida, P&L, y contexto de mercado.
*   **`Opportunity`**: Oportunidades de trading detectadas, con análisis de IA, estado, y feedback del usuario.
*   **`TradingStrategyConfig`**: Configuraciones modulares de estrategias de trading (Scalping, Day Trading, Arbitraje Simple, etc.) con parámetros específicos y reglas de aplicabilidad.
*   **`PortfolioSnapshot`**: Instantáneas del estado del portafolio (valor total, balances, activos, P&L) para modos paper/real/backtest.

---

## 3. Flujos de Trabajo y Secuencias (`sequence-diagrams.md`)

El flujo de trabajo principal del sistema sigue un ciclo de 5 fases:

1.  **Detección y Registro de Oportunidad:** Eventos de mercado (Binance WS) disparan la evaluación por el `TradingEngine`, registrando oportunidades en `DataPersistenceService`.
2.  **Análisis y Enriquecimiento por IA:** `AI_Orchestrator` (LangChain + Gemini) analiza la oportunidad, utilizando herramientas (Mobula, Binance REST) para enriquecer datos. El resultado (confianza, parámetros) se actualiza en la oportunidad.
3.  **Presentación y Confirmación:** `TradingEngine` presenta la oportunidad a la UI (si requiere confirmación del usuario para operaciones reales).
4.  **Ejecución de Orden Real:** Tras confirmación (si aplica), `TradingEngine` usa `CredentialManager` y `BinanceAPI` para colocar la orden real, registrando el `Trade`.
5.  **Gestión Post-Ejecución y Notificación:** `TradingEngine` notifica a `NotificationService`, que envía alertas a la UI y Telegram.

---

## 4. Guías Operativas Esenciales

### 4.1. Manejo de Errores (`operational-guidelines.md`)
*   **Enfoque General:** Excepciones de Python, manejadores de FastAPI.
*   **Logging:** `logging` estándar de Python (DEBUG, INFO, WARNING, ERROR, CRITICAL).
*   **Patrones Específicos:** Captura de excepciones `httpx` (timeouts, reintentos), excepciones de lógica de negocio, transacciones de DB.

### 4.2. Estándares de Codificación (`operational-guidelines.md`)
*   **Runtime:** Python `3.11.9`.
*   **Linter/Formateador:** `Ruff` (principal), con `pre-commit hooks` obligatorios.
*   **Convenciones de Nomenclatura:** `snake_case` para variables/funciones, `PascalCase` para clases, `UPPER_SNAKE_CASE` para constantes.
*   **Operaciones Asíncronas:** Uso extensivo de `async`/`await` para I/O.
*   **Seguridad de Tipos:** `Type Hints` obligatorios, `Pydantic Models` para validación, análisis estático con `Ruff` (y `MyPy` si es necesario).
*   **Comentarios y Documentación:** Docstrings en estilo Google Style para funciones/clases públicas.

### 4.3. Estrategia de Pruebas (`operational-guidelines.md`)
*   **Herramientas:** `pytest` (principal), `pytest-asyncio`, `unittest.mock`.
*   **Tipos de Pruebas:**
    *   **Unitarias:** Aislamadas, cubren lógica de negocio. Ubicación: `tests/unit/`.
    *   **Integración:** Interacción entre módulos, con mocks para externos. Ubicación: `tests/integration/`.
    *   **E2E (v1.0):** Principalmente pruebas manuales para UI; integración de alto nivel para flujos de backend.
*   **Cobertura:** Cobertura razonable de lógica crítica.

### 4.4. Mejores Prácticas de Seguridad (`operational-guidelines.md`)
*   **Validación de Entrada:** Pydantic para APIs, validación en backend.
*   **Gestión de Secretos:** Claves API encriptadas en DB (`APICredential`), desencriptación solo en uso. `APP_ENCRYPTION_KEY` crucial.
*   **Seguridad de Dependencias:** `Poetry` para gestión, revisión periódica de vulnerabilidades.
*   **Principio de Mínimo Privilegio:** Permisos mínimos para API keys.
*   **Manejo de Errores:** No exponer detalles sensibles en UI/logs.

### 4.5. Cómo Añadir Nuevas Estrategias (`adding-new-strategies-guide.md`)
El sistema es modular para añadir nuevas estrategias sin modificar código existente:
1.  Definir el Modelo de Parámetros (clase Pydantic).
2.  Actualizar el Enum `BaseStrategyType`.
3.  Actualizar el `Union Type` de `StrategySpecificParameters`.
4.  Añadir Validación en `TradingStrategyConfig`.
5.  Actualizar `StrategyService` para la conversión de parámetros.

---

## 5. Estructura del Proyecto (`project-structure.md`)

La estructura del monorepo es la siguiente:

```
{project-root}/
├── .github/                    # Workflows de CI/CD
├── .vscode/                    # Configuración VSCode
├── docs/                       # Documentación del proyecto
├── infra/                      # Configuración de infraestructura (Docker)
├── scripts/                    # Scripts de utilidad
├── src/                        # Código fuente principal
│   ├── ultibot_backend/        # Backend (FastAPI)
│   │   ├── api/                # Endpoints
│   │   ├── core/               # Lógica de negocio central
│   │   ├── services/           # Implementaciones de servicios
│   │   └── adapters/           # Adaptadores para servicios externos
│   ├── ultibot_ui/             # Interfaz de Usuario (PyQt5)
│   └── shared/                 # Código compartido
├── tests/                      # Pruebas automatizadas
├── .env.example                # Ejemplo de variables de entorno
├── .gitignore                  # Archivos ignorados por Git
├── Dockerfile                  # Dockerfile del backend
├── pyproject.toml              # Definición del proyecto (Poetry)
└── README.md                   # Visión general del proyecto
