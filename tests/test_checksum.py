"""
Tests for checksum module.
"""

import os
import pytest

from checksum import generate_checksum


class TestGenerateChecksum:
    """Tests for generate_checksum function."""

    def test_generate_checksum_creates_file(self, tmp_path):
        """Test that checksum file is created."""
        # Create a test file
        test_file = tmp_path / "backup.sql.gz"
        test_file.write_bytes(b"test backup content")
        
        # Generate checksum
        result = generate_checksum(str(test_file))
        
        # Check .sha256 file was created
        assert result == str(test_file) + ".sha256"
        assert os.path.exists(result)

    def test_checksum_format(self, tmp_path):
        """Test that checksum file has correct format: 'hash  filename'."""
        # Create a test file
        test_file = tmp_path / "backup.sql.gz"
        test_file.write_bytes(b"test backup content")
        
        # Generate checksum
        checksum_file = generate_checksum(str(test_file))
        
        # Read and verify format
        with open(checksum_file, 'r') as f:
            content = f.read()
        
        # Format should be: "hash  filename\n"
        parts = content.strip().split('  ')
        assert len(parts) == 2
        assert len(parts[0]) == 64  # SHA256 = 64 hex chars
        assert parts[1] == "backup.sql.gz"

    def test_checksum_reproducible(self, tmp_path):
        """Test that same file produces same checksum."""
        # Create a test file
        test_file = tmp_path / "backup.sql.gz"
        test_file.write_bytes(b"identical content")
        
        # Generate checksum twice
        generate_checksum(str(test_file))
        
        with open(str(test_file) + ".sha256", 'r') as f:
            first_checksum = f.read().split()[0]
        
        generate_checksum(str(test_file))
        
        with open(str(test_file) + ".sha256", 'r') as f:
            second_checksum = f.read().split()[0]
        
        assert first_checksum == second_checksum

    def test_generate_checksum_file_not_found(self, tmp_path):
        """Test that OSError is raised for non-existent file."""
        with pytest.raises(OSError):
            generate_checksum(str(tmp_path / "nonexistent.sql.gz"))
