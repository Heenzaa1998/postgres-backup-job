"""
Tests for storage module.
"""

import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest

from storage import ensure_backup_dir, cleanup_old_backups, upload_to_remote


class TestEnsureBackupDir:
    """Tests for ensure_backup_dir function."""

    def test_ensure_backup_dir_creates(self, tmp_path):
        """Test that directory is created if it doesn't exist."""
        new_dir = tmp_path / "new_backups"
        
        ensure_backup_dir(str(new_dir))
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_backup_dir_exists(self, tmp_path):
        """Test that no error when directory already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        # Should not raise
        ensure_backup_dir(str(existing_dir))
        
        assert existing_dir.exists()


class TestCleanupOldBackups:
    """Tests for cleanup_old_backups function."""

    def test_cleanup_deletes_old_files(self, tmp_path):
        """Test that files older than retention are deleted."""
        # Create an old backup file
        old_file = tmp_path / "old_backup.sql.gz"
        old_file.write_bytes(b"old backup")
        
        # Set file mtime to 10 days ago
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        cleanup_old_backups(str(tmp_path), retention_days=7)
        
        assert not old_file.exists()

    def test_cleanup_keeps_new_files(self, tmp_path):
        """Test that recent files are not deleted."""
        # Create a new backup file (today)
        new_file = tmp_path / "new_backup.sql.gz"
        new_file.write_bytes(b"new backup")
        
        cleanup_old_backups(str(tmp_path), retention_days=7)
        
        assert new_file.exists()

    def test_cleanup_retention_zero_skips(self, tmp_path):
        """Test that cleanup is skipped when retention_days=0."""
        # Create a file
        test_file = tmp_path / "backup.sql.gz"
        test_file.write_bytes(b"backup")
        
        # Set mtime to 100 days ago
        old_time = (datetime.now() - timedelta(days=100)).timestamp()
        os.utime(test_file, (old_time, old_time))
        
        cleanup_old_backups(str(tmp_path), retention_days=0)
        
        # File should still exist (retention disabled)
        assert test_file.exists()

    def test_cleanup_ignores_non_gz_files(self, tmp_path):
        """Test that only .sql.gz files are cleaned up."""
        # Create non-gz file
        other_file = tmp_path / "notes.txt"
        other_file.write_text("notes")
        
        # Set mtime to old
        old_time = (datetime.now() - timedelta(days=100)).timestamp()
        os.utime(other_file, (old_time, old_time))
        
        cleanup_old_backups(str(tmp_path), retention_days=7)
        
        # Non-gz file should remain
        assert other_file.exists()


class TestUploadToRemote:
    """Tests for upload_to_remote function."""

    @patch('storage.boto3.client')
    def test_upload_to_remote_success(self, mock_boto_client, tmp_path, mock_config):
        """Test successful upload to S3."""
        # Create test file
        test_file = tmp_path / "backup.sql.gz"
        test_file.write_bytes(b"backup content")
        
        # Mock S3 client
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        upload_to_remote(str(test_file), mock_config)
        
        # Verify upload_file was called
        mock_s3.upload_file.assert_called_once()

    @patch('storage.boto3.client')
    def test_upload_to_remote_error(self, mock_boto_client, tmp_path, mock_config):
        """Test that exception is raised on upload failure."""
        test_file = tmp_path / "backup.sql.gz"
        test_file.write_bytes(b"backup")
        
        # Mock S3 client to raise error
        mock_s3 = MagicMock()
        mock_s3.upload_file.side_effect = Exception("S3 error")
        mock_boto_client.return_value = mock_s3
        
        with pytest.raises(Exception, match="S3 error"):
            upload_to_remote(str(test_file), mock_config)
