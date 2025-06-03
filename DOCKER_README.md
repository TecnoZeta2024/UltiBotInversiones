# 🐳 UltiBot Inversiones - Despliegue Completo con Docker

## Descripción General
Este documento describe cómo desplegar UltiBot Inversiones utilizando Docker, con todos sus componentes containerizados: backend (FastAPI), frontend (PyQt5 con TightVNC) y servicio MCP para asistencia IA.

## Prerrequisitos
- Docker instalado ([Guía de instalación](https://docs.docker.com/get-docker/))
- Docker Compose instalado ([Guía de instalación](https://docs.docker.com/compose/install/))
- Cliente VNC (como [TightVNC Viewer](https://www.tightvnc.com/), [RealVNC Viewer](https://www.realvnc.com/), o similar)
- Archivo `.env` configurado con credenciales (ver `.env.example`)

## Arquitectura del Despliegue
![Arquitectura](https://i.ibb.co/gVk9QyQ/ultibot-architecture.png)

## Estructura del Proyecto Dockerizado
```
UltiBotInversiones/
├── Dockerfile                  # Configuración del contenedor de backend
├── Dockerfile.frontend         # Configuración del contenedor de frontend con TightVNC
├── docker-compose.yml          # Configuración principal de servicios
├── docker-compose.override.yml # Configuración para desarrollo
├── docker/                     # Scripts y archivos de configuración para Docker
│   ├── supervisord.conf        # Configuración de supervisor para frontend
│   ├── frontend-entrypoint.sh  # Script de entrada para el frontend
│   ├── vnc-startup.sh          # Script para iniciar TightVNC
│   ├── xfce-startup.sh         # Script para iniciar el entorno XFCE
│   └── wait-for-it.sh          # Utilidad para esperar a que servicios estén listos
├── mcp_service/                # Servicio MCP para asistencia IA
│   ├── Dockerfile              # Configuración del contenedor MCP
│   ├── src/                    # Código fuente del servicio MCP
│   ├── package.json            # Dependencias del servicio MCP
│   └── requirements.txt        # Dependencias Python para el servicio MCP
├── .env                        # Variables de entorno (creado manualmente)
├── src/
│   ├── ultibot_backend/        # Código del backend
│   ├── ultibot_ui/             # Código del frontend
│   └── shared/                 # Módulos compartidos
└── logs/                       # Logs (compartido entre contenedores y host)
```

## Configuración del Entorno

1. **Crear archivo `.env`**:
   ```bash
   cp .env.example .env
   ```

2. **Editar variables de entorno**:
   ```
   # Credenciales y llaves de encriptación
   CREDENTIAL_ENCRYPTION_KEY=tu_llave_segura_de_encriptacion
   VNC_PASSWORD=tu_contraseña_para_vnc  # Por defecto 1234 si no se especifica

   # Configuración de Supabase (si aplica)
   SUPABASE_URL=https://tu_proyecto.supabase.co
   SUPABASE_ANON_KEY=tu_llave_anonima
   SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
   DATABASE_URL=postgresql://postgres:password@db.tu_proyecto.supabase.co:6543/postgres

   # Configuración de API de terceros (según se requiera)
   BINANCE_API_KEY=tu_binance_api_key
   BINANCE_API_SECRET=tu_binance_api_secret
   ```

## Despliegue Completo

### Inicio Rápido (Todos los Servicios)

Para iniciar todos los componentes (backend, frontend con VNC, y servicio MCP):

1. **Construir y ejecutar todos los contenedores**:
   ```bash
   docker compose up -d --build
   ```

2. **Verificar el estado de los servicios**:
   ```bash
   docker compose ps
   ```

3. **Acceso a los servicios**:
   - Backend API: http://localhost:8000/docs
   - Frontend UI (vía VNC): localhost:5900 (usar cliente VNC)
   - Servicio MCP: http://localhost:3000

### Construcción Manual de Imágenes

Si desea construir las imágenes individualmente:

```bash
# Construir todas las imágenes
docker compose build

# O construir imágenes específicas
docker compose build backend
docker compose build frontend
docker compose build mcp-server
```

### Modo Desarrollo

Para desarrollo con recarga automática de código:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
```

## Acceso al Frontend vía TightVNC

El frontend PyQt5 ahora se ejecuta dentro de un contenedor Docker y se accede mediante un cliente VNC:

1. **Instalar un cliente VNC** (como TightVNC Viewer, RealVNC, etc.)

2. **Conectarse al servidor VNC**:
   - Dirección: `localhost:5900`
   - Contraseña: La definida en `VNC_PASSWORD` (por defecto: 1234)

3. **Interfaz de Usuario**:
   - Verá el escritorio XFCE con la aplicación UltiBot ejecutándose
   - La interfaz es completamente funcional como si estuviera corriendo localmente

## Servicio MCP (Model Context Protocol)

El servicio MCP proporciona análisis de mercado y otras funcionalidades para el asistente de IA:

1. **Endpoints principales**:
   - `/api/v1/signals`: Proporciona señales de trading
   - `/api/v1/market-data/ticker/{symbol}`: Información actual de precios
   - `/api/v1/market-data/orderbook/{symbol}`: Libro de órdenes

2. **Verificación de funcionamiento**:
   ```bash
   curl http://localhost:3000/health
   ```

## Gestión de los Contenedores

### Ver logs de servicios
```bash
# Ver logs de todos los servicios
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mcp-server
```

### Detener servicios
```bash
docker compose down
```

### Reiniciar servicios específicos
```bash
docker compose restart frontend
```

## Solución de Problemas

### Si el Frontend con VNC no responde:
```bash
# Reiniciar solo el contenedor frontend
docker compose restart frontend

# Verificar logs específicos
docker compose logs -f frontend
```

### Si no puede conectarse al VNC:
1. Verifique que el puerto 5900 no esté bloqueado por un firewall
2. Asegúrese de que la contraseña VNC sea correcta
3. Intente reiniciar el contenedor del frontend

## Solución de Problemas

### Error de conexión al backend
- Verifica que el contenedor esté ejecutándose: `docker-compose ps`
- Revisa los logs: `docker-compose logs backend`
- Verifica que el puerto 8000 esté disponible: `netstat -ano | findstr :8000`

### Problemas con el frontend
- Revisa `logs/frontend.log`
- Asegúrate de que las variables de entorno estén configuradas correctamente
- Verifica que Poetry haya instalado todas las dependencias

## Notas Importantes

1. **Seguridad**: Nunca incluyas `.env` con credenciales reales en el control de versiones.
2. **Persistencia**: Los logs se mantienen entre reinicios gracias al volumen montado.
3. **Desarrollo**: La configuración de desarrollo permite la recarga en caliente del código del backend.
4. **Producción**: Para producción, considera usar un proxy inverso como Nginx delante del backend.

