import re
import aiohttp
from pyrogram import filters
from pyrogram.types import Message
from SONALI import app


# ✅ Download Reel Function
async def send_instagram_media(message: Message, url: str):

    processing = await message.reply_text("⏳ Downloading Reel...")

    api_url = f"https://insta-dl.hazex.workers.dev/?url={url}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                result = await resp.json()

        data = result.get("result", {})

    except Exception as e:
        return await processing.edit(f"❌ Error:\n{e}")

    if not result.get("error", True) and data.get("url"):

        video_url = data["url"]

        await processing.delete()
        return await message.reply_video(
            video_url,
            caption="✅ Reel Downloaded Successfully"
        )

    return await processing.edit("❌ Failed to Download Reel")


# ✅ AUTO LINK DETECTOR (REAL WORKING)
@app.on_message(filters.group & filters.text)
async def insta_auto_handler(client, message: Message):

    text = message.text or ""

    # अगर instagram word ही नहीं है तो skip
    if "instagram.com" not in text:
        return

    # message से URL निकालो
    urls = re.findall(r"https?://[^\s]+", text)

    if not urls:
        return

    url = urls[0]

    # सिर्फ reel links allow
    if "/reel/" not in url:
        return

    await send_instagram_media(message, url)
