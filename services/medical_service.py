"""
Medical Service Layer
Business logic for medical phrase operations.
"""
from typing import List, Dict, Optional, Any
from db.medical_db import MedicalDatabaseManager


class MedicalPhraseService:
    """Service layer for medical phrase business logic."""
    
    def __init__(self, db_manager: Optional[MedicalDatabaseManager] = None, db_path: Optional[str] = None):
        """
        Initialize the medical phrase service.
        
        Args:
            db_manager: Database manager instance. Creates new one if not provided.
            db_path: Database path to use if creating new manager.
        """
        self.db = db_manager or MedicalDatabaseManager(db_path=db_path)
    
    def get_all_categories(self) -> List[str]:
        """
        Get all main categories.
        
        Returns:
            List of category names, sorted alphabetically.
        """
        categories = self.db.get_categorias_principais()
        return sorted(categories)
    
    def get_subcategories(self, categoria_principal: str) -> List[str]:
        """
        Get subcategories for a given main category.
        
        Args:
            categoria_principal: Main category name.
            
        Returns:
            List of subcategory names, sorted alphabetically.
            
        Raises:
            ValueError: If category name is empty.
        """
        if not categoria_principal or not categoria_principal.strip():
            raise ValueError("Category name cannot be empty")
        
        return self.db.get_subcategorias(categoria_principal.strip())
    
    def get_phrases(
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
            List of phrase dictionaries.
        """
        # Trim whitespace if provided
        if categoria_principal:
            categoria_principal = categoria_principal.strip()
        if subcategoria:
            subcategoria = subcategoria.strip()
        
        return self.db.get_frases(categoria_principal, subcategoria)
    
    def get_phrase_by_id(self, phrase_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single phrase by its ID.
        
        Args:
            phrase_id: The phrase ID.
            
        Returns:
            Dictionary with phrase data or None if not found.
            
        Raises:
            ValueError: If phrase_id is invalid.
        """
        if not isinstance(phrase_id, int) or phrase_id <= 0:
            raise ValueError("Invalid phrase ID")
        
        return self.db.get_phrase_by_id(phrase_id)
    
    def search_phrases(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for phrases by content.
        
        Args:
            query: Search query string.
            
        Returns:
            List of matching phrases.
        """
        if not query or not query.strip():
            return []
        
        query_lower = query.strip().lower()
        all_phrases = self.db.get_frases()
        
        # Filter phrases that match the query
        matching_phrases = []
        for phrase in all_phrases:
            # Check if query matches nome, conteudo, categoria, or subcategoria
            if (query_lower in phrase.get('nome', '').lower() or
                query_lower in phrase.get('conteudo', '').lower() or
                query_lower in phrase.get('categoria_principal', '').lower() or
                query_lower in phrase.get('subcategoria', '').lower()):
                matching_phrases.append(phrase)
        
        return matching_phrases
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about categories and phrases.
        
        Returns:
            Dictionary with various statistics.
        """
        categories = self.get_all_categories()
        all_phrases = self.db.get_frases()
        
        # Count phrases per category
        category_counts = {}
        for phrase in all_phrases:
            cat = phrase.get('categoria_principal', 'Unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Count subcategories
        subcategory_counts = {}
        for phrase in all_phrases:
            subcat = phrase.get('subcategoria', 'Unknown')
            subcategory_counts[subcat] = subcategory_counts.get(subcat, 0) + 1
        
        return {
            "total_categories": len(categories),
            "total_subcategories": len(subcategory_counts),
            "total_phrases": len(all_phrases),
            "phrases_per_category": category_counts,
            "phrases_per_subcategory": subcategory_counts
        }
    
    def get_phrases_by_category_tree(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Get all phrases organized by category and subcategory.
        
        Returns:
            Nested dictionary: {category: {subcategory: [phrases]}}
        """
        all_phrases = self.db.get_frases()
        
        tree = {}
        for phrase in all_phrases:
            cat = phrase.get('categoria_principal', 'Unknown')
            subcat = phrase.get('subcategoria', 'Unknown')
            
            if cat not in tree:
                tree[cat] = {}
            
            if subcat not in tree[cat]:
                tree[cat][subcat] = []
            
            tree[cat][subcat].append(phrase)
        
        return tree
    
    def validate_database(self) -> Dict[str, Any]:
        """
        Validate the database state.
        
        Returns:
            Dictionary with validation results.
        """
        try:
            categories = self.get_all_categories()
            all_phrases = self.db.get_frases()
            
            return {
                "valid": True,
                "total_categories": len(categories),
                "total_phrases": len(all_phrases),
                "message": "Database is valid and accessible"
            }
        except Exception as e:
            return {
                "valid": False,
                "message": f"Database validation failed: {str(e)}"
            }
