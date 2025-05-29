# "UltiBotInversiones" UI/UX Specification

## Target user - Personas

- Perfil Principal: Un único usuario (el desarrollador/propietario de la aplicación) con experiencia en el uso de aplicaciones de software. No se considera un experto técnico en profundidad ni un experto en trading algorítmico. Busca una herramienta potente que le asista activamente, simplificando la toma de decisiones de trading complejas a través de análisis claros y una interfaz intuitiva. Su objetivo es gestionar y hacer crecer su capital de inversión personal.

## Key Usability Goals

-   **Facilidad de Aprendizaje:** El usuario debe ser capaz de entender y operar las funciones principales del sistema con una curva de aprendizaje mínima.
-   **Eficiencia de Uso:** Una vez familiarizado, el usuario debe poder realizar tareas comunes (configurar estrategias, revisar el portafolio, confirmar operaciones) de manera rápida y sin pasos innecesarios.
-   **Claridad Informativa:** La información presentada (datos de mercado, análisis de IA, estado del portafolio, notificaciones) debe ser fácil de entender, permitiendo la toma de decisiones informadas.
-   **Soporte a la Decisión:** El sistema debe guiar y asistir al usuario en la toma de decisiones complejas relacionadas con el trading.
-   **Prevención de Errores:** El diseño debe ayudar a prevenir errores críticos, especialmente en la operativa real, mediante confirmaciones claras y una presentación de datos inequívoca.
-   **Experiencia Fluida:** La interacción con la interfaz debe ser ágil y sin demoras perceptibles, especialmente al manejar datos en tiempo real.

## Core Design Principles

1.  **Profesional y Moderno:** El diseño debe reflejar seriedad y confianza, utilizando una estética actual y alineada con herramientas financieras avanzadas.
2.  **Claridad Ante Todo:** Priorizar la legibilidad y la comprensión inmediata de la información. Evitar la ambigüedad y el desorden visual.
3.  **Consistencia Visual y de Interacción:** Mantener patrones de diseño y comportamiento coherentes a lo largo de toda la aplicación para facilitar el aprendizaje y la eficiencia.
4.  **Asistencia Activa e Intuitiva:** La interfaz debe guiar al usuario de forma natural, simplificando procesos complejos y haciendo que las funciones potentes sean accesibles.
5.  **Enfoque en el Rendimiento Visual:** Optimizar para una experiencia fluida, con un tema oscuro que reduzca la fatiga visual durante usos prolongados.
6.  **Confiabilidad y Transparencia:** El diseño debe inspirar confianza, mostrando el estado del sistema y los resultados de las acciones de forma transparente.

##  Arquitectura de la Información (AI)

### Inventario de Pantallas / Mapa del Sitio 
-   **Dashboard Principal** (incluirá prominentemente el estado del portafolio y resumen de inversiones)
    -   (Sección/Vista) Resumen de Datos de Mercado
    -   (Sección/Vista) Estado del Portafolio (Paper y Real)
    -   (Sección/Vista) Visualización de Gráficos Financieros
    -   (Sección/Vista) Centro de Notificaciones del Sistema
    - Oportunidades (Nueva pantalla dedicada)
-   **Configuración del Sistema**
    -   (Sub-Pantalla) Gestión de Conexiones y Credenciales
    -   (Sub-Pantalla) Configuración General de la Aplicación (preferencias, listas de seguimiento, perfiles de riesgo, configuración de IA)
-   **Panel de Gestión de Estrategias**
-   **Historial y Detalles de Operaciones**

### Estructura de Navegación:

1.  **Barra Lateral de Navegación (Sidebar):** Un panel vertical a la izquierda de la pantalla que liste las secciones principales (Dashboard, Configuración, Gestión de Estrategias, Historial). Esta es una opción común que permite un acceso rápido y claro.
2.  **Barra de Menú Superior Tradicional:** Un menú en la parte superior de la ventana (como en muchas aplicaciones de escritorio, ej. Archivo, Editar, Ver, Herramientas, etc.), donde "Herramientas" o una sección similar podría desplegar el acceso a las diferentes vistas principales.
3.  **Pestañas Principales (Tabs):** Si las secciones no son demasiadas, podríamos usar un sistema de pestañas en la parte superior del área de contenido para cambiar entre el Dashboard, Configuración, etc.

### Barra Lateral de Navegación (Sidebar) 

-   **Dashboard:** (Acceso al Dashboard Principal con todas sus sub-vistas/secciones internas como Portafolio, Datos de Mercado, Gráficos, Notificaciones).
-   **Configuración:** (Acceso a la pantalla de Configuración del Sistema, que internamente tendría sub-secciones para Credenciales y Configuración General).
-   **Estrategias:** (Acceso al Panel de Gestión de Estrategias).
-   **Historial de Operaciones:** (Acceso a la pantalla de Historial y Detalles de Operaciones).
-   **Oportunidades:** (Si decidimos que necesita una vista dedicada).
-   **Iconografía**: Iconos representativos a cada ítem de la barra lateral en los wireframes y especificaciones.
-   **Estado Activo**: El ítem de la sección activa en la barra lateral estará claramente resaltado.

**Barra Lateral de Navegación Actualizada:**

-   &lt;Icono> Dashboard
-   &lt;Icono> Oportunidades
-   &lt;Icono> Estrategias
-   &lt;Icono> Historial
-   &lt;Icono> Configuración

## Flujos de Usuario

### Configuración Inicial del Sistema y Gestión de Credenciales"

