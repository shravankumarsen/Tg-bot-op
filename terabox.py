# terabox.py — patched for compatibility and robustness
from aria2p import API as Aria2API, Client as Aria2Client
import asyncio
from dotenv import load_dotenv
from datetime import datetime
import os
import logging
import math
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
import time
import urllib.parse
from urllib.parse import urlparse
from flask import Flask, render_template
from threading import Thread

# Load config.env if present (non-destructive)
load_dotenv("config.env", override=False)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(name)s - %(levelname)s] %(message)s - %(filename)s:%(lineno)d"
)

logger = logging.getLogger(__name__)

# reduce pyrogram noise
logging.getLogger("pyrogram.session").setLevel(logging.ERROR)
logging.getLogger("pyrogram.connection").setLevel(logging.ERROR)
logging.getLogger("pyrogram.dispatcher").setLevel(logging.ERROR)

# aria2 client (expects aria2c / RPC running locally)
aria2 = Aria2API(
    Aria2Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)
options = {
    "max-tries": "50",
    "retry-wait": "3",
    "continue": "true",
    "allow-overwrite": "true",
    "min-split-size": "4M",
    "split": "10"
}

# try to set options but continue if aria2 not available yet
try:
    aria2.set_global_options(options)
except Exception as e:
    logger.warning(f"Could not set aria2 global options at startup: {e}")

# --------------------------
# env vars / config checks
# --------------------------
API_ID = os.environ.get("TELEGRAM_API", "")
if len(API_ID) == 0:
    logging.error("TELEGRAM_API variable is missing! Exiting now")
    exit(1)

API_HASH = os.environ.get("TELEGRAM_HASH", "")
if len(API_HASH) == 0:
    logging.error("TELEGRAM_HASH variable is missing! Exiting now")
    exit(1)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if len(BOT_TOKEN) == 0:
    logging.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

DUMP_CHAT_ID = os.environ.get("DUMP_CHAT_ID", "")
if len(DUMP_CHAT_ID) == 0:
    logging.error("DUMP_CHAT_ID variable is missing! Exiting now")
    exit(1)
else:
    DUMP_CHAT_ID = int(DUMP_CHAT_ID)

FSUB_ID = os.environ.get("FSUB_ID", "")
if len(FSUB_ID) == 0:
    logging.error("FSUB_ID variable is missing! Exiting now")
    exit(1)
else:
    FSUB_ID = int(FSUB_ID)

USER_SESSION_STRING = os.environ.get("USER_SESSION_STRING", "")
if len(USER_SESSION_STRING) == 0:
    logging.info("USER_SESSION_STRING variable is missing! Bot will split Files in 2Gb...")
    USER_SESSION_STRING = None

