"""
Bot endpoints for trading bot state, trades, and performance
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Literal
import logging
from datetime import datetime

from app.database import get_db
from app.models.schemas import (
    BotStateResponse,
    BotStateData,
    TradesResponse,
    TradesPaginatedResponse,
    TradeData,
    PaginationInfo,
    PerformanceResponse,
    PerformanceData,
    ErrorResponse
)
from app.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bot", tags=["Bot"])

# Valid trading pairs
VALID_PAIRS = ["ETHUSDT", "BTCUSDT"]


@router.get("/state/{pair}", response_model=BotStateResponse, status_code=status.HTTP_200_OK)
async def get_bot_state(
    pair: Literal["ETHUSDT", "BTCUSDT"],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current bot state for a specific trading pair

    - Returns latest bot state including position, PnL, and market analysis
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        # Query latest bot state
        result = db.execute(
            text("""
                SELECT
                    id, user_id, pair, environment, in_position,
                    entry_price, entry_time, current_price, position_amount, position_original,
                    tp1_executed, tp2_executed,
                    current_pnl_usd, current_pnl_percent,
                    regime, probability, volatility, threshold_used,
                    available_capital,
                    total_trades, winning_trades, trades_blocked,
                    last_check, last_signal_action
                FROM bot_states
                WHERE user_id = :user_id AND pair = :pair
                ORDER BY last_check DESC
                LIMIT 1
            """),
            {"user_id": user_id, "pair": pair}
        ).fetchone()

        if not result:
            # Return default state if no data
            default_state = BotStateData(
                id=0,
                user_id=user_id,
                pair=pair,
                environment="testnet",
                in_position=False,
                tp1_executed=False,
                tp2_executed=False,
                tp3_executed=False,
                total_trades=0,
                winning_trades=0,
                blocked_trades=0
            )
            return BotStateResponse(success=True, data=default_state)

        # Convert result to dict
        bot_state = BotStateData(
            id=result[0],
            user_id=result[1],
            pair=result[2],
            environment=result[3],
            in_position=bool(result[4]),
            entry_price=result[5],
            entry_time=result[6],
            current_price=result[7],
            position_amount=result[8],
            position_original=result[9],
            tp1_executed=bool(result[10]),
            tp2_executed=bool(result[11]),
            tp3_executed=False,  # Not in real schema
            pnl_usd=result[12],  # current_pnl_usd
            pnl_percent=result[13],  # current_pnl_percent
            stop_loss_price=None,  # Not in real schema
            stop_loss_percent=None,  # Not in real schema
            tp1_price=None,  # Not in real schema
            tp1_percent=None,  # Not in real schema
            tp2_price=None,  # Not in real schema
            tp2_percent=None,  # Not in real schema
            tp3_price=None,  # Not in real schema
            tp3_percent=None,  # Not in real schema
            regime=result[14],
            probability=result[15],
            volatility=result[16],
            available_capital=result[18],
            total_pnl=None,  # Not in real schema
            total_pnl_percent=None,  # Not in real schema
            total_trades=result[19],
            winning_trades=result[20],
            blocked_trades=result[21],  # trades_blocked
            last_check=result[22]
        )

        return BotStateResponse(success=True, data=bot_state)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_bot_state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/trades/recent/{pair}", response_model=TradesResponse, status_code=status.HTTP_200_OK)
async def get_recent_trades(
    pair: Literal["ETHUSDT", "BTCUSDT"],
    limit: int = Query(default=10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent trades for a specific trading pair

    - Returns most recent closed trades
    - Limit parameter controls number of trades returned (1-100)
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        # Query recent trades
        results = db.execute(
            text("""
                SELECT
                    id, pair, entry_price, exit_price, entry_time, exit_time,
                    entry_amount, pnl_usd, pnl_percent, exit_reason, status,
                    TIMESTAMPDIFF(HOUR, entry_time, exit_time) as duration
                FROM trades
                WHERE user_id = :user_id AND pair = :pair AND status = 'CLOSED'
                ORDER BY exit_time DESC
                LIMIT :limit
            """),
            {"user_id": user_id, "pair": pair, "limit": limit}
        ).fetchall()

        trades = []
        for row in results:
            trade = TradeData(
                id=row[0],
                pair=row[1],
                entry_price=row[2],
                exit_price=row[3],
                entry_time=row[4],
                exit_time=row[5],
                amount=row[6],  # entry_amount from DB
                pnl_usd=row[7],
                pnl_percent=row[8],
                exit_reason=row[9],
                status=row[10],
                duration=row[11]
            )
            trades.append(trade)

        return TradesResponse(success=True, data=trades)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_recent_trades: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/trades", response_model=TradesPaginatedResponse, status_code=status.HTTP_200_OK)
async def get_all_trades(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    pair: Optional[Literal["ETHUSDT", "BTCUSDT"]] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all trades with pagination

    - Returns paginated list of trades
    - Optional pair filter
    - Requires authentication
    """
    try:
        user_id = current_user["id"]
        offset = (page - 1) * limit

        # Build query with optional pair filter
        count_query = """
            SELECT COUNT(*) as total
            FROM trades
            WHERE user_id = :user_id
        """
        trades_query = """
            SELECT
                id, pair, entry_price, exit_price, entry_time, exit_time,
                entry_amount, pnl_usd, pnl_percent, exit_reason, status
            FROM trades
            WHERE user_id = :user_id
        """

        params = {"user_id": user_id}

        if pair:
            count_query += " AND pair = :pair"
            trades_query += " AND pair = :pair"
            params["pair"] = pair

        trades_query += " ORDER BY entry_time DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        # Get total count
        total_result = db.execute(text(count_query), params).fetchone()
        total = total_result[0] if total_result else 0
        total_pages = (total + limit - 1) // limit  # Ceiling division

        # Get trades
        results = db.execute(text(trades_query), params).fetchall()

        trades = []
        for row in results:
            trade = TradeData(
                id=row[0],
                pair=row[1],
                entry_price=row[2],
                exit_price=row[3],
                entry_time=row[4],
                exit_time=row[5],
                amount=row[6],
                pnl_usd=row[7],
                pnl_percent=row[8],
                exit_reason=row[9],
                status=row[10]
            )
            trades.append(trade)

        pagination = PaginationInfo(
            page=page,
            limit=limit,
            total=total,
            totalPages=total_pages
        )

        return TradesPaginatedResponse(
            success=True,
            data=trades,
            pagination=pagination
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_all_trades: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/performance", response_model=PerformanceResponse, status_code=status.HTTP_200_OK)
async def get_performance(
    pair: Optional[Literal["ETHUSDT", "BTCUSDT"]] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get performance statistics

    - Returns aggregated performance metrics
    - Optional pair filter
    - Requires authentication
    """
    try:
        user_id = current_user["id"]

        # Build query with optional pair filter
        query = """
            SELECT
                pair,
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as winning_trades,
                COALESCE(SUM(pnl_usd), 0) as total_pnl,
                COALESCE(AVG(pnl_percent), 0) as avg_pnl_percent,
                COALESCE(MAX(pnl_usd), 0) as best_trade,
                COALESCE(MIN(pnl_usd), 0) as worst_trade,
                (SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) / COUNT(*)) * 100 as win_rate
            FROM trades
            WHERE user_id = :user_id AND status = 'CLOSED'
        """

        params = {"user_id": user_id}

        if pair:
            query += " AND pair = :pair"
            params["pair"] = pair

        query += " GROUP BY pair"

        results = db.execute(text(query), params).fetchall()

        performance_list = []
        for row in results:
            perf = PerformanceData(
                pair=row[0],
                total_trades=row[1],
                winning_trades=row[2],
                total_pnl=float(row[3]),
                avg_pnl_percent=float(row[4]),
                best_trade=float(row[5]),
                worst_trade=float(row[6]),
                win_rate=float(row[7])
            )
            performance_list.append(perf)

        return PerformanceResponse(success=True, data=performance_list)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
