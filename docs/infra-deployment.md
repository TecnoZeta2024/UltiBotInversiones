##  Infrastructure and Deployment Overview

Dada la naturaleza de "UltiBotInversiones" como una aplicación de escritorio/local para uso personal en su v1.0, la infraestructura y el despliegue se simplifican significativamente:

-   **Cloud Provider(s):**
    -   El proveedor principal de servicios en la nube es **Supabase** para la funcionalidad de Base de Datos como Servicio (DBaaS) con PostgreSQL, autenticación y APIs de datos si se utilizan.
    -   No se prevé el uso de otras plataformas cloud (AWS, Azure, GCP) para componentes de backend o infraestructura central en la v1.0.
-   **Core Services Used:**
    -   Los servicios principales son los proporcionados por **Supabase** (PostgreSQL, Auth, APIs).
    -   **Redis** (listado en el stack) se ejecutará localmente (ej. vía Docker o instalación nativa) o se podría considerar una instancia gestionada simple si fuera estrictamente necesario y Supabase no ofreciera una alternativa integrada suficiente para cach L2. Para v1.0, se prioriza la ejecución local de Redis para simplicidad.
-   **Infrastructure as Code (IaC):**
    -   No aplica (N/A) para la v1.0, ya que no se gestionará infraestructura cloud compleja.
-   **Deployment Strategy:**
    -   El "despliegue" consistirá en la ejecución local de la aplicación Python (backend FastAPI y UI PyQt5) desde el código fuente gestionado con Git.
    -   Se utilizará Poetry para gestionar el entorno y las dependencias.
    -   La aplicación se iniciará mediante scripts (ej. `poetry run python src/ultibot_backend/main.py` y `poetry run python src/ultibot_ui/main.py`).
    -   Si se utiliza Docker para servicios como Redis, se gestionará con `docker-compose.yml` localmente.
-   **Environments:**
    -   Principalmente un entorno de **desarrollo local**.
    -   No se definen entornos formales de `staging` o `production` en servidores remotos para la v1.0.
-   **Environment Promotion:**
    -   No aplica (N/A) en el sentido tradicional. Las "promociones" se gestionan a través de commits y ramas en Git.
-   **Rollback Strategy:**
    -   Se basará en el control de versiones con **Git**. Las reversiones a estados anteriores del código se realizarán mediante comandos de Git (ej. `git revert`, `git checkout <commit>`).
    -   Para la base de datos (Supabase), los rollbacks de esquema o datos dependerán de las capacidades de Supabase para backups y restauración, o de migraciones reversibles si se implementan.
