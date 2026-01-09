"""
Database configuration and connection management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=10,        # Maximum number of connections
    max_overflow=20      # Maximum overflow connections
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session

    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """
    Test database connection

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def init_db():
    """
    Initialize database (create tables if they don't exist)
    Note: In production, use migrations (Alembic) instead
    """
    try:
        # Test connection first
        if test_connection():
            logger.info("Database initialized successfully")
        else:
            logger.error("Database initialization failed")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
