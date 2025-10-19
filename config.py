"""
Configuration management for Medical Automation Suite.
Supports multiple environments (development, production) and uses environment variables.
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Base configuration class."""
    
    # Project paths
    BASE_DIR = Path(__file__).parent.absolute()
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Server configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    MEDICAL_SERVER_PORT = int(os.getenv("MEDICAL_SERVER_PORT", "8080"))
    SNIPPET_SERVER_PORT = int(os.getenv("SNIPPET_SERVER_PORT", "5000"))
    
    # Database configuration
    MEDICAL_DB_PATH = os.getenv("MEDICAL_DB_PATH", str(DATA_DIR / "automation.db"))
    SNIPPET_DB_PATH = os.getenv("SNIPPET_DB_PATH", str(DATA_DIR / "snippets.db"))
    MEDICAL_SQL_FILE = str(BASE_DIR / "SQL2.sql")
    SNIPPET_SQL_FILE = str(BASE_DIR / "snippets_data.sql")
    
    # Client configuration
    DEFAULT_SERVER_IP = os.getenv("DEFAULT_SERVER_IP", "pi.local")
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Security settings
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
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


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    LOG_LEVEL = "WARNING"


# Select configuration based on environment
ENV = os.getenv("ENVIRONMENT", "development").lower()
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()

# Ensure directories exist on import
config.ensure_directories()