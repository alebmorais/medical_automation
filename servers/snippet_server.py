"""
Snippet Server Module
Flask application initialization and server runner for snippet management.
"""
from flask import Flask
from api.snippet_routes import snippet_bp, init_snippet_database
from config.settings import SNIPPET_PORT, PRODUCTION_WARNING, PRODUCTION_EXAMPLE


def create_snippet_app() -> Flask:
    """
    Create and configure the Flask application for snippet management.
    
    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    
    # Register the snippet blueprint
    app.register_blueprint(snippet_bp)
    
    # Initialize database
    init_snippet_database()
    
    return app


def run_snippet_server(host: str = '127.0.0.1', port: int = None, debug: bool = False):
    """
    Run the snippet management server.
    
    Args:
        host: Host address to bind to. Default is localhost (127.0.0.1).
        port: Port number to use. Uses config default if not provided.
        debug: Enable debug mode (not recommended for production).
    """
    if port is None:
        port = SNIPPET_PORT
    
    app = create_snippet_app()
    
    print(f"✓ Servidor de snippets pronto em http://{host}:{port}")
    
    if not debug:
        print(PRODUCTION_WARNING)
        print(PRODUCTION_EXAMPLE)
    
    # Run the Flask development server
    # For production, use a WSGI server like Gunicorn or uWSGI
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # Run in safe mode if executed directly (debug disabled by default)
    run_snippet_server(debug=False)
