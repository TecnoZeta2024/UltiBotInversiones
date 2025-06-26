# Checklist de Validación de UI

## Vistas y Datos a Verificar:

- [ ] **Vista Principal (Dashboard):**
    - [ ] Verificar que se muestre el balance disponible (USDT).
    - [ ] Verificar que se muestre el valor total de los activos.
    - [ ] Verificar que se muestre el valor total del portafolio.
    - [ ] Verificar que la lista de activos esté vacía o muestre datos correctos si hay activos.
    - [ ] Verificar que el selector de modo de trading (Paper/Real) funcione correctamente y refleje el modo actual.

- [ ] **Vista de Estrategias:**
    - [ ] Verificar que se muestre la lista de estrategias configuradas.
    - [ ] Verificar que los botones de activar/desactivar estrategias funcionen.

- [ ] **Vista de Órdenes/Trades:**
    - [ ] Verificar que se muestre la lista de órdenes abiertas.
    - [ ] Verificar que se muestre el historial de paper trading.

- [ ] **Vista de Oportunidades de IA:**
    - [ ] Verificar que se muestren las oportunidades de IA.
    - [ ] Verificar que el botón de "Analizar con IA" funcione.
    - [ ] Verificar que el botón de "Confirmar Trade Real" funcione.

- [ ] **Vista de Notificaciones:**
    - [ ] Verificar que se muestre el historial de notificaciones.

## Instrucciones:
1. Inicia la aplicación UI localmente (ej. `poetry run python src/ultibot_ui/main.py`).
2. Una vez iniciada, el Tejedor usará el navegador para interactuar con ella y verificar visualmente cada punto del checklist.
