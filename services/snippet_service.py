"""
Snippet Service Layer
Business logic for snippet operations.
"""
from typing import List, Dict, Optional, Any
from db.snippet_db import SnippetDatabaseManager
from models.snippet import Snippet


class SnippetService:
    """Service layer for snippet business logic."""
    
    def __init__(self, db_manager: Optional[SnippetDatabaseManager] = None):
        """
        Initialize the snippet service.
        
        Args:
            db_manager: Database manager instance. Creates new one if not provided.
        """
        self.db = db_manager or SnippetDatabaseManager()
    
    def initialize(self) -> None:
        """Initialize the database schema."""
        self.db.initialize_database()
    
    def get_all_snippets_dict(self) -> Dict[str, str]:
        """
        Get all snippets as a simple dictionary.
        Useful for snippet expander clients.
        
        Returns:
            Dictionary mapping abbreviations to phrases.
        """
        return self.db.get_all_snippets()
    
    def get_all_snippets_detailed(self) -> List[Dict[str, Any]]:
        """
        Get all snippets with full details.
        
        Returns:
            List of snippet dictionaries with all fields.
        """
        return self.db.get_all_snippets_full()
    
    def create_snippet(self, abbreviation: str, phrase: str) -> Dict[str, Any]:
        """
        Create a new snippet with validation.
        
        Args:
            abbreviation: The snippet abbreviation/trigger.
            phrase: The expanded text.
            
        Returns:
            Dictionary with success status and message.
            
        Raises:
            ValueError: If validation fails.
        """
        # Validate inputs
        if not abbreviation or not abbreviation.strip():
            raise ValueError("Abbreviation cannot be empty")
        
        if not phrase or not phrase.strip():
            raise ValueError("Phrase cannot be empty")
        
        # Trim whitespace
        abbreviation = abbreviation.strip()
        phrase = phrase.strip()
        
        # Validate length
        if len(abbreviation) > 100:
            raise ValueError("Abbreviation too long (max 100 characters)")
        
        if len(phrase) > 10000:
            raise ValueError("Phrase too long (max 10000 characters)")
        
        # Create snippet
        try:
            self.db.create_snippet(abbreviation, phrase)
            return {
                "success": True,
                "message": "Snippet created successfully",
                "abbreviation": abbreviation
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to create snippet: {str(e)}"
            }
    
    def update_snippet(self, abbreviation: str, phrase: str) -> Dict[str, Any]:
        """
        Update an existing snippet with validation.
        
        Args:
            abbreviation: The snippet abbreviation to update.
            phrase: The new expanded text.
            
        Returns:
            Dictionary with success status and message.
            
        Raises:
            ValueError: If validation fails.
        """
        # Validate inputs
        if not phrase or not phrase.strip():
            raise ValueError("Phrase cannot be empty")
        
        phrase = phrase.strip()
        
        if len(phrase) > 10000:
            raise ValueError("Phrase too long (max 10000 characters)")
        
        # Update snippet
        rows_affected = self.db.update_snippet(abbreviation, phrase)
        
        if rows_affected == 0:
            return {
                "success": False,
                "message": "Snippet not found"
            }
        
        return {
            "success": True,
            "message": "Snippet updated successfully",
            "abbreviation": abbreviation
        }
    
    def delete_snippet(self, abbreviation: str) -> Dict[str, Any]:
        """
        Delete a snippet.
        
        Args:
            abbreviation: The snippet abbreviation to delete.
            
        Returns:
            Dictionary with success status and message.
        """
        rows_affected = self.db.delete_snippet(abbreviation)
        
        if rows_affected == 0:
            return {
                "success": False,
                "message": "Snippet not found"
            }
        
        return {
            "success": True,
            "message": "Snippet deleted successfully",
            "abbreviation": abbreviation
        }
    
    def get_snippet(self, abbreviation: str) -> Optional[Dict[str, Any]]:
        """
        Get a single snippet by abbreviation.
        
        Args:
            abbreviation: The snippet abbreviation to find.
            
        Returns:
            Snippet dictionary or None if not found.
        """
        return self.db.get_snippet_by_abbreviation(abbreviation)
    
    def record_usage(self, abbreviation: str) -> bool:
        """
        Record that a snippet was used.
        
        Args:
            abbreviation: The snippet abbreviation that was used.
            
        Returns:
            True if usage was recorded, False otherwise.
        """
        rows_affected = self.db.increment_usage_count(abbreviation)
        return rows_affected > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about snippets.
        
        Returns:
            Dictionary with various statistics.
        """
        snippets = self.db.get_all_snippets_full()
        
        total_snippets = len(snippets)
        total_usage = sum(s.get('usage_count', 0) for s in snippets)
        
        # Find most used snippet
        most_used = None
        if snippets:
            most_used = max(snippets, key=lambda s: s.get('usage_count', 0))
        
        return {
            "total_snippets": total_snippets,
            "total_usage": total_usage,
            "most_used": most_used.get('abbreviation') if most_used else None,
            "most_used_count": most_used.get('usage_count', 0) if most_used else 0
        }
