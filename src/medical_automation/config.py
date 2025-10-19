"""
Configuration management for Medical Automation Suite.
Supports multiple environments (development, production) and uses environment variables.
"""
import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Resolve project base directory (repo root)
BASE_DIR = Path(__file__).resolve().parents[2]


class Config:
    """Configuration class with sensible defaults and env overrides."""

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    SQL_DIR: Path = BASE_DIR / "sql"

    # Server
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    MEDICAL_SERVER_PORT: int = int(os.getenv("MEDICAL_SERVER_PORT", "8080"))
    SNIPPET_SERVER_PORT: int = int(os.getenv("SNIPPET_SERVER_PORT", "5000"))

    # Databases
    MEDICAL_DB_PATH: str = os.getenv("MEDICAL_DB_PATH", str(DATA_DIR / "automation.db"))
    SNIPPET_DB_PATH: str = os.getenv("SNIPPET_DB_PATH", str(DATA_DIR / "snippets.db"))
    MEDICAL_SQL_FILE: str = os.getenv("MEDICAL_SQL_FILE", str(SQL_DIR / "SQL2.sql"))
    SNIPPET_SQL_FILE: str = os.getenv("SNIPPET_SQL_FILE", str(SQL_DIR / "snippets_data.sql"))

    # Client defaults
    DEFAULT_SERVER_IP: str = os.getenv("DEFAULT_SERVER_IP", "pi.local")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    MAX_LOG_SIZE: int = int(os.getenv("MAX_LOG_SIZE", str(10 * 1024 * 1024)))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Security
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # CORS
    CORS_ORIGINS: List[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

    # Timeouts
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))

    # SQLite
    DB_TIMEOUT: int = int(os.getenv("DB_TIMEOUT", "5"))
    DB_CHECK_SAME_THREAD: bool = os.getenv("DB_CHECK_SAME_THREAD", "True").lower() == "true"

    # Snippet admin guardrails
    SNIPPET_ADMIN_ENABLED: bool = os.getenv("SNIPPET_ADMIN_ENABLED", "0") in ("1", "true", "True")
    SNIPPET_ADMIN_TOKEN: str = os.getenv("SNIPPET_ADMIN_TOKEN", "")
    SNIPPET_ADMIN_HEADER: str = os.getenv("SNIPPET_ADMIN_HEADER", "X-Admin-Token")

    @classmethod
    def get_medical_server_url(cls, server_ip: Optional[str] = None) -> str:
        ip = server_ip or cls.DEFAULT_SERVER_IP
        return f"http://{ip}:{cls.MEDICAL_SERVER_PORT}"

    @classmethod
    def get_snippet_server_url(cls, server_ip: Optional[str] = None) -> str:
        ip = server_ip or cls.DEFAULT_SERVER_IP
        return f"http://{ip}:{cls.SNIPPET_SERVER_PORT}"

    @classmethod
    def ensure_directories(cls):
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.SQL_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        missing = []
        if not Path(cls.MEDICAL_SQL_FILE).exists():
            missing.append(cls.MEDICAL_SQL_FILE)
        if not Path(cls.SNIPPET_SQL_FILE).exists():
            missing.append(cls.SNIPPET_SQL_FILE)
        if missing and not cls.DEBUG:
            raise ValueError(f"Missing SQL files: {missing}")
        if not cls.DEBUG and cls.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set in production.")
        return True


 Select environment (single class; DEBUG toggles stricter checks)
ENV = os.getenv("ENVIRONMENT", "development").lower()

Exported config handle
config = Config
config.ensure_directories()