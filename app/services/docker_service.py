"""
Docker service for managing trading bot containers
"""
import docker
from docker.errors import DockerException, NotFound, APIError
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List, Dict
import logging

from app.config import settings
from app.services.encryption_service import encryption_service

logger = logging.getLogger(__name__)


class DockerService:
    """Service for managing Docker containers for trading bots"""

    def __init__(self):
        try:
            self.client = docker.from_env()
            logger.info("✅ Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"❌ Failed to initialize Docker client: {e}")
            self.client = None

    def _get_container_name(self, user_id: int, pair: str, environment: str) -> str:
        """Generate unique container name"""
        return f"bot-user{user_id}-{pair.lower()}-{environment}"

    def _get_api_keys(self, db: Session, user_id: int, environment: str) -> Optional[tuple]:
        """Get and decrypt API keys from database"""
        try:
            result = db.execute(
                text("""
                    SELECT api_key_encrypted, secret_key_encrypted
                    FROM api_configurations
                    WHERE user_id = :user_id AND environment = :environment AND is_active = 1
                """),
                {"user_id": user_id, "environment": environment}
            ).fetchone()

            if not result:
                logger.error(f"❌ No API keys found for user {user_id} in {environment}")
                return None

            # Decrypt keys
            api_key = encryption_service.decrypt(result[0])
            secret_key = encryption_service.decrypt(result[1])

            return api_key, secret_key

        except Exception as e:
            logger.error(f"❌ Error getting API keys: {e}")
            return None

    def _build_environment_vars(
        self,
        user_id: int,
        pair: str,
        environment: str,
        api_key: str,
        secret_key: str
    ) -> Dict[str, str]:
        """Build environment variables for the bot container"""

        # Prefix based on environment
        env_prefix = "BINANCE_TESTNET" if environment == "testnet" else "BINANCE_PRODUCTION"

        env_vars = {
            # Bot configuration
            "USER_ID": str(user_id),
            "PAIR": pair,
            "ENVIRONMENT": environment,

            # Binance API keys
            f"{env_prefix}_API_KEY": api_key,
            f"{env_prefix}_SECRET_KEY": secret_key,

            # Database configuration
            "DB_HOST": settings.db_host,
            "DB_PORT": str(settings.db_port),
            "DB_NAME": settings.db_name,
            "DB_USER": settings.db_user,
            "DB_PASSWORD": settings.db_password,

            # Encryption key (for bot to encrypt/decrypt if needed)
            "ENCRYPTION_KEY": settings.encryption_key,

            # Email configuration (from settings or env)
            "EMAIL_ENABLED": "true",  # You can make this configurable
        }

        return env_vars

    def create_and_start_container(
        self,
        db: Session,
        user_id: int,
        pair: str,
        environment: str,
        image_name: str = "trading-bot:latest"
    ) -> Optional[str]:
        """
        Create and start a trading bot container

        Args:
            db: Database session
            user_id: User ID
            pair: Trading pair (ETHUSDT or BTCUSDT)
            environment: testnet or production
            image_name: Docker image name

        Returns:
            Container ID if successful, None otherwise
        """
        if not self.client:
            logger.error("❌ Docker client not initialized")
            return None

        container_name = self._get_container_name(user_id, pair, environment)

        try:
            # Check if container already exists
            existing_container = self._get_existing_container(container_name)
            if existing_container:
                logger.info(f"🔄 Container {container_name} already exists, removing it first")
                existing_container.remove(force=True)

            # Get API keys
            keys = self._get_api_keys(db, user_id, environment)
            if not keys:
                return None

            api_key, secret_key = keys

            # Build environment variables
            env_vars = self._build_environment_vars(user_id, pair, environment, api_key, secret_key)

            logger.info(f"🚀 Creating container: {container_name}")
            logger.info(f"   Image: {image_name}")
            logger.info(f"   Environment: {environment}")
            logger.info(f"   Pair: {pair}")

            # Create container
            container = self.client.containers.run(
                image=image_name,
                name=container_name,
                environment=env_vars,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                network_mode="bridge",
                labels={
                    "user_id": str(user_id),
                    "pair": pair,
                    "environment": environment,
                    "managed_by": "trading_bot_api"
                }
            )

            container_id = container.id
            logger.info(f"✅ Container created and started: {container_id[:12]}")

            # Save to database
            self._save_container_to_db(db, user_id, container_id, environment, "running", image_name)

            return container_id

        except NotFound:
            logger.error(f"❌ Docker image '{image_name}' not found. Please build it first.")
            return None
        except APIError as e:
            logger.error(f"❌ Docker API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error creating container: {e}")
            return None

    def stop_container(self, user_id: int, pair: str, environment: str) -> bool:
        """Stop a trading bot container"""
        if not self.client:
            return False

        container_name = self._get_container_name(user_id, pair, environment)

        try:
            container = self._get_existing_container(container_name)
            if not container:
                logger.warning(f"⚠️ Container {container_name} not found")
                return False

            logger.info(f"🛑 Stopping container: {container_name}")
            container.stop(timeout=10)
            logger.info(f"✅ Container stopped: {container_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error stopping container: {e}")
            return False

    def remove_container(self, user_id: int, pair: str, environment: str) -> bool:
        """Remove a trading bot container"""
        if not self.client:
            return False

        container_name = self._get_container_name(user_id, pair, environment)

        try:
            container = self._get_existing_container(container_name)
            if not container:
                logger.warning(f"⚠️ Container {container_name} not found")
                return False

            logger.info(f"🗑️ Removing container: {container_name}")
            container.remove(force=True)
            logger.info(f"✅ Container removed: {container_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error removing container: {e}")
            return False

    def restart_container(self, user_id: int, pair: str, environment: str) -> bool:
        """Restart a trading bot container"""
        if not self.client:
            return False

        container_name = self._get_container_name(user_id, pair, environment)

        try:
            container = self._get_existing_container(container_name)
            if not container:
                logger.warning(f"⚠️ Container {container_name} not found")
                return False

            logger.info(f"🔄 Restarting container: {container_name}")
            container.restart(timeout=10)
            logger.info(f"✅ Container restarted: {container_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Error restarting container: {e}")
            return False

    def get_container_status(self, user_id: int, pair: str, environment: str) -> Optional[Dict]:
        """Get container status"""
        if not self.client:
            return None

        container_name = self._get_container_name(user_id, pair, environment)

        try:
            container = self._get_existing_container(container_name)
            if not container:
                return {
                    "status": "stopped",
                    "container_id": None,
                    "name": container_name
                }

            container.reload()  # Refresh container data

            return {
                "status": container.status,
                "container_id": container.id[:12],
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs['Created'],
                "started_at": container.attrs['State'].get('StartedAt')
            }

        except Exception as e:
            logger.error(f"❌ Error getting container status: {e}")
            return None

    def start_all_bots_for_user(
        self,
        db: Session,
        user_id: int,
        environment: str,
        image_name: str = "trading-bot:latest"
    ) -> Dict[str, Optional[str]]:
        """
        Start bot containers for all pairs (ETHUSDT and BTCUSDT)

        Returns:
            Dict with container IDs: {"ETHUSDT": "container_id", "BTCUSDT": "container_id"}
        """
        results = {}
        pairs = ["ETHUSDT", "BTCUSDT"]

        for pair in pairs:
            logger.info(f"🚀 Starting bot for {pair}...")
            container_id = self.create_and_start_container(
                db, user_id, pair, environment, image_name
            )
            results[pair] = container_id

            if container_id:
                logger.info(f"✅ {pair} bot started: {container_id[:12]}")
            else:
                logger.error(f"❌ Failed to start {pair} bot")

        return results

    def stop_all_bots_for_user(
        self,
        user_id: int,
        environment: str
    ) -> Dict[str, bool]:
        """Stop all bot containers for a user in a specific environment"""
        results = {}
        pairs = ["ETHUSDT", "BTCUSDT"]

        for pair in pairs:
            logger.info(f"🛑 Stopping bot for {pair}...")
            success = self.stop_container(user_id, pair, environment)
            results[pair] = success

        return results

    def _get_existing_container(self, container_name: str):
        """Get existing container by name"""
        try:
            return self.client.containers.get(container_name)
        except NotFound:
            return None

    def _save_container_to_db(
        self,
        db: Session,
        user_id: int,
        container_id: str,
        environment: str,
        status: str,
        image_version: str
    ):
        """Save container info to database"""
        try:
            # Check if exists
            existing = db.execute(
                text("""
                    SELECT id FROM docker_containers
                    WHERE user_id = :user_id AND environment = :environment
                """),
                {"user_id": user_id, "environment": environment}
            ).fetchone()

            if existing:
                # Update
                db.execute(
                    text("""
                        UPDATE docker_containers
                        SET container_id = :container_id,
                            status = :status,
                            image_version = :image_version,
                            last_restart = NOW()
                        WHERE user_id = :user_id AND environment = :environment
                    """),
                    {
                        "user_id": user_id,
                        "environment": environment,
                        "container_id": container_id,
                        "status": status,
                        "image_version": image_version
                    }
                )
            else:
                # Insert
                db.execute(
                    text("""
                        INSERT INTO docker_containers
                        (user_id, container_id, environment, status, image_version, last_restart, created_at)
                        VALUES (:user_id, :container_id, :environment, :status, :image_version, NOW(), NOW())
                    """),
                    {
                        "user_id": user_id,
                        "container_id": container_id,
                        "environment": environment,
                        "status": status,
                        "image_version": image_version
                    }
                )

            db.commit()
            logger.info(f"✅ Container info saved to database")

        except Exception as e:
            logger.error(f"❌ Error saving container to DB: {e}")
            db.rollback()


# Global instance
docker_service = DockerService()
