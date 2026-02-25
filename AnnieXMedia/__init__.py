# Authored By DoraemonBro © 2026
"""Shindora x Music - Lean Runtime Exports

This module intentionally avoids heavy side-effects at import time.
Use `bootstrap()` in __main__ to initialize directories and in-memory state.
"""

from .logging import LOGGER
from AnnieXMedia.core.bot import MusicBotClient
from AnnieXMedia.core.userbot import Userbot

# Lightweight platform APIs used by streaming core
from AnnieXMedia.platforms.Telegram import TeleAPI
from AnnieXMedia.platforms.Youtube import YouTubeAPI
from AnnieXMedia.platforms.Carbon import CarbonAPI

app = MusicBotClient()
userbot = Userbot()

Telegram = TeleAPI()
YouTube = YouTubeAPI()
Carbon = CarbonAPI()


def bootstrap() -> None:
    """Initialize required folders and in-memory state."""
    from AnnieXMedia.core.dir import StorageManager
    from AnnieXMedia.misc import dbb

    StorageManager()
    dbb()
  
