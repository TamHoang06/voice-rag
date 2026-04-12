import logging
import os
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("ai_podcast")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Console handler with timestamp
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formatter with timestamp
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger = setup_logging(
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    log_file=os.environ.get("LOG_FILE", None),
)


def get_logger(name: str = "ai_podcast") -> logging.Logger:
    """Get or create a named logger."""
    return logging.getLogger(name)
