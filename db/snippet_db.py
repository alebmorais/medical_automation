"""
Snippet Database Manager
Handles all database operations for text snippets.
"""
import sqlite3
from typing import List, Optional, Dict, Any
from config.settings import SNIPPET_DB_PATH


class SnippetDatabaseManager:
    """Manages database connections and operations for snippets."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the snippet database manager.
        
        Args:
            db_path: Path to the SQLite database file. Uses config default if not provided.
        """
        self.db_path = db_path or SNIPPET_DB_PATH
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection.
        
        Returns:
            sqlite3.Connection: Database connection with Row factory.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_database(self) -> None:
        """Create the snippets table if it doesn't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    abbreviation TEXT NOT NULL UNIQUE,
                    phrase TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("✓ Banco de dados de snippets inicializado.")
    
    def get_all_snippets(self) -> Dict[str, str]:
        """
        Get all snippets as a dictionary for the expander client.
        
        Returns:
            Dict mapping abbreviations to phrases.
        """
        with self.get_connection() as conn:
            snippets = conn.execute('SELECT abbreviation, phrase FROM snippets').fetchall()
            return {row['abbreviation']: row['phrase'] for row in snippets}
    
    def get_all_snippets_full(self) -> List[Dict[str, Any]]:
        """
        Get all snippets with full details.
        
        Returns:
            List of snippet dictionaries with all fields.
        """
        with self.get_connection() as conn:
            snippets = conn.execute(
                'SELECT id, abbreviation, phrase, usage_count FROM snippets'
            ).fetchall()
            return [dict(row) for row in snippets]
    
    def create_snippet(self, abbreviation: str, phrase: str) -> bool:
        """
        Create a new snippet.
        
        Args:
            abbreviation: The snippet abbreviation/trigger.
            phrase: The expanded text.
            
        Returns:
            True if created successfully, False if abbreviation already exists.
            
        Raises:
            sqlite3.IntegrityError: If abbreviation already exists.
        """
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO snippets (abbreviation, phrase) VALUES (?, ?)',
                (abbreviation, phrase)
            )
            conn.commit()
            return True
    
    def update_snippet(self, abbreviation: str, phrase: str) -> int:
        """
        Update an existing snippet.
        
        Args:
            abbreviation: The snippet abbreviation to update.
            phrase: The new expanded text.
            
        Returns:
            Number of rows affected (0 if snippet not found, 1 if updated).
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                'UPDATE snippets SET phrase = ? WHERE abbreviation = ?',
                (phrase, abbreviation)
            )
            conn.commit()
            return cursor.rowcount
    
    def delete_snippet(self, abbreviation: str) -> int:
        """
        Delete a snippet.
        
        Args:
            abbreviation: The snippet abbreviation to delete.
            
        Returns:
            Number of rows affected (0 if snippet not found, 1 if deleted).
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                'DELETE FROM snippets WHERE abbreviation = ?',
                (abbreviation,)
            )
            conn.commit()
            return cursor.rowcount
    
    def get_snippet_by_abbreviation(self, abbreviation: str) -> Optional[Dict[str, Any]]:
        """
        Get a single snippet by its abbreviation.
        
        Args:
            abbreviation: The snippet abbreviation to find.
            
        Returns:
            Dictionary with snippet data or None if not found.
        """
        with self.get_connection() as conn:
            row = conn.execute(
                'SELECT id, abbreviation, phrase, usage_count, created_at FROM snippets WHERE abbreviation = ?',
                (abbreviation,)
            ).fetchone()
            return dict(row) if row else None
    
    def increment_usage_count(self, abbreviation: str) -> int:
        """
        Increment the usage count for a snippet.
        
        Args:
            abbreviation: The snippet abbreviation.
            
        Returns:
            Number of rows affected.
        """
        with self.get_connection() as conn:
            cursor = conn.execute(
                'UPDATE snippets SET usage_count = usage_count + 1 WHERE abbreviation = ?',
                (abbreviation,)
            )
            conn.commit()
            return cursor.rowcount