graph TD
    A[Inicio de Aplicación] --> B{¿Primera Ejecución / Faltan Credenciales Esenciales (Binance, Gemini)?};
    
    B -- Sí --> WIZ_START[Inicio: Asistente de Configuración Esencial];
    WIZ_START --> WIZ_BINANCE[Paso 1: Configurar Binance];
    WIZ_BINANCE --> WIZ_BN_Input[Usuario ingresa API Key y Secret de Binance];
    WIZ_BN_Input --> WIZ_BN_Save[Clic: 'Verificar y Guardar Binance'];
    WIZ_BN_Save --> WIZ_BN_Validate[Sistema valida (asíncrono, con feedback UI)];
    WIZ_BN_Validate --> WIZ_BN_Decision{¿Validación Exitosa?};
    WIZ_BN_Decision -- Sí --> WIZ_BN_Success[Cred. Binance Guardadas. Feedback: Éxito con detalles de permisos];
    WIZ_BN_Decision -- No --> WIZ_BN_Error[Feedback: Error Detallado Binance (ej. clave/permisos). Reintentar];
    WIZ_BN_Error --> WIZ_BN_Input;
    WIZ_BN_Success --> WIZ_GEMINI[Paso 2: Configurar Gemini AI];
    
    WIZ_GEMINI --> WIZ_GM_Input[Usuario ingresa API Key de Gemini];
    WIZ_GM_Input --> WIZ_GM_Save[Clic: 'Verificar y Guardar Gemini'];
    WIZ_GM_Save --> WIZ_GM_Validate[Sistema valida (asíncrono)];
    WIZ_GM_Validate --> WIZ_GM_Decision{¿Validación Exitosa?};
    WIZ_GM_Decision -- Sí --> WIZ_GM_Success[Cred. Gemini Guardadas. Feedback: Éxito];
    WIZ_GM_Decision -- No --> WIZ_GM_Error[Feedback: Error Detallado Gemini. Reintentar];
    WIZ_GM_Error --> WIZ_GM_Input;
    WIZ_GM_Success --> WIZ_TG_OPTIONAL{¿Configurar Telegram ahora (opcional)?};
    
    WIZ_TG_OPTIONAL -- Sí --> WIZ_TELEGRAM[Paso 3: Configurar Telegram];
    WIZ_TELEGRAM --> WIZ_TG_Input[Usuario ingresa Bot Token y Chat ID de Telegram];
    WIZ_TG_Input --> WIZ_TG_Save[Clic: 'Verificar y Guardar Telegram'];
    WIZ_TG_Save --> WIZ_TG_Validate[Sistema envía mensaje de prueba (asíncrono)];
    WIZ_TG_Validate --> WIZ_TG_Decision{¿Envío Exitoso?};
    WIZ_TG_Decision -- Sí --> WIZ_TG_Success[Cred. Telegram Guardadas. Feedback: Éxito];
    WIZ_TG_Decision -- No --> WIZ_TG_Error[Feedback: Error Detallado Telegram. Reintentar];
    WIZ_TG_Error --> WIZ_TG_Input;
    WIZ_TG_Success --> WIZ_END[Fin Asistente. Navegar a Dashboard o Gestión Completa];
    
    WIZ_TG_OPTIONAL -- No/Luego --> WIZ_END;
    WIZ_END --> MAIN_DASHBOARD[Dashboard Principal];
    WIZ_END --> G_CredMan_Entry[O a 'Gestión de Credenciales Completa'];


    B -- No --> D[Usuario Navega a 'Configuración' desde Sidebar];
    D --> E[Pantalla: Configuración del Sistema];
    E --> F[Usuario selecciona 'Gestión de Conexiones y Credenciales'];
    G_CredMan_Entry --> F;
    
    F --> G_CredMan[Pantalla: Gestión de Credenciales];
    G_CredMan --> G_List[UI muestra lista de servicios (Binance, Telegram, Gemini, Mobula, MCPs) con su estado (Configurado ✔️, Pendiente ⚠️, Error ❌)];
    
    G_List --> G_UserSelectsService[Usuario selecciona un servicio de la lista];
    G_UserSelectsService --> G_ActionDecision{¿Acción para el servicio seleccionado?};

    G_ActionDecision -- Añadir/Configurar --> G_ADD_Input[Usuario ingresa datos para Servicio X (campos específicos, ej. API Key, Secret, OtherDetails)];
    G_ADD_Input --> G_ADD_Save[Clic: 'Verificar y Guardar Servicio X'];
    G_ADD_Save --> G_ADD_Validate[Sistema valida credenciales con API de Servicio X (asíncrono, con feedback UI)];
    G_ADD_Validate --> G_ADD_Decision{¿Validación Exitosa?};
    G_ADD_Decision -- Sí --> G_ADD_Success[Cred. Servicio X Encriptadas y Guardadas. Feedback: Éxito. Actualizar estado en G_List];
    G_ADD_Decision -- No --> G_ADD_Error[Feedback: Error Detallado Servicio X. Reintentar];
    G_ADD_Error --> G_ADD_Input;
    G_ADD_Success --> G_List;

    G_ActionDecision -- Editar --> G_EDIT_Flow[Flujo de Edición para Servicio X (similar a Añadir, pre-rellena datos no secretos)];
    G_EDIT_Flow --> G_List;
    
    G_ActionDecision -- Eliminar --> G_DELETE_Confirm[Confirmar eliminación de credenciales para Servicio X];
    G_DELETE_Confirm -- Sí --> G_DELETE_Exec[Eliminar credenciales. Actualizar estado en G_List];
    G_DELETE_Confirm -- No --> G_List;
    G_DELETE_Exec --> G_List;

    G_ActionDecision -- Ver Estado/Detalles --> G_VIEW_Status[Mostrar detalles y estado (no secretos) de Servicio X];
    G_VIEW_Status --> G_List;
    
    G_List --> G_DoneWithCreds{¿Finalizar Gestión de Credenciales?};
    G_DoneWithCreds -- Sí --> E; 
    G_DoneWithCreds -- No (selecciona otro servicio) --> G_UserSelectsService;

    E --> X_GeneralConfig_Nav{¿Ir a 'Configuración General de la Aplicación'?};
    X_GeneralConfig_Nav -- Sí --> Y_GeneralScreen[Pantalla: Configuración General de la App];
    Y_GeneralScreen --> Z_GeneralInput[Usuario ingresa ajustes (capital paper, etc.)];
    Z_GeneralInput --> AA_GeneralSave[Clic: 'Guardar Ajustes Generales'];
    AA_GeneralSave --> AB_GeneralFeedback[Feedback: Ajustes Guardados / Error];
    AB_GeneralFeedback --> MAIN_DASHBOARD;
    X_GeneralConfig_Nav -- No / Volver --> MAIN_DASHBOARD;


    subgraph Leyenda de Errores Comunes en Validaciones
        Err_GENERIC[Error genérico de validación]
        Err_NETWORK[Fallo de Red/Conexión]
        Err_API_SERVICE[Error específico del servicio API externo]
        Err_PERMISSIONS[Permisos insuficientes en la API Key]
    end

    style WIZ_START fill:#f9f,stroke:#333,stroke-width:2px
    style G_CredMan fill:#ccf,stroke:#333,stroke-width:2px


## Wireframes & Mockups

-   **Zona 1: Barra de Estado y Métricas Globales (Superior)**
    
    -   **Validación:** ¡Perfecta! Proporciona la información global crítica de un vistazo. El estado del bot, modo de operación, conectividad de servicios y las métricas de P&L/Portafolio son esenciales aquí.
    -   **Sugerencia Menor:** El botón opcional de "Pausar/Reanudar Motor de Trading" es una excelente idea para un acceso rápido. Si se incluye, deberíamos asegurar que su estado (activo/pausado) sea muy claro visualmente, quizás con el propio texto del botón cambiando o un icono distintivo.
