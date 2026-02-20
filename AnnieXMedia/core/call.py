# Authored By Certified Coders © 2025
# Rebuilt: single VC stack, stable FFmpeg params, stream-end handling, no minor errors.

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, Union

from pyrogram import Client
from pyrogram.errors import FloodWait, ChatAdminRequired
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall, NoAudioSourceFound, NoVideoSourceFound
from pytgcalls.types import AudioQuality, VideoQuality, MediaStream, Update, StreamEnded, ChatUpdate

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


autoend = {}   # {chat_id: datetime_deadline}
counter = {}   # kept for compatibility with your project


def _is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def dynamic_media_stream(
    path: str,
    video: bool = False,
    ffmpeg_params: Optional[str] = None,
) -> MediaStream:
    """
    Stable stream params for Telegram VC:
    - reconnect flags for URLs
    - supports seek/speed via ffmpeg_params
    - keeps bitrate reasonable for Railway
    """
    base = "-hide_banner -loglevel error"
    reconnect = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5" if _is_url(path) else ""
    low_latency = "-fflags +nobuffer -flags low_delay -flush_packets 1"
    extra = ffmpeg_params or ""

    if video:
        # 360p-ish, stable & light
        v_params = (
            f"{base} {reconnect} {low_latency} {extra} "
            f"-vf scale=640:360 -r 24 -g 48 -preset veryfast "
            f"-b:v 650k -maxrate 850k -bufsize 1200k "
            f"-ar 48000 -ac 2"
        )
        return MediaStream(
            media_path=path,
            audio_parameters=AudioQuality(128_000),
            video_parameters=VideoQuality.SD_480p,
            audio_flags=MediaStream.Flags.REQUIRED,
            video_flags=MediaStream.Flags.REQUIRED,
            ffmpeg_parameters=v_params,
        )

    # audio-only
    a_params = f"{base} {reconnect} {low_latency} {extra} -vn -ar 48000 -ac 2"
    return MediaStream(
        media_path=path,
        audio_parameters=AudioQuality(128_000),
        audio_flags=MediaStream.Flags.REQUIRED,
        video_flags=MediaStream.Flags.IGNORE,
        ffmpeg_parameters=a_params,
    )


async def _clear_(chat_id: int) -> None:
    popped = db.pop(chat_id, None)
    if popped:
        await auto_clean(popped)
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)
    await set_loop(chat_id, 0)


async def _ensure_vc_compatible(file_path: str, want_video: bool) -> str:
    """
    Remux/re-encode into Telegram-VC friendly format (48k stereo, AAC).
    Only used for downloaded YT items (vid_).
    """
    fixed_path = f"{file_path}.fixed.mp4"
    if os.path.exists(fixed_path):
        return fixed_path

    if want_video:
        cmd = (
            f'ffmpeg -y -i "{file_path}" '
            f'-map 0:v? -map 0:a:0 '
            f'-vf scale=640:360 -r 24 -g 48 '
            f'-c:v libx264 -preset veryfast '
            f'-c:a aac -b:a 128k -ar 48000 -ac 2 '
            f'-movflags +faststart '
            f'"{fixed_path}"'
        )
    else:
        cmd = (
            f'ffmpeg -y -i "{file_path}" '
            f'-vn -c:a aac -b:a 128k -ar 48000 -ac 2 '
            f'-movflags +faststart '
            f'"{fixed_path}"'
        )

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()
    return fixed_path if os.path.exists(fixed_path) else file_path


