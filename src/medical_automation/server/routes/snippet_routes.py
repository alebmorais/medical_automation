"""Snippet expansion API routes."""
from flask import Blueprint, jsonify, request

from ...config import config
from ...utils.logger import get_logger
from ...utils.db_manager import DatabaseManager

logger = get_logger(__name__)
snippet_bp = Blueprint('snippets', __name__)

# Initialize database manager
db = DatabaseManager(config.SNIPPET_DB_PATH, config.SNIPPET_SQL_FILE)


@snippet_bp.route('/', methods=['GET'])
def get_all_snippets():
    """Get all snippets."""
    try:
        query = "SELECT id, abbreviation, full_text FROM snippets ORDER BY abbreviation"
        rows = db.execute_query(query)
        
        snippets = [
            {
                'id': row['id'],
                'abbreviation': row['abbreviation'],
                'full_text': row['full_text']
            }
            for row in rows
        ]
        
        logger.info(f"Retrieved {len(snippets)} snippets")
        return jsonify(snippets), 200
        
    except Exception as e:
        logger.error(f"Error fetching snippets: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch snippets'}), 500


@snippet_bp.route('/<abbreviation>', methods=['GET'])
def get_snippet(abbreviation):
    """
    Get a snippet by abbreviation.
    
    Args:
        abbreviation: Snippet abbreviation
    """
    try:
        query = "SELECT full_text FROM snippets WHERE abbreviation = ?"
        rows = db.execute_query(query, (abbreviation,))
        
        if not rows:
            return jsonify({'error': 'Snippet not found'}), 404
        
        full_text = rows[0]['full_text']
        logger.info(f"Retrieved snippet for abbreviation: {abbreviation}")
        return jsonify({'full_text': full_text}), 200
        
    except Exception as e:
        logger.error(f"Error fetching snippet {abbreviation}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch snippet'}), 500


@snippet_bp.route('/', methods=['POST'])
def add_snippet():
    """Add a new snippet."""
    try:
        data = request.get_json()
        
        if not data or 'abbreviation' not in data or 'full_text' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        abbreviation = data['abbreviation'].strip()
        full_text = data['full_text'].strip()
        
        if not abbreviation or not full_text:
            return jsonify({'error': 'Abbreviation and text cannot be empty'}), 400
        
        # Check if abbreviation already exists
        check_query = "SELECT id FROM snippets WHERE abbreviation = ?"
        existing = db.execute_query(check_query, (abbreviation,))
        
        if existing:
            return jsonify({'error': 'Abbreviation already exists'}), 409
        
        query = "INSERT INTO snippets (abbreviation, full_text) VALUES (?, ?)"
        db.execute_update(query, (abbreviation, full_text))
        
        logger.info(f"Added snippet: {abbreviation}")
        return jsonify({'message': 'Snippet added successfully'}), 201
        
    except Exception as e:
        logger.error(f"Error adding snippet: {e}", exc_info=True)
        return jsonify({'error': 'Failed to add snippet'}), 500


@snippet_bp.route('/<int:snippet_id>', methods=['PUT'])
def update_snippet(snippet_id):
    """
    Update an existing snippet.
    
    Args:
        snippet_id: ID of the snippet to update
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        abbreviation = data.get('abbreviation', '').strip()
        full_text = data.get('full_text', '').strip()
        
        if not abbreviation or not full_text:
            return jsonify({'error': 'Abbreviation and text cannot be empty'}), 400
        
        query = """
            UPDATE snippets 
            SET abbreviation = ?, full_text = ? 
            WHERE id = ?
        """
        rows_affected = db.execute_update(query, (abbreviation, full_text, snippet_id))
        
        if rows_affected == 0:
            return jsonify({'error': 'Snippet not found'}), 404
        
        logger.info(f"Updated snippet with ID: {snippet_id}")
        return jsonify({'message': 'Snippet updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error updating snippet {snippet_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update snippet'}), 500


@snippet_bp.route('/<int:snippet_id>', methods=['DELETE'])
def delete_snippet(snippet_id):
    """
    Delete a snippet by ID.
    
    Args:
        snippet_id: ID of the snippet to delete
    """
    try:
        query = "DELETE FROM snippets WHERE id = ?"
        rows_affected = db.execute_update(query, (snippet_id,))
        
        if rows_affected == 0:
            return jsonify({'error': 'Snippet not found'}), 404
        
        logger.info(f"Deleted snippet with ID: {snippet_id}")
        return jsonify({'message': 'Snippet deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting snippet {snippet_id}: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete snippet'}), 500