# Dockerfile para Trading Bot
# Este template debe adaptarse a tu bot específico

FROM python:3.11-slim

# Instalar dependencias del sistema si son necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt del bot
COPY requirements.txt .

# Instalar dependencias Python del bot
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del bot
COPY . .

# Variables de entorno por defecto (serán sobrescritas por Docker al ejecutar)
# Estas son solo para documentación

# 🗄️ DATABASE CONFIGURATION
ENV DB_HOST=""
ENV DB_PORT="3306"
ENV DB_USER=""
ENV DB_PASSWORD=""
ENV DB_NAME=""

# 👤 USER CONFIGURATION
ENV USER_ID=""

# 🔑 BINANCE API KEYS (se configuran dinámicamente según environment)
# Para testnet: BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_SECRET_KEY
# Para production: BINANCE_PRODUCTION_API_KEY, BINANCE_PRODUCTION_SECRET_KEY

# ⚙️ BOT CONFIGURATION
ENV TESTNET="true"
ENV ENVIRONMENT="testnet"
ENV ACTIVE_PAIR="ETH"

# 📧 EMAIL NOTIFICATIONS
ENV EMAIL_ENABLED="true"
ENV EMAIL_HOST="smtp.gmail.com"
ENV EMAIL_PORT="587"
# ENV EMAIL_USER=""
# ENV EMAIL_PASSWORD=""
# ENV EMAIL_TO=""

# 🔔 TELEGRAM NOTIFICATIONS (Optional)
ENV TELEGRAM_ENABLED="false"
# ENV TELEGRAM_BOT_TOKEN=""
# ENV TELEGRAM_CHAT_ID=""

# ⚡ ADVANCED SETTINGS
ENV CHECK_INTERVAL="3600"
ENV LOOKBACK_DAYS="1825"
ENV DEBUG="false"

# 🔐 ENCRYPTION
ENV ENCRYPTION_KEY=""

# Comando para ejecutar el bot
# Ajusta esto según el punto de entrada de tu bot
CMD ["python", "main.py"]
