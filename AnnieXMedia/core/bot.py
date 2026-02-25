# Authored By DoraemonBro © 2026
import sys
from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus

import config
from ..logging import LOGGER


class MusicBotClient(Client):
    def __init__(self):
        super().__init__(
            name="ShindoraXMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            workers=16,
            max_concurrent_transmissions=4,
        )
        LOGGER(__name__).info("Bot client initialized.")

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username, self.id = me.username, me.id
        self.name = f"{me.first_name} {me.last_name or ''}".strip()
        self.mention = me.mention

        # LOGGER_ID is optional. If not set, bot will run without log chat.
        if not getattr(config, 'LOGGER_ID', None) or int(getattr(config, 'LOGGER_ID', 0)) == 0:
            LOGGER(__name__).warning('LOGGER_ID not set - running without log group/channel checks.')
            LOGGER(__name__).info(f"✅ Music Bot started as {self.name} (@{self.username})")
            return


        try:
            await self.send_message(
                config.LOGGER_ID,
                (
                    f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\n"
                    f"ɪᴅ : <code>{self.id}</code>\n"
                    f"ɴᴀᴍᴇ : {self.name}\n"
                    f"ᴜsᴇʀɴᴀᴍᴇ : @{self.username}"
                ),
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error("❌ Bot cannot access the log group/channel – add & promote it first!")
            sys.exit()
        except Exception as exc:
            LOGGER(__name__).error(f"❌ Bot has failed to access the log group.\nReason: {type(exc).__name__}")
            sys.exit()

        try:
            member = await self.get_chat_member(config.LOGGER_ID, self.id)
            if member.status != ChatMemberStatus.ADMINISTRATOR:
                LOGGER(__name__).error("❌ Promote the bot as admin in the log group/channel.")
                sys.exit()
        except Exception as e:
            LOGGER(__name__).error(f"❌ Could not check admin status: {e}")
            sys.exit()

        LOGGER(__name__).info(f"✅ Music Bot started as {self.name} (@{self.username})")
        
