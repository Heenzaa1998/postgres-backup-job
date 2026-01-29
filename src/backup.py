"""
PostgreSQL Backup Script

This script connects to a PostgreSQL database and performs automated backups.
"""

import os
import sys
import gzip
import shutil
import hashlib
import subprocess
from datetime import datetime

from dotenv import load_dotenv

from config import get_config
from logger import logger
from database import connect_with_retry, verify_backup
from storage import ensure_backup_dir, cleanup_old_backups, upload_to_remote

# Load environment variables from .env file
load_dotenv()


def main():
    """Main entry point."""
    logger.info("Starting backup script...")
    
    try:
        # Load configuration
        config = get_config()
        logger.info(f"Backup directory: {config['backup_dir']}")
        
        # Test database connection with retry
        if not connect_with_retry(config):
            logger.error("Database connection failed after all retries. Exiting.")
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
        
        # Generate SHA256 checksum
        checksum_file = generate_checksum(final_file)
        
        # Show final file info
        file_size = os.path.getsize(final_file)
        logger.info(f"Backup completed: {final_file} ({file_size / 1024:.1f} KB)")
        
        # Upload to remote if enabled
        target = config['backup_target']
        if target in ['remote', 'all']:
            upload_to_remote(final_file, config)
            upload_to_remote(checksum_file, config)
        
        # Cleanup old backups (only if keeping local)
        if target in ['local', 'all']:
            cleanup_old_backups(config['backup_dir'], config['retention_days'])
        
        # Verify backup if enabled (before deleting local file)
        if config['verify_enabled']:
            verify_backup(final_file, config)
        
        # Delete local files if remote-only mode
        if target == 'remote':
            os.remove(final_file)
            os.remove(checksum_file)
            logger.info(f"Removed local files (remote-only mode)")
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        sys.exit(1)


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


def generate_checksum(file_path):
    """Generate SHA256 checksum for a file and save to .sha256 file."""
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        
        checksum = sha256_hash.hexdigest()
        checksum_file = file_path + '.sha256'
        filename = os.path.basename(file_path)
        
        # Write checksum in standard format: "hash  filename"
        with open(checksum_file, 'w') as f:
            f.write(f"{checksum}  {filename}\n")
        
        logger.info(f"Checksum generated: {checksum[:16]}...")
        return checksum_file
    except OSError as e:
        logger.error(f"Failed to generate checksum: {e}")
        raise


if __name__ == '__main__':
    main()
