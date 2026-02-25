# Authored By DoraemonBro © 2026
import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from ntgcalls import TelegramServerError, ConnectionNotFound
from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall, NoAudioSourceFound, NoVideoSourceFound
from pytgcalls.types import AudioQuality, ChatUpdate, MediaStream, StreamEnded, Update, VideoQuality

import config
from strings import get_string
from AnnieXMedia import LOGGER, YouTube, app
from AnnieXMedia.misc import db
from AnnieXMedia.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from AnnieXMedia.utils.exceptions import AssistantErr
from AnnieXMedia.utils.formatters import check_duration, seconds_to_min, speed_converter
from AnnieXMedia.utils.inline.play import stream_markup
from AnnieXMedia.utils.stream.autoclear import auto_clean
from AnnieXMedia.utils.thumbnails import get_thumb
from AnnieXMedia.utils.errors import capture_internal_err

autoend = {}
counter = {}  # kept for compatibility (some forks rely on it)

# Internal: per-chat autoend tasks (prevents spam + keeps smooth)
_autoend_tasks: dict[int, asyncio.Task] = {}


def dynamic_media_stream(path: str, video: bool = False, ffmpeg_params: str = None) -> MediaStream:
    if video:
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=ffmpeg_params,
        )
    return MediaStream(
        media_path=path,
        audio_parameters=AudioQuality.HIGH,
        audio_flags=MediaStream.Flags.REQUIRED,
        video_flags=MediaStream.Flags.IGNORE,
        ffmpeg_parameters=ffmpeg_params,
    )


async def _clear_(chat_id: int) -> None:
    """
    Clears queue + state safely. Never let cleanup crash playback.
    """
    popped = db.pop(chat_id, None)
    if popped:
        try:
            await auto_clean(popped)
        except Exception:
            pass
    db[chat_id] = []
    try:
        await remove_active_video_chat(chat_id)
    except Exception:
        pass
    try:
        await remove_active_chat(chat_id)
    except Exception:
        pass
    try:
        await set_loop(chat_id, 0)
    except Exception:
        pass

    t = _autoend_tasks.pop(chat_id, None)
    if t and not t.done():
        t.cancel()


