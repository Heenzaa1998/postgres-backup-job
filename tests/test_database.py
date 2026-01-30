"""
Tests for database module.
"""

import pytest
from unittest.mock import patch, MagicMock

import psycopg2

from database import check_connection, connect_with_retry


class TestTestConnection:
    """Tests for test_connection function."""

    @patch('database.psycopg2.connect')
    def test_connection_success(self, mock_connect, mock_config):
        """Test successful database connection."""
        # Mock successful connection
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        result = check_connection(mock_config)
        
        assert result is True
        mock_conn.close.assert_called_once()

    @patch('database.psycopg2.connect')
    def test_connection_failure(self, mock_connect, mock_config):
        """Test failed database connection."""
        # Mock connection error
        mock_connect.side_effect = psycopg2.Error("Connection refused")
        
        result = check_connection(mock_config)
        
        assert result is False


class TestConnectWithRetry:
    """Tests for connect_with_retry function."""

    @patch('database.check_connection')
    def test_connect_with_retry_success_first_try(self, mock_test_conn, mock_config):
        """Test successful connection on first try."""
        mock_test_conn.return_value = True
        
        result = connect_with_retry(mock_config)
        
        assert result is True
        assert mock_test_conn.call_count == 1

    @patch('database.time.sleep')
    @patch('database.check_connection')
    def test_connect_with_retry_success_after_retry(self, mock_test_conn, mock_sleep, mock_config):
        """Test successful connection after retry."""
        # Fail first, succeed second
        mock_test_conn.side_effect = [False, True]
        
        result = connect_with_retry(mock_config)
        
        assert result is True
        assert mock_test_conn.call_count == 2

    @patch('database.time.sleep')
    @patch('database.check_connection')
    def test_connect_with_retry_all_fail(self, mock_test_conn, mock_sleep, mock_config):
        """Test all retry attempts fail."""
        mock_test_conn.return_value = False
        
        result = connect_with_retry(mock_config)
        
        assert result is False
        # Should try retry_count times (default 3)
        assert mock_test_conn.call_count == mock_config['retry_count']
