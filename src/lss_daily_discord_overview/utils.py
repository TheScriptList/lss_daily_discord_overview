"""Utility functions for lss_daily_discord_overview."""

import sys
import logging
from pathlib import Path
from http.cookiejar import MozillaCookieJar
from datetime import datetime, timezone
import apprise
from pydantic_settings import BaseSettings
from inquirer.shortcuts import text as text_input, confirm as confirm_input, list_input

log = logging.getLogger(__name__)

# Global Apprise instance for notifications
_apprise_instance = None


def get_apprise():
    """Get or create the global Apprise instance for notifications.

    Returns:
        An apprise.Apprise instance
    """
    global _apprise_instance
    if _apprise_instance is None:
        _apprise_instance = apprise.Apprise()
    return _apprise_instance


def add_apprise_url(url):
    """Add a notification URL to the Apprise instance.

    Args:
        url: The notification URL (e.g., Discord webhook URL)
    """
    appr = get_apprise()
    appr.add(url)


def send_msg(message):
    """Send a notification message in markdown format.

    Args:
        message: The message to send
    """
    appr = get_apprise()
    appr.notify(body=message, body_format=apprise.NotifyFormat.MARKDOWN)


def send_error(error_message):
    """Send an error message and exit.

    Args:
        error_message: The error message to log and send
    """
    log.error(error_message)
    appr = get_apprise()
    appr.notify(body=error_message, title="⚠️ ERROR", notify_type=apprise.NotifyType.FAILURE)
    exit(1)


# Get the root directory (parent of the src directory)
# When running as a PyInstaller bundle, use the executable's directory
# Otherwise, use the parent of the src directory
if getattr(sys, "frozen", False):
    # Running as compiled executable
    ROOT_DIR = Path(sys.executable).parent
else:
    # Running as script
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = ROOT_DIR / ".env"
COOKIES_FILE = ROOT_DIR / "cookies.txt"


class Settings(BaseSettings):
    """Application settings with automatic .env support."""
    
    send_always: bool = False
    apprise_url: str = ""
    logging_level: str = "INFO"
    debug_days: int = 0
    
    class Config:
        env_file = str(CONFIG_FILE)
        case_sensitive = False


_settings = Settings()


def get_setting(name: str, message: str, confirm: bool = False, choices: list = None, default = None):
    """Get a setting from environment or prompt user interactively.
    
    If the setting doesn't exist, prompts the user and saves to .env file.

    Args:
        name: Setting name (e.g., "APPRISE_URL")
        message: Prompt message for user
        confirm: If True, prompt for yes/no confirmation
        choices: List of choices for selection
        default: Default value

    Returns:
        The setting value
    """
    # Convert name to lowercase for pydantic
    setting_key = name.lower()
    
    # Try to get existing value from settings
    try:
        existing_val = getattr(_settings, setting_key, None)
        if existing_val:
            log.info(f"{name} = {(str(existing_val)[:77] + '...') if len(str(existing_val)) > 80 else str(existing_val)}")
            return existing_val
    except Exception:
        pass
    
    # Prompt user
    if confirm:
        ans = confirm_input(message=message, default=default)
        ans_str = "true" if ans else "false"
    elif choices:
        ans = list_input(message=message, choices=choices, default=default)
        ans_str = str(ans)
    else:
        ans = text_input(message=message, default=default)
        ans_str = str(ans)
    
    # Save to .env file
    env_file = Path(CONFIG_FILE)
    content = ""
    if env_file.exists():
        with open(env_file, "r") as f:
            content = f.read()
    
    lines = content.strip().split("\n") if content.strip() else []
    key_found = False
    
    for i, line in enumerate(lines):
        if line.startswith(f"{name}="):
            lines[i] = f"{name}={ans_str}"
            key_found = True
            break
    
    if not key_found:
        lines.append(f"{name}={ans_str}")
    
    with open(env_file, "w") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")
    
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
    cookie_jar = MozillaCookieJar()
    try:
        cookie_jar.load(str(file_path), ignore_discard=True, ignore_expires=True)
    except FileNotFoundError:
        send_error("cookies.txt nicht gefunden")
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
