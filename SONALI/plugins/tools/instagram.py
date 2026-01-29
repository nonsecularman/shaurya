import re
import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from SONALI import app


# ✅ Download Function
async def send_instagram_media(message: Message, url: str):

    processing = await message.reply_text("⏳ Downloading Instagram Reel...")

    api_url = f"https://insta-dl.hazex.workers.dev/?url={url}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                result = await resp.json()

        data = result.get("result", {})

    except Exception as e:
        return await processing.edit(f"❌ Error:\n{e}")

    if not result.get("error", True) and data.get("url"):

        await processing.delete()
        return await message.reply_video(
            data["url"],
            caption="✅ Reel Downloaded Successfully"
        )

    return await processing.edit("❌ Failed To Download Reel")


# ✅ Extract URL from Any Telegram Message
def extract_url(message: Message):

    # 1. Normal Text
    if message.text:
        urls = re.findall(r"https?://[^\s]+", message.text)
        if urls:
            return urls[0]

    # 2. Caption (Media Messages)
    if message.caption:
        urls = re.findall(r"https?://[^\s]+", message.caption)
        if urls:
            return urls[0]

    # 3. Web Page Preview (Instagram Card)
    if message.web_page:
        if message.web_page.url:
            return message.web_page.url

    return None


# ✅ AUTO Handler (Group + DM)
@app.on_message(filters.group | filters.private)
async def insta_handler(client, message: Message):

    url = extract_url(message)

    if not url:
        return

    if "instagram.com" not in url:
        return

    if "/reel/" not in url:
        return

    await send_instagram_media(message, url)
