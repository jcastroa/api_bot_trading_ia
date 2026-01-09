"""
Main FastAPI application
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import sys

from app.config import settings
from app.database import test_connection, init_db
from app.routers import auth, bot, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="API for managing trading bot operations, configurations, and monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Cookie"],
    expose_headers=["Set-Cookie"]
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with headers and cookies"""
    logger.info(f"📥 Incoming request: {request.method} {request.url.path}")
    logger.info(f"   Origin: {request.headers.get('origin', 'Not set')}")
    logger.info(f"   User-Agent: {request.headers.get('user-agent', 'Not set')[:50]}...")

    # Log cookies
    if request.cookies:
        logger.info(f"   🍪 Cookies present: {list(request.cookies.keys())}")
        if 'auth_token' in request.cookies:
            logger.info(f"   🍪 auth_token: {request.cookies['auth_token'][:30]}...")
    else:
        logger.info(f"   🍪 No cookies in request")

    # Log Authorization header
    if 'authorization' in request.headers:
        auth_header = request.headers['authorization']
        logger.info(f"   🔑 Authorization header: {auth_header[:30]}...")
    else:
        logger.info(f"   🔑 No Authorization header")

    # Process request
    response = await call_next(request)

    # Log response
    logger.info(f"📤 Response: {response.status_code} for {request.method} {request.url.path}")

    # Log Set-Cookie headers if present
    if 'set-cookie' in response.headers:
        logger.info(f"   🍪 Setting cookie in response")

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": "Validation error",
            "code": "VALIDATION_ERROR",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Trading Bot API...")
    logger.info(f"Environment: {settings.api_env}")
    logger.info(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")

    # Test database connection
    if test_connection():
        logger.info("Database connection successful")
        init_db()
    else:
        logger.error("Database connection failed - some features may not work")

    # Log CORS configuration
    logger.info(f"CORS Origins: {settings.cors_origins}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Trading Bot API...")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint

    Returns API status and database connection status
    """
    db_status = test_connection()

    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "version": "1.0.0",
        "environment": settings.api_env
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint

    Returns basic API information
    """
    return {
        "message": "Trading Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(auth.router)
app.include_router(bot.router)
app.include_router(config.router)


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production,
        log_level="info"
    )
