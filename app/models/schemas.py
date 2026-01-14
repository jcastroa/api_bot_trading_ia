"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# STANDARD RESPONSES
# ============================================================================

class StandardResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: Optional[str] = None
    code: Optional[str] = None


class StandardDataResponse(BaseModel):
    """Standard API response with data"""
    success: bool
    data: dict


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth authentication"""
    idToken: str = Field(..., description="Firebase ID token")
    email: EmailStr = Field(..., description="User email")
    displayName: str = Field(..., description="User display name")
    photoURL: Optional[str] = Field(None, description="User photo URL")
    uid: str = Field(..., description="Firebase UID")


class UserResponse(BaseModel):
    """User data in response"""
    id: int
    email: str
    name: str
    photoURL: Optional[str] = None


class AuthResponse(BaseModel):
    """Response for successful authentication"""
    success: bool
    token: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh"""
    idToken: str = Field(..., description="New Firebase ID token")


class TokenResponse(BaseModel):
    """Response for token refresh"""
    success: bool
    token: str


class ValidateResponse(BaseModel):
    """Response for token validation"""
    success: bool
    valid: bool
    user: Optional[UserResponse] = None


# ============================================================================
# BOT STATE SCHEMAS
# ============================================================================

class BotStateData(BaseModel):
    """Bot state data"""
    id: int
    user_id: int
    pair: str
    environment: str
    in_position: bool
    entry_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    current_price: Optional[float] = None
    position_amount: Optional[float] = None
    position_original: Optional[float] = None
    tp1_executed: bool = False
    tp2_executed: bool = False
    tp3_executed: bool = False
    pnl_usd: Optional[float] = None
    pnl_percent: Optional[float] = None
    stop_loss_price: Optional[float] = None
    stop_loss_percent: Optional[float] = None
    tp1_price: Optional[float] = None
    tp1_percent: Optional[float] = None
    tp2_price: Optional[float] = None
    tp2_percent: Optional[float] = None
    tp3_price: Optional[float] = None
    tp3_percent: Optional[float] = None
    regime: Optional[str] = None
    probability: Optional[float] = None
    volatility: Optional[float] = None
    threshold_used: Optional[float] = None  # Adaptive threshold for entry signals
    available_capital: Optional[float] = None
    total_pnl: Optional[float] = None
    total_pnl_percent: Optional[float] = None
    total_trades: int = 0
    winning_trades: int = 0
    blocked_trades: int = 0
    last_check: Optional[datetime] = None
    last_signal_action: Optional[str] = None

    class Config:
        from_attributes = True


class BotStateResponse(BaseModel):
    """Response for bot state"""
    success: bool
    data: BotStateData


# ============================================================================
# TRADE SCHEMAS
# ============================================================================

class TradeData(BaseModel):
    """Trade data"""
    id: int
    pair: str
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    amount: float
    pnl_usd: Optional[float] = None
    pnl_percent: Optional[float] = None
    exit_reason: Optional[str] = None
    status: str
    duration: Optional[int] = None  # in hours

    class Config:
        from_attributes = True


class TradesResponse(BaseModel):
    """Response for trades list"""
    success: bool
    data: List[TradeData]


class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    limit: int
    total: int
    totalPages: int


class TradesPaginatedResponse(BaseModel):
    """Response for paginated trades"""
    success: bool
    data: List[TradeData]
    pagination: PaginationInfo


# ============================================================================
# PERFORMANCE SCHEMAS
# ============================================================================

class PerformanceData(BaseModel):
    """Performance statistics for a pair"""
    pair: str
    total_trades: int
    winning_trades: int
    total_pnl: float
    avg_pnl_percent: float
    best_trade: float
    worst_trade: float
    win_rate: float


class PerformanceResponse(BaseModel):
    """Response for performance statistics"""
    success: bool
    data: List[PerformanceData]


# ============================================================================
# CONFIGURATION SCHEMAS
# ============================================================================

class ConfigStatusData(BaseModel):
    """Configuration status data"""
    hasKeys: bool
    environment: str
    updatedAt: Optional[datetime] = None


class ConfigStatusResponse(BaseModel):
    """Response for configuration status"""
    success: bool
    data: ConfigStatusData


class SaveConfigRequest(BaseModel):
    """Request body for saving API configuration"""
    environment: Literal["testnet", "production"] = Field(..., description="Environment type")
    apiKey: str = Field(..., description="Binance API key (plain text)")
    secretKey: str = Field(..., description="Binance secret key (plain text)")


class ContainerStatusData(BaseModel):
    """Container status data"""
    status: Literal["running", "stopped", "restarting", "error"]
    lastRestart: Optional[datetime] = None
    containerId: Optional[str] = None


class ContainerStatusResponse(BaseModel):
    """Response for container status"""
    success: bool
    data: ContainerStatusData


class BotConfigData(BaseModel):
    """Bot configuration data"""
    id: int
    user_id: int
    pair: str
    environment: str
    stop_loss_percent: float
    position_size_percent: float
    take_profit_1_percent: float
    take_profit_2_percent: float
    take_profit_3_percent: float
    buy_threshold: float
    regime_filter_enabled: bool
    adaptive_threshold: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BotConfigResponse(BaseModel):
    """Response for bot configuration"""
    success: bool
    data: BotConfigData


# ============================================================================
# ERROR RESPONSE
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response format"""
    success: bool = False
    message: str
    code: Optional[str] = None
