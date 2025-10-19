"""
Configuration management for Medical Automation Suite.
Supports multiple environments (development, production) and uses environment variables.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Project paths
    BASE_DIR = Path(__file__).parent.parent.parent.absolute()
    SRC_DIR = BASE_DIR / "src"
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    SQL_DIR = BASE_DIR / "sql"
    
    # Server configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    MEDICAL_SERVER_PORT = int(os.getenv("MEDICAL_SERVER_PORT", "8080"))
    SNIPPET_SERVER_PORT = int(os.getenv("SNIPPET_SERVER_PORT", "5000"))
    
    # Database configuration
    MEDICAL_DB_PATH = os.getenv(
        "MEDICAL_DB_PATH", 
        str(DATA_DIR / "automation.db")
    )
    SNIPPET_DB_PATH = os.getenv(
        "SNIPPET_DB_PATH", 
        str(DATA_DIR / "snippets.db")
    )
    MEDICAL_SQL_FILE = str(SQL_DIR / "SQL2.sql")
    SNIPPET_SQL_FILE = str(SQL_DIR / "snippets_data.sql")
    
    # Client configuration
    DEFAULT_SERVER_IP = os.getenv("DEFAULT_SERVER_IP", "pi.local")
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE", str(10 * 1024 * 1024)))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Security settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # CORS settings for Flask
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Request timeout settings
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Database connection settings
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "5"))
    DB_CHECK_SAME_THREAD = os.getenv("DB_CHECK_SAME_THREAD", "True").lower() == "true"
    
    @classmethod
    def get_medical_server_url(cls, server_ip: Optional[str] = None) -> str:
        """Get the medical server URL."""
        ip = server_ip or cls.DEFAULT_SERVER_IP
        return f"http://{ip}:{cls.MEDICAL_SERVER_PORT}"
    
    @classmethod
    def get_snippet_server_url(cls, server_ip: Optional[str] = None) -> str:
        """Get the snippet server URL."""
        ip = server_ip or cls.DEFAULT_SERVER_IP
        return f"http://{ip}:{cls.SNIPPET_SERVER_PORT}"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.SQL_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        errors = []
        
        # Check if secret key is set in production
        if not cls.DEBUG and cls.SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("SECRET_KEY must be changed in production environment")
        
        # Check if SQL files exist
        if not Path(cls.MEDICAL_SQL_FILE).exists():
            errors.append(f"Medical SQL file not found: {cls.MEDICAL_SQL_FILE}")
        
        if not Path(cls.SNIPPET_SQL_FILE).exists():
            errors.append(f"Snippet SQL file not found: {cls.SNIPPET_SQL_FILE}")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        return True


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    
    @classmethod
    def validate_production_config(cls):
        """Additional production configuration validation."""
        super().validate()
        
        # Ensure secure settings in production
        if cls.SERVER_HOST == "0.0.0.0":
            import logging
            logging.warning(
                "Server is listening on all interfaces (0.0.0.0). "
                "Ensure firewall is properly configured."
            )


# Select configuration based on environment
ENV = os.getenv("ENVIRONMENT", "development").lower()
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()

# Ensure directories exist on import
config.ensure_directories()