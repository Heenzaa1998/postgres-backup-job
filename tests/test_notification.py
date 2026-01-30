"""Tests for notification module."""

import pytest
from unittest.mock import patch, MagicMock
import urllib.error

import sys
sys.path.insert(0, 'src')

from notification import (
    send_discord_notification,
    _create_success_embed,
    _create_failure_embed,
)


class TestSuccessEmbed:
    """Test success embed creation."""
    
    def test_success_embed_format(self):
        """Verify success embed has required fields."""
        embed = _create_success_embed(
            database="testdb",
            filename="backup_2026-01-31.sql.gz",
            file_size="1.3 KB",
            storage="S3 + Local",
            duration=5.5,
            timestamp="2026-01-31 01:00:00",
        )
        
        assert embed["title"] == "Backup Successful"
        assert embed["color"] == 5763719  # Green
        assert "testdb" in embed["description"]
        assert "backup_2026-01-31.sql.gz" in embed["description"]
        assert "1.3 KB" in embed["description"]
        assert "S3 + Local" in embed["description"]
        assert "5.5s" in embed["description"]
        assert "footer" in embed
        assert "timestamp" in embed


class TestFailureEmbed:
    """Test failure embed creation."""
    
    def test_failure_embed_format(self):
        """Verify failure embed has required fields."""
        embed = _create_failure_embed(
            database="testdb",
            error_message="Connection refused",
            error_step="Database connection",
            timestamp="2026-01-31 01:00:00",
        )
        
        assert embed["title"] == "Backup Failed"
        assert embed["color"] == 15548997  # Red
        assert "testdb" in embed["description"]
        assert "Connection refused" in embed["description"]
        assert "Database connection" in embed["description"]
        assert "footer" in embed
        assert "timestamp" in embed


class TestSendNotification:
    """Test send_discord_notification function."""
    
    def test_skip_when_no_url(self):
        """Should return False when webhook URL is empty."""
        result = send_discord_notification(
            webhook_url="",
            success=True,
            database="testdb",
        )
        assert result is False
    
    @patch('notification.urllib.request.urlopen')
    def test_send_notification_success(self, mock_urlopen):
        """Should send notification successfully."""
        mock_urlopen.return_value = MagicMock()
        
        result = send_discord_notification(
            webhook_url="https://discord.com/api/webhooks/test",
            success=True,
            database="testdb",
            filename="backup.sql.gz",
            file_size="1.0 KB",
            storage="Local",
            duration=3.0,
        )
        
        assert result is True
        mock_urlopen.assert_called_once()
    
    @patch('notification.urllib.request.urlopen')
    def test_http_error_handling(self, mock_urlopen):
        """Should handle HTTP errors gracefully."""
        mock_urlopen.side_effect = urllib.error.URLError("Network error")
        
        result = send_discord_notification(
            webhook_url="https://discord.com/api/webhooks/test",
            success=False,
            database="testdb",
            error_message="Test error",
            error_step="Test step",
        )
        
        assert result is False
