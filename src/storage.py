"""
Storage module for PostgreSQL backup job.

Handles file storage and S3-compatible remote storage.
"""

import os
from datetime import datetime, timedelta

import boto3
from botocore.client import Config

from logger import logger


def ensure_backup_dir(backup_dir):
    """Create backup directory if it doesn't exist."""
    try:
        os.makedirs(backup_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create backup directory: {e}")
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
