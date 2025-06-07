import asyncio
import sys
import uvicorn
from uvicorn.config import LOGGING_CONFIG

if __name__ == "__main__":
    # Aplicar la política de eventos de Windows de forma incondicional al inicio.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        print("WindowsSelectorEventLoopPolicy aplicada.")

    # Modificar la configuración de logging de Uvicorn para asegurar la visibilidad de los logs de acceso
    log_config = LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = '%(asctime)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
    
    # Iniciar el servidor Uvicorn apuntando a la aplicación FastAPI.
    uvicorn.run(
        "src.ultibot_backend.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_config=log_config
    )
