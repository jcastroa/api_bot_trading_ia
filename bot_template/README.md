# 🤖 Bot Template - Archivos de Referencia

Este directorio contiene **archivos de ejemplo** para ayudarte a construir las imágenes Docker de tus bots de trading.

## 📁 Archivos Incluidos

### 1. `Dockerfile` ⭐

Template del Dockerfile para el bot. Incluye:

- Configuración base de Python 3.11
- Instalación de dependencias
- Documentación de todas las variables de entorno que el bot recibirá
- Comando para ejecutar el bot

**Debes:**
- Copiar este archivo al directorio de tu bot
- Ajustar el comando `CMD` según el punto de entrada de tu bot
- Agregar cualquier dependencia del sistema que necesites

### 2. `build_images.sh` ⭐

Script para construir ambas imágenes Docker (ETH y BTC) automáticamente.

**Uso:**

```bash
cd /path/to/tu/bot
cp /path/to/bot_template/Dockerfile .
cp /path/to/bot_template/build_images.sh .
./build_images.sh
```

### 3. `requirements.txt`

Template de dependencias Python para el bot. Incluye:

- `python-binance` - Cliente de Binance API
- `pymysql` + `sqlalchemy` - Base de datos
- `pandas` + `numpy` - Análisis de datos
- `scikit-learn` - Machine Learning (opcional)
- Utilidades varias

**Debes:**
- Ajustar según las dependencias reales de tu bot
- Agregar/eliminar librerías según necesites

### 4. `config_example.py`

Clase de ejemplo mostrando cómo leer las variables de entorno en tu bot.

**Características:**

- Lee todas las variables de entorno automáticamente
- Valida que las variables requeridas estén presentes
- Selecciona API keys correctas según environment (testnet/production)
- Proporciona métodos útiles (`get_database_url()`, etc.)

**Uso en tu bot:**

```python
from config import BotConfig

config = BotConfig()
config.validate()

print(f"Trading {config.full_pair} on {config.environment}")
print(f"User ID: {config.user_id}")
```

### 5. `database_example.py`

Clase de ejemplo mostrando cómo conectarse a la base de datos y trabajar con las tablas.

**Funcionalidades:**

- `connect()` - Conectar a la base de datos
- `get_bot_configuration()` - Leer config desde `bot_configurations`
- `get_bot_state()` - Leer estado desde `bot_states`
- `update_bot_state()` - Actualizar estado del bot
- `save_trade()` - Guardar trades

**Uso en tu bot:**

```python
from config import BotConfig
from database import BotDatabase

config = BotConfig()
db = BotDatabase(config)
db.connect()

# Leer configuración
bot_config = db.get_bot_configuration()
stop_loss = bot_config["stop_loss_percent"]

# Actualizar estado
db.update_bot_state({
    "in_position": True,
    "entry_price": 2500.50,
    "regime": "BULL",
    "probability": 0.75
})
```

---

## 🚀 Cómo Usar Estos Templates

### Paso 1: Copiar al Directorio de Tu Bot

```bash
# Crear directorio para tu bot (si no existe)
mkdir -p ~/my_trading_bot
cd ~/my_trading_bot

# Copiar templates
cp /home/user/api_bot_trading_ia/bot_template/Dockerfile .
cp /home/user/api_bot_trading_ia/bot_template/build_images.sh .
cp /home/user/api_bot_trading_ia/bot_template/requirements.txt .

# Opcional: copiar ejemplos de código
cp /home/user/api_bot_trading_ia/bot_template/config_example.py ./config.py
cp /home/user/api_bot_trading_ia/bot_template/database_example.py ./database.py
```

### Paso 2: Adaptar a Tu Bot

**A. Ajustar `requirements.txt`:**

Agrega/elimina dependencias según tu bot:

```txt
python-binance==1.0.19
pymysql==1.1.0
pandas==2.1.4
# Agregar tus dependencias aquí
```

**B. Ajustar `Dockerfile`:**

Cambia el comando de ejecución:

```dockerfile
# Si tu bot se ejecuta con main.py
CMD ["python", "main.py"]

# O si tiene otro punto de entrada
CMD ["python", "-m", "bot.trading_engine"]
```

**C. Ajustar tu código:**

Asegúrate de que tu bot lea las variables de entorno. Puedes usar los ejemplos `config.py` y `database.py` como base.

### Paso 3: Construir las Imágenes

```bash
chmod +x build_images.sh
./build_images.sh
```

Verás:

