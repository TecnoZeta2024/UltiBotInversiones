import os
from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

# Asumiendo que las estrategias están en un directorio conocido.
# Esto debería moverse a una configuración más robusta.
STRATEGIES_DIR = "src/ultibot_backend/strategies" 

router = APIRouter()

class FileNode(BaseModel):
    id: str
    name: str
    children: List['FileNode'] = []

# Esto permite que el modelo se refiera a sí mismo.
FileNode.update_forward_refs()

class FileContent(BaseModel):
    content: str

def get_directory_tree(root_dir: str) -> List[FileNode]:
    """
    Construye un árbol de archivos y directorios para una ruta dada.
    """
    tree = []
    if not os.path.isdir(root_dir):
        return tree

    for item in os.listdir(root_dir):
        path = os.path.join(root_dir, item)
        node = FileNode(id=path, name=item)
        if os.path.isdir(path):
            node.children = get_directory_tree(path)
        tree.append(node)
    return tree

@router.get("/strategies/files", response_model=List[FileNode])
async def get_strategy_files_tree():
    """
    Retorna la estructura de archivos de las estrategias como un árbol.
    """
    try:
        # Construimos un nodo raíz para que coincida con la estructura que espera el frontend
        root_node = FileNode(id=STRATEGIES_DIR, name="strategies", children=get_directory_tree(STRATEGIES_DIR))
        return [root_node]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer el directorio de estrategias: {e}"
        )

@router.get("/strategies/files/{file_path:path}", response_model=FileContent)
async def get_strategy_file_content(file_path: str):
    """
    Retorna el contenido de un archivo de estrategia específico.
    La ruta del archivo es relativa al directorio base de estrategias.
    """
    try:
        # Por seguridad, nos aseguramos de que la ruta no escape del directorio de estrategias.
        full_path = os.path.abspath(os.path.join(STRATEGIES_DIR, file_path))
        
        if not full_path.startswith(os.path.abspath(STRATEGIES_DIR)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

        if not os.path.isfile(full_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return FileContent(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer el archivo de estrategia: {e}"
        )
