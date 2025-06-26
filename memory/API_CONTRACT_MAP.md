# Mapa de Contratos de API - Auditoría PACA

## Auditoría: GET /api/v1/tickers

| Componente Cliente | Método Invocado | Endpoint Esperado (Cliente) | Método HTTP | Discrepancy Log |
| :--- | :--- | :--- | :--- | :--- |
| `src/ultibot_ui/services/api_client.py` | `get_market_data` | `/api/v1/tickers` | `GET` | **DISCREPANCIA ENCONTRADA:** El router `market_data` se registra en `main.py` sin el prefijo `/api/v1`. La ruta real es `/tickers`, mientras que el cliente espera `/api/v1/tickers`. |
