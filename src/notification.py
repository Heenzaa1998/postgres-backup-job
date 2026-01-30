"""Discord notification module for backup alerts."""

import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional
from logger import logger


def send_discord_notification(
    webhook_url: str,
    success: bool,
    database: str,
    filename: Optional[str] = None,
    file_size: Optional[str] = None,
    storage: Optional[str] = None,
    duration: Optional[float] = None,
    error_message: Optional[str] = None,
    error_step: Optional[str] = None,
) -> bool:
    """Send Discord webhook notification.
    
    Args:
        webhook_url: Discord webhook URL
        success: True for success, False for failure
        database: Database name
        filename: Backup filename (success only)
        file_size: Backup file size (success only)
        storage: Storage target (success only)
        duration: Backup duration in seconds (success only)
        error_message: Error message (failure only)
        error_step: Step where error occurred (failure only)
    
    Returns:
        True if notification sent successfully
    """
    if not webhook_url:
        logger.info("Discord webhook URL not configured, skipping notification")
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if success:
        embed = _create_success_embed(
            database, filename, file_size, storage, duration, timestamp
        )
    else:
        embed = _create_failure_embed(
            database, error_message, error_step, timestamp
        )

    payload = {"embeds": [embed]}
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PostgreSQL-Backup-Job/1.0",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        logger.info(f"Discord notification sent: {'success' if success else 'failure'}")
        return True
    except urllib.error.URLError as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False


def _create_success_embed(
    database: str,
    filename: str,
    file_size: str,
    storage: str,
    duration: float,
    timestamp: str,
) -> dict:
    """Create Discord embed for successful backup."""
    desc = f"""**Database:** {database}
            **Backup File:** {filename or 'N/A'}
            **Backup Size:** {file_size or 'N/A'}
            **Storage:** {storage or 'N/A'}
            **Duration:** {f'{duration:.1f}s' if duration else 'N/A'}"""
    
    return {
        "title": "Backup Successful",
        "description": desc,
        "color": 5763719,  # Green
        "footer": {"text": "PostgreSQL Backup Job"},
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _create_failure_embed(
    database: str,
    error_message: str,
    error_step: str,
    timestamp: str,
) -> dict:
    """Create Discord embed for failed backup."""
    desc = f"""**Database:** {database}
**Error:** {error_message or 'Unknown error'}
**Step:** {error_step or 'Unknown'}"""
    
    return {
        "title": "Backup Failed",
        "description": desc,
        "color": 15548997,  # Red
        "footer": {"text": "PostgreSQL Backup Job"},
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

