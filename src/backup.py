"""
PostgreSQL Backup Script

This script connects to a PostgreSQL database and performs automated backups.
"""

import os
import sys
import gzip
import shutil
import logging
import subprocess
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
    
    try:
        # Load configuration
        config = get_config()
        logger.info(f"Backup directory: {config['backup_dir']}")
        
        # Test database connection
        if not test_connection(config):
            logger.error("Database connection failed. Exiting.")
            sys.exit(1)
        
        logger.info("Database connection successful!")
        
        # Ensure backup directory exists
        ensure_backup_dir(config['backup_dir'])
        
        # Generate backup filename
        backup_file = generate_backup_filename(config['backup_dir'])
        
        # Run pg_dump
        run_pg_dump(config, backup_file)
        
        # Compress backup
        final_file = compress_backup(backup_file)
        
        # Show final file info
        file_size = os.path.getsize(final_file)
        logger.info(f"Backup completed: {final_file} ({file_size / 1024:.1f} KB)")
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        sys.exit(1)


def ensure_backup_dir(backup_dir):
    """Create backup directory if it doesn't exist."""
    try:
        os.makedirs(backup_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create backup directory: {e}")
        raise


def generate_backup_filename(backup_dir):
    """Generate backup filename with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"backup_{timestamp}.sql"
    return os.path.join(backup_dir, filename)


def run_pg_dump(config, output_file):
    """Run pg_dump to create backup file."""
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    cmd = [
        'pg_dump',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '-f', output_file
    ]
    
    try:
        logger.info("Running pg_dump...")
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        logger.info(f"Backup created: {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed: {e.stderr}")
        raise
    except FileNotFoundError:
        logger.error("pg_dump not found. Please install PostgreSQL client tools.")
        raise


def compress_backup(backup_file):
    """Compress backup file with gzip."""
    compressed_file = backup_file + '.gz'
    
    try:
        logger.info("Compressing backup with gzip...")
        with open(backup_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original .sql file
        os.remove(backup_file)
        return compressed_file
    except OSError as e:
        logger.error(f"Failed to compress backup: {e}")
        raise


if __name__ == '__main__':
    main()
