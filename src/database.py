"""
Database module for PostgreSQL backup job.

Handles database connections and verification.
"""

import os
import time
import subprocess

import psycopg2

from logger import logger


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
        logger.warning(f"Connection attempt failed: {e}")
        return False


def connect_with_retry(config):
    """Try to connect to database with retry logic."""
    retry_count = config['retry_count']
    retry_delay = config['retry_delay']
    
    for attempt in range(1, retry_count + 1):
        if test_connection(config):
            return True
        
        if attempt < retry_count:
            logger.warning(f"Retrying in {retry_delay} seconds... ({attempt}/{retry_count})")
            time.sleep(retry_delay)
    
    return False


def verify_backup(backup_file, config):
    """Verify backup by restoring to a temporary database."""
    logger.info("Verifying backup...")
    
    verify_config = {
        'host': config['verify_host'],
        'port': config['verify_port'],
        'user': config['verify_user'],
        'password': config['verify_password'],
        'database': config['verify_db']
    }
    
    try:
        # Create temp database
        create_temp_db(verify_config)
        
        # Restore backup to temp database
        restore_backup(backup_file, verify_config)
        
        # Verify data exists
        verify_data(verify_config)
        
        logger.info("Backup verified successfully")
        
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        raise
    finally:
        # Always drop temp database
        drop_temp_db(verify_config)


def create_temp_db(config):
    """Create temporary database for verification."""
    logger.info(f"Creating temp database: {config['database']}")
    
    conn = psycopg2.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        dbname='postgres'  # Connect to default DB to create new one
    )
    conn.autocommit = True
    
    cursor = conn.cursor()
    # Drop if exists (in case of previous failed run)
    cursor.execute(f"DROP DATABASE IF EXISTS {config['database']}")
    cursor.execute(f"CREATE DATABASE {config['database']}")
    cursor.close()
    conn.close()


def restore_backup(backup_file, config):
    """Restore backup to temp database."""
    logger.info("Restoring backup to temp database...")
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    # Decompress and restore using gunzip + psql
    gunzip_cmd = ['gunzip', '-c', backup_file]
    psql_cmd = [
        'psql',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '-q'  # Quiet mode
    ]
    
    # Pipe gunzip output to psql
    gunzip_proc = subprocess.Popen(gunzip_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    psql_proc = subprocess.Popen(psql_cmd, stdin=gunzip_proc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    gunzip_proc.stdout.close()
    
    _, stderr = psql_proc.communicate()
    if psql_proc.returncode != 0:
        raise Exception(f"Restore failed: {stderr.decode()}")


def verify_data(config):
    """Verify that data exists in temp database."""
    conn = psycopg2.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        dbname=config['database']
    )
    
    cursor = conn.cursor()
    # Count tables
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    table_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    logger.info(f"Verified: {table_count} tables found")
    
    if table_count == 0:
        raise Exception("No tables found in restored database")


def drop_temp_db(config):
    """Drop temporary database."""
    logger.info(f"Dropping temp database: {config['database']}")
    
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            dbname='postgres'
        )
        conn.autocommit = True
        
        cursor = conn.cursor()
        # Terminate connections to the database
        cursor.execute(f"""
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = '{config['database']}'
        """)
        cursor.execute(f"DROP DATABASE IF EXISTS {config['database']}")
        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to drop temp database: {e}")
