import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

# Load environment variables from .env file (if you use one)
load_dotenv()

# ── Core bot config ────────────────────────────────────────────────────────────
API_ID = int(getenv("API_ID", "0"))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
OWNER_ID = int(getenv("OWNER_ID", "0"))
OWNER_USERNAME = "@DoraemonBro"
BOT_USERNAME = "@Shindoraxmusic_bot"
BOT_NAME = "˹𝙎𝙃𝙄𝙉𝘿𝙊𝙍𝘼 ✘ 𝙈𝙐𝙎𝙄𝘾˼ ♪"
ASSUSERNAME = "shindoraxmusic"

# ── Database & logging ─────────────────────────────────────────────────────────
MONGO_DB_URI = getenv("MONGO_DB_URI", "")
# FIXED: Added missing parenthesis
LOGGER_ID = int(getenv("LOGGER_ID", "0"))

# ── Limits ──────────────────────────────────────────────────────────────
# Note: getenv is okay here if you have defaults, but kept as strings for safety then cast to int
DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 300))
SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "1200"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "1800"))
TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "157286400"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "1288490189"))
PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", "30"))

# ── External APIs ──────────────────────────────────────────────────────────────
COOKIE_URL = "https://gist.githubusercontent.com/vzbzbzbzbbxbxbx-cloud/420384c268dc22598cef0c4f624e0589/raw/45ed7a2b4e0e23f7045d875d35f74b38c09c75d6/gistfile1.txt"
API_URL = getenv("API_URL")
VIDEO_API_URL = getenv("VIDEO_API_URL")
API_KEY = getenv("API_KEY")
DEEP_API = getenv("DEEP_API")

# ── Hosting ───────────────────────────────────────────────────────
HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

# ── Git ──────────────────────────────────────────────────────────────
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/CertifiedCoders/AnnieXMusic")
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "Master")
GIT_TOKEN = getenv("GIT_TOKEN")

# ── Support links ──────────────────────────────────────────────────────────────
SUPPORT_CHANNEL = "https://t.me/nothingheloo" # Ensure this is a valid link if used
# FIXED: Changed from @DoraemonBro to a full URL to pass regex check
SUPPORT_CHAT = "https://t.me/DoraemonBro"

# ── Assistant auto-leave ───────────────────────────────────────────────────────
AUTO_LEAVING_ASSISTANT = False
AUTO_LEAVE_ASSISTANT_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "3600"))

# ── Debug ──────────────────────────────────────────────────────────────────────
DEBUG_IGNORE_LOG = True

# ── Spotify ─────────────────────────────────────────────────────────
SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "22b6125bfe224587b722d6815002db2b")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "c9c63c6fbf2f467c8bc68624851e9773")

# ── Session strings ─────────────────────────────────────────────────
STRING1 = getenv("STRING1") or getenv("STRING_SESSION") or getenv("STRING_SESSION1")
STRING2 = getenv("STRING2") or getenv("STRING_SESSION2")
STRING3 = getenv("STRING3") or getenv("STRING_SESSION3")
STRING4 = getenv("STRING4") or getenv("STRING_SESSION4")
STRING5 = getenv("STRING5") or getenv("STRING_SESSION5")

# ── Media assets ───────────────────────────────────────────────────────────────
START_VIDS = [
    "https://files.catbox.moe/6zy65l.mp4",
    "https://files.catbox.moe/vju0by.mp4",
    "https://files.catbox.moe/1ki16a.mp4",
]
STICKERS = [
    "CAACAgUAAx0Cd6nKUAACASBl_rnalOle6g7qS-ry-aZ1ZpVEnwACgg8AAizLEFfI5wfykoCR4h4E",
    "CAACAgUAAx0Cd6nKUAACATJl_rsEJOsaaPSYGhU7bo7iEwL8AAPMDgACu2PYV8Vb8aT4_HUPHgQ",
]
HELP_IMG_URL = "https://files.catbox.moe/4uw0h1.png"
PING_VID_URL = "https://files.catbox.moe/gop9yn.mp4"
PLAYLIST_IMG_URL = "https://files.catbox.moe/3y8ban.png"
STATS_VID_URL = "https://files.catbox.moe/mmz1om.mp4"
TELEGRAM_AUDIO_URL = "https://files.catbox.moe/h8kpcn.png"
TELEGRAM_VIDEO_URL = "https://files.catbox.moe/dtmb9t.png"
STREAM_IMG_URL = "https://files.catbox.moe/skk8kq.jpg"
SOUNCLOUD_IMG_URL = "https://files.catbox.moe/kk68xi.png"
YOUTUBE_IMG_URL = "https://files.catbox.moe/lk5r39.png"
SPOTIFY_ARTIST_IMG_URL = SPOTIFY_ALBUM_IMG_URL = SPOTIFY_PLAYLIST_IMG_URL = YOUTUBE_IMG_URL

# ── Helpers ────────────────────────────────────────────────────────────────────
def time_to_seconds(time: str) -> int:
    return sum(int(x) * 60**i for i, x in enumerate(reversed(time.split(":"))))

DURATION_LIMIT = time_to_seconds(f"{DURATION_LIMIT_MIN}:00")

