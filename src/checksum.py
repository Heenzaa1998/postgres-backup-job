"""
Checksum module for PostgreSQL backup job.

Generates SHA256 checksums for backup integrity verification.
"""

import os
import hashlib

from logger import logger


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
