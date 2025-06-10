import uvicorn
import os

def main():
    """
    Punto de entrada para lanzar el backend usando uvicorn.
    Esto asegura que la aplicación se ejecute como un módulo,
    lo que resuelve los problemas de importación en un src-layout.
    """
    # Eliminar la manipulación de sys.path de main.py si aún existe, ya no es necesaria.
    # La ejecución con 'python -m' se encarga de esto.
    
    # Obtener el host y el puerto de las variables de entorno si están disponibles,
    # de lo contrario, usar valores predeterminados.
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    print(f"Iniciando servidor Uvicorn en {host}:{port}")
    
    uvicorn.run(
        "src.ultibot_backend.main:app",
        host=host,
        port=port,
        reload=True,
        # El reload_dirs es importante para que uvicorn vigile todo el proyecto
        reload_dirs=["src"]
    )

if __name__ == "__main__":
    main()
