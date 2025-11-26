"""
Database session management for dynamic database operations.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from app.core.config import Config
from app.core.logging_config import logger


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, db_directory: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            db_directory: Directory where database files are stored (defaults to Config.DB_DIRECTORY)
        """
        self.db_directory = Path(db_directory or Config.DB_DIRECTORY)
        self.db_directory.mkdir(parents=True, exist_ok=True)
        self._connections: Dict[str, sqlite3.Connection] = {}
    
    def get_db_path(self, db_name: str) -> Path:
        """
        Get the full path to a database file.
        
        Args:
            db_name: Name of the database
            
        Returns:
            Path to the database file
        """
        # Sanitize database name to prevent path traversal
        safe_name = "".join(c for c in db_name if c.isalnum() or c in ('_', '-'))
        if not safe_name:
            raise ValueError("Invalid database name")
        
        return self.db_directory / f"{safe_name}.db"
    
    @contextmanager
    def get_connection(self, db_name: str):
        """
        Get a database connection (context manager).
        
        Args:
            db_name: Name of the database
            
        Yields:
            SQLite connection object
        """
        db_path = self.get_db_path(db_name)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error for {db_name}: {e}", exc_info=True)
            raise
        finally:
            conn.close()
    
    def table_exists(self, db_name: str, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        with self.get_connection(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
    
    def get_table_schema(self, db_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Get the schema of a table.
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        with self.get_connection(db_name) as conn:
            cursor = conn.cursor()
            # Sanitize table name - only allow alphanumeric, underscore, hyphen
            if not all(c.isalnum() or c in ('_', '-') for c in table_name):
                raise ValueError(f"Invalid table name: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema = []
            for col in columns:
                schema.append({
                    "name": col[1],
                    "type": col[2],
                    "not_null": bool(col[3]),
                    "default_value": col[4],
                    "primary_key": bool(col[5])
                })
            return schema
    
    def get_all_tables(self, db_name: str) -> List[str]:
        """
        Get all table names in a database.
        
        Args:
            db_name: Name of the database
            
        Returns:
            List of table names
        """
        with self.get_connection(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_all_databases(self) -> List[str]:
        """
        Get all database names.
        
        Returns:
            List of database names (without .db extension)
        """
        db_files = list(self.db_directory.glob("*.db"))
        return [db.stem for db in db_files]


# Global database manager instance
db_manager = DatabaseManager()
