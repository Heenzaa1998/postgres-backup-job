"""
Configuration module for PostgreSQL backup job.

Reads configuration from environment variables.
"""

import os


def get_config():
    """Read configuration from environment variables."""
    config = {
        # Database connection
        'host': os.environ.get('POSTGRES_HOST', 'localhost'),
        'port': os.environ.get('POSTGRES_PORT', '5432'),
        'user': os.environ.get('POSTGRES_USER', 'backup_user'),
        'password': os.environ.get('POSTGRES_PASSWORD', 'backup_password'),
        'database': os.environ.get('POSTGRES_DB', 'testdb'),
        
        # Backup settings
        'backup_dir': os.environ.get('BACKUP_DIR', './backups'),
        'retry_count': int(os.environ.get('RETRY_COUNT', '3')),
        'retry_delay': int(os.environ.get('RETRY_DELAY', '5')),
        'retention_days': int(os.environ.get('RETENTION_DAYS', '7')),
        
        # Verify configuration
        'verify_enabled': os.environ.get('VERIFY_ENABLED', 'false').lower() == 'true',
        'verify_host': os.environ.get('VERIFY_HOST', os.environ.get('POSTGRES_HOST', 'localhost')),
        'verify_port': os.environ.get('VERIFY_PORT', os.environ.get('POSTGRES_PORT', '5432')),
        'verify_user': os.environ.get('VERIFY_USER', os.environ.get('POSTGRES_USER', 'backup_user')),
        'verify_password': os.environ.get('VERIFY_PASSWORD', os.environ.get('POSTGRES_PASSWORD', 'backup_password')),
        'verify_db': os.environ.get('VERIFY_DB', 'testdb_verify'),
        
        # Storage configuration
        'backup_target': os.environ.get('BACKUP_TARGET', 'local'),  # local | remote | all
        'remote_endpoint': os.environ.get('REMOTE_ENDPOINT', 'http://localhost:9000'),
        'remote_bucket': os.environ.get('REMOTE_BUCKET', 'test-backup'),
        'remote_access_key': os.environ.get('REMOTE_ACCESS_KEY', 'minioadmin'),
        'remote_secret_key': os.environ.get('REMOTE_SECRET_KEY', 'minioadmin'),
        'remote_region': os.environ.get('REMOTE_REGION', 'us-east-1'),
        'remote_path_format': os.environ.get('REMOTE_PATH_FORMAT', 'monthly'),  # flat | monthly | daily
        
        # Discord notification
        'discord_webhook_url': os.environ.get('DISCORD_WEBHOOK_URL', ''),
        'discord_notify_success': os.environ.get('DISCORD_NOTIFY_SUCCESS', 'true').lower() == 'true',
        'discord_notify_failure': os.environ.get('DISCORD_NOTIFY_FAILURE', 'true').lower() == 'true',
    }
    return config