-   **Zona 2: Estado del Portafolio (Panel Principal Izquierdo o Superior-Izquierdo)**
    
    -   **Validación:** Muy completo y bien estructurado. El selector de cuenta Paper/Real es fundamental. El resumen de la cuenta y la tabla de desglose de activos son exactamente lo que se necesita.
    -   **Sugerencia Menor:** Para el "Gráfico de Distribución del Portafolio (Opcional v1.0)", si el espacio es un factor, podríamos hacerlo un componente que se pueda mostrar/ocultar, o una visualización más pequeña y concisa inicialmente. Pero si es factible para v1.0, añade mucho valor. La ordenación de la tabla por columnas es una funcionalidad estándar que debemos incluir.
-   **Zona 3: Inteligencia de Mercado y Gráficos (Panel Principal Derecho o Central)**
    
    -   **Validación:** La división en Pestaña/Sección para Gráficos Financieros y Lista de Seguimiento es una excelente manera de organizar esta información densa. Los detalles para los selectores de par, intervalo y los controles del gráfico son muy acertados. La vinculación de la lista de seguimiento al gráfico principal es una gran mejora para la UX.
    -   **Sugerencia Menor:** Para los "Controles del Gráfico" en v1.0, nos aseguraremos de que los más comunes (ej. selección de intervalo, tipo de vela) sean de fácil acceso. Indicadores más avanzados (más allá de 1-2 Medias Móviles, RSI o MACD básicos) o herramientas de dibujo complejas podrían quedar para una v2.0 para no sobrecargar la interfaz inicialmente.
-   **Zona 4: Notificaciones y Actividad Reciente (Panel Inferior o Lateral Secundario)**
    
    -   **Validación:** Una zona de notificaciones y actividad bien definida es crucial. La lista de notificaciones con iconos de prioridad/tipo, timestamp, y mensaje corto es ideal. Los filtros opcionales y las acciones por notificación son muy buenas ideas.
    -   **Sugerencia Menor:** La pestaña de "Actividad Reciente del Bot" es una excelente adición para la transparencia y para que el usuario entienda lo que el sistema está haciendo. Deberíamos priorizarla si es posible para v1.0.

**Consideraciones Adicionales para el Dashboard:**

-   **Responsividad del Layout (QSplitter):** Tu sugerencia de usar `QSplitter` es excelente y la adoptaremos. Permitirá al usuario personalizar el espacio de cada zona, lo cual es muy valioso en aplicaciones con mucha información.
-   **Actualizaciones en Tiempo Real y Rendimiento:** Son consideraciones técnicas clave que informarán la implementación, como bien señalas.

**Esquema de Bloques del Dashboard Principal:**

**(A) BARRA SUPERIOR HORIZONTAL (Ancho completo, altura fija reducida)** * **Zona 1: Barra de Estado y Métricas Globales** * **[Bloque 1.1 - Izquierda/Centro] Indicadores de Estado:** * Texto/Icono: "Estado del Bot: `ACTIVO`/`PAUSADO`/`ERROR`" * Texto: "Modo Actual: `REAL`/`PAPER`" * Iconos de Conectividad: Binance API (`OK`✅/`Error`❌), Gemini API (`OK`✅/`Error`❌), MCPs (`Activos: 2/3` o similar) * **[Bloque 1.2 - Derecha] Métricas Globales (Real):** * Etiqueta y Valor: "P&L Hoy (Real): `+$120.50 (1.5%)`" * Etiqueta y Valor: "Portafolio Total (Real): `$8,120.50`" * **[Bloque 1.3 - Extremo Derecho, Opcional] Controles Rápidos:** * Botón (Toggle): "Motor: `Pausar`/`Reanudar`"

**(B) ÁREA DE CONTENIDO PRINCIPAL (Debajo de la Barra Superior, dividida verticalmente por un `QSplitter`)**

```
* **(B1) PANEL IZQUIERDO PRINCIPAL (Altura completa del área de contenido, ancho ajustable)**
    * **Zona 2: Estado del Portafolio**
        * **[Bloque 2.1 - Superior] Selector de Cuenta:**
            * Pestañas Horizontales: `Cuenta Real` | `Cuenta Paper` (la pestaña activa determina los datos mostrados abajo)
        * **[Bloque 2.2] Resumen de Cuenta Seleccionada (según pestaña activa):**
            * Tarjeta/Etiqueta: "Valor Total Cuenta: `[Valor]`" (ej. `PortfolioSnapshot.totalPortfolioValue`)
            * Tarjeta/Etiqueta: "Efectivo Disponible: `[Valor]`" (ej. `PortfolioSnapshot.totalCashBalance`)
            * Tarjeta/Etiqueta: "Valor en Activos: `[Valor]`" (ej. `PortfolioSnapshot.totalSpotAssetsValue`)
            * Tarjeta/Etiqueta: "P&L Acumulado: `[Valor]` (`[Porcentaje]%` )" (ej. `PortfolioSnapshot.cumulativePnl`, `cumulativePnlPercentage`)
            * Tarjeta/Etiqueta: "P&L Hoy (Cuenta Sel.): `[Valor]`"
        * **[Bloque 2.3] Desglose de Activos en Tenencia (para cuenta seleccionada):**
            * Tabla/Grid (interactiva, ordenable):
                * Columnas: Símbolo, Cantidad, Precio Prom. Compra, Precio Actual Mercado, Valor Actual (Moneda Cotiz.), P&L No Realizado (Absoluto, %), % Portafolio. (Basado en `AssetHolding`)
        * **[Bloque 2.4 - Opcional v1.0, Inferior del Panel Izquierdo] Gráfico de Distribución del Portafolio:**
            * Gráfico de Torta (Pie Chart) o Barras mostrando distribución porcentual de activos.

* **(B2) PANEL DERECHO PRINCIPAL (Altura completa del área de contenido, ancho ajustable)**
    * **Zona 3: Inteligencia de Mercado y Gráficos**
        * **[Bloque 3.1 - Superior] Pestañas Internas:** `Gráficos Financieros` | `Lista de Seguimiento`
        * **Contenido de Pestaña "Gráficos Financieros":**
            * **[Bloque 3.1.1 - Área Principal] Visualización del Gráfico:**
                * Gráfico de Velas Japonesas y Volumen (ej. pyqtgraph).
            * **[Bloque 3.1.2 - Controles del Gráfico (dispuestos arriba o al lado del gráfico)]**
                * ComboBox/Búsqueda: Selector de Par (ej. BTC/USDT).
                * Botones/ComboBox: Selector de Intervalo (1m, 5m, 1h, etc.).
                * Grupo de Botones/Menú: Tipo de Gráfico, Indicadores (Medias Móviles, RSI, MACD - básicos para v1.0), Herramientas de Dibujo (simples).
            * **[Bloque 3.1.3 - Panel de Información del Par (adyacente o debajo de controles)]**
                * Texto: Precio Actual, Cambio 24h (%, abs), Volumen 24h, Máx/Mín 24h.
        * **Contenido de Pestaña "Lista de Seguimiento":**
            * **[Bloque 3.2.1] Tabla/Grid de Watchlist:**
                * Columnas: Símbolo, Último Precio, Cambio 24h (%), Volumen 24h, (Opcional) Sparkline.
                * Funcionalidad: Clic en un par actualiza el gráfico en la pestaña "Gráficos Financieros".

```

