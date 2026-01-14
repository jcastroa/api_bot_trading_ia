# 🤖 Trading Bot API

API backend para el sistema de trading bot con autenticación Firebase, gestión de configuraciones y monitoreo de operaciones.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Firebase Setup](#firebase-setup)
- [Uso](#uso)
- [Endpoints](#endpoints)
- [Docker](#docker)
- [Desarrollo](#desarrollo)
- [Seguridad](#seguridad)

## ✨ Características

- 🔐 **Autenticación JWT con Firebase**: Integración completa con Google OAuth
- 🍪 **Cookies Seguras**: HttpOnly, Secure, SameSite=Strict
- 🔒 **Encriptación AES-256**: Para API keys de Binance
- 📊 **Endpoints Completos**: Auth, Bot State, Trades, Performance, Configuration
- 🐳 **Dockerizado**: Listo para producción
- 🤖 **Orquestación Automática**: Levanta contenedores Docker de bots automáticamente
- 🎯 **Imágenes Específicas por Par**: ETH y BTC con imágenes separadas
- 📝 **Documentación Automática**: Swagger UI y ReDoc
- ✅ **Validación de Datos**: Pydantic schemas
- 🌐 **CORS Configurado**: Para frontend React

## 📦 Requisitos

- Python 3.11+
- MySQL 8.0+
- Docker & Docker Compose (opcional)
- Cuenta de Firebase con servicio de autenticación habilitado

## 🚀 Instalación

### Opción 1: Instalación Local

```bash
# Clonar el repositorio
git clone <repository-url>
cd api_bot_trading_ia

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de configuración
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

### Opción 2: Docker

```bash
# Clonar el repositorio
git clone <repository-url>
cd api_bot_trading_ia

# Copiar archivo de configuración
cp .env.example .env

# Editar .env con tus credenciales
nano .env

# Construir y ejecutar con Docker Compose
docker-compose up --build
```

## ⚙️ Configuración

### Archivo .env

Edita el archivo `.env` con tus valores:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_ENV=development

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3005,http://localhost:3000

# Database Configuration
DB_HOST=your-mysql-host
DB_PORT=3306
DB_NAME=trading_bot
DB_USER=your-db-user
DB_PASSWORD=your-db-password

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# Encryption Configuration
ENCRYPTION_KEY=your-32-character-encryption-key

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
# O usar JSON directo:
# FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}

# Docker Configuration
DOCKER_NETWORK=bot_trading_web_trading-network

# Email Configuration (for bot notifications)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD="your google app password with spaces"
```

**⚠️ Nota importante sobre EMAIL_PASSWORD:**
- Usa comillas dobles si tu contraseña contiene espacios (típico de las contraseñas de aplicación de Google)
- Las claves de aplicación de Google tienen el formato: `xxxx xxxx xxxx xxxx` (con espacios)
- Ejemplo: `EMAIL_PASSWORD="abcd efgh ijkl mnop"`

### Generar Claves Secretas

```python
# Para JWT_SECRET_KEY
import secrets
print(secrets.token_urlsafe(32))

# Para ENCRYPTION_KEY (debe ser exactamente 32 caracteres)
import secrets
print(secrets.token_urlsafe(32)[:32])
```

### Configurar Email para Notificaciones

Para que los bots puedan enviar notificaciones por email, necesitas configurar una cuenta de Gmail:

1. **Habilitar verificación en 2 pasos** en tu cuenta de Gmail
2. **Generar una contraseña de aplicación**:
   - Ve a [myaccount.google.com](https://myaccount.google.com)
   - Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones
   - Selecciona "Correo" y "Otro (nombre personalizado)"
   - Copia la contraseña generada (formato: `xxxx xxxx xxxx xxxx`)
3. **Configurar en .env**:
   ```env
   EMAIL_USER=tu_cuenta@gmail.com
   EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
   ```

**Nota:** El bot recupera automáticamente el email destino desde la base de datos (campo `users.email`), por lo que no necesitas configurar `EMAIL_TO`.

## 🔥 Firebase Setup

### Paso 1: Crear Proyecto Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita **Authentication** > **Sign-in method** > **Google**

### Paso 2: Obtener Credenciales de Service Account

1. En Firebase Console, ve a **Project Settings** (⚙️)
2. Selecciona la pestaña **Service Accounts**
3. Click en **Generate New Private Key**
4. Guarda el archivo JSON descargado como `firebase-credentials.json`

### Paso 3: Configurar Credenciales

**Opción A: Archivo de credenciales**

```bash
# Copiar archivo de credenciales al directorio del proyecto
cp /path/to/downloaded-key.json ./firebase-credentials.json

# Actualizar .env
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
```

**Opción B: JSON String (recomendado para Docker)**

```bash
# Convertir JSON a string de una línea
cat firebase-credentials.json | jq -c . | sed 's/"/\\"/g'

# Pegar el resultado en .env
FIREBASE_CREDENTIALS_JSON="{\"type\":\"service_account\",\"project_id\":\"...\"}"
```

### Paso 4: Configurar Firebase en el Frontend

```javascript
// En tu frontend React
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  // ... otros campos
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

## 🎯 Uso

### Iniciar el Servidor

**Desarrollo (local):**

```bash
# Con reload automático
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

# O usando el script main.py
python -m app.main
```

**Producción (Docker):**

```bash
docker-compose up -d
```

### Verificar que Funciona

```bash
# Health check
curl http://localhost:5000/health

# Documentación interactiva
open http://localhost:5000/docs
```

## 📡 Endpoints

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/google` | Login con Google/Firebase |
| POST | `/api/auth/logout` | Cerrar sesión |
| POST | `/api/auth/refresh` | Refrescar token JWT |
| GET | `/api/auth/validate` | Validar token actual |

### Bot

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/bot/state/{pair}` | Estado del bot para un par |
| GET | `/api/bot/trades/recent/{pair}` | Trades recientes |
| GET | `/api/bot/trades` | Todos los trades (paginado) |
| GET | `/api/bot/performance` | Estadísticas de rendimiento |

### Configuración

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/config/{environment}` | Estado de API keys |
| POST | `/api/config/save` | Guardar API keys + Auto-start bots 🚀 |
| GET | `/api/config/container/status/{environment}` | Estado de contenedores |
| GET | `/api/config/bot/{pair}/{environment}` | Configuración del bot |

### Control de Contenedores Docker

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/config/container/start/{environment}` | Iniciar todos los bots (ETH + BTC) |
| POST | `/api/config/container/stop/{environment}` | Detener todos los bots |
| POST | `/api/config/container/restart/{environment}` | Reiniciar todos los bots |
| POST | `/api/config/container/toggle/{pair}/{environment}` | Iniciar/detener bot específico (query: `?action=start\|stop`) |

### Ejemplos de Uso

**Login:**

```bash
curl -X POST http://localhost:5000/api/auth/google \
  -H "Content-Type: application/json" \
  -d '{
    "idToken": "firebase-id-token",
    "email": "user@example.com",
    "displayName": "User Name",
    "photoURL": "",
    "uid": "firebase-uid"
  }'
```

**Obtener Estado del Bot:**

```bash
curl -X GET http://localhost:5000/api/bot/state/ETHUSDT \
  -H "Authorization: Bearer your-jwt-token"
```

**Guardar API Keys:**

```bash
curl -X POST http://localhost:5000/api/config/save \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "testnet",
    "apiKey": "binance-api-key",
    "secretKey": "binance-secret-key"
  }'
```

## 🐳 Docker

### Comandos Útiles

```bash
# Construir imagen
docker-compose build

# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Detener servicios
docker-compose down

# Reiniciar
docker-compose restart

# Rebuild completo
docker-compose down && docker-compose up --build -d
```

### Variables de Entorno en Docker

El archivo `docker-compose.yml` lee las variables del archivo `.env` automáticamente.

### 🚀 Docker Container Orchestration

Esta API puede **gestionar automáticamente contenedores Docker** para los bots de trading.

#### Cómo Funciona

Cuando un usuario guarda sus API keys (`POST /api/config/save`), la API automáticamente:

1. ✅ Encripta y guarda las API keys
2. ✅ Crea configuraciones para ETH y BTC
3. ✅ **Levanta 2 contenedores Docker:**
   - `bot-user{id}-ethusdt-{environment}` con imagen `bot_trading_ia-eth-ai:latest`
   - `bot-user{id}-btcusdt-{environment}` con imagen `bot_trading_ia-btc-ai:latest`
4. ✅ Pasa 30+ variables de entorno a cada contenedor
5. ✅ Registra en la base de datos

#### Requisitos

**IMPORTANTE:** Para que la orquestación funcione, necesitas:

1. **Construir las imágenes del bot:**
   ```bash
   # Ver bot_template/ para templates
   docker build -t bot_trading_ia-eth-ai:latest /path/to/eth/bot
   docker build -t bot_trading_ia-btc-ai:latest /path/to/btc/bot
   ```

2. **Docker socket montado** (ya configurado en docker-compose.yml):
   ```yaml
   volumes:
     - /var/run/docker.sock:/var/run/docker.sock
   ```

#### Endpoints de Control

```bash
# Iniciar todos los bots
POST /api/config/container/start/{environment}

# Detener todos los bots
POST /api/config/container/stop/{environment}

# Reiniciar todos los bots
POST /api/config/container/restart/{environment}

# Control granular por par
POST /api/config/container/toggle/{pair}/{environment}?action=start|stop
```

#### Verificar Contenedores

```bash
# Ver contenedores de bots
docker ps | grep bot-user

# Ver logs de un bot específico
docker logs -f bot-user1-ethusdt-testnet

# Ver variables de entorno
docker inspect bot-user1-ethusdt-testnet | grep -A 50 Env
```

#### Seguridad del Socket Docker

⚠️ **IMPORTANTE:** Montar `/var/run/docker.sock` da acceso completo al Docker daemon.

**Consideraciones:**
- ✅ Usar solo en entornos confiables
- ✅ No exponer la API públicamente sin autenticación robusta
- ✅ Considerar usar Docker-in-Docker para mayor aislamiento en producción
- ✅ Revisar logs regularmente para detectar actividad sospechosa

Para **producción**, considera alternativas más seguras:
- Usar Kubernetes con RBAC
- Usar Docker Swarm con secrets
- Usar un servicio de orquestación dedicado

## 🛠️ Desarrollo

### Estructura del Proyecto

```
api_bot_trading_ia/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── config.py                  # Configuración y variables de entorno
│   ├── database.py                # Conexión a base de datos
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Modelos Pydantic
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                # Endpoints de autenticación
│   │   ├── bot.py                 # Endpoints del bot
│   │   └── config.py              # Endpoints de configuración
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py        # Lógica de autenticación
│   │   ├── firebase_service.py    # Integración con Firebase
│   │   ├── jwt_service.py         # Manejo de JWT
│   │   └── encryption_service.py  # Encriptación AES-256
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py     # Middleware de autenticación
│   └── utils/
│       └── __init__.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

### Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

### Logs

```bash
# Ver logs en Docker
docker-compose logs -f api

# Ver logs en local
# Los logs se imprimen en stdout
```

## 🔒 Seguridad

### Características de Seguridad Implementadas

1. **JWT con Expiración**: Tokens expiran después de 7 días
2. **Cookies Seguras**: HttpOnly, Secure (en producción), SameSite=Strict
3. **Encriptación AES-256**: Para API keys sensibles
4. **Validación Firebase**: Tokens de Firebase verificados con Admin SDK
5. **CORS Configurado**: Solo orígenes permitidos
6. **Validación de Datos**: Pydantic valida todas las entradas
7. **SQL Injection Protection**: Uso de prepared statements
8. **Rate Limiting**: Configurado (100 req/15 min)

### Mejores Prácticas

- ✅ Usa HTTPS en producción
- ✅ Cambia las claves secretas en `.env`
- ✅ No commitees el archivo `.env` o `firebase-credentials.json`
- ✅ Usa variables de entorno en Docker/producción
- ✅ Mantén las dependencias actualizadas
- ✅ Revisa los logs regularmente

### Generar Claves Seguras

```python
import secrets
import string

# JWT Secret (32+ caracteres)
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET_KEY={jwt_secret}")

# Encryption Key (exactamente 32 caracteres)
encryption_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
print(f"ENCRYPTION_KEY={encryption_key}")
```

## 📝 Documentación API

Una vez que el servidor esté corriendo, puedes acceder a la documentación interactiva:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y propietario.

## 🐛 Troubleshooting

### Error: "Firebase is not initialized"

```bash
# Verificar que el archivo de credenciales existe
ls -la firebase-credentials.json

# O verificar que la variable de entorno está configurada
echo $FIREBASE_CREDENTIALS_PATH
```

### Error: "Database connection failed"

```bash
# Verificar credenciales de base de datos
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME

# Verificar que el host de base de datos es accesible
ping $DB_HOST
```

### Error: "ModuleNotFoundError"

```bash
# Reinstalar dependencias
pip install -r requirements.txt

# Verificar versión de Python
python --version  # Debe ser 3.11+
```

### Docker: "Port already in use"

```bash
# Encontrar proceso usando el puerto
lsof -i :5000

# Matar el proceso
kill -9 <PID>

# O cambiar el puerto en docker-compose.yml
ports:
  - "5001:5000"  # Usar puerto 5001 en lugar de 5000
```

## 📞 Soporte

Para preguntas o problemas, abre un issue en el repositorio.

---

**Desarrollado con ❤️ usando FastAPI**
