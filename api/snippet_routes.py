"""
Snippet API Routes
Flask Blueprint for snippet management endpoints.
"""
import datetime
import sqlite3
from flask import Blueprint, jsonify, request
from db.snippet_db import SnippetDatabaseManager

# Create Blueprint
snippet_bp = Blueprint('snippets', __name__)

# Initialize database manager
snippet_db = SnippetDatabaseManager()


@snippet_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for snippet server.
    
    Returns:
        JSON response with status and timestamp.
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    })


@snippet_bp.route('/snippets', methods=['GET'])
def get_snippets():
    """
    Get all snippets for the expander client.
    
    Returns:
        JSON object mapping abbreviations to phrases.
    """
    snippets = snippet_db.get_all_snippets()
    return jsonify(snippets)


@snippet_bp.route('/snippets/all', methods=['GET'])
def get_all_snippets_full():
    """
    Get all snippets with full details for the manager GUI.
    
    Returns:
        JSON array of snippet objects with all fields.
    """
    snippets = snippet_db.get_all_snippets_full()
    return jsonify(snippets)


@snippet_bp.route('/snippets', methods=['POST'])
def create_snippet():
    """
    Create a new snippet.
    
    Request body:
        {
            "abbreviation": "abbr",
            "phrase": "expanded text"
        }
    
    Returns:
        201: Success message
        400: Missing required fields
        409: Abbreviation already exists
    """
    data = request.get_json()
    
    if not data or 'abbreviation' not in data or 'phrase' not in data:
        return jsonify({"error": "Missing abbreviation or phrase"}), 400
    
    try:
        snippet_db.create_snippet(data['abbreviation'], data['phrase'])
        return jsonify({"message": "Snippet created successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Abbreviation already exists"}), 409


@snippet_bp.route('/snippets/<path:abbreviation>', methods=['PUT'])
def update_snippet(abbreviation):
    """
    Update an existing snippet.
    
    Args:
        abbreviation: The snippet abbreviation to update.
    
    Request body:
        {
            "phrase": "new expanded text"
        }
    
    Returns:
        200: Success message
        400: Missing phrase field
    """
    data = request.get_json()
    
    if not data or 'phrase' not in data:
        return jsonify({"error": "Missing phrase"}), 400
    
    snippet_db.update_snippet(abbreviation, data['phrase'])
    return jsonify({"message": "Snippet updated successfully"})


@snippet_bp.route('/snippets/<path:abbreviation>', methods=['DELETE'])
def delete_snippet(abbreviation):
    """
    Delete a snippet.
    
    Args:
        abbreviation: The snippet abbreviation to delete.
    
    Returns:
        200: Success message
    """
    snippet_db.delete_snippet(abbreviation)
    return jsonify({"message": "Snippet deleted successfully"})


def init_snippet_database():
    """Initialize the snippet database tables."""
    snippet_db.initialize_database()