**(C) PANEL INFERIOR HORIZONTAL (Ancho completo, altura ajustable mediante `QSplitter` o fija)** * **Zona 4: Notificaciones y Actividad Reciente** * **[Bloque 4.1 - Superior] Pestañas Internas (Opcional, si se incluyen ambos apartados):** `Notificaciones` | `Actividad Reciente del Bot` * **Contenido de Pestaña "Notificaciones" (o contenido principal si no hay pestañas):** * **[Bloque 4.1.1] Indicador de No Leídas y Filtros (Opcional v1.0):** * Texto: "X Nuevas Notificaciones" * Botones/ComboBox: Filtro (Todas, Trades, Alertas IA, Sistema). * **[Bloque 4.1.2] Lista de Notificaciones:** * Lista desplazable/Tabla: Icono (tipo/prioridad), Timestamp, Mensaje corto. (Basado en `Notification entity`) * Fondo con color según prioridad. * **[Bloque 4.1.3 - Contextual] Detalles/Acciones de Notificación Seleccionada:** * Al seleccionar: mostrar mensaje completo. * Botones: "Ver Trade Relacionado", "Marcar como Leída", "Descartar". * **Contenido de Pestaña "Actividad Reciente del Bot" (Opcional v1.0):** * **[Bloque 4.2.1] Log Simplificado:** * Lista de acciones importantes del bot (ej. "Estrategia X activada...", "Análisis IA iniciado...").


## Gestión de Conexiones y Credenciales

**Wireframe Textual / Esquema de Bloques: Pantalla de Gestión de Conexiones y Credenciales**

**Título de la Pantalla:** Gestión de Conexiones y Credenciales

**Layout General:**

-   La pantalla estará accesible desde la **Barra Lateral de Navegación Principal (Sidebar)** bajo "Configuración" -> "Gestión de Conexiones y Credenciales".
-   Se propone un layout de **dos paneles verticales**, ajustables mediante un `QSplitter`:
    -   **Panel Izquierdo:** Lista de todos los servicios integrables.
    -   **Panel Derecho:** Formulario/Detalles para el servicio seleccionado en el panel izquierdo.

----------

**(A) PANEL IZQUIERDO: LISTA DE SERVICIOS INTEGRABLES**

-   **Título del Panel:** "Servicios Conectables"
-   **Estructura:** Lista vertical desplazable.
-   **Cada ítem de la lista representará un servicio (ej. Binance, Telegram, Gemini, Mobula, MCPs definidos) y mostrará:**
    -   **[Bloque A.1] Icono del Servicio:** (Opcional, mejora visual) Un pequeño icono representativo del servicio.
    -   **[Bloque A.2] Nombre del Servicio:** Texto claro, ej. "Binance (Spot)", "Telegram (Notificaciones)", "Gemini AI (Análisis)", "Mobula (Datos de Activos)", "MCP: DoggyBee CCXT".
    -   **[Bloque A.3] Estado de Configuración:** Un indicador visual y textual:
        -   `Configurado ✔️`
        -   `Requiere Configuración ⚠️`
        -   `Error de Validación ❌`
    -   **[Bloque A.4] Etiqueta de Credencial (si configurado):** Pequeño texto con el `credentialLabel` definido por el usuario (ej. "Mi Cuenta Principal").
    -   **Funcionalidad:** Al hacer clic en un servicio de la lista, el panel derecho se actualizará para mostrar los detalles o el formulario de configuración de ese servicio.

**(B) PANEL DERECHO: DETALLE Y CONFIGURACIÓN DEL SERVICIO SELECCIONADO**

-   **Contenido dinámico** basado en el servicio seleccionado en el Panel Izquierdo y la acción deseada (Añadir, Editar).
    
-   **Caso 1: Usuario selecciona un servicio con estado `Requiere Configuración ⚠️` o elige "Añadir/Configurar":**
    
    -   **[Bloque B.1.1] Título:** "Configurar: `[Nombre del Servicio Seleccionado]`"
    -   **[Bloque B.1.2] Formulario de Configuración (campos varían según el servicio, basados en `APICredential` y `CreateOrUpdateApiCredentialRequest`):**
        -   Campo (Texto): "Etiqueta Descriptiva" (ej. `credentialLabel`, para que el usuario identifique esta conexión).
        -   Campo (Contraseña): "API Key".
        -   Campo (Contraseña, si aplica): "API Secret".
        -   Campo (Contraseña, si aplica): "API Passphrase" (ej. para algunos exchanges).
        -   Campos Adicionales (`otherDetails`, si el servicio lo requiere):
            -   Ej. para Telegram: Campo (Texto) "Chat ID".
            -   Ej. para MCP genérico: Campo (URL) "URL del Servidor MCP".
        -   Campo (Texto Multilínea, Opcional): "Notas".
    -   **[Bloque B.1.3] Acciones del Formulario:**
        -   Botón: "Probar Conexión y Guardar" (desactivado mientras se procesa).
            -   Al hacer clic: Muestra indicador de "Verificando..." (asíncrono).
            -   Tras la validación: Muestra mensaje de Éxito (detallando permisos si es Binance) o Error (detallado, ej. "Clave API inválida", "No se pudo conectar", "Permisos insuficientes").
            -   Si Éxito: Guarda credenciales (encriptadas por backend), actualiza estado en Panel Izquierdo a `Configurado ✔️`.
            -   Si Error: Permite al usuario corregir los datos y reintentar.
        -   Botón: "Cancelar".
-   **Caso 2: Usuario selecciona un servicio con estado `Configurado ✔️` o `Error de Validación ❌` y elige "Editar":**
    
    -   **[Bloque B.2.1] Título:** "Editar Configuración: `[Nombre del Servicio Seleccionado] - [Etiqueta Credencial]`"
    -   **[Bloque B.2.2] Formulario de Edición:** Similar al formulario de "Añadir", pero podría pre-rellenar la "Etiqueta Descriptiva" y "Notas". Los campos de secretos (API Key, Secret) estarán vacíos para que el usuario los ingrese nuevamente si desea cambiarlos. Se indicará que ingresar nuevos secretos sobrescribirá los anteriores.
    -   **[Bloque B.2.3] Acciones del Formulario:**
        -   Botón: "Probar Nueva Conexión y Guardar Cambios".
        -   Botón: "Cancelar".
        -   Botón (separado o en otra área): "Eliminar Configuración" (con diálogo de confirmación).
