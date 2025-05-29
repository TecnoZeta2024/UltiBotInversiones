## Definitive Tech Stack Selections

¡Entendido, Carlos! Comprendo perfectamente la directiva: agilidad, estabilidad y potencia para poner "UltiBotInversiones" en marcha lo antes posible, manteniendo la simplicidad en esta v1.0, especialmente siendo una aplicación de uso personal y local.

Con ese enfoque, tomaré la iniciativa de responder las preguntas pendientes sobre el stack tecnológico, buscando el equilibrio entre robustez y mínima complejidad para esta fase.

**Integración de tus Adiciones y Respuestas a las Preguntas Pendientes:**

1.  **Herramientas de Calidad de Código (`Black`, `Ruff`, `pytest`):**
    * `pytest` es fundamental como framework de pruebas y debe estar en el stack.
    * `Black` (formateador) y `Ruff` (linter extremadamente rápido que puede reemplazar a `Flake8` y otros) son herramientas de desarrollo esenciales para mantener la calidad y consistencia del código. Las detallaremos más en la sección "Coding Standards", pero podemos listarlas aquí como herramientas de desarrollo.
    * Añadiré `pytest-asyncio` ya que trabajaremos con código asíncrono (FastAPI, `httpx`).

2.  **Manejo de Migraciones de Base de Datos (Supabase):**
    * Dado que Supabase facilita esto, actualizaré la descripción de PostgreSQL para reflejar que las migraciones se manejarán principalmente a través de las herramientas que provee Supabase (su CLI y/o interfaz de usuario). Esto evita añadir una dependencia como Alembic si no es estrictamente necesaria para la v1.0.

3.  **Cloud Platform:**
    * Para la v1.0, y enfocándonos en una aplicación local, nuestra dependencia principal es Supabase para el BaaS/DBaaS. No introduciremos una plataforma cloud adicional (AWS, Azure, GCP) para otros servicios, para mantener la simplicidad.

4.  **Cloud Services:**
    * Consecuentemente, no se prevén servicios cloud específicos más allá de los inherentes a Supabase.

5.  **Infrastructure as Code (IaC):**
    * Para una aplicación de escritorio/local v1.0, IaC (Terraform, CDK, etc.) no es necesario y añadiría complejidad.

6.  **CI/CD:**
    * Un pipeline formal de CI/CD es más de lo que necesitamos para la v1.0 de una aplicación local. Las pruebas y builds se ejecutarán localmente. Se podrían usar scripts de Poetry/make/shell para automatizar tareas comunes.

Aquí está la tabla **"Definitive Tech Stack Selections"** actualizada con estas consideraciones. 

