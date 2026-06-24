"""
Logging configuration for Topology Management System
"""

import logging
import sys

# Configure logging
def setup_logging(log_level=logging.INFO):
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (default: INFO)
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name):
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()