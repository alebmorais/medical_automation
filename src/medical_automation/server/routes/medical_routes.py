"""Medical phrases API routes."""
from flask import Blueprint, jsonify, request

from ...config import config
from ...utils.logger import get_logger
from ...utils.db_manager import DatabaseManager

logger = get_logger(__name__)
medical_bp = Blueprint('medical', __name__)

# Initialize database manager
db = DatabaseManager(config.MEDICAL_DB_PATH, config.MEDICAL_SQL_FILE)


@medical_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all medical categories."""
    try:
        query = "SELECT DISTINCT categoria FROM frases ORDER BY categoria"
        rows = db.execute_query(query)
        categories = [row['categoria'] for row in rows]
        logger.info(f"Retrieved {len(categories)} categories")
        return jsonify(categories), 200
    except Exception as e:
        logger.error(f"Error fetching categories: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch categories'}), 500


@medical_bp.route('/phrases/<category>', methods=['GET'])
def get_phrases(category):
    """
    Get all phrases for a specific category.
    
    Args:
        category: Category name
    """
    try:
        query = "SELECT frase FROM frases WHERE categoria = ? ORDER BY frase"
        rows = db.execute_query(query, (category,))
        phrases = [row['frase'] for row in rows]
        logger.info(f"Retrieved {len(phrases)} phrases for category: {category}")
        return jsonify(phrases), 200
    except Exception as e:
        logger.error(f"Error fetching phrases for {category}: {e}", exc_info=True)
        return jsonify({'error': f'Failed to fetch phrases for {category}'}), 500


@medical_bp.route('/phrases', methods=['POST'])
def add_phrase():
    """Add a new medical phrase."""
    try:
        data = request.get_json()
        
        if not data or 'categoria' not in data or 'frase' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        category = data['categoria'].strip()
        phrase = data['frase'].strip()
        
        if not category or not phrase:
            return jsonify({'error': 'Category and phrase cannot be empty'}), 400
        
        query = "INSERT INTO frases (categoria, frase) VALUES (?, ?)"
        db.execute_update(query, (category, phrase))
        
        logger.info(f"Added phrase to category {category}: {phrase}")
        return jsonify({'message': 'Phrase added successfully'}), 201
        
    except Exception as e:
        logger.error(f"Error adding phrase: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add phrase'}), 500


@medical_bp.route('/phrases/<int:phrase_id>', methods=['DELETE'])
def delete_phrase(phrase_id):
    """
    Delete a medical phrase by ID.
    
    Args:
        phrase_id: ID of the phrase to delete
    """
    try:
        query = "DELETE FROM frases WHERE id = ?"
        rows_affected = db.execute_update(query, (phrase_id,))
        
        if rows_affected == 0:
            return jsonify({'error': 'Phrase not found'}), 404
        
        logger.info(f"Deleted phrase with ID: {phrase_id}")
        return jsonify({'message': 'Phrase deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting phrase {phrase_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete phrase'}), 500


@medical_bp.route('/search', methods=['GET'])
def search_phrases():
    """Search for phrases containing the query string."""
    try:
        query_param = request.args.get('q', '').strip()
        
        if not query_param:
            return jsonify({'error': 'Search query cannot be empty'}), 400
        
        query = """
            SELECT id, categoria, frase 
            FROM frases 
            WHERE frase LIKE ? OR categoria LIKE ?
            ORDER BY categoria, frase
        """
        search_term = f"%{query_param}%"
        rows = db.execute_query(query, (search_term, search_term))
        
        results = [
            {
                'id': row['id'],
                'categoria': row['categoria'],
                'frase': row['frase']
            }
            for row in rows
        ]
        
        logger.info(f"Search for '{query_param}' returned {len(results)} results")
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error searching phrases: {e}", exc_info=True)
        return jsonify({'error': 'Failed to search phrases'}), 500