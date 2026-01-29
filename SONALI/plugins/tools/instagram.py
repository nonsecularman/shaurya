import re
import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from SONALI import app
from config import LOGGER_ID


# ==============================
# ✅ Instagram Download Function
# ==============================
async def send_instagram_media(message: Message, url: str):

    processing = await message.reply_text("⏳ Downloading Instagram Media...")

    api_url = f"https://insta-dl.hazex.workers.dev/?url={url}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                result = await resp.json()

        data = result.get("result", {})

    except Exception as e:
        await processing.edit(f"❌ API Error:\n{e}")
        return await app.send_message(LOGGER_ID, f"Instagram Error:\n{e}")

    # ✅ Success Case
    if not result.get("error", True) and data.get("url"):

        video_url = data["url"]

        caption = (
            "✅ Instagram Media Downloaded\n\n"
            "📌 Powered By : @kryshmusicbot"
        )

        await processing.delete()
        return await message.reply_video(video_url, caption=caption)

    # ❌ Fail Case
    return await processing.edit("❌ Failed to Download Instagram Media")


# =====================================
# ✅ Extract Instagram URL from Message
# =====================================
def extract_instagram_url(message: Message):

    text = message.text or ""

    # 1️⃣ Entity Based Extraction (Best for Groups)
    if message.entities:
        for entity in message.entities:

            if entity.type == "url":
                url = text[entity.offset : entity.offset + entity.length]
                if "instagram.com" in url:
                    return url

            elif entity.type == "text_link":
                url = entity.url
                if "instagram.com" in url:
                    return url

    # 2️⃣ Regex Fallback
    match = re.search(r"https?://[^\s]+", text)
    if match and "instagram.com" in match.group(0):
        return match.group(0)

    return None


# ==============================
# ✅ Auto Handler (DM + Group)
# ==============================
@app.on_message(filters.text)
async def insta_auto_handler(client, message: Message):

    url = extract_instagram_url(message)

    if not url:
        return

    # सिर्फ Instagram पर चले
    if "instagram.com" not in url:
        return

    await send_instagram_media(message, url)


# ==============================
# ✅ Command Handler (/ig link)
# ==============================
@app.on_message(filters.command(["ig", "instagram", "reel"]))
async def insta_command_handler(client, message: Message):

    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ Use Like This:\n\n"
            "/ig https://www.instagram.com/reel/xxxx/"
        )

    url = message.text.split(maxsplit=1)[1]

    if "instagram.com" not in url:
        return await message.reply_text("❌ Invalid Instagram URL")

    await send_instagram_media(message, url)


# ==============================
# Plugin Info
# ==============================
MODULE = "Instagram"

HELP = """
✅ Instagram Downloader Plugin

• Just send any Instagram Reel/Post link in Group or DM
• Bot will auto download it

Commands:
• /ig <link>
• /instagram <link>
• /reel <link>
"""