| Categoría     | Tecnología | Versión / Detalles | Descripción / Propósito | Justificación (Opcional) |
| :------------ | :--------- | :----------------- | :---------------------- | :----------------------- |
| **Lenguajes** | Python | `3.11.9` | Lenguaje principal para el backend, lógica del bot, scripts y orquestación de IA. | Versatilidad, ecosistema robusto para IA y web, rendimiento mejorado en versiones 3.11+. Versión específica para consistencia.|
| **Runtime** | Python Interpreter | `Corresponde a Python 3.11.9` | Entorno de ejecución para el código Python. |
| | SQL | `Estándar SQL implementado por PostgreSQL 15` | Lenguaje para consultas y gestión de la base de datos relacional. | Estándar para bases de datos relacionales; PostgreSQL ofrece un dialecto SQL rico y eficiente. |
| **Frameworks** | FastAPI | `0.111.0` | Framework de alto rendimiento para construir las APIs del backend. | Moderno, rápido (comparable a NodeJS y Go), basado en type hints de Python, auto-documentación OpenAPI, asíncrono nativo. |
| | PyQt5 | `5.15.11 (Vinculado a Qt 5.15.x LTS)` | Framework para la Interfaz de Usuario (UI) de escritorio. | Requisito del proyecto; bindings maduros y completos de Qt para Python, amplio conjunto de widgets. |
| | LangChain (Python) | `Core: 0.2.5` | Orquestación de interacciones con Modelos de Lenguaje (LLM) y construcción de apl. basadas en IA. | Facilita el patrón Agente-Herramientas con Gemini, gestión de prompts, cadenas de LLMs, e integraciones. |
| **Bases de Datos** | PostgreSQL (via Supabase) | `15.6 o sup. (Gestionada por Supabase)` | Almacén de datos relacional principal. Migraciones gestionadas vía Supabase CLI/UI. | Robustez, escalabilidad. Supabase facilita gestión, auth y APIs en tiempo real. |
| | Redis | `7.2.5` | Caché L2, colas de tareas (potencial), almacenamiento de sesión (potencial). | Alta velocidad, estructuras de datos versátiles, ideal para reducir latencia. |
| **Proveedor IA** | Google Gemini (via API) | `Modelos: Gemini 1.5 Pro/Flash (seleccionables)` | Motor principal de Inteligencia Artificial. | Capacidades avanzadas de razonamiento multimodal, ventana de contexto grande, integración con herramientas. |
| **Bibliotecas Clave** | `google-generativeai` | `0.5.4` | Cliente Python oficial para la API de Google Gemini. | Interacción directa y eficiente con los modelos Gemini. |
| | `langchain-core` | `0.2.5` | Núcleo de LangChain. | Base para el ecosistema LangChain. |
| | `langchain-google-genai` | `0.1.7 (o compatible con LC Core 0.2.x)` | Integración LangChain para modelos Gemini. | Permite usar Gemini fluidamente dentro de LangChain. |
| | `langchain-community` | `0.2.5 (o compatible con LC Core 0.2.x)` | Componentes comunitarios de LangChain. | Amplía capacidades de LangChain con diversas herramientas. |
| | `pydantic` | `2.7.1 (Compatible con FastAPI 0.111.0)` | Validación de datos y gestión de configuraciones. | Usado por FastAPI para validación y modelos de datos; robusto. |
| | `supabase-py` | `2.5.0` | Cliente Python para API de Supabase (PostgreSQL). | Facilita la comunicación con la BD gestionada por Supabase. |
| | `httpx` | `0.27.0` | Cliente HTTP asíncrono para APIs externas (Binance, MCPs, Mobula). | Comunicación eficiente y no bloqueante, esencial para baja latencia. |
| | `websockets` | `12.0` | Biblioteca para conexiones WebSocket (ej. streams de Binance). | Comunicación en tiempo real bidireccional, crucial para datos de mercado. |
| **Gestión Dependencias**| Poetry | `1.8.3` | Gestión de dependencias, empaquetado y entornos virtuales. | Entornos reproducibles, resolución robusta, `pyproject.toml`. |
| **Containerización** | Docker Engine | `26.1.4 (o más reciente estable)` | Creación, gestión y despliegue de la aplicación en contenedores (opcional para v1.0 local). | Consistencia entre entornos; útil para dependencias complejas como Redis si no se instala nativo. |
| **Servidor ASGI** | Uvicorn | `0.29.0 (o compatible con FastAPI)` | Servidor ASGI para ejecutar FastAPI. | Alto rendimiento para FastAPI; se puede usar con Gunicorn en producción (pero para v1.0 local, Uvicorn solo es suficiente). |
| **Testing** | `pytest` | `(Versión específica compatible?)` | Framework principal para pruebas unitarias y de integración. | Popular, flexible y con amplio ecosistema de plugins en Python. |
| | `pytest-asyncio` | `(Versión específica compatible?)` | Plugin de Pytest para soportar pruebas de código asíncrono. | Necesario para probar endpoints y lógica de FastAPI/httpx. |
| **Herramientas de Desarrollo y Calidad** | `Ruff` | `(Versión específica?)` | Linter y formateador de Python extremadamente rápido. | Eficiencia y consistencia en el formato y calidad del código. Puede reemplazar Black, Flake8, isort. |
| | `Black` (Opcional si se usa Ruff para formateo) | `(Versión específica?)` | Formateador de código Python. | Consistencia en el formato del código (puede ser redundante si Ruff se usa para formateo). |
| **Cloud Platform** | N/A | N/A | Principalmente Supabase para DBaaS; no se prevé otra plataforma cloud principal para v1.0. | Simplificación para v1.0 de aplicación local. |
| **Cloud Services** | N/A | N/A | No se utilizan servicios cloud adicionales más allá de Supabase para v1.0. | Simplificación para v1.0. |
| **Infrastructure as Code (IaC)** | N/A | N/A | No aplica para v1.0 (aplicación de escritorio/local). | Simplificación para v1.0. |
| **CI/CD** | N/A | N/A | Pruebas y builds ejecutados localmente para v1.0. Scripts locales para automatización. | Simplificación para v1.0. |
