"""
Ejemplo de conexión a la base de datos desde el bot
Este archivo muestra cómo el bot debe conectarse y trabajar con la DB
"""

import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config_example import BotConfig
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BotDatabase:
    """Manejador de base de datos para el bot"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.engine = None
        self.Session = None

    def connect(self):
        """Conectar a la base de datos"""
        try:
            # Crear engine de SQLAlchemy
            database_url = self.config.get_database_url()
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=self.config.debug
            )

            # Crear session factory
            self.Session = sessionmaker(bind=self.engine)

            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info(f"✅ Conectado a la base de datos: {self.config.db_host}/{self.config.db_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            raise

    def get_session(self):
        """Obtener una sesión de base de datos"""
        if not self.Session:
            self.connect()
        return self.Session()

    def get_bot_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Obtener la configuración del bot desde la tabla bot_configurations

        Returns:
            Dict con la configuración o None si no existe
        """
        session = self.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT
                        stop_loss_percent,
                        position_size_percent,
                        take_profit_1_percent,
                        take_profit_2_percent,
                        take_profit_3_percent,
                        buy_threshold,
                        regime_filter_enabled,
                        adaptive_threshold,
                        is_active
                    FROM bot_configurations
                    WHERE user_id = :user_id
                      AND pair = :pair
                      AND environment = :environment
                      AND is_active = 1
                """),
                {
                    "user_id": self.config.user_id,
                    "pair": self.config.full_pair,
                    "environment": self.config.environment
                }
            ).fetchone()

            if not result:
                logger.warning(f"⚠️ No se encontró configuración para user_id={self.config.user_id}, pair={self.config.full_pair}")
                return None

            return {
                "stop_loss_percent": float(result[0]),
                "position_size_percent": float(result[1]),
                "take_profit_1_percent": float(result[2]),
                "take_profit_2_percent": float(result[3]),
                "take_profit_3_percent": float(result[4]),
                "buy_threshold": float(result[5]),
                "regime_filter_enabled": bool(result[6]),
                "adaptive_threshold": bool(result[7]),
                "is_active": bool(result[8])
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración: {e}")
            return None
        finally:
            session.close()

    def get_bot_state(self) -> Optional[Dict[str, Any]]:
        """
        Obtener el estado actual del bot desde bot_states

        Returns:
            Dict con el estado o None si no existe
        """
        session = self.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT
                        in_position,
                        entry_price,
                        entry_time,
                        current_price,
                        position_amount,
                        position_original,
                        tp1_executed,
                        tp2_executed,
                        current_pnl_usd,
                        current_pnl_percent,
                        regime,
                        probability,
                        available_capital
                    FROM bot_states
                    WHERE user_id = :user_id
                      AND pair = :pair
                      AND environment = :environment
                """),
                {
                    "user_id": self.config.user_id,
                    "pair": self.config.full_pair,
                    "environment": self.config.environment
                }
            ).fetchone()

            if not result:
                logger.info(f"ℹ️ No existe estado previo, creando nuevo...")
                return None

            return {
                "in_position": bool(result[0]),
                "entry_price": float(result[1]) if result[1] else None,
                "entry_time": result[2],
                "current_price": float(result[3]) if result[3] else None,
                "position_amount": float(result[4]) if result[4] else None,
                "position_original": float(result[5]) if result[5] else None,
                "tp1_executed": bool(result[6]),
                "tp2_executed": bool(result[7]),
                "current_pnl_usd": float(result[8]) if result[8] else None,
                "current_pnl_percent": float(result[9]) if result[9] else None,
                "regime": result[10],
                "probability": float(result[11]) if result[11] else None,
                "available_capital": float(result[12]) if result[12] else None
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo estado: {e}")
            return None
        finally:
            session.close()

    def update_bot_state(self, state_data: Dict[str, Any]):
        """
        Actualizar el estado del bot en la tabla bot_states

        Args:
            state_data: Dict con los campos a actualizar
        """
        session = self.get_session()
        try:
            # Verificar si existe
            exists = session.execute(
                text("""
                    SELECT id FROM bot_states
                    WHERE user_id = :user_id AND pair = :pair AND environment = :environment
                """),
                {
                    "user_id": self.config.user_id,
                    "pair": self.config.full_pair,
                    "environment": self.config.environment
                }
            ).fetchone()

            if exists:
                # UPDATE
                session.execute(
                    text("""
                        UPDATE bot_states
                        SET in_position = :in_position,
                            current_price = :current_price,
                            current_pnl_usd = :current_pnl_usd,
                            current_pnl_percent = :current_pnl_percent,
                            regime = :regime,
                            probability = :probability,
                            available_capital = :available_capital,
                            last_check = NOW(),
                            last_signal_action = :last_signal_action
                        WHERE user_id = :user_id AND pair = :pair AND environment = :environment
                    """),
                    {
                        "user_id": self.config.user_id,
                        "pair": self.config.full_pair,
                        "environment": self.config.environment,
                        **state_data
                    }
                )
            else:
                # INSERT
                session.execute(
                    text("""
                        INSERT INTO bot_states
                        (user_id, pair, environment, in_position, current_price,
                         current_pnl_usd, current_pnl_percent, regime, probability,
                         available_capital, last_signal_action, last_check)
                        VALUES
                        (:user_id, :pair, :environment, :in_position, :current_price,
                         :current_pnl_usd, :current_pnl_percent, :regime, :probability,
                         :available_capital, :last_signal_action, NOW())
                    """),
                    {
                        "user_id": self.config.user_id,
                        "pair": self.config.full_pair,
                        "environment": self.config.environment,
                        **state_data
                    }
                )

            session.commit()
            logger.info(f"✅ Estado actualizado correctamente")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error actualizando estado: {e}")
            raise
        finally:
            session.close()

    def save_trade(self, trade_data: Dict[str, Any]):
        """
        Guardar un trade en la tabla trades

        Args:
            trade_data: Dict con los datos del trade
        """
        session = self.get_session()
        try:
            session.execute(
                text("""
                    INSERT INTO trades
                    (user_id, pair, environment, entry_price, entry_time, entry_amount,
                     entry_regime, entry_probability, entry_volatility, status, created_at)
                    VALUES
                    (:user_id, :pair, :environment, :entry_price, :entry_time, :entry_amount,
                     :entry_regime, :entry_probability, :entry_volatility, 'OPEN', NOW())
                """),
                {
                    "user_id": self.config.user_id,
                    "pair": self.config.full_pair,
                    "environment": self.config.environment,
                    **trade_data
                }
            )

            session.commit()
            logger.info(f"✅ Trade guardado: {trade_data}")

        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error guardando trade: {e}")
            raise
        finally:
            session.close()


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Cargar configuración
    config = BotConfig()
    config.validate()

    # Conectar a la base de datos
    db = BotDatabase(config)
    db.connect()

    # Obtener configuración del bot
    bot_config = db.get_bot_configuration()
    if bot_config:
        print(f"✅ Configuración del bot: {bot_config}")
    else:
        print("❌ No se encontró configuración")

    # Obtener estado del bot
    state = db.get_bot_state()
    if state:
        print(f"✅ Estado actual: {state}")
    else:
        print("ℹ️ No hay estado previo")

    # Actualizar estado (ejemplo)
    db.update_bot_state({
        "in_position": False,
        "current_price": 2500.50,
        "current_pnl_usd": 0.0,
        "current_pnl_percent": 0.0,
        "regime": "BULL",
        "probability": 0.75,
        "available_capital": 1000.0,
        "last_signal_action": "HOLD"
    })

    print("✅ Ejemplo completado")
