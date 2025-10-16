"""
Configuration settings for Medical Automation Server.
Centralized configuration for database paths, ports, and other settings.
"""
import os

# Database configuration
SNIPPET_DB_PATH = os.environ.get('SNIPPET_DB_PATH', 'snippets.db')
MEDICAL_DB_PATH = os.environ.get('AUTOMATION_DB_PATH') or os.environ.get('DB_PATH', 'automation.db')
SQL_BOOTSTRAP_FILE = 'SQL2.sql'

# Server configuration
SNIPPET_PORT = int(os.environ.get('SNIPPET_PORT', 5000))
MEDICAL_PORT = int(os.environ.get('MEDICAL_PORT', 8080))

# Flask configuration
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

# Database SQL file candidates
SQL_FILE_NAMES = [
    'SQL2.sql',
    'database.sql',
    'automation.sql',
]

# Additional SQL file locations
SQL_SUBDIRECTORY_FILES = [
    'database/SQL_File.sql',
    'database/SQL_File',
    'database/automation.sql',
]

# Default database locations (relative to project root)
DEFAULT_DB_LOCATIONS = [
    'automation.db',
    'database/automation.db',
]

# Production warning
PRODUCTION_WARNING = "⚠️ Atenção: Não utilize o servidor Flask embutido em produção. Use Gunicorn ou outro WSGI server."
PRODUCTION_EXAMPLE = "Exemplo para produção: gunicorn -w 4 -b 0.0.0.0:5000 server:snippet_app"
