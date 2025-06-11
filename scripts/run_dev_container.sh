#!/bin/bash
echo "Ejecutando el contenedor de desarrollo de UltiBotInversiones..."
docker run -it --rm \
    -p 8000:8000 \
    -v "$(pwd)":/app \
    --name ultibot-dev-container \
    ultibot-inversiones
if [ $? -eq 0 ]; then
    echo "Contenedor de desarrollo iniciado exitosamente."
else
    echo "Error al iniciar el contenedor de desarrollo."
    exit 1
fi