-   **Caso 3: Usuario selecciona un servicio `Configurado ✔️` (solo para ver, antes de "Editar"):**
    
    -   **[Bloque B.3.1] Título:** "Detalles de Conexión: `[Nombre del Servicio Seleccionado] - [Etiqueta Credencial]`"
    -   **[Bloque B.3.2] Información Visible (no sensible):**
        -   Nombre del Servicio.
        -   Etiqueta Descriptiva.
        -   Estado Actual: `Configurado ✔️` (o `Error de Validación ❌` si fue el último estado).
        -   Fecha de Última Verificación Exitosa (si aplica y se almacena).
        -   Notas.
    -   **[Bloque B.3.3] Acciones Disponibles:**
        -   Botón: "Editar Credenciales".
        -   Botón: "Eliminar Credenciales" (con diálogo de confirmación).
        -   Botón: "Probar Conexión Nuevamente" (para re-validar).

## Gestión de Estrategias de Trading"

**Acceso y Visualización General de Estrategias (Panel de Gestión de Estrategias):**

-   **Información Adicional en la Lista de Estrategias:**
    -   Sí, añadiremos columnas/información visible para: **ID de Configuración/Versión**, un resumen de **Pares Aplicables** (ej. "BTC/USDT, ETH/USDT" o "Múltiples"), y **Fecha de Última Modificación**.
-   **Widgets/Componentes Mejorados:**
    -   **Búsqueda y Filtros:** Implementaremos una **barra de búsqueda** (por nombre de configuración) y **filtros** (por tipo de estrategia base, estado de activación Paper/Real) para gestionar la lista eficazmente.
    -   **Acciones por Estrategia:** Junto a "Editar", se incluirán acciones claras (probablemente en un menú contextual o con iconos) para **"Duplicar/Clonar"**, **"Eliminar"** (con diálogo de confirmación robusto), y **"Ver Detalles/Desempeño Avanzado"** (que llevaría a una vista más profunda).
    -   **Creación de Estrategias:** El botón **"Crear Nueva Configuración de Estrategia"** será prominente. La idea de "Crear desde Plantilla" es excelente y, aunque el modelo de datos `TradingStrategyConfig.sharingMetadata.isTemplate` lo prevé, la funcionalidad de plantillas predefinidas o compartidas podría ser una mejora para v1.1 para mantener la simplicidad inicial de v1.0.

**2. Creación o Edición de una Configuración de Estrategia (Formulario/Vista):**

-   **Selección de Tipo de Estrategia Base:** Confirmado, la sección de **"Parámetros Específicos" se actualizará dinámicamente** al seleccionar un tipo de estrategia, mostrando solo los campos relevantes.
-   **Parámetros Específicos de la Estrategia:**
    -   **Validación en Tiempo Real/Desenfoque:** Se implementará para campos numéricos y otros que lo requieran, con feedback inmediato.
    -   **Tooltips/Ayudas:** ¡Fundamental! Cada parámetro tendrá un **icono de ayuda (?) con una descripción clara** de su propósito, rango esperado y formato.
-   **Arbitraje Simple - Selección de Credenciales:** Totalmente de acuerdo. Los campos para "Exchange A Credential Label" y "Exchange B Credential Label" serán **desplegables poblados con las credenciales de exchange relevantes** ya configuradas por el usuario (filtradas desde el `CredentialManager`).
-   **Configuración de Integración IA:** Excelente sugerencia. En lugar de campos libres, habrá un **selector para "Perfil de Análisis IA Aplicable"**, que se llenará con los perfiles definidos en `UserConfiguration.aiStrategyConfigurations`. Se mostrará un resumen del perfil seleccionado.
-   **Reglas de Aplicabilidad (`TradingStrategyConfig.applicabilityRules`):**
    -   Para "pares de monedas", utilizaremos un **selector múltiple o un campo de "tags"** fácil de usar.
    -   Para "condiciones de mercado", la v1.0 se centrará en la selección de **watchlists aplicables** (`applicabilityRules.dynamicFilter.includedWatchlistIds`).
-   **Parámetros de Riesgo Específicos (`TradingStrategyConfig.riskParametersOverride`):** Se indicará claramente que estos parámetros **sobrescriben la configuración de riesgo global**, y se mostrarán los valores globales como referencia.
-   **Botón "Guardar Configuración":**
    -   La validación del backend (`StrategyManager`) será exhaustiva.
    -   Los mensajes de error serán específicos por campo.
    -   Añadiremos un botón secundario como **"Guardar y Activar en Paper Trading"** para agilizar el flujo.

**3. Activación / Desactivación de una Configuración de Estrategia:**

-   **Controles:** Los interruptores (toggles) en la lista son la opción preferida.
-   **Pre-condiciones para Activación (Modo Real):** ¡Crítico! Antes de activar en Modo Real, el sistema **verificará automáticamente**:
    -   Validez y permisos de credenciales necesarias (Binance, etc., vía `CredentialManager`).
    -   Cumplimiento de límites de riesgo globales y de capital.
    -   Requisitos específicos de la estrategia (ej. dos exchanges válidos para arbitraje).
    -   Si no se cumplen, el interruptor de Modo Real estará **deshabilitado o mostrará un mensaje claro** con los requisitos faltantes al intentar la activación.
-   **Confirmación Adicional para Modo Real:** Implementaremos un **diálogo de confirmación adicional y explícito** antes de activar cualquier estrategia en Modo Real.
-   **Interacción con `TradingEngine`:** Confirmado, el `StrategyManager` notificará al `TradingEngine` para cargar/descargar la estrategia.

**4. Monitoreo Básico del Desempeño de una Estrategia:**

-   **Visualización de Métricas (`TradingStrategyConfig.performanceMetrics`):** La distinción Paper vs. Real será muy clara.
-   **Información Adicional:** Para v1.0, nos centraremos en: Número de operaciones, P&L Total, Win Rate. El Riesgo/Beneficio Promedio y el Drawdown Máximo son excelentes candidatos para v1.1.
-   **Acceso a Detalles:** Desde la lista de estrategias, un clic permitirá **navegar a una vista más detallada del desempeño de esa configuración**, incluyendo una lista/tabla de sus trades individuales.
-   **Actualización de Métricas:** El sistema (`TradingEngine` o `PortfolioManager`) actualizará las `performanceMetrics` de la `TradingStrategyConfig` dinámicamente al cerrar trades.

**5. Posibles Casos de Error / Alternativas (Ampliación):**

