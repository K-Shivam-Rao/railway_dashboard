"""
Logging configuration for SicherGleis Railway Dashboard.
Configures structured logging with both file and console output.
"""
import logging
import os
from datetime import datetime


def setup_logging(
    log_file="app.log",
    level=logging.INFO,
    console_level=logging.WARNING
):
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to log file (default: app.log)
        level: File logging level (default: INFO)
        console_level: Console logging level (default: WARNING)
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler - logs everything from level and above
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Console handler - logs warnings and above by default
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name):
    """
    Get a logger with the specified name.
    """
    return logging.getLogger(name)


# Initialize logging with default config
setup_logging()


if __name__ == "__main__":
    # Test logging
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
