# Authored By DoraemonBro © 2026
import asyncio
import importlib
import os

from pyrogram import idle

import config
from AnnieXMedia import LOGGER, app, bootstrap, userbot
from AnnieXMedia.core.call import StreamController
from AnnieXMedia.plugins import ALL_MODULES
from AnnieXMedia.utils.cookie_handler import fetch_and_store_cookies
from config import BANNED_USERS


def _validate_env() -> None:
    missing = []
    if not config.API_ID:
        missing.append("API_ID")
    if not config.API_HASH:
        missing.append("API_HASH")
    if not config.BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not config.OWNER_ID:
        missing.append("OWNER_ID")
    if not (config.STRING1 or config.STRING2 or config.STRING3 or config.STRING4 or config.STRING5):
        missing.append("STRING_SESSION (or STRING1..STRING5)")
    if missing:
        raise SystemExit("Missing required env vars: " + ", ".join(missing))


async def main() -> None:
    _validate_env()

    # init folders + in-memory state (no heavy side effects)
    bootstrap()

    # Optional cookies
    if config.COOKIE_URL:
        try:
            ok = await fetch_and_store_cookies()
            if ok:
                LOGGER(__name__).info("YouTube cookies loaded ✅")
        except Exception as e:
            LOGGER(__name__).warning(f"Cookie load skipped: {e}")

    # Start bot
    await app.start()

    # Load only selected modules (LEAN_MODE default)
    loaded = 0
    for mod in ALL_MODULES:
        try:
            importlib.import_module("AnnieXMedia.plugins" + mod)
            loaded += 1
        except Exception as e:
            LOGGER("PluginLoader").error(f"Failed to load module {mod}: {e}")

    LOGGER("PluginLoader").info(f"Modules loaded: {loaded}/{len(ALL_MODULES)} (LEAN_MODE={os.getenv('LEAN_MODE','1')})")

    # Start assistants + voice engine
    await userbot.start()
    await StreamController.start()
    await StreamController.decorators()

    LOGGER("ShindoraXMusic").info("Shindora x Music started successfully ✅")

    await idle()

    # Shutdown
    await app.stop()
    await userbot.stop()
    LOGGER("ShindoraXMusic").info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
    