-   **Problemas de Concurrencia al Modificar Estrategias Activas:** Para v1.0, adoptaremos la **Opción A (Más Simple): No permitir la edición de parámetros operativos críticos de una estrategia mientras esté activa.** El usuario deberá desactivarla primero. El versionado (Opción B) es una mejora ideal para v1.1+, y el modelo de datos (`TradingStrategyConfig.version`, `parentConfigId`) ya lo contempla.
-   **Límites de Recursos del Sistema Excedidos:** Para v1.0, implementaremos un **límite configurable simple en el número máximo de estrategias activas simultáneamente**.
-   **Errores de Comunicación con APIs Externas durante Configuración (ej. validación de creds para Arbitraje):** Se permitirá **guardar la configuración en un estado "pendiente de verificación"**, pero no se podrá activar en Modo Real hasta que la verificación sea exitosa.

**Otras Mejoras Adicionales (Mi "Experticia"):**

1.  **Flujo de "Duplicar/Clonar Estrategia":** Al duplicar, se pre-rellenará el formulario de creación con los datos de la estrategia original, añadiendo "- Copia" al nombre, y se pedirá al usuario que lo revise y modifique.
2.  **Wizard para Crear Primera Estrategia:** Consideraremos un mini-asistente para guiar la creación de la primera configuración de estrategia, explicando brevemente las secciones de parámetros.
3.  **Feedback Visual en Acciones:** Además de mensajes, usaremos breves resaltados o animaciones sutiles para confirmar acciones como guardar o activar/desactivar.
4.  **Ordenación en Lista de Estrategias:** Permitiremos ordenar la lista de configuraciones (por nombre, P&L, última modificación).
5.  **Consistencia de Botones:** Aseguraremos etiquetas de botones consistentes en toda la aplicación

#### Diagrama Mermaid Gestión de Estrategias de Trading

graph TD
    A[Usuario en Aplicación] --> B[Clic en 'Estrategias' en Sidebar];
    B --> C{Panel de Gestión de Estrategias};
    C --> C_List[Lista de Configuraciones de Estrategias (con Nombre, Tipo, Estado Paper/Real, Últ. Mod., Pares Aplicables)];
    C --> C_Controls[Controles Panel: Barra de Búsqueda, Filtros];
    C --> C_NewStrat[Botón: 'Crear Nueva Configuración de Estrategia'];

    C_NewStrat --> D_FormCreateMode[Formulario Configuración Estrategia (Modo Creación)];
    
    subgraph D_FormCreateMode [Formulario Configuración Estrategia]
        D_InputName[Nombre Configuración]
        D_SelectBaseType[Selector: Tipo Estrategia Base (actualiza params dinámicamente)]
        D_ParamsSpecific[Parámetros Específicos (con tooltips ?, validación en vivo)]
        D_ParamsArbitrageCreds[Si Arbitraje: Selectores Credenciales Exchange A/B (de CredMan)]
        D_SelectAIProfile[Selector: Perfil Análisis IA Aplicable (de UserConfig)]
        D_Applicability[Reglas Aplicabilidad (pares con multi-selector/tags, watchlists)]
        D_RiskOverride[Parámetros Riesgo Específicos (mostrar defaults globales)]
        D_Buttons[Botones: 'Guardar', 'Guardar y Activar (Paper)', 'Cancelar']
    end

    D_Buttons -- Guardar o Guardar y Activar --> D_ValidateSave[Validación Backend y Guardado];
    D_ValidateSave -- Éxito --> C_List_Updated_After_Create[Lista Actualizada];
    D_ValidateSave -- Error --> D_ErrorFeedback[Feedback Específico Error en Formulario];
    D_ErrorFeedback --> D_FormCreateMode;
    C_List_Updated_After_Create --> C;
    D_Buttons -- Cancelar --> C;

    C_List -- Clic en Estrategia Existente --> E_ContextMenuOrActions[Mostrar Acciones para Estrategia Seleccionada];
    
    E_ContextMenuOrActions -- Editar Configuración --> F_FormEditMode[Formulario Configuración Estrategia (Modo Edición, pre-llenado)];
    subgraph F_FormEditMode [Formulario Configuración Estrategia (Editar)]
        F_ConcurrencyCheck{¿Estrategia Activa?}
        F_ConcurrencyCheck -- Sí (v1.0) --> F_WarnEditActive[Aviso: Desactivar para editar parámetros críticos / Solo editar no críticos] --> F_InputsPreFilled[Inputs Pre-llenados, Nombre, Tipo (no editable o con aviso), etc.]
        F_ConcurrencyCheck -- No --> F_InputsPreFilled
        %% F_ConcurrencyCheck -- Sí (v1.1+) --> F_NewVersion[Opción: Crear Nueva Versión] --> D_FormCreateMode_PreFilled_NewVersion
        F_InputsPreFilled --> F_Buttons[Botones: 'Guardar Cambios', 'Cancelar']
    end
    F_Buttons -- Guardar Cambios --> F_ValidateSave[Validación Backend y Guardado];
    F_ValidateSave -- Éxito --> C_List_Updated_After_Edit[Lista Actualizada];
    F_ValidateSave -- Error --> F_ErrorFeedback[Feedback Específico Error en Formulario];
    F_ErrorFeedback --> F_FormEditMode;
    C_List_Updated_After_Edit --> C;
    F_Buttons -- Cancelar --> C;

    E_ContextMenuOrActions -- Activar/Desactivar Modo Paper --> G_TogglePaper[Toggle Modo Paper];
    G_TogglePaper --> G_UpdateStatusPaper[Actualizar Estado Paper. Feedback UI.];
    G_UpdateStatusPaper --> C_List_Updated_After_ToggleP[Lista Actualizada];
    C_List_Updated_After_ToggleP --> C;

    E_ContextMenuOrActions -- Activar/Desactivar Modo Real --> H_ToggleReal[Toggle Modo Real];
    H_ToggleReal -- Intento Activar --> H_PreChecks{Pre-condiciones Modo Real OK? (Creds, Riesgo, etc.)};
    H_PreChecks -- No --> H_FeedbackPreFail[Feedback: Requisitos Faltantes. No se activa.];
    H_FeedbackPreFail --> C_List_Updated_After_ToggleRFail[Lista Actualizada];
    C_List_Updated_After_ToggleRFail --> C;
    H_PreChecks -- Sí --> H_ConfirmDialog[Diálogo Confirmación Adicional: 'Activar en REAL?'];
    H_ConfirmDialog -- Sí --> H_UpdateStatusReal[Actualizar Estado Real. Notificar TradingEngine. Feedback UI.];
    H_ConfirmDialog -- No --> C_List_Updated_After_ToggleRCancel[Lista Actualizada];
    C_List_Updated_After_ToggleRCancel --> C;
    H_UpdateStatusReal --> C_List_Updated_After_ToggleR[Lista Actualizada];
    C_List_Updated_After_ToggleR --> C;
    H_ToggleReal -- Intento Desactivar --> H_UpdateStatusReal; %% Desactivar no necesita tantas pre-condiciones

    E_ContextMenuOrActions -- Ver Detalles/Desempeño --> I_DetailView[Pantalla Detalle y Desempeño Estrategia];
    subgraph I_DetailView [Detalle y Desempeño de Estrategia]
        I_ConfigParams[Parámetros Configuración (Read-Only)]
        I_PerfMetrics[Métricas Desempeño Detalladas (Paper/Real, WinRate, P&L, Trades, etc.)]
        I_TradeList[Lista/Tabla de Trades ejecutados por esta Configuración]
        I_BackToList[Botón: 'Volver a Lista de Estrategias']
    end
    I_BackToList --> C;

    E_ContextMenuOrActions -- Duplicar/Clonar --> J_FormDuplicateMode[Formulario Configuración Estrategia (Modo Creación, pre-llenado, nombre con '- Copia')];
    J_FormDuplicateMode --> D_Buttons; %% Reutiliza el flujo de creación/guardado

    E_ContextMenuOrActions -- Eliminar --> K_DeleteConfirm[Diálogo Confirmación: 'Eliminar Estrategia?'];
    K_DeleteConfirm -- Sí --> K_DeleteExec[Eliminar Estrategia. Feedback.];
    K_DeleteConfirm -- No --> C;
    K_DeleteExec --> C_List_Updated_After_Delete[Lista Actualizada];
    C_List_Updated_After_Delete --> C;

