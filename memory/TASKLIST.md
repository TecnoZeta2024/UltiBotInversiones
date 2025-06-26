# TASKLIST: Estabilización del Flujo de Paper Trading

## Fase 1: Reparación de la Capa de Persistencia y API

- [ ] **TASK-1.1: Corregir el `upsert_all` para `MarketDataORM`**
    - [ ] **Análisis:** Investigar `persistence_service.py` para entender por qué `MarketDataORM` no es un tipo soportado.
    - [ ] **Hipótesis:** Probablemente, el diccionario de mapeo de modelos (`MODEL_TO_TABLE_MAP`) no incluye `MarketDataORM`.
    - [ ] **Acción:** Añadir `MarketDataORM` al `MODEL_TO_TABLE_MAP` en `persistence_service.py`.
    - [ ] **Validación:** Reiniciar el backend y verificar que el error `Tipo de modelo no soportado` desaparece de `logs/backend.log`.

- [ ] **TASK-1.2: Corregir Rutas de API (404 Not Found)**
    - [ ] **Análisis:** El log muestra 404 para `/api/v1/market/data` y `/api/v1/notifications`.
    - [ ] **Acción (`/market/data`):** Inspeccionar `market_data.py` en los endpoints de la API para encontrar la ruta correcta (probablemente `/tickers`) y corregir la llamada en `api_client.py`.
    - [ ] **Acción (`/notifications`):** Inspeccionar `notifications.py` en los endpoints de la API para encontrar la ruta correcta (probablemente `/history`) y corregir la llamada en `api_client.py`.
    - [ ] **Validación:** Reiniciar el sistema y verificar que los errores 404 desaparecen de `logs/backend.log`.

## Fase 2: Creación y Ejecución del Test de Sistema E2E

- [ ] **TASK-2.1: Crear el Archivo de Test del Sistema**
    - [ ] **Acción:** Crear un nuevo archivo `tests/system/test_e2e_paper_trading_workflow.py`.

- [ ] **TASK-2.2: Implementar el Test E2E**
    - [ ] **Acción:** Escribir un test `pytest` que utilice el `api_client` para:
        1.  Verificar que el modo de trading es "paper".
        2.  Llamar al endpoint de oportunidades de IA (`/gemini/opportunities`).
        3.  Filtrar oportunidades con `ai_confidence` > 0.5.
        4.  Tomar la primera oportunidad válida y extraer los datos necesarios (símbolo, lado, etc.).
        5.  Ejecutar una orden de mercado (`execute_market_order`) con los datos de la oportunidad.
        6.  Verificar que la respuesta de la orden es exitosa (código 200).
        7.  Repetir el proceso 5 veces.

- [ ] **TASK-2.3: Ejecutar y Validar el Test**
    - [ ] **Acción:** Ejecutar `pytest tests/system/test_e2e_paper_trading_workflow.py`.
    - [ ] **Validación:** El test debe pasar, confirmando que el flujo completo es funcional y cumpliendo el criterio de éxito.