"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLASession
from contextlib import contextmanager
from typing import Generator

from mcp_framework.config import settings
from mcp_framework.storage.models import Base


class DatabaseManager:
    """Manages database connection and sessions."""
    
    def __init__(self, database_url: str = None):
        """Initialize database manager."""
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            echo=settings.log_level == "DEBUG"
        )
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
    
    def create_tables(self) -> None:
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[SQLASession, None, None]:
        """Get database session with automatic commit/rollback."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager
_db_manager: DatabaseManager = None


def init_database(database_url: str = None) -> DatabaseManager:
    """Initialize database."""
    global _db_manager
    _db_manager = DatabaseManager(database_url)
    _db_manager.create_tables()
    return _db_manager


def get_db_manager() -> DatabaseManager:
    """Get global database manager."""
    if _db_manager is None:
        return init_database()
    return _db_manager