### Referencia de Guía de Estilo y Branding

### Paleta de Colores (Color Palette)

### Paleta de Colores (Color Palette)

-   **Tema Principal:** Oscuro.
    -   **Fondos Principales:**
        -   `#252526` (Gris oscuro profundo para el fondo más general).
        -   `#1E1E1E` (Gris aún más oscuro para áreas secundarias/contenedores).
        -   `#2D2D2D` (Gris oscuro ligeramente más claro para barras laterales, cabeceras, modales).
    -   **Texto Principal y Secundario:**
        -   `#E0E0E0` (Blanco hueso/Gris muy claro para texto principal).
        -   `#A0A0A0` (Gris medio para texto secundario/etiquetas).
-   **Color Primario/Acento Principal (Azul Oscuro Tecnológico):**
    -   Optaremos por: `#0D6EFD` (Un azul moderno y enérgico que ofrecerá buen contraste y es ampliamente reconocido por su claridad).
-   **Colores de Feedback/Semántica:**
    -   **Éxito:** `#28A745` (Verde).
    -   **Error/Alerta Crítica:** `#DC3545` (Rojo).
    -   **Advertencia:** `#FFC107` (Amarillo ámbar).
    -   **Información:** `#0DCAF0` (Un cian claro y limpio, que complementa bien el azul de acento principal).
-   **Colores para Gráficos:**
    -   Líneas/Velas Ascendentes: `#28A745` (Éxito) o una variante más clara del acento como `#589BFF`.
    -   Líneas/Velas Descendentes: `#DC3545` (Error) o un naranja como `#FD7E14`.
    -   Indicadores (Medias Móviles, etc.): Se utilizará una paleta secundaria que contraste bien, como: `#6F42C1` (Violeta), `#20C997` (Turquesa), `#E83E8C` (Magenta Rosado).
-   **Bordes y Separadores:**
    -   `#444444` (Un gris medio oscuro para sutiles separaciones).

### 2. Tipografía (Typography)

-   **Familia Principal:** Optaremos por una fuente Sans-Serif moderna, limpia y altamente legible, ideal para interfaces de usuario y visualización de datos.
    -   **Sugerencia:** "Roboto" o "Open Sans". Estas fuentes son estándar, ofrecen una amplia variedad de pesos y están diseñadas para la legibilidad en pantalla. Para PyQt5, aseguraríamos que la fuente seleccionada esté disponible o se empaquete con la aplicación. Si no, nos basaremos en fuentes Sans-Serif genéricas de alta calidad que Qt pueda renderizar bien (como "Noto Sans" o "DejaVu Sans" que suelen estar disponibles en muchos sistemas).
    -   **Fallback:** `Arial`, `Helvetica`, `sans-serif`.
-   **Tamaños y Pesos:**
    -   **Títulos Principales (H1):** 24px - Peso: Bold (700)
    -   **Subtítulos (H2):** 20px - Peso: Semibold (600)
    -   **Títulos de Sección (H3):** 18px - Peso: Medium (500)
    -   **Texto del Cuerpo Principal:** 14px - Peso: Regular (400)
    -   **Texto Secundario/Etiquetas:** 12px - Peso: Regular (400)
    -   **Botones:** 14px - Peso: Medium (500)
    -   _(Los tamaños en `px` son una referencia para el diseño; PyQt5 maneja los tamaños de fuente de manera que puede ser ligeramente diferente, pero la jerarquía y pesos relativos son la clave)._

### 3. Iconografía (Iconography)

-   **Estilo:** Iconos limpios, modernos y fácilmente reconocibles, consistentes con el tema oscuro. Se preferirán iconos de estilo "outline" o "filled" sutiles.
-   **Biblioteca Sugerida:**
    -   **FontAwesome:** Es una biblioteca muy completa y ampliamente utilizada. Existen integraciones o formas de usar sus iconos en aplicaciones Qt.
    -   **Material Design Icons:** Otra excelente opción, con una gran variedad y un estilo que se adapta bien.
    -   **SVG Personalizados:** Para iconos muy específicos, se pueden crear SVGs. PyQt5 tiene buen soporte para SVG.
-   **Uso:** Los iconos se usarán para mejorar la comprensión visual en botones, elementos de navegación, indicadores de estado y junto a etiquetas informativas. Deben tener un color que contraste bien con el fondo, usualmente el color del texto o el color de acento para acciones.

### 4. Espaciado y Cuadrícula (Spacing & Grid)

-   **Unidad Base de Espaciado:** Se recomienda un sistema de espaciado basado en múltiplos de una unidad base (ej. 8px). Esto significa que los márgenes, paddings y el espacio entre elementos serían 8px, 16px, 24px, 32px, etc. Esto ayuda a mantener la consistencia visual.
-   **Cuadrícula (Grid):** Aunque una cuadrícula estricta de 12 columnas como en la web puede no aplicarse directamente de la misma manera en PyQt5, el principio de alinear elementos de forma coherente y mantener un ritmo visual es importante.
    -   Los layouts se diseñarán con una alineación lógica y consistente.
    -   Se utilizarán `QSplitter` y layouts de Qt (QVBoxLayout, QHBoxLayout, QGridLayout) para organizar los elementos de manera flexible y adaptable.
