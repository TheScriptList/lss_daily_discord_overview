"""LSS Daily Discord Overview - Daily overview of building extensions and schoolings"""

from importlib.metadata import version

__version__ = version("lss-daily-discord-overview")

# Import the main function to expose it at package level
from .lss_daily_discord_overview import main

__all__ = ["main", "__version__"]
