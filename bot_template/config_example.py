"""
Ejemplo de cómo el bot debe leer las variables de entorno
Este archivo debe adaptarse a tu bot específico
"""

import os
from typing import Literal

class BotConfig:
    """Configuración del bot desde variables de entorno"""

    def __init__(self):
        # 🗄️ DATABASE CONFIGURATION
        self.db_host = os.getenv("DB_HOST")
        self.db_port = int(os.getenv("DB_PORT", "3306"))
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")

        # 👤 USER CONFIGURATION
        self.user_id = int(os.getenv("USER_ID"))

        # ⚙️ BOT CONFIGURATION
        self.testnet = os.getenv("TESTNET", "true").lower() == "true"
        self.environment: Literal["testnet", "production"] = os.getenv("ENVIRONMENT", "testnet")
        self.active_pair = os.getenv("ACTIVE_PAIR", "ETH")  # "ETH" o "BTC"
        self.full_pair = f"{self.active_pair}USDT"  # "ETHUSDT" o "BTCUSDT"

        # 🔑 BINANCE API KEYS
        if self.testnet:
            self.api_key = os.getenv("BINANCE_TESTNET_API_KEY")
            self.secret_key = os.getenv("BINANCE_TESTNET_SECRET_KEY")
        else:
            self.api_key = os.getenv("BINANCE_PRODUCTION_API_KEY")
            self.secret_key = os.getenv("BINANCE_PRODUCTION_SECRET_KEY")

        # 📧 EMAIL NOTIFICATIONS
        self.email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
        self.email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.email_port = int(os.getenv("EMAIL_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_to = os.getenv("EMAIL_TO")

        # 🔔 TELEGRAM NOTIFICATIONS
        self.telegram_enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        # ⚡ ADVANCED SETTINGS
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "3600"))  # segundos
        self.lookback_days = int(os.getenv("LOOKBACK_DAYS", "1825"))   # días
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # 🔐 ENCRYPTION
        self.encryption_key = os.getenv("ENCRYPTION_KEY")

    def validate(self):
        """Valida que todas las variables requeridas estén presentes"""
        required = [
            ("DB_HOST", self.db_host),
            ("DB_USER", self.db_user),
            ("DB_PASSWORD", self.db_password),
            ("DB_NAME", self.db_name),
            ("USER_ID", self.user_id),
            ("API_KEY", self.api_key),
            ("SECRET_KEY", self.secret_key),
        ]

        missing = [name for name, value in required if not value]

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        return True

    def get_database_url(self) -> str:
        """Retorna URL de conexión a la base de datos"""
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def __str__(self):
        """Representación string (oculta secrets)"""
        return f"""
BotConfig:
  Environment: {self.environment}
  User ID: {self.user_id}
  Pair: {self.full_pair}
  Testnet: {self.testnet}
  Database: {self.db_host}:{self.db_port}/{self.db_name}
  API Key: {'***' + self.api_key[-4:] if self.api_key else 'NOT SET'}
  Check Interval: {self.check_interval}s
  Debug: {self.debug}
"""


# Ejemplo de uso
if __name__ == "__main__":
    config = BotConfig()

    try:
        config.validate()
        print("✅ Configuración válida")
        print(config)
    except ValueError as e:
        print(f"❌ Error en configuración: {e}")
