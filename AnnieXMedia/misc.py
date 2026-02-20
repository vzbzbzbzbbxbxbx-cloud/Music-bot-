# Authored By Certified Coders © 2025
import socket
import time

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus

from config import OWNER_ID
from AnnieXMedia.core.mongo import mongodb
from .logging import LOGGER

SUDOERS = filters.user()
COMMANDERS = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
HAPP = None
_boot_ = time.time()

def is_heroku():
    return "heroku" in socket.getfqdn()


def dbb():
    global db
    db = {}
    LOGGER(__name__).info("ᴅᴀᴛᴀʙᴀsᴇ ʟᴏᴀᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ💗")

async def sudo():
    global SUDOERS
    SUDOERS.add(OWNER_ID)
    sudoersdb = mongodb.sudoers
    data = await sudoersdb.find_one({"sudo": "sudo"}) or {}
    sudoers = data.get("sudoers", [])

    if OWNER_ID not in sudoers:
        sudoers.append(OWNER_ID)
        await sudoersdb.update_one(
            {"sudo": "sudo"}, {"$set": {"sudoers": sudoers}}, upsert=True
        )

    for user_id in sudoers:
        SUDOERS.add(user_id)

    LOGGER(__name__).info("sᴜᴅᴏ ᴜsᴇʀs ᴅᴏɴᴇ..")

def heroku():
    # Disabled for Railway / Docker hosting
    global HAPP
    HAPP = None
    LOGGER(__name__).info("Heroku system disabled (Railway mode)")
    