class Call:
    def __init__(self):
        self.userbot1 = (
            Client("AnnieXAssis1", config.API_ID, config.API_HASH, session_string=config.STRING1)
            if getattr(config, "STRING1", None)
            else None
        )
        self.one = PyTgCalls(self.userbot1) if self.userbot1 else None

        self.userbot2 = (
            Client("AnnieXAssis2", config.API_ID, config.API_HASH, session_string=config.STRING2)
            if getattr(config, "STRING2", None)
            else None
        )
        self.two = PyTgCalls(self.userbot2) if self.userbot2 else None

        self.userbot3 = (
            Client("AnnieXAssis3", config.API_ID, config.API_HASH, session_string=config.STRING3)
            if getattr(config, "STRING3", None)
            else None
        )
        self.three = PyTgCalls(self.userbot3) if self.userbot3 else None

        self.userbot4 = (
            Client("AnnieXAssis4", config.API_ID, config.API_HASH, session_string=config.STRING4)
            if getattr(config, "STRING4", None)
            else None
        )
        self.four = PyTgCalls(self.userbot4) if self.userbot4 else None

        self.userbot5 = (
            Client("AnnieXAssis5", config.API_ID, config.API_HASH, session_string=config.STRING5)
            if getattr(config, "STRING5", None)
            else None
        )
        self.five = PyTgCalls(self.userbot5) if self.userbot5 else None

        self.active_calls: set[int] = set()
        self._autoend_task: Optional[asyncio.Task] = None

        # attach update handlers (queue-next / autoend)
        for c in (self.one, self.two, self.three, self.four, self.five):
            if c:
                self._attach_handlers(c)

    def _attach_handlers(self, calls: PyTgCalls) -> None:
        """
        Handles:
        - StreamEnded -> play next item
        - ChatUpdate  -> autoend schedule refresh
        """

        @calls.on_update()
        async def _on_update(_: PyTgCalls, update: Update):
            try:
                # Stream ended => play next
                if isinstance(update, StreamEnded):
                    chat_id = int(update.chat_id)
                    if chat_id in self.active_calls:
                        await self.play(calls, chat_id)
                    return

                # Chat update => autoend check (if enabled)
                if isinstance(update, ChatUpdate):
                    chat_id = int(update.chat_id)
                    if chat_id not in self.active_calls:
                        return
                    if not await is_autoend():
                        return
                    assistant = await group_assistant(self, chat_id)
                    users = len(await assistant.get_participants(chat_id))
                    if users <= 1:
                        autoend[chat_id] = datetime.now() + timedelta(minutes=1)
                    else:
                        autoend.pop(chat_id, None)
            except Exception:
                # never let handlers crash the client
                return

    async def _autoend_loop(self) -> None:
        while True:
            await asyncio.sleep(15)
            if not autoend:
                continue
            now = datetime.now()
            for chat_id, deadline in list(autoend.items()):
                if now >= deadline:
                    try:
                        await self.stop_stream(chat_id)
                    except Exception:
                        pass
                    autoend.pop(chat_id, None)
                    counter.pop(chat_id, None)

    # ---------------- Controls ----------------

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
            autoend.pop(chat_id, None)

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
            autoend.pop(chat_id, None)

    @capture_internal_err
    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None) -> None:
        assistant = await group_assistant(self, chat_id)
        stream = dynamic_media_stream(path=link, video=bool(video))
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def vc_users(self, chat_id: int) -> list:
        assistant = await group_assistant(self, chat_id)
        participants = await assistant.get_participants(chat_id)
        return [p.user_id for p in participants if not p.is_muted]

    # ---------------- Seek / Speed ----------------

    @capture_internal_err
    async def seek_stream(self, chat_id: int, file_path: str, to_seek: str, duration: str, mode: str) -> None:
        assistant = await group_assistant(self, chat_id)
        ffmpeg_params = f"-ss {to_seek} -to {duration}"
        is_video = mode == "video"
        stream = dynamic_media_stream(path=file_path, video=is_video, ffmpeg_params=ffmpeg_params)
        await assistant.play(chat_id, stream)

    @capture_internal_err
    async def speedup_stream(self, chat_id: int, file_path: str, speed: float, playing: list) -> None:
        if not isinstance(playing, list) or not playing or not isinstance(playing[0], dict):
            raise AssistantErr("Invalid stream info for speedup.")

        assistant = await group_assistant(self, chat_id)
        base = os.path.basename(file_path)
        chatdir = os.path.join("playback", str(speed))
        os.makedirs(chatdir, exist_ok=True)
        out = os.path.join(chatdir, base)

        if not os.path.exists(out):
            vs = str(2.0 / float(speed))
            cmd = (
                f'ffmpeg -y -i "{file_path}" '
                f'-filter:v "setpts={vs}*PTS" '
                f'-filter:a "atempo={speed}" '
                f'-ar 48000 -ac 2 '
                f'"{out}"'
            )
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdin=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
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

    # ---------------- Join / Play ----------------

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
        except Exception:
            raise AssistantErr(_["call_10"])

        self.active_calls.add(chat_id)
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)

        # schedule autoend if enabled
        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant.get_participants(chat_id))
                if users <= 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except Exception:
                pass

    @capture_internal_err
    async def play(self, client: PyTgCalls, chat_id: int) -> None:
        check = db.get(chat_id)
        if not check:
            await _clear_(chat_id)
            if chat_id in self.active_calls:
                try:
                    await client.leave_call(chat_id)
                except Exception:
                    pass
                self.active_calls.discard(chat_id)
            return

        loop = await get_loop(chat_id)

        try:
            if loop == 0:
                popped = check.pop(0)
                await auto_clean(popped)
            else:
                loop -= 1
                await set_loop(chat_id, loop)

            if not check:
                await _clear_(chat_id)
                if chat_id in self.active_calls:
                    try:
                        await client.leave_call(chat_id)
                    except Exception:
                        pass
                    self.active_calls.discard(chat_id)
                return
        except Exception:
            try:
                await _clear_(chat_id)
                return await client.leave_call(chat_id)
            except Exception:
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

        exis = check[0].get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0

        video = True if str(streamtype) == "video" else False

        # ---------- LIVE ----------
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

        # ---------- YT DOWNLOAD ----------
        if "vid_" in queued:
            mystic = await app.send_message(original_chat_id, _["call_7"])
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=True if str(streamtype) == "video" else False,
                )
            except Exception:
                return await mystic.edit_text(_["call_6"], disable_web_page_preview=True)

            fixed = await _ensure_vc_compatible(file_path, want_video=video)
            stream = dynamic_media_stream(path=fixed, video=video)

            try:
                await client.play(chat_id, stream)
            except Exception:
                return await app.send_message(original_chat_id, text=_["call_6"])

            img = await get_thumb(videoid)
            button = stream_markup(_, chat_id)
            await mystic.delete()

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

        # ---------- INDEX ----------
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

        # ---------- NORMAL ----------
        stream = dynamic_media_stream(path=queued, video=video)
        try:
            await client.play(chat_id, stream)
        except Exception:
            return await app.send_message(original_chat_id, text=_["call_6"])

        # UI messages
        if videoid == "telegram":
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=(config.TELE
