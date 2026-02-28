"""Logging configuration"""
import logging
import sys
from app.config import get_settings

settings = get_settings()


def setup_logging():
    """Configure application logging"""
    
    # Create logger
    logger = logging.getLogger("bharatsahayak")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logging()
