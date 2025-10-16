"""
Medical Database Manager
Handles all database operations for medical phrases and categories.
"""
import os
import sys
import sqlite3
from typing import List, Optional, Dict, Any
from utils.database_bootstrap import DatabaseBootstrap
from models.medical_phrase import MedicalPhrase


class MedicalDatabaseManager:
    """Manages database connections and operations for medical phrases."""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the medical database manager.
        
        Args:
            db_path: Path to the SQLite database file. Auto-resolves if not provided.
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up to project root from db/ directory
        self.base_dir = os.path.dirname(self.base_dir)
        self.db_path = self.resolve_database_path(db_path)
        self.bootstrap = DatabaseBootstrap(self.base_dir)
        self.verify_database()
    
    def resolve_database_path(self, preferred_path: Optional[str]) -> str:
        """
        Determine the database path considering multiple possibilities.
        
        Args:
            preferred_path: Explicitly provided database path.
            
        Returns:
            Resolved absolute path to the database file.
        """
        candidates = []
        
        # Priority order: explicit argument, environment variables, default paths
        if preferred_path:
            candidates.append(preferred_path)
        
        # Environment variables
        env_candidates = [
            os.environ.get("AUTOMATION_DB_PATH"),
            os.environ.get("DB_PATH"),
        ]
        candidates.extend(filter(None, env_candidates))
        
        # Default locations relative to project root
        script_dir = self.base_dir
        parent_dir = os.path.dirname(script_dir)
        default_locations = [
            os.path.join(script_dir, "automation.db"),
            os.path.join(script_dir, "database", "automation.db"),
            os.path.join(parent_dir, "automation.db"),
            os.path.join(parent_dir, "database", "automation.db"),
        ]
        candidates.extend(default_locations)
        
        # Normalize paths and remove duplicates
        normalized = []
        seen = set()
        for path in candidates:
            if not path:
                continue
            full_path = os.path.abspath(os.path.expanduser(path))
            if full_path not in seen:
                normalized.append(full_path)
                seen.add(full_path)
        
        if not normalized:
            return os.path.join(script_dir, "automation.db")
        
        # Return first existing path
        for path in normalized:
            if os.path.exists(path):
                return path
        
        # No existing path found: use first candidate for creation
        return normalized[0]
    
    def verify_database(self, rebuilt: bool = False) -> None:
        """
        Verify that the database exists and has data.
        
        Args:
            rebuilt: Internal flag to prevent infinite recursion.
            
        Raises:
            SystemExit: If database cannot be created or verified.
        """
        if not os.path.exists(self.db_path):
            print(f"AVISO: Banco de dados não encontrado em {self.db_path}")
            print("Tentando criar automaticamente a partir do arquivo SQL de referência...")
            if self.bootstrap.bootstrap_database(self.db_path, overwrite=False):
                self.verify_database(rebuilt=True)
                return
            print("ERRO: Não foi possível localizar ou criar o banco de dados.")
            sys.exit(1)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM frases")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                if not rebuilt and self.bootstrap.bootstrap_database(self.db_path, overwrite=True):
                    self.verify_database(rebuilt=True)
                    return
                print("AVISO: Banco de dados vazio")
            else:
                print(f"✓ Banco de dados OK: {count} frases encontradas")
        except Exception as e:
            print(f"ERRO no banco de dados: {e}")
            if not rebuilt and self.bootstrap.bootstrap_database(self.db_path, overwrite=True):
                self.verify_database(rebuilt=True)
                return
            sys.exit(1)
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection.
        
        Returns:
            sqlite3.Connection: Database connection.
        """
        return sqlite3.connect(self.db_path)
    
    def get_categorias_principais(self) -> List[str]:
        """
        Get all main categories.
        
        Returns:
            List of category names.
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute("SELECT DISTINCT categoria_principal FROM frases")
            categorias = [row[0] for row in cursor]
            conn.close()
            return categorias
        except Exception as e:
            print(f"Erro ao buscar categorias: {e}")
            return []
    
    def get_subcategorias(self, categoria_principal: str) -> List[str]:
        """
        Get subcategories for a given main category.
        
        Args:
            categoria_principal: Main category name.
            
        Returns:
            List of subcategory names, sorted alphabetically.
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute(
                "SELECT DISTINCT subcategoria FROM frases WHERE categoria_principal = ? ORDER BY subcategoria",
                (categoria_principal,)
            )
            subcategorias = [row[0] for row in cursor]
            conn.close()
            return subcategorias
        except Exception as e:
            print(f"Erro ao buscar subcategorias: {e}")
            return []
    
    def get_frases(
        self,
        categoria_principal: Optional[str] = None,
        subcategoria: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get medical phrases with optional filters.
        
        Args:
            categoria_principal: Filter by main category (optional).
            subcategoria: Filter by subcategory (optional).
            
        Returns:
            List of phrase dictionaries with all fields.
        """
        try:
            conn = self.get_connection()
            
            if categoria_principal and subcategoria:
                cursor = conn.execute(
                    "SELECT * FROM frases WHERE categoria_principal = ? AND subcategoria = ? ORDER BY ordem",
                    (categoria_principal, subcategoria)
                )
            elif categoria_principal:
                cursor = conn.execute(
                    "SELECT * FROM frases WHERE categoria_principal = ? ORDER BY subcategoria, ordem",
                    (categoria_principal,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM frases ORDER BY categoria_principal, subcategoria, ordem"
                )
            
            frases = []
            for row in cursor:
                phrase = MedicalPhrase.from_db_row(row)
                frases.append(phrase.to_dict())
            
            conn.close()
            return frases
        except Exception as e:
            print(f"Erro ao buscar frases: {e}")
            return []
    
    def get_phrase_by_id(self, phrase_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single phrase by its ID.
        
        Args:
            phrase_id: The phrase ID.
            
        Returns:
            Dictionary with phrase data or None if not found.
        """
        try:
            conn = self.get_connection()
            cursor = conn.execute("SELECT * FROM frases WHERE id = ?", (phrase_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                phrase = MedicalPhrase.from_db_row(row)
                return phrase.to_dict()
            return None
        except Exception as e:
            print(f"Erro ao buscar frase por ID: {e}")
            return None
