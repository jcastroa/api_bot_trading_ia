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
                        api_secret_encrypted = :secret_key,
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
                    (user_id, environment, api_key_encrypted, api_secret_encrypted, created_at, updated_at)
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

        return StandardResponse(
            success=True,
            message="Configuración guardada correctamente"
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
