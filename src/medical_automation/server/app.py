"""Flask application factory for Medical Automation Suite."""
from flask import Flask
from flask_cors import CORS

from ..config import config
from ..utils.logger import setup_logger
from .routes import medical_bp, snippet_bp

logger = setup_logger(__name__, "server.log")


def create_app(config_override=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_override: Optional configuration object to override defaults
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Use provided config or default
    app_config = config_override or config
    
    # Configure Flask
    app.config['SECRET_KEY'] = app_config.SECRET_KEY
    app.config['DEBUG'] = app_config.DEBUG
    
    # Enable CORS
    CORS(app, origins=app_config.CORS_ORIGINS)
    
    # Register blueprints
    app.register_blueprint(medical_bp, url_prefix='/medical')
    app.register_blueprint(snippet_bp, url_prefix='/snippets')
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return {'status': 'healthy', 'version': '1.0.0'}, 200
    
    logger.info(f"Application created in {app_config.LOG_LEVEL} mode")
    
    return app