"""
PostgreSQL Backup Script

This script connects to a PostgreSQL database and performs automated backups.
"""

import os
import sys
import logging
from datetime import datetime

from dotenv import load_dotenv
import psycopg2

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_config():
    """Read configuration from environment variables."""
    config = {
        'host': os.environ.get('POSTGRES_HOST', 'localhost'),
        'port': os.environ.get('POSTGRES_PORT', '5432'),
        'user': os.environ.get('POSTGRES_USER', 'backup_user'),
        'password': os.environ.get('POSTGRES_PASSWORD', 'backup_password'),
        'database': os.environ.get('POSTGRES_DB', 'testdb'),
        'backup_dir': os.environ.get('BACKUP_DIR', './backups'),
    }
    return config


def test_connection(config):
    """Test connection to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            dbname=config['database']
        )
        conn.close()
        logger.info(f"Connected to {config['database']}@{config['host']}:{config['port']}")
        return True
    except psycopg2.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        return False


def main():
    """Main entry point."""
    logger.info("Starting backup script...")
    
    # Load configuration
    config = get_config()
    logger.info(f"Backup directory: {config['backup_dir']}")
    
    # Test database connection
    if not test_connection(config):
        logger.error("Database connection failed. Exiting.")
        sys.exit(1)
    
    logger.info("Database connection successful!")


if __name__ == '__main__':
    main()