-   **Márgenes y Paddings Generales:**
    -   Contenedores principales: Padding generoso (ej. 16px o 24px).
    -   Espacio entre elementos agrupados: Espacio moderado (ej. 8px o 12px).
    -   Espacio entre texto y borde de botón: Consistente (ej. 8px vertical, 12px horizontal).


## "Requisitos de Accesibilidad (AX)" (Accessibility (AX) Requirements).

-   **Objetivo de Conformidad (Target Compliance):**
    -   Aspiraremos a cumplir con las directrices de **WCAG 2.1 Nivel AA** donde sea aplicable y factible dentro del contexto de una aplicación de escritorio PyQt5. Esto proporciona un estándar reconocido internacionalmente.
-   **Requisitos Específicos:**
    1.  **Navegación por Teclado:**
        -   Todos los elementos interactivos (botones, campos de entrada, pestañas, elementos de menú, etc.) deben ser completamente accesibles y operables utilizando únicamente el teclado.
        -   El orden de tabulación debe ser lógico y predecible, siguiendo el flujo visual de la interfaz.
        -   Los componentes personalizados (si los creamos) deben implementar patrones de interacción de teclado apropiados (ej. teclas de flecha para listas o grupos de opciones).
    2.  **Contraste de Color:**
        -   Se asegurará que el texto y los elementos gráficos importantes cumplan con los ratios de contraste mínimos especificados por WCAG AA (generalmente 4.5:1 para texto normal y 3:1 para texto grande o elementos gráficos). Nuestra paleta de tema oscuro ya busca esto, pero lo verificaremos.
    3.  **Etiquetas y Descripciones:**
        -   Todos los controles de la interfaz (campos de formulario, botones) deben tener etiquetas textuales claras y asociadas programáticamente.
        -   Los iconos que transmitan información o acción deben tener alternativas textuales (ej. tooltips) si su significado no es obvio solo con el icono.
    4.  **Tamaño del Texto y Zoom:**
        -   El texto debe ser legible. Consideraremos que la aplicación respete las configuraciones del sistema operativo para el tamaño de fuente en la medida que PyQt5 lo permita, o bien, se evitarán tamaños de fuente excesivamente pequeños.
    5.  **Feedback Claro:**
        -   Las acciones del usuario y los cambios de estado del sistema deben ser comunicados de forma clara (visual y, si es posible, a través de otros medios si se implementaran alertas sonoras o similares para eventos críticos).
    6.  **Consistencia:**
        -   La navegación y la ubicación de los elementos comunes deben ser consistentes a lo largo de toda la aplicación.
    7.  **Uso de ARIA (si aplica para componentes web embebidos o customizados):**
        -   Aunque PyQt5 es una tecnología de escritorio, si se desarrollaran componentes muy personalizados que no mapean directamente a widgets estándar con buena accesibilidad nativa, se consideraría cómo Qt maneja la información de accesibilidad para exponerla a tecnologías asistivas. Para QML (si se usara) o si se embebiera contenido web, ARIA sería más relevante. Para v1.0 con widgets estándar de PyQt5, nos apoyaremos en la accesibilidad que estos ya proveen.


## Responsiveness" (Capacidad de Respuesta / Adaptabilidad).

Para una aplicación de escritorio como "UltiBotInversiones" desarrollada con PyQt5, el concepto de "responsiveness" es un poco diferente al de las aplicaciones web (donde pensamos en múltiples tamaños de pantalla como móviles, tablets y escritorios). Sin embargo, sigue siendo crucial que la interfaz sea usable y se vea bien en diferentes tamaños de ventana que el usuario pueda configurar en su escritorio, y potencialmente en diferentes resoluciones de pantalla.

Aquí te propongo cómo podríamos abordar esta sección:

### 7. Capacidad de Respuesta / Adaptabilidad (Responsiveness)

-   **Objetivo Principal:** La interfaz de "UltiBotInversiones" debe ser flexible y adaptarse de manera inteligente a los cambios en el tamaño de la ventana principal de la aplicación, asegurando que la información clave permanezca visible y accesible, y que el layout no se rompa.
-   **Estrategia de Adaptación General:**
    1.  **Layouts Fluidos:** Utilizaremos los gestores de layout de PyQt5 (como `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`, y especialmente `QSplitter`) para permitir que los elementos de la interfaz se expandan, contraigan o redistribuyan el espacio disponible de forma dinámica.
        
    2.  **Contenido Redimensionable:** Los elementos que muestran datos, como tablas y gráficos, deben permitir el redimensionamiento y, si es necesario, mostrar barras de desplazamiento cuando el contenido exceda el espacio visible.
    3.  **Priorización de Contenido:** Si el espacio se reduce significativamente, se considerará la posibilidad de ocultar información menos crítica o proporcionar formas de acceder a ella (ej. mediante botones de "más detalles" o tooltips más informativos), aunque para una aplicación de escritorio el objetivo principal es que todo lo esencial sea visible.
    4.  **Tamaños Mínimos de Ventana:** Se definirá un tamaño mínimo razonable para la ventana de la aplicación, por debajo del cual la usabilidad podría verse comprometida. El sistema podría impedir que la ventana se redimensione por debajo de este mínimo.
-   **Puntos de Consideración para Diferentes Tamaños (Breakpoints Conceptuales para Escritorio):**
    -   **Ventana Optimizada/Grande (Ej. >1600px de ancho):** Todo el contenido y paneles se muestran con amplitud. Los gráficos pueden mostrar más puntos de datos, las tablas más columnas sin scroll horizontal.
    -   **Ventana Mediana (Ej. ~1200px - 1600px de ancho):** Los `QSplitter` permiten al usuario ajustar el espacio, pero el layout principal se mantiene. Podría haber una ligera compactación de elementos si es necesario, o los gráficos podrían volverse un poco más pequeños por defecto.
    -   **Ventana Pequeña/Mínima (Ej. ~900px - 1200px de ancho):** Se debe asegurar que los controles críticos y la información esencial sigan siendo accesibles. Las tablas podrían necesitar scroll horizontal para todas sus columnas. Los paneles gestionados por `QSplitter` podrían tener tamaños mínimos más restrictivos.
-   **Consideraciones Específicas:**
    -   **Dashboard Principal:** Como ya discutimos, los `QSplitter` permitirán al usuario ajustar las zonas del dashboard (Portafolio, Inteligencia de Mercado, Notificaciones).
        
    -   **Diálogos y Ventanas Modales:** Deben tener un tamaño predeterminado razonable pero también ser redimensionables si contienen información variable, o bien, adaptarse al contenido que muestran.

## Change Log (Registro de Cambios)

Change	Date	Version	Description	Author
Creación Inicial del Documento de UI/UX Spec.	2025-05-28	0.1	Definición inicial de metas, IA, flujos, branding y accesibilidad.	Jane (Arquitecta de Diseño)




