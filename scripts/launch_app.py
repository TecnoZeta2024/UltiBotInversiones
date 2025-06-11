import os
import sys
import subprocess
import time
import logging
import shutil
import psutil
import httpx

# --- Configuración ---
LOGS_DIR = "logs"
BACKEND_LOG = os.path.join(LOGS_DIR, "backend.log")
FRONTEND_LOG = os.path.join(LOGS_DIR, "frontend.log")
FRONTEND_LOG_1 = os.path.join(LOGS_DIR, "frontend1.log")
LOG_FILES = [BACKEND_LOG, FRONTEND_LOG, FRONTEND_LOG_1]
ABS_LOG_FILES = [os.path.abspath(f) for f in LOG_FILES]

BACKEND_COMMAND = "poetry run uvicorn src.ultibot_backend.main:app --host 0.0.0.0 --port 8000 --reload"
FRONTEND_COMMAND = "poetry run python src/ultibot_ui/main.py"
HEALTH_CHECK_URL = "http://localhost:8000/health"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def terminate_processes_locking_files(file_paths: list[str]):
    """Encuentra y termina cualquier proceso que esté bloqueando los archivos especificados."""
    procs_to_kill = set()
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            open_files = proc.info.get('open_files')
            if open_files:
                for file in open_files:
                    if file.path in file_paths:
                        logging.info(f"Archivo '{file.path}' está bloqueado por el proceso '{proc.name()}' (PID: {proc.pid}). Marcando para terminación.")
                        procs_to_kill.add(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            # Ignorar errores menores al acceder a la información de un proceso
            pass

    if not procs_to_kill:
        logging.info("No se encontraron procesos bloqueando los archivos de log.")
        return

    for proc in list(procs_to_kill):
        try:
            logging.info(f"Enviando señal de terminación al proceso '{proc.name()}' (PID: {proc.pid})")
            proc.kill()
        except psutil.NoSuchProcess:
            logging.warning(f"El proceso {proc.pid} ya no existía al intentar terminarlo.")
        except Exception as e:
            logging.error(f"Error al terminar el proceso {proc.pid}: {e}")

    gone, alive = psutil.wait_procs(list(procs_to_kill), timeout=5)
    
    for p in gone:
        logging.info(f"Proceso {p.pid} terminado exitosamente.")
    for p in alive:
        logging.warning(f"El proceso {p.pid} no respondió a la terminación. Forzando de nuevo.")
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass

def cleanup():
    """Limpia el entorno antes de lanzar la aplicación."""
    logging.info("--- Fase de Limpieza Iniciada ---")

    logging.info("Buscando y terminando procesos que bloquean los archivos de log...")
    terminate_processes_locking_files(ABS_LOG_FILES)
    logging.info("Verificación de procesos bloqueadores completada.")

    # Pequeña pausa adicional para asegurar que el SO libera los handles
    time.sleep(1)

    logging.info("Limpiando logs anteriores...")
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        
    for log_file in LOG_FILES:
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logging.info(f"Archivo de log eliminado: {log_file}")
            except OSError as e:
                logging.error(f"No se pudo eliminar {log_file} después de la limpieza de procesos: {e}. Abortando.")
                sys.exit(1)
    logging.info("Limpieza de logs completada.")

    logging.info("Limpiando directorios __pycache__...")
    for root, dirs, _ in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                logging.info(f"Directorio __pycache__ eliminado: {pycache_path}")
            except OSError as e:
                logging.error(f"No se pudo eliminar {pycache_path}: {e}")
    logging.info("Limpieza de __pycache__ completada.")
    logging.info("--- Fase de Limpieza Finalizada ---")

def launch_backend():
    """Lanza el servidor backend como un subproceso."""
    logging.info("Lanzando el backend...")
    try:
        with open(BACKEND_LOG, 'wb') as log_file:
            process = subprocess.Popen(
                BACKEND_COMMAND,
                shell=True,
                stdout=log_file,
                stderr=log_file,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        logging.info(f"Backend lanzado con PID: {process.pid}")
        return process
    except Exception as e:
        logging.error(f"Error al lanzar el backend: {e}")
        return None

def wait_for_backend():
    """Espera a que el backend esté disponible."""
    logging.info("Esperando a que el backend esté disponible (max 60 segundos)...")
    start_time = time.time()
    while time.time() - start_time < 60:
        try:
            with httpx.Client() as client:
                response = client.get(HEALTH_CHECK_URL, timeout=2)
            if response.status_code == 200 and response.json().get("status") == "ok":
                logging.info("Backend disponible.")
                return True
        except httpx.RequestError:
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Error durante el health check: {e}")
            time.sleep(1)
    logging.error("El backend no se inició a tiempo. Revisa logs/backend.log")
    return False

def launch_frontend():
    """Lanza la aplicación de frontend como un subproceso."""
    logging.info("Lanzando el frontend...")
    try:
        with open(FRONTEND_LOG_1, 'wb') as log_file:
            process = subprocess.Popen(
                FRONTEND_COMMAND,
                shell=True,
                stdout=log_file,
                stderr=log_file,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        logging.info(f"Frontend lanzado con PID: {process.pid}")
        return process
    except Exception as e:
        logging.error(f"Error al lanzar el frontend: {e}")
        return None

def main():
    """Función principal de orquestación."""
    cleanup()

    backend_process = launch_backend()
    if not backend_process:
        sys.exit(1)

    if wait_for_backend():
        frontend_process = launch_frontend()
        if not frontend_process:
            backend_process.kill()
            sys.exit(1)
    else:
        backend_process.kill()
        sys.exit(1)

    logging.info("--- UltiBotInversiones: Backend y Frontend lanzados ---")
    logging.info("Monitorea los archivos en la carpeta 'logs' para ver la salida.")
    logging.info("Para detener los servicios, cierra esta ventana.")

if __name__ == "__main__":
    main()
