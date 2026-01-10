# 🤖 Guía de Deployment de Bots - Orquestación Automática

Esta guía explica cómo funciona el sistema de orquestación automática de contenedores Docker para los bots de trading.

## 📋 Índice

1. [Cómo Funciona](#cómo-funciona)
2. [Construir las Imágenes Docker](#construir-las-imágenes-docker)
3. [Variables de Entorno](#variables-de-entorno)
4. [Flujo de Deployment Automático](#flujo-de-deployment-automático)
5. [Endpoints de Control de Contenedores](#endpoints-de-control-de-contenedores)
6. [Cambiar entre Testnet y Production](#cambiar-entre-testnet-y-production)
7. [Troubleshooting](#troubleshooting)

---

## 🔄 Cómo Funciona

### Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌────────────────────┐         ┌──────────────────────┐    │
│  │ Docker Service     │ ◄─────► │ Docker Engine        │    │
│  │ (docker_service.py)│         │                      │    │
│  └────────────────────┘         └──────────────────────┘    │
│           │                               │                  │
│           │                               ▼                  │
│           │                    ┌──────────────────────┐     │
│           │                    │  Container: ETH Bot  │     │
│           │                    │  Image: eth-ai       │     │
│           │                    │  Pair: ETHUSDT       │     │
│           │                    └──────────────────────┘     │
│           │                               │                  │
│           │                               ▼                  │
│           │                    ┌──────────────────────┐     │
│           ▼                    │  Container: BTC Bot  │     │
│  ┌────────────────────┐        │  Image: btc-ai       │     │
│  │   MariaDB          │ ◄──────│  Pair: BTCUSDT       │     │
│  │   - users          │        └──────────────────────┘     │
│  │   - api_configs    │                                      │
│  │   - bot_configs    │                                      │
│  │   - bot_states     │                                      │
│  │   - trades         │                                      │
│  │   - docker_cont... │                                      │
│  └────────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

### Flujo Automático

1. **Usuario guarda API keys** → `POST /api/config/save`
2. **API encripta keys** con AES-256
3. **API guarda en DB** → tabla `api_configurations`
4. **API crea configuraciones bot** → tabla `bot_configurations` (ETH y BTC)
5. **🚀 API inicia contenedores automáticamente**:
   - Contenedor ETH: `bot-user{id}-ethusdt-{environment}`
   - Contenedor BTC: `bot-user{id}-btcusdt-{environment}`
6. **API registra en DB** → tabla `docker_containers`
7. **Bots empiezan a operar** y alimentan las tablas `bot_states` y `trades`

---

## 🏗️ Construir las Imágenes Docker

### Paso 1: Preparar el Código del Bot

Asegúrate de que tu bot tiene esta estructura:

```
bot_trading_ia/
├── Dockerfile
├── requirements.txt
├── main.py              # Punto de entrada del bot
├── config.py            # Lee variables de entorno
├── trading_logic.py
├── database.py
└── ...
```

### Paso 2: Adaptar el Dockerfile

Usa el template en `bot_template/Dockerfile` y adáptalo a tu bot:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del bot
COPY . .

# El bot debe leer variables de entorno
CMD ["python", "main.py"]
```

### Paso 3: Construir las Imágenes

Hay dos opciones:

#### Opción A: Script Automático

```bash
cd bot_template
chmod +x build_images.sh
./build_images.sh
```

#### Opción B: Manual

```bash
# Desde el directorio del bot
docker build -t bot_trading_ia-eth-ai:latest .
docker build -t bot_trading_ia-btc-ai:latest .
```

**Nota:** Actualmente ambas imágenes usan el mismo código. La API selecciona automáticamente qué imagen usar según el par. Si en el futuro quieres imágenes diferentes para ETH y BTC, puedes usar build args:

```bash
# ETH Bot
docker build --build-arg PAIR=ETH -t bot_trading_ia-eth-ai:latest .

# BTC Bot
docker build --build-arg PAIR=BTC -t bot_trading_ia-btc-ai:latest .
```

### Paso 4: Verificar las Imágenes

```bash
docker images | grep bot_trading_ia
```

Deberías ver:

```
bot_trading_ia-eth-ai    latest    abc123...    2 minutes ago    500MB
bot_trading_ia-btc-ai    latest    def456...    1 minute ago     500MB
```

---

## 🔧 Variables de Entorno

El bot recibirá estas variables de entorno **automáticamente** desde la API:

### 🗄️ Base de Datos

```bash
DB_HOST=xxx.xxx.xxx.xxx
DB_PORT=3306
DB_USER=trading_bot
DB_PASSWORD=secure_password
DB_NAME=trading_bot_db
```

**Uso en el bot:**

```python
import os
import pymysql

connection = pymysql.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
```

### 👤 Usuario

```bash
USER_ID=1
```

**Uso:** Todas las operaciones del bot deben usar este user_id para guardar en DB.

### 🔑 Binance API Keys

**Para Testnet:**

```bash
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_SECRET_KEY=your_testnet_secret
```

**Para Production:**

```bash
BINANCE_PRODUCTION_API_KEY=your_production_key
BINANCE_PRODUCTION_SECRET_KEY=your_production_secret
```

**Uso en el bot:**

```python
import os

testnet = os.getenv("TESTNET", "true") == "true"

if testnet:
    api_key = os.getenv("BINANCE_TESTNET_API_KEY")
    secret_key = os.getenv("BINANCE_TESTNET_SECRET_KEY")
else:
    api_key = os.getenv("BINANCE_PRODUCTION_API_KEY")
    secret_key = os.getenv("BINANCE_PRODUCTION_SECRET_KEY")
```

### ⚙️ Configuración del Bot

```bash
TESTNET=true                  # true o false
ENVIRONMENT=testnet           # testnet o production
ACTIVE_PAIR=ETH              # ETH o BTC
```

**Uso:**

```python
pair = os.getenv("ACTIVE_PAIR")  # "ETH" o "BTC"
full_pair = f"{pair}USDT"        # "ETHUSDT" o "BTCUSDT"
```

### 📧 Notificaciones Email

```bash
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com      # Configurable
EMAIL_PASSWORD=your_app_password      # Configurable
EMAIL_TO=recipient@example.com        # Configurable
```

### 🔔 Telegram (Opcional)

```bash
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### ⚡ Configuración Avanzada

```bash
CHECK_INTERVAL=3600          # Segundos entre checks (1 hora)
LOOKBACK_DAYS=1825          # Días históricos (5 años)
DEBUG=false
ENCRYPTION_KEY=your_32_byte_key
```

---

## 🚀 Flujo de Deployment Automático

### Cuando Usuario Guarda Configuración

```http
POST /api/config/save
Content-Type: application/json

{
  "environment": "testnet",
  "apiKey": "binance_api_key",
  "secretKey": "binance_secret_key"
}
```

**La API hace automáticamente:**

1. ✅ Encripta API keys con AES-256
2. ✅ Guarda en `api_configurations`
3. ✅ Crea configs default en `bot_configurations` (ETH y BTC)
4. ✅ **Inicia 2 contenedores Docker**:
   - `bot-user1-ethusdt-testnet` (imagen: bot_trading_ia-eth-ai:latest)
   - `bot-user1-btcusdt-testnet` (imagen: bot_trading_ia-btc-ai:latest)
5. ✅ Pasa todas las variables de entorno
6. ✅ Registra en `docker_containers`

**Respuesta:**

```json
{
  "success": true,
  "message": "Configuración guardada correctamente. 2/2 bots iniciados."
}
```

### Qué Hace Cada Contenedor

Cada bot:

1. **Lee variables de entorno** (DB, API keys, USER_ID, etc.)
2. **Conecta a la base de datos**
3. **Lee su configuración** desde `bot_configurations`:
   - `WHERE user_id = {USER_ID} AND pair = {ACTIVE_PAIR}USDT AND environment = {ENVIRONMENT}`
4. **Ejecuta lógica de trading**
5. **Actualiza `bot_states`** con estado actual
6. **Guarda trades** en tabla `trades`

---

## 🎮 Endpoints de Control de Contenedores

### 1️⃣ Obtener Estado de Contenedores

```http
GET /api/config/container/status/{environment}
```

**Ejemplo:**

```bash
curl http://localhost:5000/api/config/container/status/testnet \
  -H "Cookie: auth_token=your_jwt_token"
```

**Respuesta:**

```json
{
  "success": true,
  "data": {
    "status": "running",
    "lastRestart": "2026-01-10T10:30:00",
    "containerId": "MULTI:ETHUSDT:abc123456789"
  }
}
```

### 2️⃣ Iniciar Contenedores Manualmente

```http
POST /api/config/container/start/{environment}
```

**Uso:**

```bash
curl -X POST http://localhost:5000/api/config/container/start/testnet \
  -H "Cookie: auth_token=your_jwt_token"
```

**Qué hace:** Inicia ambos contenedores (ETH y BTC) para el environment especificado.

### 3️⃣ Detener Contenedores

```http
POST /api/config/container/stop/{environment}
```

**Uso:**

```bash
curl -X POST http://localhost:5000/api/config/container/stop/testnet \
  -H "Cookie: auth_token=your_jwt_token"
```

### 4️⃣ Reiniciar Contenedores

```http
POST /api/config/container/restart/{environment}
```

**Uso:**

```bash
curl -X POST http://localhost:5000/api/config/container/restart/testnet \
  -H "Cookie: auth_token=your_jwt_token"
```

### 5️⃣ Control Granular por Par

```http
POST /api/config/container/toggle/{pair}/{environment}?action={start|stop}
```

**Ejemplo - Iniciar solo ETH:**

```bash
curl -X POST "http://localhost:5000/api/config/container/toggle/ETHUSDT/testnet?action=start" \
  -H "Cookie: auth_token=your_jwt_token"
```

**Ejemplo - Detener solo BTC:**

```bash
curl -X POST "http://localhost:5000/api/config/container/toggle/BTCUSDT/production?action=stop" \
  -H "Cookie: auth_token=your_jwt_token"
```

---

## 🔄 Cambiar entre Testnet y Production

### Opción 1: Desde el Frontend

Usuario simplemente guarda nuevas API keys con environment diferente:

```javascript
// Cambiar a production
await apiClient.post('/config/save', {
  environment: 'production',
  apiKey: 'production_api_key',
  secretKey: 'production_secret_key'
});
```

**La API automáticamente:**

1. Guarda las nuevas keys de production
2. Inicia nuevos contenedores con `environment=production`
3. Los contenedores antiguos de testnet siguen corriendo (o puedes detenerlos)

### Opción 2: Mantener Ambos Ambientes

Puedes tener **4 contenedores corriendo simultáneamente**:

- `bot-user1-ethusdt-testnet`
- `bot-user1-btcusdt-testnet`
- `bot-user1-ethusdt-production`
- `bot-user1-btcusdt-production`

Cada uno opera independientemente con sus propias API keys.

### Cambio de Variables de Entorno

**No necesitas reconstruir imágenes.** Las variables de entorno se pasan al crear el contenedor:

```python
# En docker_service.py
env_vars = {
    "TESTNET": "false",  # ← Cambia automáticamente
    "ENVIRONMENT": "production",
    "BINANCE_PRODUCTION_API_KEY": api_key,
    # ...
}
```

---

## 🔍 Troubleshooting

### Problema 1: Contenedores No Se Inician

**Síntoma:**

```json
{
  "success": true,
  "message": "Configuración guardada correctamente. 0/2 bots iniciados."
}
```

**Diagnóstico:**

```bash
# Ver logs de la API
docker-compose logs api | grep "Docker"
```

**Posibles causas:**

1. **Imágenes no construidas:**

```bash
docker images | grep bot_trading_ia
# Si no ves las imágenes, constrúyelas
```

2. **Docker daemon no accesible:**

```bash
# Verificar Docker
docker ps
```

3. **Permisos:**

```bash
# El usuario que corre la API debe tener acceso a Docker socket
sudo usermod -aG docker $USER
```

### Problema 2: Contenedor Se Crea Pero Falla

**Diagnóstico:**

```bash
# Listar todos los contenedores
docker ps -a | grep bot-user

# Ver logs del contenedor
docker logs bot-user1-ethusdt-testnet
```

**Posibles causas:**

1. **Error en el bot** (Python exception)
2. **Variables de entorno incorrectas**
3. **No puede conectar a la base de datos**

**Verificar variables de entorno:**

```bash
docker inspect bot-user1-ethusdt-testnet | grep -A 50 Env
```

### Problema 3: Base de Datos No Accesible

**Síntoma en logs del bot:**

```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solución:**

Verificar que `DB_HOST` en el bot sea accesible desde el contenedor:

```bash
# Entrar al contenedor
docker exec -it bot-user1-ethusdt-testnet /bin/bash

# Intentar conexión
ping $DB_HOST
telnet $DB_HOST $DB_PORT
```

Si usas Docker Compose, asegúrate de que los contenedores estén en la misma red:

```yaml
# docker-compose.yml
networks:
  trading-network:
    driver: bridge

services:
  api:
    networks:
      - trading-network
  db:
    networks:
      - trading-network
```

Y en `docker_service.py`:

```python
container = self.client.containers.run(
    # ...
    network_mode="trading-network",  # ← Cambiar de "bridge"
)
```

### Problema 4: Contenedor en Estado "Restarting"

```bash
docker ps
# STATUS: Restarting (1) 5 seconds ago
```

**Causa:** El bot termina inmediatamente (exit code != 0).

**Solución:**

```bash
# Ver logs
docker logs bot-user1-ethusdt-testnet

# Revisar qué está fallando en el bot
```

### Problema 5: UNIQUE Constraint en docker_containers

**Error en logs:**

```
IntegrityError: (1062, "Duplicate entry '1-testnet' for key 'unique_user_container'")
```

**Causa:** Intentaste crear contenedores cuando ya existe un registro.

**Solución (Automática):** El código ya maneja esto usando "MULTI" prefix. Si persiste:

```sql
-- Ver registros existentes
SELECT * FROM docker_containers WHERE user_id = 1;

-- Eliminar registros antiguos si es necesario
DELETE FROM docker_containers WHERE user_id = 1 AND environment = 'testnet';
```

---

## 🎯 Checklist de Deployment

### Antes de Producción

- [ ] Construir ambas imágenes Docker (eth-ai y btc-ai)
- [ ] Verificar que las imágenes existen: `docker images | grep bot_trading_ia`
- [ ] Probar en testnet primero
- [ ] Verificar conexión del bot a la base de datos
- [ ] Revisar logs del bot: `docker logs bot-user{id}-ethusdt-testnet`
- [ ] Confirmar que bot guarda datos en `bot_states` y `trades`
- [ ] Configurar email/telegram notifications (opcional)

### Deployment a Production

- [ ] Guardar API keys de production desde frontend
- [ ] Verificar que contenedores de production se inician
- [ ] Monitorear logs: `docker logs -f bot-user{id}-ethusdt-production`
- [ ] Verificar trades en la base de datos
- [ ] Configurar alertas/monitoring

---

## 📊 Monitoreo

### Ver Estado de Todos los Contenedores

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

### Logs en Tiempo Real

```bash
# Todos los contenedores del usuario 1
docker logs -f bot-user1-ethusdt-testnet

# Filtrar por errores
docker logs bot-user1-ethusdt-testnet 2>&1 | grep ERROR
```

### Estadísticas de Uso

```bash
# CPU, RAM por contenedor
docker stats bot-user1-ethusdt-testnet bot-user1-btcusdt-testnet
```

---

## 🔐 Seguridad

1. **API Keys Encriptadas:** Nunca se almacenan en texto plano
2. **Variables de Entorno:** No se loguean (solo preview de token)
3. **Contenedores Aislados:** Cada bot corre en su propio contenedor
4. **Network Isolation:** Usa Docker networks para aislar comunicación
5. **Restart Policy:** `unless-stopped` - los bots se reinician automáticamente

---

## 📝 Resumen

1. **Construye las imágenes** → `./build_images.sh`
2. **Inicia la API** → `docker-compose up -d`
3. **Guarda configuración** → Frontend llama `POST /api/config/save`
4. **Contenedores se inician automáticamente** 🚀
5. **Bots operan y alimentan DB** 📊

**¡Listo!** El sistema de orquestación está completo y funcionando.
