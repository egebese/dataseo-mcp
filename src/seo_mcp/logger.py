"""Safe logging helpers for DataSEO MCP."""
import logging
import os
from datetime import datetime

DEBUG = os.environ.get("DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def setup_logger(
    name: str,
    log_dir: str = "logs",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Setup a logger for the given name.
    
    Args:
        name: The name of the logger
        log_dir: The directory to save the log files
        level: The level of the logger
    
    Returns:
        logging.Logger: The configured logger
    """
    logger = logging.getLogger(name)
    if not DEBUG:
        logger.addHandler(logging.NullHandler())
        return logger
    
    # Create the log directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Create the log file name, format: module_name_YYYYMMDD.log
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Create the logger
    logger.setLevel(level)
    
    # If the logger already has handlers, don't add a new handler
    if not logger.handlers:
        # Create the file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        # Create the console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create the formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add the handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger
