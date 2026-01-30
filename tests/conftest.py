"""
Pytest fixtures for postgres-backup-job tests.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_config():
    """Return a mock configuration dictionary."""
    return {
        'host': 'localhost',
        'port': '5432',
        'user': 'testuser',
        'password': 'testpass',
        'database': 'testdb',
        'backup_dir': './backups',
        'retry_count': 3,
        'retry_delay': 1,
        'retention_days': 7,
        'verify_enabled': False,
        'verify_host': 'localhost',
        'verify_port': '5432',
        'verify_user': 'testuser',
        'verify_password': 'testpass',
        'verify_db': 'testdb_verify',
        'backup_target': 'local',
        'remote_endpoint': 'http://localhost:9000',
        'remote_bucket': 'test-bucket',
        'remote_access_key': 'minioadmin',
        'remote_secret_key': 'minioadmin',
        'remote_region': 'us-east-1',
        'remote_path_format': 'monthly',
    }


@pytest.fixture
def temp_backup_dir(tmp_path):
    """Create a temporary backup directory."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    return backup_dir
