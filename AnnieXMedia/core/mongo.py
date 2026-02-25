# Authored By DoraemonBro © 2026
from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_DB_URI
from ..logging import LOGGER

mongodb = None

if not MONGO_DB_URI:
    LOGGER(__name__).warning("MongoDB is not configured (MONGO_DB_URI missing). Running in no-DB mode.")
else:
    try:
        _mongo_async_ = AsyncIOMotorClient(MONGO_DB_URI, serverSelectionTimeoutMS=12500)
        mongodb = _mongo_async_.Annie
        LOGGER(__name__).info("Connected to MongoDB.")
    except Exception as e:
        mongodb = None
        LOGGER(__name__).warning(f"MongoDB connection failed (no-DB mode): {e}")
        
