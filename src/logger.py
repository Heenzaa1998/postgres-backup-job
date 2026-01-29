"""
Logger module for PostgreSQL backup job.

Configures logging with consistent format.
"""

import logging


def setup_logger(name=__name__):
    """Setup and return a configured logger."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)


# Default logger instance
logger = setup_logger('backup')
