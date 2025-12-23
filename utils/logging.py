"""Logging configuration for the bot."""
import logging
import sys
from typing import Optional

from config import Config


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    log_level = level or Config.LOG_LEVEL
    
    # Create logger
    logger = logging.getLogger("music_bot")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger


# Create default logger instance
logger = setup_logging()
