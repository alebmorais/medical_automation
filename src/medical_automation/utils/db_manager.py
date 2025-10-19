"""Database management utilities with connection pooling and error handling."""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import config
from .logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Thread-safe database manager with connection pooling."""
    
    def __init__(self, db_path: str, sql_init_file: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            sql_init_file: Optional SQL file to initialize database
        """
        self.db_path = Path(db_path)
        self.sql_init_file = Path(sql_init_file) if sql_init_file else None
        self._local = threading.local()
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if it doesn't exist
        if not self.db_path.exists() and self.sql_init_file:
            self._initialize_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                timeout=config.DB_TIMEOUT,
                check_same_thread=config.DB_CHECK_SAME_THREAD
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for database cursor.
        
        Yields:
            sqlite3.Cursor: Database cursor
            
        Example:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
    
    def _initialize_database(self):
        """Initialize database from SQL file."""
        if not self.sql_init_file or not self.sql_init_file.exists():
            logger.warning(f"SQL init file not found: {self.sql_init_file}")
            return
        
        logger.info(f"Initializing database from {self.sql_init_file}")
        
        try:
            with open(self.sql_init_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            with self.get_cursor() as cursor:
                cursor.executescript(sql_script)
            
            logger.info(f"Database initialized successfully: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise
    
    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[sqlite3.Row]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of result rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_update(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> int:
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
    
    def execute_many(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> int:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def close(self):
        """Close database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            delattr(self._local, 'connection')
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()