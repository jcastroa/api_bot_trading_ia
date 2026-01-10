"""
Configuration endpoints for API keys, bot settings, and container status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Literal
import logging
from datetime import datetime

from app.database import get_db
from app.models.schemas import (
    ConfigStatusResponse,
    ConfigStatusData,
    SaveConfigRequest,
    StandardResponse,
    ContainerStatusResponse,
    ContainerStatusData,
    BotConfigResponse,
    BotConfigData,
    ErrorResponse
)
from app.middleware.auth_middleware import get_current_user
from app.services.encryption_service import encryption_service
from app.services.docker_service import docker_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["Configuration"])


@router.get("/{environment}", response_model=ConfigStatusResponse, status_code=status.HTTP_200_OK)
async def get_config_status(
    environment: Literal["testnet", "production"],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get API configuration status (checks if keys exist, but doesn't return them)

    - Returns whether API keys are configured
    - Does NOT return the actual keys (security)
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        # Check if configuration exists
        result = db.execute(
            text("""
                SELECT id, environment, updated_at
                FROM api_configurations
                WHERE user_id = :user_id AND environment = :environment
            """),
            {"user_id": user_id, "environment": environment}
        ).fetchone()

        if result:
            config_data = ConfigStatusData(
                hasKeys=True,
                environment=environment,
                updatedAt=result[2]
            )
        else:
            config_data = ConfigStatusData(
                hasKeys=False,
                environment=environment,
                updatedAt=None
            )

        return ConfigStatusResponse(success=True, data=config_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_config_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/save", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def save_config(
    request: SaveConfigRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save API keys (encrypted)

    - Encrypts API keys using AES-256
    - Stores encrypted keys in database
    - Creates default bot configurations if they don't exist
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        # Encrypt the API keys
        encrypted_api_key, encrypted_secret_key = encryption_service.encrypt_api_keys(
            request.apiKey,
            request.secretKey
        )

        # Check if configuration already exists
        existing = db.execute(
            text("""
                SELECT id FROM api_configurations
                WHERE user_id = :user_id AND environment = :environment
            """),
            {"user_id": user_id, "environment": request.environment}
        ).fetchone()

        if existing:
            # Update existing configuration
            db.execute(
                text("""
                    UPDATE api_configurations
                    SET api_key_encrypted = :api_key,
                        secret_key_encrypted = :secret_key,
                        updated_at = NOW()
                    WHERE user_id = :user_id AND environment = :environment
                """),
                {
                    "user_id": user_id,
                    "environment": request.environment,
                    "api_key": encrypted_api_key,
                    "secret_key": encrypted_secret_key
                }
            )
        else:
            # Insert new configuration
            db.execute(
                text("""
                    INSERT INTO api_configurations
                    (user_id, environment, api_key_encrypted, secret_key_encrypted, created_at, updated_at)
                    VALUES (:user_id, :environment, :api_key, :secret_key, NOW(), NOW())
                """),
                {
                    "user_id": user_id,
                    "environment": request.environment,
                    "api_key": encrypted_api_key,
                    "secret_key": encrypted_secret_key
                }
            )

        # Create default bot configurations for both pairs if they don't exist
        for pair in ["ETHUSDT", "BTCUSDT"]:
            bot_config_exists = db.execute(
                text("""
                    SELECT id FROM bot_configurations
                    WHERE user_id = :user_id AND pair = :pair AND environment = :environment
                """),
                {"user_id": user_id, "pair": pair, "environment": request.environment}
            ).fetchone()

            if not bot_config_exists:
                db.execute(
                    text("""
                        INSERT INTO bot_configurations
                        (user_id, pair, environment, stop_loss_percent, position_size_percent,
                         take_profit_1_percent, take_profit_2_percent, take_profit_3_percent,
                         buy_threshold, regime_filter_enabled, adaptive_threshold, is_active,
                         created_at, updated_at)
                        VALUES
                        (:user_id, :pair, :environment, 4.5, 50.0, 5.0, 7.5, 10.0, 0.6, 1, 1, 1, NOW(), NOW())
                    """),
                    {"user_id": user_id, "pair": pair, "environment": request.environment}
                )

        db.commit()

        # Start bot containers automatically
        logger.info(f"🚀 Starting bot containers for user {user_id} in {request.environment}")
        container_results = docker_service.start_all_bots_for_user(
            db=db,
            user_id=user_id,
            environment=request.environment,
            image_name="trading-bot:latest"  # Change this to your image name
        )

        # Log results
        started_count = sum(1 for cid in container_results.values() if cid is not None)
        logger.info(f"✅ Started {started_count}/2 bot containers")

        if started_count == 0:
            logger.warning("⚠️ No containers were started. Make sure Docker image 'trading-bot:latest' exists")

        return StandardResponse(
            success=True,
            message=f"Configuración guardada correctamente. {started_count}/2 bots iniciados."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in save_config: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/container/status/{environment}", response_model=ContainerStatusResponse, status_code=status.HTTP_200_OK)
async def get_container_status(
    environment: Literal["testnet", "production"],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get bot/container status

    - Returns current status of the bot container
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        # Query container status
        result = db.execute(
            text("""
                SELECT status, last_restart, container_id
                FROM docker_containers
                WHERE user_id = :user_id AND environment = :environment
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"user_id": user_id, "environment": environment}
        ).fetchone()

        if result:
            container_data = ContainerStatusData(
                status=result[0],
                lastRestart=result[1],
                containerId=result[2]
            )
        else:
            # Return default status if no container found
            container_data = ContainerStatusData(
                status="stopped",
                lastRestart=None,
                containerId=None
            )

        return ContainerStatusResponse(success=True, data=container_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_container_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/bot/{pair}/{environment}", response_model=BotConfigResponse, status_code=status.HTTP_200_OK)
async def get_bot_config(
    pair: Literal["ETHUSDT", "BTCUSDT"],
    environment: Literal["testnet", "production"],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get bot configuration for a specific pair and environment

    - Returns bot trading parameters
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        # Query bot configuration
        result = db.execute(
            text("""
                SELECT
                    id, user_id, pair, environment,
                    stop_loss_percent, position_size_percent,
                    take_profit_1_percent, take_profit_2_percent, take_profit_3_percent,
                    buy_threshold, regime_filter_enabled, adaptive_threshold,
                    is_active, created_at, updated_at
                FROM bot_configurations
                WHERE user_id = :user_id AND pair = :pair AND environment = :environment
            """),
            {"user_id": user_id, "pair": pair, "environment": environment}
        ).fetchone()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot configuration not found"
            )

        bot_config = BotConfigData(
            id=result[0],
            user_id=result[1],
            pair=result[2],
            environment=result[3],
            stop_loss_percent=float(result[4]),
            position_size_percent=float(result[5]),
            take_profit_1_percent=float(result[6]),
            take_profit_2_percent=float(result[7]),
            take_profit_3_percent=float(result[8]),
            buy_threshold=float(result[9]),
            regime_filter_enabled=bool(result[10]),
            adaptive_threshold=bool(result[11]),
            is_active=bool(result[12]),
            created_at=result[13],
            updated_at=result[14]
        )

        return BotConfigResponse(success=True, data=bot_config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_bot_config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/container/start/{environment}", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def start_containers(
    environment: Literal["testnet", "production"],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start bot containers for all pairs (ETHUSDT and BTCUSDT)

    - Creates and starts Docker containers
    - Passes API keys and configuration via environment variables
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        logger.info(f"🚀 Starting bot containers for user {user_id} in {environment}")

        # Start all bots
        results = docker_service.start_all_bots_for_user(
            db=db,
            user_id=user_id,
            environment=environment,
            image_name="trading-bot:latest"
        )

        started_count = sum(1 for cid in results.values() if cid is not None)

        if started_count == 0:
            return StandardResponse(
                success=False,
                message="No se pudo iniciar ningún contenedor. Verifica que la imagen Docker 'trading-bot:latest' exista."
            )

        return StandardResponse(
            success=True,
            message=f"{started_count}/2 contenedores iniciados correctamente"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in start_containers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/container/stop/{environment}", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def stop_containers(
    environment: Literal["testnet", "production"],
    current_user: dict = Depends(get_current_user)
):
    """
    Stop bot containers for all pairs

    - Stops running containers
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        logger.info(f"🛑 Stopping bot containers for user {user_id} in {environment}")

        results = docker_service.stop_all_bots_for_user(user_id, environment)
        stopped_count = sum(1 for success in results.values() if success)

        return StandardResponse(
            success=True,
            message=f"{stopped_count}/2 contenedores detenidos correctamente"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in stop_containers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/container/restart/{environment}", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def restart_containers(
    environment: Literal["testnet", "production"],
    current_user: dict = Depends(get_current_user)
):
    """
    Restart bot containers for all pairs

    - Useful when configuration changes or switching environments
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        logger.info(f"🔄 Restarting bot containers for user {user_id} in {environment}")

        pairs = ["ETHUSDT", "BTCUSDT"]
        restarted_count = 0

        for pair in pairs:
            success = docker_service.restart_container(user_id, pair, environment)
            if success:
                restarted_count += 1

        return StandardResponse(
            success=True,
            message=f"{restarted_count}/2 contenedores reiniciados correctamente"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in restart_containers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/container/toggle/{pair}/{environment}", response_model=StandardResponse, status_code=status.HTTP_200_OK)
async def toggle_pair_container(
    pair: Literal["ETHUSDT", "BTCUSDT"],
    environment: Literal["testnet", "production"],
    action: Literal["start", "stop"] = Query(..., description="Action to perform"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start or stop a specific pair container

    - Allows granular control over individual trading pairs
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        if action == "start":
            logger.info(f"🚀 Starting {pair} bot for user {user_id} in {environment}")
            container_id = docker_service.create_and_start_container(
                db=db,
                user_id=user_id,
                pair=pair,
                environment=environment,
                image_name="trading-bot:latest"
            )

            if container_id:
                return StandardResponse(
                    success=True,
                    message=f"Bot {pair} iniciado correctamente"
                )
            else:
                return StandardResponse(
                    success=False,
                    message=f"No se pudo iniciar el bot {pair}"
                )

        else:  # stop
            logger.info(f"🛑 Stopping {pair} bot for user {user_id} in {environment}")
            success = docker_service.stop_container(user_id, pair, environment)

            if success:
                return StandardResponse(
                    success=True,
                    message=f"Bot {pair} detenido correctamente"
                )
            else:
                return StandardResponse(
                    success=False,
                    message=f"No se pudo detener el bot {pair}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in toggle_pair_container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
