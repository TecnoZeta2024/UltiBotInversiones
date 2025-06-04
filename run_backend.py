import asyncio
import uvicorn
import os

if os.name == 'nt': # Solo para Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    # Configuración de logging para Uvicorn (opcional, pero puede ayudar a depurar)
    # Si se define log_config=None, Uvicorn usa su propia configuración por defecto
    # que debería respetar el logger raíz si está configurado.
    # Para más control, se podría pasar un diccionario de configuración de logging.
    # Por ahora, dejaremos que use la configuración del logger raíz que ya tenemos.
    # Sin embargo, podemos forzar un nivel de log para Uvicorn si es necesario.
    uvicorn.run(
        "src.ultibot_backend.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info"  # Asegura que Uvicorn loguee al menos a nivel INFO
    )
