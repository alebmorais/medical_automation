"""
Database Bootstrap Utilities
Handles database creation and initialization from SQL files.
"""
import os
import sqlite3
from typing import List, Optional
from config.settings import SQL_FILE_NAMES, SQL_SUBDIRECTORY_FILES


class DatabaseBootstrap:
    """Utility class for bootstrapping databases from SQL files."""
    
    def __init__(self, base_dir: str):
        """
        Initialize the bootstrap utility.
        
        Args:
            base_dir: Base directory to search for SQL files.
        """
        self.base_dir = base_dir
    
    def find_sql_candidates(self) -> List[str]:
        """
        Find possible SQL file paths for database initialization.
        
        Returns:
            List of existing SQL file paths, in order of preference.
        """
        candidates = []
        locations = [self.base_dir, os.path.dirname(self.base_dir)]
        
        for location in locations:
            if not location:
                continue
            
            # Add standard SQL file names
            for name in SQL_FILE_NAMES:
                candidates.append(os.path.join(location, name))
            
            # Add subdirectory SQL files
            for subpath in SQL_SUBDIRECTORY_FILES:
                candidates.append(os.path.join(location, subpath))
        
        # Filter to only existing files, preserving order and removing duplicates
        existing = []
        seen = set()
        for path in candidates:
            full_path = os.path.abspath(path)
            if full_path in seen:
                continue
            seen.add(full_path)
            if os.path.exists(full_path):
                existing.append(full_path)
        
        return existing
    
    def bootstrap_database(self, db_path: str, overwrite: bool = False) -> bool:
        """
        Create a database from an SQL file if available.
        
        Args:
            db_path: Path where the database should be created.
            overwrite: If True, remove existing database before creating.
            
        Returns:
            True if database was created successfully, False otherwise.
        """
        sql_candidates = self.find_sql_candidates()
        if not sql_candidates:
            print("Nenhum arquivo SQL de referência encontrado para criar o banco de dados.")
            return False
        
        # Create target directory if needed
        target_dir = os.path.dirname(db_path)
        if target_dir and not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except OSError as err:
                print(f"Erro ao criar diretório do banco de dados: {err}")
                return False
        
        # Remove old database if overwrite is requested
        if overwrite and os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError as err:
                print(f"Não foi possível remover o banco de dados antigo: {err}")
                return False
        
        # Try each SQL file until one works
        for sql_path in sql_candidates:
            try:
                with open(sql_path, "r", encoding="utf-8") as sql_file:
                    script = sql_file.read()
                
                with sqlite3.connect(db_path) as conn:
                    conn.executescript(script)
                
                print(f"✓ Banco de dados criado em {db_path} a partir de {sql_path}")
                return True
            except Exception as err:
                print(f"Falha ao criar banco de dados a partir de {sql_path}: {err}")
        
        return False
    
    def verify_database_exists(self, db_path: str) -> bool:
        """
        Check if a database file exists.
        
        Args:
            db_path: Path to the database file.
            
        Returns:
            True if the database file exists, False otherwise.
        """
        return os.path.exists(db_path)
    
    def get_table_count(self, db_path: str, table_name: str) -> Optional[int]:
        """
        Get the number of rows in a database table.
        
        Args:
            db_path: Path to the database file.
            table_name: Name of the table to count.
            
        Returns:
            Number of rows in the table, or None if error occurs.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            print(f"Erro ao contar linhas na tabela {table_name}: {e}")
            return None
