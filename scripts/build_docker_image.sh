#!/bin/bash
echo "Construyendo la imagen Docker para UltiBotInversiones..."
docker build -t ultibot-inversiones .
if [ $? -eq 0 ]; then
    echo "Imagen Docker construida exitosamente: ultibot-inversiones"
else
    echo "Error al construir la imagen Docker."
    exit 1
fi
