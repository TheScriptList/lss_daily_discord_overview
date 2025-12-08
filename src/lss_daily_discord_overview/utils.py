"""Utility functions for lss_daily_discord_overview."""

import os
import sys
import logging
from pathlib import Path
from http.cookiejar import MozillaCookieJar
from dotenv import set_key
from datetime import datetime, timezone

log = logging.getLogger(__name__)


# Get the root directory (parent of the src directory)
# When running as a PyInstaller bundle, use the executable's directory
# Otherwise, use the parent of the src directory
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    ROOT_DIR = Path(sys.executable).parent
else:
    # Running as script
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = ROOT_DIR / ".env"
COOKIES_FILE = ROOT_DIR / "cookies.txt"


def get_setting(name, message, confirm=False, choices=None, default=None):
    """Load or prompt for a configuration setting.
    
    Args:
        name: Environment variable name
        message: Message to display when prompting
        confirm: If True, prompt for yes/no confirmation
        choices: List of choices for list input
        default: Default value
        
    Returns:
        The configuration value (from env or user input)
    """
    from inquirer.shortcuts import text as text_input, confirm as confirm_input, list_input
    
    env_val = os.getenv(name)

    if env_val:
        log.info(f"{name} = {(str(env_val)[:77] + '...') if len(str(env_val)) > 80 else str(env_val)}")
        
        if confirm:
            env_val = env_val.lower() == "true"

        return env_val

    if confirm:
        ans = confirm_input(message=message, default=default)
    elif choices:
        ans = list_input(message=message, choices=choices, default=default)
    else:
        ans = text_input(message=message, default=default)

    set_key(str(CONFIG_FILE), name, str(ans))

    return ans


def load_cookies(file_path):
    """Load cookies from a Mozilla cookies file.
    
    Args:
        file_path: Path to the cookies.txt file
        
    Returns:
        Dictionary of cookie names and values
        
    Raises:
        SystemExit: If the cookies file is not found
    """
    from . import lss_daily_discord_overview
    
    cookie_jar = MozillaCookieJar()
    try:
        cookie_jar.load(str(file_path), ignore_discard=True, ignore_expires=True)
    except FileNotFoundError:
        lss_daily_discord_overview.send_error("cookies.txt nicht gefunden")
    return {cookie.name: cookie.value for cookie in cookie_jar}


def parse_iso_epoch(timestamp):
    """Return unix epoch integer (seconds) from an ISO timestamp string or None.
    
    Args:
        timestamp: ISO timestamp string
        
    Returns:
        Unix epoch timestamp as integer, or None if parsing fails
    """
    dt = parse_iso_datetime(timestamp)
    return int(dt.timestamp()) if dt else None


def parse_iso_datetime(timestamp):
    """Parse an ISO timestamp string into a datetime, return None if parsing fails.
    
    Args:
        timestamp: ISO timestamp string (e.g., "2024-12-08T10:30:00Z")
        
    Returns:
        timezone-aware datetime in UTC, or None if parsing fails
    """
    if not timestamp:
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        # Normalize to timezone-aware UTC
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None