```
🔨 Construyendo imágenes Docker para los bots de trading...

📦 Construyendo imagen para ETH bot...
✅ Imagen bot_trading_ia-eth-ai:latest construida exitosamente

📦 Construyendo imagen para BTC bot...
✅ Imagen bot_trading_ia-btc-ai:latest construida exitosamente

🎉 Ambas imágenes construidas exitosamente!
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

### Paso 5: ¡Listo!

Ahora cuando guardes la configuración desde el frontend, la API automáticamente:

1. Creará contenedores usando estas imágenes
2. Pasará todas las variables de entorno
3. Los bots empezarán a operar

---

## 🔧 Estructura Recomendada del Bot

```
my_trading_bot/
├── Dockerfile                 # Copiado del template
├── build_images.sh           # Copiado del template
├── requirements.txt          # Adaptado a tu bot
├── config.py                 # Basado en config_example.py
├── database.py               # Basado en database_example.py
├── main.py                   # Tu código principal
├── trading/
│   ├── __init__.py
│   ├── strategy.py           # Lógica de trading
│   ├── binance_client.py     # Cliente de Binance
│   └── risk_management.py    # Gestión de riesgo
├── models/
│   ├── __init__.py
│   └── ml_model.py           # Modelos ML (si usas IA)
└── utils/
    ├── __init__.py
    ├── logger.py
    └── notifications.py      # Email/Telegram
```

---

## 📝 Ejemplo Completo de `main.py`

```python
#!/usr/bin/env python3
"""
Trading Bot - Main Entry Point
"""

import logging
import time
from config import BotConfig
from database import BotDatabase
from binance.client import Client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Función principal del bot"""

    # 1. Cargar configuración desde variables de entorno
    logger.info("🚀 Iniciando Trading Bot...")
    config = BotConfig()
    config.validate()

    logger.info(f"📊 Configuración: {config.environment} - {config.full_pair}")
    logger.info(f"👤 User ID: {config.user_id}")

    # 2. Conectar a la base de datos
    db = BotDatabase(config)
    db.connect()

    # 3. Obtener configuración del bot desde la DB
    bot_config = db.get_bot_configuration()
    if not bot_config:
        logger.error("❌ No se encontró configuración del bot en la DB")
        return

    logger.info(f"⚙️ Config Bot: SL={bot_config['stop_loss_percent']}%, TP1={bot_config['take_profit_1_percent']}%")

    # 4. Conectar a Binance
    client = Client(
        api_key=config.api_key,
        api_secret=config.secret_key,
        testnet=config.testnet
    )

    logger.info(f"✅ Conectado a Binance {'Testnet' if config.testnet else 'Production'}")

    # 5. Loop principal
    logger.info(f"🔄 Iniciando loop principal (check cada {config.check_interval}s)")

    while True:
        try:
            # Obtener estado actual
            state = db.get_bot_state()

            # Obtener precio actual
            ticker = client.get_symbol_ticker(symbol=config.full_pair)
            current_price = float(ticker['price'])

            logger.info(f"💰 Precio actual {config.full_pair}: ${current_price:.2f}")

            # TODO: Implementar tu lógica de trading aquí
            # - Analizar mercado
            # - Decidir entrada/salida
            # - Ejecutar órdenes
            # - Actualizar estado

            # Actualizar estado en DB
            db.update_bot_state({
                "in_position": False,
                "current_price": current_price,
                "current_pnl_usd": 0.0,
                "current_pnl_percent": 0.0,
                "regime": "NEUTRAL",
                "probability": 0.5,
                "available_capital": 1000.0,
                "last_signal_action": "HOLD"
            })

            # Esperar antes del próximo check
            time.sleep(config.check_interval)

        except KeyboardInterrupt:
            logger.info("⏹️ Bot detenido manualmente")
            break
        except Exception as e:
            logger.error(f"❌ Error en el loop principal: {e}")
            time.sleep(60)  # Esperar 1 minuto antes de reintentar


if __name__ == "__main__":
    main()
```

---

## ⚠️ Notas Importantes

1. **Mismo código, dos imágenes:** Actualmente `build_images.sh` construye dos imágenes con el mismo código. La API selecciona qué imagen usar según el par. Si en el futuro quieres código diferente para ETH y BTC, puedes usar build args en el Dockerfile.

2. **Variables de entorno:** NUNCA hardcodees credenciales en el código. Siempre usa `os.getenv()`.

3. **Base de datos:** El bot DEBE usar el `user_id`, `pair` y `environment` correctos al guardar datos.

4. **Logging:** Usa logging para facilitar el debugging con `docker logs`.

5. **Error handling:** Implementa manejo de errores robusto para que el bot no se caiga.

---

## 🎯 Checklist Antes de Build

- [ ] `requirements.txt` tiene todas las dependencias
- [ ] `Dockerfile` tiene el comando correcto
- [ ] Tu bot lee variables de entorno (no hardcoded)
- [ ] Tu bot se conecta a la base de datos
- [ ] Tu bot actualiza `bot_states` regularmente
- [ ] Tu bot guarda trades en la tabla `trades`
- [ ] Logging configurado correctamente
- [ ] Error handling implementado

---

## 🆘 Ayuda

Si tienes problemas, revisa:

1. **BOT_DEPLOYMENT_GUIDE.md** - Guía completa de deployment
2. **Logs del contenedor:** `docker logs bot-user1-ethusdt-testnet`
3. **Variables de entorno:** `docker inspect bot-user1-ethusdt-testnet | grep Env`

---

**¡Buena suerte con tu bot de trading! 🚀📈**
