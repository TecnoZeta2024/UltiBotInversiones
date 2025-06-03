#!/bin/bash
# Script para iniciar entorno gráfico XFCE y servidor VNC (TigerVNC)
# Este script queda como referencia pero no se usa en el entorno Docker actualizado

# Configura la contraseña VNC (cambia aquí si quieres otra)
mkdir -p /root/.vnc
echo "1234" | vncpasswd -f > /root/.vnc/passwd
chmod 600 /root/.vnc/passwd

# Inicia el entorno XFCE y el servidor VNC
# Opción insegura para exponer VNC (solo para uso personal/controlado)
rm -f /root/.vnc/*.pid  # Elimina posibles locks previos
vncserver -kill :0 2>/dev/null || true  # Mata cualquier sesión previa
tini -- vncserver :0 -geometry 1280x800 -depth 24 -localhost no -SecurityTypes None --I-KNOW-THIS-IS-INSECURE &

# Espera unos segundos para asegurar que el VNC está arriba
sleep 2

# Ejecuta la app PyQt5 en el display virtual
export DISPLAY=:0
exec python -m src.ultibot_ui.main
