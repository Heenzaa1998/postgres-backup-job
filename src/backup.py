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
from datetime import datetime, timedelta

from dotenv import load_dotenv
import boto3
from botocore.client import Config


from config import get_config
from logger import logger
from database import connect_with_retry, verify_backup

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


def cleanup_old_backups(backup_dir, retention_days):
    """Delete backup files older than retention_days."""
    if retention_days <= 0:
        logger.info("Retention disabled (RETENTION_DAYS=0)")
        return
    
    logger.info(f"Cleaning up backups older than {retention_days} days...")
    cutoff_time = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0
    
    try:
        for filename in os.listdir(backup_dir):
            if not filename.endswith('.sql.gz'):
                continue
            
            filepath = os.path.join(backup_dir, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if file_mtime < cutoff_time:
                os.remove(filepath)
                logger.info(f"Deleted old backup: {filename}")
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleanup complete: {deleted_count} file(s) removed")
        else:
            logger.info("No old backups to clean up")
            
    except OSError as e:
        logger.error(f"Cleanup failed: {e}")
        # Don't raise - cleanup failure shouldn't fail the backup




def upload_to_remote(backup_file, config):
    """Upload backup file to S3-compatible storage."""
    logger.info(f"Uploading to remote storage: {config['remote_bucket']}")
    
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=config['remote_endpoint'],
            aws_access_key_id=config['remote_access_key'],
            aws_secret_access_key=config['remote_secret_key'],
            region_name=config['remote_region'],
            config=Config(signature_version='s3v4')
        )
        
        filename = os.path.basename(backup_file)
        
        # Generate path based on format
        path_format = config['remote_path_format']
        now = datetime.now()
        
        if path_format == 'monthly':
            remote_path = f"{now.strftime('%Y-%m')}/{filename}"
        elif path_format == 'daily':
            remote_path = f"{now.strftime('%Y-%m-%d')}/{filename}"
        else:  # flat
            remote_path = filename
        
        s3_client.upload_file(backup_file, config['remote_bucket'], remote_path)
        
        logger.info(f"Uploaded to remote: {remote_path}")
        
    except Exception as e:
        logger.error(f"Remote upload failed: {e}")
        raise


if __name__ == '__main__':
    main()