# --------------------------
# pyrogram clients
# --------------------------
app = Client("jetbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user = None
SPLIT_SIZE = 2093796556
if USER_SESSION_STRING:
    user = Client("jetu", api_id=API_ID, api_hash=API_HASH, session_string=USER_SESSION_STRING)
    SPLIT_SIZE = 4241280205

# --------------------------
# constants & helpers
# --------------------------
VALID_DOMAINS = [
    "terabox.com", "nephobox.com", "4funbox.com", "mirrobox.com",
    "momerybox.com", "teraboxapp.com", "1024tera.com",
    "terabox.app", "gibibox.com", "goaibox.com", "terasharelink.com",
    "teraboxlink.com", "terafileshare.com"
]
last_update_time = 0

async def is_user_member(client, user_id):
    try:
        member = await client.get_chat_member(FSUB_ID, user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error checking membership status for user {user_id}: {e}")
        return False

def is_valid_url(url):
    try:
        parsed_url = urlparse(url)
        return any(parsed_url.netloc.endswith(domain) for domain in VALID_DOMAINS)
    except Exception:
        return False

def format_size(size):
    try:
        size = int(size)
    except Exception:
        return "0 B"
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

# --------------------------
# pyrogram filters compatibility
# --------------------------
# Some pyrogram builds don't expose filters.edited — be compatible.
try:
    MSG_FILTER = filters.text & ~filters.edited
except Exception:
    MSG_FILTER = filters.text

# --------------------------
# bot handlers
# --------------------------
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    join_button = InlineKeyboardButton("ᴊᴏɪɴ ❤️🚀", url="https://t.me/jetmirror")
    developer_button = InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡️", url="https://t.me/rtx5069")
    repo69 = InlineKeyboardButton("ʀᴇᴘᴏ 🌐", url="https://github.com/Hrishi2861/Terabox-Downloader-Bot")
    user_mention = message.from_user.mention
    reply_markup = InlineKeyboardMarkup([[join_button, developer_button], [repo69]])
    final_msg = f"ᴡᴇʟᴄᴏᴍᴇ, {user_mention}.\n\n🌟 ɪ ᴀᴍ ᴀ ᴛᴇʀᴀʙᴏx ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ. sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ ɪ ᴡɪʟʟ ᴅᴏᴡɴʟᴏᴀᴅ ᴡɪᴛʜɪɴ ғᴇᴡ sᴇᴄᴏɴᴅs ᴀɴᴅ sᴇɴᴅ ɪᴛ ᴛᴏ ʏᴏᴜ ✨."
    video_file_id = "/app/Jet-Mirror.mp4"
    if os.path.exists(video_file_id):
        await client.send_video(
            chat_id=message.chat.id,
            video=video_file_id,
            caption=final_msg,
            reply_markup=reply_markup
        )
    else:
        await message.reply_text(final_msg, reply_markup=reply_markup)

async def update_status_message(status_message, text):
    try:
        await status_message.edit_text(text)
    except Exception as e:
        logger.error(f"Failed to update status message: {e}")

@app.on_message(MSG_FILTER)
async def handle_message(client: Client, message: Message):
    if message.text.startswith("/"):
        return
    if not message.from_user:
        return

    user_id = message.from_user.id
    is_member = await is_user_member(client, user_id)

    if not is_member:
        join_button = InlineKeyboardButton("ᴊᴏɪɴ ❤️🚀", url="https://t.me/jetmirror")
        reply_markup = InlineKeyboardMarkup([[join_button]])
        await message.reply_text("ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴍʏ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ.", reply_markup=reply_markup)
        return

    url = None
    for word in message.text.split():
        if is_valid_url(word):
            url = word
            break

    if not url:
        await message.reply_text("Please provide a valid Terabox link.")
        return

    # Use boogafantastic / custom worker as converter (works as you discovered)
    encoded_url = urllib.parse.quote(url)
    final_url = f"https://teraapi.boogafantastic.workers.dev/?url={encoded_url}"

    # Add to aria2
    try:
        download = aria2.add_uris([final_url])
    except Exception as e:
        logger.error(f"Failed to add URI to aria2: {e}")
        return await message.reply_text(f"❌ Failed to start download: {e}")

    status_message = await message.reply_text("sᴇɴᴅɪɴɢ ʏᴏᴜ ᴛʜᴇ ᴍᴇᴅɪᴀ...🤤")

    start_time = datetime.now()

    # Wait for aria2 to produce metadata (robust loop)
    try:
        # if aria2 library returns object with update() method — use it
        while not getattr(download, "is_complete", False):
            await asyncio.sleep(5)
            try:
                download.update()
            except Exception:
                # if update fails, still continue
                pass

            progress = getattr(download, "progress", 0) or 0
            completed_length = getattr(download, "completed_length", 0) or 0
            total_length = getattr(download, "total_length", 0) or 0
            download_speed = getattr(download, "download_speed", 0) or 0
            eta = getattr(download, "eta", None)

            # Build progress bar safely
            try:
                bar_filled = int(min(max(progress, 0), 100) / 10)
            except Exception:
                bar_filled = 0
            bar = "★" * bar_filled + "☆" * (10 - bar_filled)

            elapsed_time = datetime.now() - start_time
            elapsed_minutes, elapsed_seconds = divmod(elapsed_time.seconds, 60)

            status_text = (
                f"┏ ғɪʟᴇɴᴀᴍᴇ: {getattr(download, 'name', '') or ''}\n"
                f"┠ [{bar}] {progress:.2f}%\n"
                f"┠ ᴘʀᴏᴄᴇssᴇᴅ: {format_size(completed_length)} ᴏғ {format_size(total_length)}\n"
                f"┠ sᴛᴀᴛᴜs: 📥 Downloading\n"
                f"┠ ᴇɴɢɪɴᴇ: <b><u>Aria2c</u></b>\n"
                f"┠ sᴘᴇᴇᴅ: {format_size(download_speed)}/s\n"
                f"┠ ᴇᴛᴀ: {eta} | ᴇʟᴀᴘsᴇᴅ: {elapsed_minutes}m {elapsed_seconds}s\n"
                f"┖ ᴜsᴇʀ: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a> | ɪᴅ: {user_id}\n"
            )

            # update status (handle floodwait)
            while True:
                try:
                    await update_status_message(status_message, status_text)
                    break
                except FloodWait as e:
                    logger.error(f"Flood wait detected! Sleeping for {e.value} seconds")
                    await asyncio.sleep(e.value)
                except Exception:
                    # ignore minor edit errors and continue
                    break

            # safety: if aria2 returns no file metadata after a while, break
            # (avoid infinite loop if converter returned no playable media)
            # if total_length == 0 and progress == 0 for long time -> break after some minutes
            if total_length == 0 and (datetime.now() - start_time).seconds > 300:
                break

        # final update before uploading
        try:
            download.update()
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Error while waiting for download: {e}")
        return await status_message.edit_text(f"❌ Error while downloading: {e}")

    # Validate that a file exists
    try:
        files = getattr(download, "files", []) or []
        if not files:
            # try to get download.status or name to show better message
            return await status_message.edit_text("❌ No files were produced by the converter / aria2.")
        file_path = files[0].path
    except Exception as e:
        logger.error(f"Failed to get downloaded file path: {e}")
        return await status_message.edit_text(f"❌ Failed to get downloaded file: {e}")

    # Prepare caption
    caption = (
        f"✨ {getattr(download, 'name', '')}\n"
        f"👤 ʟᴇᴇᴄʜᴇᴅ ʙʏ : <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>\n"
        f"📥 ᴜsᴇʀ ʟɪɴᴋ: tg://user?id={user_id}\n\n"
        "[ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴊᴇᴛ-ᴍɪʀʀᴏʀ ❤️🚀](https://t.me/JetMirror)"
    )

    last_update_time = time.time()
    UPDATE_INTERVAL = 15

    async def update_status(message_obj, text):
        nonlocal last_update_time
        current_time = time.time()
        if current_time - last_update_time >= UPDATE_INTERVAL:
            try:
                await message_obj.edit_text(text)
                last_update_time = current_time
            except FloodWait as e:
                logger.warning(f"FloodWait: Sleeping for {e.value}s")
                await asyncio.sleep(e.value)
                await update_status(message_obj, text)
            except Exception as e:
                logger.error(f"Error updating status: {e}")

    async def upload_progress(current, total):
        try:
            progress = (current / total) * 100 if total else 0
        except Exception:
            progress = 0
        elapsed_time = datetime.now() - start_time
        elapsed_minutes, elapsed_seconds = divmod(elapsed_time.seconds, 60)

        status_text = (
            f"┏ ғɪʟᴇɴᴀᴍᴇ: {getattr(download, 'name', '')}\n"
            f"┠ [{'★' * int(progress / 10) if progress >= 0 else ''}{'☆' * (10 - int(progress / 10)) if progress >= 0 else ''}] {progress:.2f}%\n"
            f"┠ ᴘʀᴏᴄᴇssᴇᴅ: {format_size(current)} ᴏғ {format_size(total)}\n"
            f"┠ sᴛᴀᴛᴜs: 📤 Uploading to Telegram\n"
            f"┠ ᴇɴɢɪɴᴇ: <b><u>PyroFork / Pyrogram</u></b>\n"
            f"┠ sᴘᴇᴇᴅ: {format_size(int(current / elapsed_time.seconds) if elapsed_time.seconds > 0 else 0)}/s\n"
            f"┠ ᴇʟᴀᴘsᴇᴅ: {elapsed_minutes}m {elapsed_seconds}s\n"
            f"┖ ᴜsᴇʀ: <a href='tg://user?id={user_id}'>{message.from_user.first_name}</a> | ɪᴅ: {user_id}\n"
        )
        await update_status(status_message, status_text)

    async def split_video_with_ffmpeg(input_path, output_prefix, split_size):
        try:
            original_ext = os.path.splitext(input_path)[1].lower() or ".mp4"
            start_time_local = datetime.now()
            last_progress_update = time.time()

            # try to get duration using ffprobe. If ffprobe missing, fallback to splitting by size.
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1", input_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await proc.communicate()
                total_duration = float(stdout.decode().strip())
            except Exception:
                total_duration = None

            file_size = os.path.getsize(input_path)
            parts = math.ceil(file_size / split_size)

            if parts == 1 or total_duration is None:
                # No splitting needed or cannot compute duration -> split by size using ffmpeg copy segments by time fallback
                if parts == 1:
                    return [input_path]
                # calculate approximate duration per part using file size ratio (very rough)
                avg_bitrate = (file_size / max(total_duration, 1)) if total_duration else None
                if total_duration and avg_bitrate:
                    duration_per_part = total_duration / parts
                else:
                    # fallback: use ffmpeg segment by size is not trivial; we'll return original file to avoid corruption
                    return [input_path]

            else:
                duration_per_part = total_duration / parts

            split_files = []
            for i in range(parts):
                current_time_local = time.time()
                if current_time_local - last_progress_update >= UPDATE_INTERVAL:
                    elapsed = datetime.now() - start_time_local
                    status_text = (
                        f"✂️ Splitting {os.path.basename(input_path)}\n"
                        f"Part {i+1}/{parts}\n"
                        f"Elapsed: {elapsed.seconds // 60}m {elapsed.seconds % 60}s"
                    )
                    await update_status(status_message, status_text)
                    last_progress_update = current_time_local

                output_path = f"{output_prefix}.{i+1:03d}{original_ext}"
                cmd = [
                    "ffmpeg", "-y", "-ss", str(i * duration_per_part),
                    "-i", input_path, "-t", str(duration_per_part),
                    "-c", "copy", "-map", "0",
                    "-avoid_negative_ts", "make_zero",
                    output_path
                ]

                proc = await asyncio.create_subprocess_exec(*cmd)
                await proc.wait()
                split_files.append(output_path)

            return split_files
        except Exception as e:
            logger.error(f"Split error: {e}")
            raise

    async def handle_upload():
        file_size = os.path.getsize(file_path)

        if file_size > SPLIT_SIZE:
            await update_status(
                status_message,
                f"✂️ Splitting {getattr(download, 'name', '')} ({format_size(file_size)})"
            )

            split_files = await split_video_with_ffmpeg(
                file_path,
                os.path.splitext(file_path)[0],
                SPLIT_SIZE
            )

            try:
                for i, part in enumerate(split_files):
                    part_caption = f"{caption}\n\nPart {i+1}/{len(split_files)}"
                    await update_status(
                        status_message,
                        f"📤 Uploading part {i+1}/{len(split_files)}\n{os.path.basename(part)}"
                    )

                    if USER_SESSION_STRING:
                        sent = await user.send_video(
                            DUMP_CHAT_ID, part,
                            caption=part_caption,
                            progress=upload_progress
                        )
                        await app.copy_message(message.chat.id, DUMP_CHAT_ID, sent.id)
                    else:
                        sent = await client.send_video(
                            DUMP_CHAT_ID, part, caption=part_caption, progress=upload_progress
                        )
                        await client.send_video(message.chat.id, sent.video.file_id, caption=part_caption)
                    try:
                        os.remove(part)
                    except Exception:
                        pass
            finally:
                for part in split_files:
                    try:
                        os.remove(part)
                    except Exception:
                        pass
        else:
            await update_status(
                status_message,
                f"📤 Uploading {getattr(download, 'name', '')}\nSize: {format_size(file_size)}"
            )

            if USER_SESSION_STRING:
                sent = await user.send_video(DUMP_CHAT_ID, file_path, caption=caption, progress=upload_progress)
                await app.copy_message(message.chat.id, DUMP_CHAT_ID, sent.id)
            else:
                sent = await client.send_video(DUMP_CHAT_ID, file_path, caption=caption, progress=upload_progress)
                # send file_id copy to user so they don't have to download from dump chat
                try:
                    await client.send_video(message.chat.id, sent.video.file_id, caption=caption)
                except Exception:
                    # fallback: upload file directly to user chat if send by file_id fails
                    try:
                        await client.send_document(message.chat.id, file_path, caption=caption)
                    except Exception as e:
                        logger.error(f"Failed to forward to user: {e}")

        # cleanup
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    # execute upload
    try:
        await handle_upload()
    except Exception as e:
        logger.error(f"Upload/processing failed: {e}")
        await status_message.edit_text(f"❌ Upload failed: {e}")
        # ensure local file removed if present
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        return

    # final cleanup of messages
    try:
        await status_message.delete()
        await message.delete()
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


# --------------------------
# small webserver to keep instance alive (optional)
# --------------------------
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return render_template("index.html")

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def keep_alive():
    Thread(target=run_flask).start()

# --------------------------
# start clients
# --------------------------
async def start_user_client():
    if user:
        await user.start()
        logger.info("User client started.")

def run_user():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_user_client())

if __name__ == "__main__":
    keep_alive()

    if user:
        logger.info("Starting user client...")
        Thread(target=run_user).start()

    logger.info("Starting bot client...")
    app.run()
