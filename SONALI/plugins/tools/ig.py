import re
import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from SONALI import app


# ✅ Download Function
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

        await processing.delete()
        return await message.reply_video(
            data["url"],
            caption="✅ Reel Downloaded Successfully"
        )

    return await processing.edit("❌ Failed To Download")


# ✅ GROUP AUTO LINK FIX (Entity Based)
@app.on_message(filters.group & filters.text)
async def insta_group_handler(client, message: Message):

    if not message.text:
        return

    # Telegram Entities से link निकालना (सबसे best तरीका)
    if message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:

                if entity.type == "url":
                    url = message.text[
                        entity.offset : entity.offset + entity.length
                    ]

                elif entity.type == "text_link":
                    url = entity.url

                # सिर्फ Instagram reel पर चले
                if "instagram.com" in url and "/reel/" in url:
                    return await send_instagram_media(message, url)

    # अगर entities ना मिले तो fallback regex
    match = re.search(r"https?://[^\s]+", message.text)
    if match:
        url = match.group(0)

        if "instagram.com" in url and "/reel/" in url:
            return await send_instagram_media(message, url)
