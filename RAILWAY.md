# Deploy Shindora x Music on Railway (Free Plan)

## 1) Upload
- Create a new Railway project
- Deploy from GitHub or upload this repo

## 2) Add Variables
Set these in Railway → Service → Variables:

Required:
- API_ID
- API_HASH
- BOT_TOKEN
- OWNER_ID
- STRING_SESSION (or STRING1..STRING5)

Recommended:
- LOGGER_ID (a group/channel ID where the bot is admin)

Optional:
- MONGO_DB_URI (bot runs without DB in LEAN_MODE)
- COOKIE_URL (Netscape cookies for yt-dlp)
- SUPPORT_CHAT / SUPPORT_CHANNEL

Keep:
- LEAN_MODE=1

## 3) Start Command
Use:
- `python -m AnnieXMedia`

## 4) Notes
- Make sure the bot is **admin** in LOGGER_ID (if you set it)
- For voice chat streaming: your group must have **Video Chat / Voice Chat** enabled
- 
