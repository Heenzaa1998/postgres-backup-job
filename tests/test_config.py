"""
Tests for config module.
"""

import os
from unittest.mock import patch

import pytest

from config import get_config


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_defaults(self):
        """Test that default values are returned when env vars not set."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config()
            
            assert config['host'] == 'localhost'
            assert config['port'] == '5432'
            assert config['backup_target'] == 'local'
            assert config['retention_days'] == 7

    def test_get_config_from_env(self):
        """Test that values are read from environment variables."""
        env_vars = {
            'POSTGRES_HOST': 'db.example.com',
            'POSTGRES_PORT': '5433',
            'POSTGRES_USER': 'admin',
            'POSTGRES_PASSWORD': 'secret',
            'POSTGRES_DB': 'production',
            'BACKUP_TARGET': 'remote',
            'RETENTION_DAYS': '30',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_config()
            
            assert config['host'] == 'db.example.com'
            assert config['port'] == '5433'
            assert config['user'] == 'admin'
            assert config['password'] == 'secret'
            assert config['database'] == 'production'
            assert config['backup_target'] == 'remote'
            assert config['retention_days'] == 30

    def test_verify_config_inherits_db_settings(self):
        """Test that verify settings fallback to DB settings."""
        env_vars = {
            'POSTGRES_HOST': 'db.example.com',
            'POSTGRES_PORT': '5433',
            'POSTGRES_USER': 'admin',
            'POSTGRES_PASSWORD': 'secret',
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = get_config()
            
            # Verify settings should inherit from DB settings
            assert config['verify_host'] == 'db.example.com'
            assert config['verify_port'] == '5433'
            assert config['verify_user'] == 'admin'
            assert config['verify_password'] == 'secret'
