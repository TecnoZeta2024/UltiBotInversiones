# CONTEXTO ACTIVO DEL SISTEMA
- **Última Actualización:** 2025-06-26 10:51 UTC
- **Agente Responsable:** Tejedor
- **Estado del Despliegue Backend:** local (uvicorn)
- **Observación Crítica:** Se ha completado una refactorización masiva de la arquitectura de comunicación entre el frontend (`ultibot_ui`) y el backend. El cambio fundamental resuelve problemas sistémicos de asincronía y simplifica drásticamente la mantenibilidad del código.

## Resumen de la Refactorización de Comunicación (TASK-UI-REFACTOR-001 & 002)
### Problema Resuelto:
- **Complejidad y Fragilidad:** El antiguo patrón `ApiWorker` actuaba como un intermediario opaco para las llamadas a la API, dificultando la depuración y el manejo de estados asíncronos.
- **Fallo de Operaciones Asíncronas:** La incorrecta gestión del bucle de eventos de asyncio impedía que los componentes de la UI realizaran tareas en segundo plano de forma fiable.

### La Nueva Arquitectura:
1.  **Eliminación del Anti-Patrón `ApiWorker`:** La clase `ApiWorker` ha sido completamente eliminada de la base de código de la UI.
2.  **Comunicación Directa y Asíncrona:** Todas las llamadas a la API desde la UI ahora se realizan directamente utilizando el singleton `UltiBotAPIClient`. Las corutinas de este cliente se ejecutan como tareas independientes y seguras a través de `asyncio.create_task(api_client.method(...))`.
3.  **Inyección de Dependencias Corregida:** El `main_event_loop` de `qasync` ahora se pasa explícitamente a todos los widgets y vistas desde `MainWindow`, garantizando que todos los componentes tengan acceso al bucle de eventos correcto para sus operaciones asíncronas.

### Estado Actual:
- La arquitectura de comunicación es ahora más simple, directa y robusta.
- Se alinea con las mejores prácticas de programación asíncrona en Python y PyQt.
- El siguiente paso es una validación funcional completa para asegurar que todos los componentes de la UI operan correctamente bajo el nuevo modelo.