# ───── Bot Introduction Messages ───── #
AYU = ["💞", "🦋", "🔍", "🧪", "⚡️", "🔥", "🎩", "🌈", "🍷", "🥂", "🥃", "🕊️", "🪄", "💌", "🧨"]
AYUV = [
    "ʜᴇʟʟᴏ {0}, 🥀\n\n ɪᴛ'ꜱ ᴍᴇ {1} !\n\n┏━━━━━━━━━━━━━━━━━⧫\n┠ ◆ ꜱᴜᴘᴘᴏʀᴛɪɴɢ ᴘʟᴀᴛꜰᴏʀᴍꜱ : ʏᴏᴜᴛᴜʙᴇ, ꜱᴘᴏᴛɪꜰʏ,\n┠ ◆ ʀᴇꜱꜱᴏ, ᴀᴘᴘʟᴇᴍᴜꜱɪᴄ , ꜱᴏᴜɴᴅᴄʟᴏᴜᴅ ᴇᴛᴄ.\n┗━━━━━━━━━━━━━━━━━⧫\n┏━━━━━━━━━━━━━━━━━⧫\n┠ ➥ Uᴘᴛɪᴍᴇ : {2}\n┠ ➥ SᴇʀᴠᴇʀSᴛᴏʀᴀɢᴇ : {3}\n┠ ➥ CPU Lᴏᴀᴅ : {4}\n┠ ➥ RAM Cᴏɴsᴜᴘᴛɪᴏɴ : {5}\n┠ ➥ ᴜꜱᴇʀꜱ : {6}\n┠ ➥ ᴄʜᴀᴛꜱ : {7}\n┗━━━━━━━━━━━━━━━━━⧫\n\n🫧 ᴅᴇᴠᴇʟᴏᴩᴇʀ 🪽 ➪ [ ⟦𝙳𝙾𝚁𝙰𝙴𝙼𝙾𝙽_𝙱𝚁𝙾⟧🍁 ✔︎](@DoraemonBro)",
    "ʜɪɪ, {0} ~\n\n◆ ɪ'ᴍ ᴀ {1} ᴛᴇʟᴇɢʀᴀᴍ ꜱᴛʀᴇᴀᴍɪɴɢ ʙᴏᴛ ᴡɪᴛʜ ꜱᴏᴍᴇ ᴜꜱᴇꜰᴜʟ\n◆ ᴜʟᴛʀᴀ ғᴀsᴛ ᴠᴄ ᴘʟᴀʏᴇʀ ꜰᴇᴀᴛᴜʀᴇꜱ.\n\n✨ ꜰᴇᴀᴛᴜʀᴇꜱ ⚡️\n◆ ʙᴏᴛ ғᴏʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘs.\n◆ Sᴜᴘᴇʀғᴀsᴛ ʟᴀɢ Fʀᴇᴇ ᴘʟᴀʏᴇʀ.\n◆ ʏᴏᴜ ᴄᴀɴ ᴘʟᴀʏ ᴍᴜꜱɪᴄ + ᴠɪᴅᴇᴏ.\n◆ ʟɪᴠᴇ ꜱᴛʀᴇᴀᴍɪɴɢ.\n◆ ɴᴏ ᴘʀᴏᴍᴏ.\n◆ ʙᴇꜱᴛ ꜱᴏᴜɴᴅ Qᴜᴀʟɪᴛʏ.\n◆ 24×7 ʏᴏᴜ ᴄᴀɴ ᴘʟᴀʏ ᴍᴜꜱɪᴄ.\n◆ ᴀᴅᴅ ᴛʜɪꜱ ʙᴏᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴍᴀᴋᴇ ɪᴛ ᴀᴅᴍɪɴ ᴀɴᴅ ᴇɴᴊᴏʏ ᴍᴜꜱɪᴄ 🎵.\n\n┏━━━━━━━━━━━━━━━━━⧫\n┠ ◆ ꜱᴜᴘᴘᴏʀᴛɪɴɢ ᴘʟᴀᴛꜰᴏʀᴍꜱ : ʏᴏᴜᴛᴜʙᴇ, ꜱᴘᴏᴛɪꜰʏ,\n┠ ◆ ʀᴇꜱꜱᴏ, ᴀᴘᴘʟᴇᴍᴜꜱɪᴄ , ꜱᴏᴜɴᴅᴄʟᴏᴜᴅ ᴇᴛᴄ.\n┗━━━━━━━━━━━━━━━━━⧫\n┏━━━━━━━━━━━━━━━━━⧫\n┠ ➥ Uᴘᴛɪᴍᴇ : {2}\n┠ ➥ SᴇʀᴠᴇʀSᴛᴏʀᴀɢᴇ : {3}\n┠ ➥ CPU Lᴏᴀᴅ : {4}\n┠ ➥ RAM Cᴏɴsᴜᴘᴛɪᴏɴ : {5}\n┠ ➥ ᴜꜱᴇʀꜱ : {6}\n┠ ➥ ᴄʜᴀᴛꜱ : {7}\n┗━━━━━━━━━━━━━━━━━⧫\n\n🫧 ᴅᴇᴠᴇʟᴏᴩᴇʀ 🪽 ➪ [ ⟦𝙳𝙾𝚁𝙰𝙴𝙼𝙾𝙽_𝙱𝚁𝙾⟧🍁 ✔︎](@DoraemonBro)",
]

# ── Runtime structures ─────────────────────────────────────────────────────────
BANNED_USERS = filters.user()
adminlist, lyrical, autoclean, confirmer = {}, {}, [], {}

# ── Minimal validation ─────────────────────────────────────────────────────────
if SUPPORT_CHANNEL and not re.match(r"^https?://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - Invalid SUPPORT_CHANNEL URL. Must start with https://")

if SUPPORT_CHAT and not re.match(r"^https?://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - Invalid SUPPORT_CHAT URL. Must start with https://")
