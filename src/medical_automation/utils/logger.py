"""Logging configuration and utilities."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from ..config import config


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.
    
    Args:
        name: Logger name
        log_file: Optional log file name (will be placed in logs directory)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or config.LOG_LEVEL
    log_level_upper = log_level.upper()
    if not hasattr(logging, log_level_upper):
        raise ValueError(f"Invalid log level: {log_level}")
    logger.setLevel(getattr(logging, log_level_upper))
    elif isinstance(level, str) and level.strip() == "":
        raise ValueError("Log level cannot be an empty string.")
    else:
        log_level = level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = config.LOGS_DIR / log_file
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=config.MAX_LOG_SIZE,
            backupCount=config.LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)