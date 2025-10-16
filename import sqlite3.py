import sqlite3
from flask import Flask, jsonify, request
import datetime

app = Flask(__name__)
DATABASE = 'snippets.db'

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database and create tables if they don't exist."""
    with app.app_context():
        conn = get_db_connection()
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
        conn.close()
        print("Database initialized.")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/snippets', methods=['GET'])
def get_snippets():
    """Get all snippets."""
    conn = get_db_connection()
    snippets = conn.execute('SELECT abbreviation, phrase FROM snippets').fetchall()
    conn.close()
    return jsonify({row['abbreviation']: row['phrase'] for row in snippets})

@app.route('/snippets/all', methods=['GET'])
def get_all_snippets_full():
    """Get all snippets with full details."""
    conn = get_db_connection()
    snippets = conn.execute('SELECT id, abbreviation, phrase, usage_count FROM snippets').fetchall()
    conn.close()
    return jsonify([dict(row) for row in snippets])

@app.route('/snippets', methods=['POST'])
def create_snippet():
    """Create a new snippet."""
    data = request.get_json()
    if not data or 'abbreviation' not in data or 'phrase' not in data:
        return jsonify({"error": "Missing abbreviation or phrase"}), 400

    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO snippets (abbreviation, phrase) VALUES (?, ?)',
            (data['abbreviation'], data['phrase'])
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Abbreviation already exists"}), 409
    finally:
        conn.close()
    
    return jsonify({"message": "Snippet created successfully"}), 201

@app.route('/snippets/<string:abbreviation>', methods=['PUT'])
def update_snippet(abbreviation):
    """Update an existing snippet."""
    data = request.get_json()
    if not data or 'phrase' not in data:
        return jsonify({"error": "Missing phrase"}), 400

    conn = get_db_connection()
    conn.execute(
        'UPDATE snippets SET phrase = ? WHERE abbreviation = ?',
        (data['phrase'], abbreviation)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Snippet updated successfully"})

@app.route('/snippets/<string:abbreviation>', methods=['DELETE'])
def delete_snippet(abbreviation):
    """Delete a snippet."""
    conn = get_db_connection()
    conn.execute('DELETE FROM snippets WHERE abbreviation = ?', (abbreviation,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Snippet deleted successfully"})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)
