"""
Data model for Snippet entity.
Represents a text snippet with abbreviation and expansion.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Snippet:
    """Represents a text snippet with abbreviation and expansion."""
    
    abbreviation: str
    phrase: str
    id: Optional[int] = None
    usage_count: int = 0
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert snippet to dictionary representation."""
        return {
            'id': self.id,
            'abbreviation': self.abbreviation,
            'phrase': self.phrase,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Snippet':
        """Create snippet from dictionary."""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            elif isinstance(data['created_at'], datetime):
                created_at = data['created_at']
        
        return cls(
            id=data.get('id'),
            abbreviation=data['abbreviation'],
            phrase=data['phrase'],
            usage_count=data.get('usage_count', 0),
            created_at=created_at
        )
