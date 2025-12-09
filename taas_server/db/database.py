"""Database connection and session management."""

import threading
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session

from taas_server.db.models import Base


class DatabaseManager:
    """Thread-safe singleton database manager."""
    
    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls, database_url: Optional[str] = None) -> "DatabaseManager":
        """Create or return singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, database_url: Optional[str] = None) -> None:
        """Initialize database manager."""
        if self._initialized:
            return
        
        self.database_url = database_url or "sqlite:///taas.db"
        self.engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        self._initialized = True
        
        self._initialize_engine()
    
    def _initialize_engine(self) -> None:
        """Initialize the database engine."""
        # SQLite-specific settings for better performance
        connect_args = {}
        if "sqlite" in self.database_url:
            connect_args = {"check_same_thread": False}
        
        self.engine = create_engine(
            self.database_url,
            connect_args=connect_args,
            pool_pre_ping=True,  # Verify connections before using
            echo=False,  # Set to True for SQL debugging
        )
        
        # Create session factory
        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        
        # Create scoped session for thread-local sessions
        self._scoped_session = scoped_session(self._session_factory)
    
    def create_tables(self) -> None:
        """Create all database tables."""
        if self.engine is None:
            raise RuntimeError("Database engine not initialized")
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        if self.engine is None:
            raise RuntimeError("Database engine not initialized")
        Base.metadata.drop_all(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session (context manager)."""
        if self._scoped_session is None:
            raise RuntimeError("Database not initialized")
        
        session = self._scoped_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_scoped_session(self) -> Session:
        """Get a thread-local scoped session."""
        if self._scoped_session is None:
            raise RuntimeError("Database not initialized")
        return self._scoped_session()
    
    def close(self) -> None:
        """Close database connections."""
        if self._scoped_session:
            self._scoped_session.remove()
        if self.engine:
            self.engine.dispose()


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def init_database(database_url: Optional[str] = None) -> DatabaseManager:
    """Initialize the global database manager."""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager


def get_db_manager() -> DatabaseManager:
    """Get the global database manager."""
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager
