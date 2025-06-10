import uvicorn
import os
import sys
import asyncio

# Solución para Windows ProactorEventLoop con psycopg/asyncio
# Debe ejecutarse ANTES de que cualquier otra cosa de asyncio se importe o configure.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def main():
    """
    Punto de entrada para lanzar el backend usando uvicorn.
    Esto asegura que la aplicación se ejecute como un módulo,
    lo que resuelve los problemas de importación en un src-layout.
    """
    # Obtener el host y el puerto de las variables de entorno si están disponibles,
    # de lo contrario, usar valores predeterminados.
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    print(f"Iniciando servidor Uvicorn en {host}:{port}")
    
    uvicorn.run(
        "src.ultibot_backend.main:app",
        host=host,
        port=port,
        reload=False
    )

if __name__ == "__main__":
    main()