class Call:
    def __init__(self):
        self.userbot1 = (
            Client("AnnieXAssis1", config.API_ID, config.API_HASH, session_string=config.STRING1)
            if config.STRING1
            else None
        )
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        self.userbot2 = (
            Client("AnnieXAssis2", config.API_ID, config.API_HASH, session_string=config.STRING2)
            if config.STRING2
            else None
        )
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        self.userbot3 = (
            Client("AnnieXAssis3", config.API_ID, config.API_HASH, session_string=config.STRING3)
            if config.STRING3
            else None
        )
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        self.userbot4 = (
            Client("AnnieXAssis4", config.API_ID, config.API_HASH, session_string=config.STRING4)
            if config.STRING4
            else None
        )
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        self.userbot5 = (
            Client("AnnieXAssis5", config.API_ID, config.API_HASH, session_string=config.STRING5)
            if config.STRING5
            else None
        )
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()

    async def _leave_with(self, client: PyTgCalls, chat_id: int) -> None:
        """
        Leaves VC using the SAME assistant that was playing.
        Prevents random 'ConnectionNotFound' during stop/autoend.
        """
        await _clear_(chat_id)
        try:
            await client.leave_call(chat_id)
        except Exception:
            pass
        self.active_calls.discard(chat_id)

    # ---------------- Basic controls ----------------
    @capture_internal_err
    async def pause_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    @capture_internal_err
    async def resume_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    @capture_internal_err
    async def mute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.mute(chat_id)

    @capture_internal_err
    async def unmute_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await assistant.unmute(chat_id)

    @capture_internal_err
    async def stop_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def force_stop_stream(self, chat_id: int) -> None:
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            if check:
                check.pop(0)
        except Exception:
            pass
        await _clear_(chat_id)
        if chat_id not in self.active_calls:
            return
        try:
            await assistant.leave_call(chat_id)
        except Exception:
            pass
        finally:
            self.active_calls.discard(chat_id)

    @capture_internal_err
    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ) -> None:
        assistant = await group_assistant(self, chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def vc_users(self, chat_id: int) -> list:
        assistant = await group_assistant(self, chat_id)
        participants = await assistant.get_participants(chat_id)
        return [p.user_id for p in participants if not p.is_muted]

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await group_assistant(self, chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        is_video = mode == "video"
        stream = dynamic_media_stream(path=file_path, video=is_video, ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)

    # ---------------- Speed (fixed + safe) ----------------
    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        if not isinstance(playing, list) or not playing or not isinstance(playing[0], dict):
            raise AssistantErr("Invalid stream info for speedup.")

        assistant = await group_assistant(self, chat_id)

        base = os.path.basename(file_path)
        chatdir = os.path.join("playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        def _atempo_chain(sp: float) -> str:
            # atempo supports 0.5–2.0 per filter; chain outside range
            parts = []
            while sp > 2.0:
                parts.append("atempo=2.0")
                sp /= 2.0
            while sp < 0.5:
                parts.append("atempo=0.5")
                sp /= 0.5
            parts.append(f"atempo={sp:.4f}")
            return ",".join(parts)

        if not os.path.exists(out):
            vpts = 1.0 / float(speed)  # correct: faster => smaller PTS
            atempo = _atempo_chain(float(speed))

            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-i", file_path,
                "-filter:v", f"setpts={vpts}*PTS",
                "-filter:a", atempo,
                "-y", out,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, err = await proc.communicate()
            if proc.returncode != 0:
                raise AssistantErr(f"FFmpeg speed failed: {err.decode(errors='ignore')[:350]}")

        loop = asyncio.get_running_loop()
        dur = int(await loop.run_in_executor(None, check_duration, out))

        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration_min = seconds_to_min(dur)
        is_video = playing[0]["streamtype"] == "video"
        ffmpeg_params = f"-ss {played} -to {duration_min}"
        stream = dynamic_media_stream(path=out, video=is_video, ffmpeg_params=ffmpeg_params)

        if chat_id in db and db[chat_id] and db[chat_id][0].get("file") == file_path:
            await assistant.play(chat_id, stream)
            db[chat_id][0].update(
                {
                    "played": con_seconds,
                    "dur": duration_min,
                    "seconds": dur,
                    "speed_path": out,
                    "speed": speed,
                    "old_dur": db[chat_id][0].get("dur"),
                    "old_second": db[chat_id][0].get("seconds"),
                }
            )
        else:
            raise AssistantErr("Stream mismatch during speedup.")

    # ---------------- Join / stream test ----------------
    @capture_internal_err
    async def stream_call(self, link: str) -> None:
        # If LOGGER_ID missing, just skip (Railway-friendly)
        if not getattr(config, "LOGGER_ID", None):
            return
        assistant = await group_assistant(self, config.LOGGER_ID)
        try:
            await assistant.play(config.LOGGER_ID, MediaStream(link))
            await asyncio.sleep(6)
        finally:
            try:
                await assistant.leave_call(config.LOGGER_ID)
            except Exception:
                pass

    @capture_internal_err
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ) -> None:
        assistant = await group_assistant(self, chat_id)
        lang = await get_lang(chat_id)
        _ = get_string(lang)
        stream = dynamic_media_stream(path=link, video=bool(video))

        try:
            await assistant.play(chat_id, stream)
        except (NoActiveGroupCall, ChatAdminRequired):
            raise AssistantErr(_["call_8"])
        except NoAudioSourceFound:
            raise AssistantErr(_["call_11"])
        except NoVideoSourceFound:
            raise AssistantErr(_["call_12"])
        except (ConnectionNotFound, TelegramServerError):
            raise AssistantErr(_["call_10"])
        except Exception as e:
            raise AssistantErr(f"ᴜɴᴀʙʟᴇ ᴛᴏ ᴊᴏɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ᴄᴀʟʟ.\nRᴇᴀsᴏɴ: {e}")

        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)

        # Auto-end: schedule stop if only assistant stays
        if await is_autoend():
            try:
                users = len(await assistant.get_participants(chat_id))
            except Exception:
                users = 2  # assume safe

            if users <= 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

                old = _autoend_tasks.get(chat_id)
                if old and not old.done():
                    old.cancel()

                async def _worker():
                    try:
                        await asyncio.sleep(60)
                        try:
                            now_users = len(await assistant.get_participants(chat_id))
                        except Exception:
                            now_users = 2
                        if now_users <= 1:
                            await self._leave_with(assistant, chat_id)
                    finally:
                        _autoend_tasks.pop(chat_id, None)

                _autoend_tasks[chat_id] = asyncio.create_task(_worker())
            else:
                autoend.pop(chat_id, None)

    # ---------------- Queue next play ----------------
    @capture_internal_err
    async def play(self, client, chat_id: int) -> None:
        check = db.get(chat_id)
        if not check:
            await self._leave_with(client, chat_id)
            return

        loop = await get_loop(chat_id)
        popped = None

        try:
            if loop == 0:
                popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)

            if popped:
                try:
                    await auto_clean(popped)
                except Exception:
                    pass

            if not check:
                await self._leave_with(client, chat_id)
                return

        except Exception:
            await self._leave_with(client, chat_id)
            return

        queued = check[0]["file"]
        language = await get_lang(chat_id)
        _ = get_string(language)
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        db[chat_id][0]["played"] = 0

        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        video = True if str(streamtype) == "video" else False

        # LIVE
        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await app.send_message(original_chat_id, text=_["call_6"])

            stream = dynamic_media_stream(path=link, video=video)
            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_6"])

            img = await get_thumb(videoid)
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            return

        # VIDEO DOWNLOAD
        if "vid_" in queued:
            mystic = await app.send_message(original_chat_id, _["call_7"])
            try:
                file_path, _direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=True if str(streamtype) == "video" else False,
                )
            except Exception:
                return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)

            stream = dynamic_media_stream(path=file_path, video=video)
            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_6"])

            img = await get_thumb(videoid)
            button = stream_markup(_, chat_id)
            try:
                await mystic.delete()
            except Exception:
                pass

            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            return

        # DIRECT URL
        if "index_" in queued:
            stream = dynamic_media_stream(path=videoid, video=video)
            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_6"])

            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=config.STREAM_IMG_URL,
                caption=_["stream_2"].format(user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            return

        # FILE / TELEGRAM
        stream = dynamic_media_stream(path=queued, video=video)
        try:
            await client.play(chat_id, stream)
        except Exception:
            return await app.send_message(original_chat_id, text=_["call_6"])

        if videoid == "telegram":
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=(config.TELEGRAM_AUDIO_URL if str(streamtype) == "audio" else config.TELEGRAM_VIDEO_URL),
                caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            return

        if videoid == "soundcloud":
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=config.SOUNCLOUD_IMG_URL,
                caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], check[0]["dur"], user),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            return

        img = await get_thumb(videoid)
        button = stream_markup(_, chat_id)
        try:
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:2
