# Tasklist: UltiBotInversiones

## [TASK-UI-REFACTOR-002] Refactorización Estratégica del Frontend

- [x] **Fase 1: Mapeo de Interacciones (Completada)**
  - [x] Buscar todas las invocaciones a `api_client` en `src/ultibot_ui/`.
  - [x] Crear `memory/API_CONTRACT_MAP.md` con los resultados.

- [x] **Fase 2: Auditoría y Verificación (Completada)**
  - [x] Iterar sobre cada entrada de `API_CONTRACT_MAP.md` y verificarla contra el código del backend.
  - [x] Auditar rutas, métodos HTTP y modelos de datos.
  - [x] Registrar todas las discrepancias encontradas en `API_CONTRACT_MAP.md`.

- [ ] **Fase 3: Generar Plan de Acción (En Progreso)**
  - [x] Sintetizar las discrepancias en un plan de refactorización.
  - [ ] **Crear un checklist detallado de correcciones en este archivo (Checklist de Refactorización de Contratos API):**

    **Backend (`src/ultibot_backend/`)**
    - [ ] **`endpoints/config.py`**:
      - [ ] Cambiar ruta de `GET /config` a `GET /config/user` para consistencia.
      - [ ] Cambiar ruta de `PATCH /config` a `PATCH /config/user` para consistencia.
      - [ ] Cambiar ruta de `POST /config/real-trading-mode/activate` a `POST /trading/mode/activate`.
      - [ ] Cambiar ruta de `POST /config/real-trading-mode/deactivate` a `POST /trading/mode/deactivate`.
    - [ ] **`endpoints/strategies.py`**:
      - [ ] Cambiar método de `PATCH` a `POST` para `/strategies/{strategy_id}/activate`.
      - [ ] Cambiar método de `PATCH` a `POST` para `/strategies/{strategy_id}/deactivate`.
    - [ ] **`endpoints/market_data.py`**:
      - [ ] Cambiar ruta de `GET /tickers` a `GET /data`.
      - [ ] Cambiar ruta de `GET /klines` a `GET /ohlcv`.
    - [ ] **`endpoints/opportunities.py`**:
      - [ ] Cambiar ruta de `GET /opportunities/real-trading-candidates` a `GET /opportunities/ai`.
      - [ ] Implementar endpoint `POST /opportunities/analyze`.
      - [ ] Implementar endpoint `POST /opportunities/{id}/confirm`.
    - [ ] **`endpoints/trades.py`**:
      - [ ] Modificar `get_user_trades` para que no acepte `user_id` como parámetro de consulta, y asegurar que el frontend no lo envíe.

    **Frontend (`src/ultibot_ui/`)**
    - [ ] **`services/api_client.py` (o donde se definan las llamadas)**:
      - [ ] Asegurar que todas las llamadas a los endpoints modificados reflejen las nuevas rutas y métodos HTTP.
      - [ ] Eliminar el envío del parámetro `user_id` en la función `get_trades`.

- [ ] **Fase 4: Ejecución y Validación (Pendiente)**
  - [ ] Implementar las correcciones del checklist del backend.
  - [ ] Implementar las correcciones del checklist del frontend.
  - [ ] Escribir/actualizar tests de integración para cada endpoint modificado para validar los contratos.
  - [ ] Ejecutar la UI y verificar que todas las funcionalidades auditadas operan correctamente sin errores de comunicación.
