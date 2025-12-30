import logging
import asyncio
import aiohttp
import io
import time
from PIL import Image
from pyrogram import filters
from pyrogram.types import Message
from SONALI import app   # ✅ IMPORTANT

logger = logging.getLogger(__name__)
NSFW_API_URL = "https://nexacoders-nexa-api.hf.space/scan"

# =========================
# SIMPLE STORAGE
# =========================
NSFW_CHATS = set()
SCAN_CACHE = {}

async def set_nsfw_status(chat_id, status):
    if status:
        NSFW_CHATS.add(chat_id)
    else:
        NSFW_CHATS.discard(chat_id)

async def get_nsfw_status(chat_id):
    return chat_id in NSFW_CHATS

async def get_cached_scan(file_id):
    return SCAN_CACHE.get(file_id)

async def cache_scan_result(file_id, safe, data):
    SCAN_CACHE[file_id] = {"safe": safe, "data": data}

# =========================
# SESSION
# =========================
ai_session = None

async def get_session():
    global ai_session
    if ai_session is None or ai_session.closed:
        ai_session = aiohttp.ClientSession()
    return ai_session

# =========================
# IMAGE OPTIMIZATION
# =========================
def optimize_image(image_bytes: bytes) -> bytes:
    if len(image_bytes) < 50 * 1024:
        return image_bytes
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        img.thumbnail((256, 256))
        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=80)
        return out_io.getvalue()
    except Exception:
        return image_bytes

# =========================
# UI FORMAT
# =========================
def format_scores_ui(scores: dict) -> str:
    icons = {"porn": "🔞", "hentai": "👾", "sexy": "💋", "neutral": "😐", "drawings": "🎨"}
    sorted_scores = sorted(scores.items(), key=lambda i: i[1], reverse=True)
    return "\n".join(
        f"{icons.get(k,'🔸')} `{k.title().ljust(10)} : {v*100:05.2f}%`"
        for k, v in sorted_scores
    )

# =========================
# NSFW TOGGLE
# =========================
@app.on_message(filters.command("nsfw") & filters.group)
async def nsfw_toggle_command(client, message: Message):
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ("administrator", "creator"):
        return await message.reply_text("❌ Only admins can use this command.")

    if len(message.command) < 2:
        status = await get_nsfw_status(message.chat.id)
        return await message.reply_text(
            f"🚀 **NSFW System:** `{'Enabled' if status else 'Disabled'}`\n"
            "Usage: `/nsfw on` or `/nsfw off`"
        )

    if message.command[1].lower() in ("on", "enable", "true"):
        await set_nsfw_status(message.chat.id, True)
        await message.reply_text("🚀 **NSFW Active.**")
    else:
        await set_nsfw_status(message.chat.id, False)
        await message.reply_text("💤 **NSFW Paused.**")

# =========================
# MANUAL SCAN
# =========================
@app.on_message(filters.command("scan") & filters.group)
async def manual_scan_command(client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to an image.")

    status_msg = await message.reply_text("⚡ **Scanning...**")
    start = time.time()
    is_nsfw, data, reason = await process_media_scan(client, message.reply_to_message, True)
    taken = time.time() - start

    if not data:
        return await status_msg.edit_text("❌ Scan failed.")

    header = "🚨 **UNSAFE**" if is_nsfw else "✅ **SAFE**"
    await status_msg.edit_text(
        f"{header}\n"
        f"⏱️ `{taken:.2f}s`\n"
        f"🔎 `{reason}`\n\n"
        f"{format_scores_ui(data.get('scores', {}))}"
    )

# =========================
# AUTO WATCHER
# =========================
@app.on_message(filters.group & (filters.photo | filters.sticker | filters.document), group=5)
async def nsfw_watcher(client, message: Message):
    if not await get_nsfw_status(message.chat.id):
        return

    is_nsfw, data, reason = await process_media_scan(client, message, False)
    if is_nsfw and data:
        await handle_nsfw_detection(client, message, data, reason)

# =========================
# CORE LOGIC
# =========================
def check_strict_nsfw(scores: dict):
    porn = scores.get("porn", 0)
    hentai = scores.get("hentai", 0)
    sexy = scores.get("sexy", 0)
    if porn > 0.08: return True, "Porn detected"
    if hentai > 0.15: return True, "Hentai detected"
    if sexy > 0.45: return True, "Explicit content"
    return False, "Safe"

async def process_media_scan(client, message, manual_override=False):
    media = message.photo or message.document or message.sticker
    if not media:
        return False, None, "No media"

    file_id = media.file_unique_id
    if not manual_override and file_id in SCAN_CACHE:
        cached = SCAN_CACHE[file_id]
        return check_strict_nsfw(cached["data"]["scores"])[0], cached["data"], "Cached"

    stream = await client.download_media(message, in_memory=True)
    image_bytes = optimize_image(bytes(stream.getbuffer()))

    session = await get_session()
    form = aiohttp.FormData()
    form.add_field("file", image_bytes, filename="scan.jpg")

    async with session.post(NSFW_API_URL, data=form, timeout=6) as r:
        data = await r.json()

    is_nsfw, reason = check_strict_nsfw(data.get("scores", {}))
    await cache_scan_result(file_id, not is_nsfw, data)
    return is_nsfw, data, reason

async def handle_nsfw_detection(client, message, data, reason):
    try:
        await message.delete()
        msg = await client.send_message(
            message.chat.id,
            f"🔞 **NSFW Removed**\n👤 {message.from_user.mention}\n🚨 {reason}"
        )
        await asyncio.sleep(15)
        await msg.delete()
    except:
        pass
