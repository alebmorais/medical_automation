"""
Data model for Medical Phrase entity.
Represents a medical phrase with categories and content.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class MedicalPhrase:
    """Represents a medical phrase with categories and ordering."""
    
    nome: str
    conteudo: str
    categoria_principal: str
    subcategoria: str
    id: Optional[int] = None
    ordem: int = 0
    
    def to_dict(self):
        """Convert medical phrase to dictionary representation."""
        return {
            'id': self.id,
            'nome': self.nome,
            'conteudo': self.conteudo,
            'categoria_principal': self.categoria_principal,
            'subcategoria': self.subcategoria,
            'ordem': self.ordem
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MedicalPhrase':
        """Create medical phrase from dictionary."""
        return cls(
            id=data.get('id'),
            nome=data['nome'],
            conteudo=data['conteudo'],
            categoria_principal=data['categoria_principal'],
            subcategoria=data['subcategoria'],
            ordem=data.get('ordem', 0)
        )
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'MedicalPhrase':
        """
        Create medical phrase from database row.
        Expected format: (id, nome, conteudo, categoria_principal, subcategoria, ordem)
        """
        conteudo = row[2]
        if isinstance(conteudo, str):
            conteudo = conteudo.replace("\\n", "\n")
        
        return cls(
            id=row[0],
            nome=row[1],
            conteudo=conteudo,
            categoria_principal=row[3],
            subcategoria=row[4],
            ordem=row[5]
        )
