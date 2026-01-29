import re
import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from SONALI import app


# ✅ Download + Send Reel Function
async def send_instagram_media(message: Message, url: str):

    processing = await message.reply_text("⏳ Reel Downloading...")

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

        caption = "✅ Reel Downloaded Successfully"

        await processing.delete()
        return await message.reply_video(video_url, caption=caption)

    else:
        return await processing.edit("❌ Failed To Download Reel")


# ✅ AUTO LINK DETECTOR (Only Link डालने पर भी चलेगा)
@app.on_message(filters.text & filters.group)
async def insta_auto_link_handler(client, message: Message):

    if not message.text:
        return

    # अगर message में instagram link है
    match = re.search(
        r"(https?://(?:www\.)?(instagram\.com|instagr\.am)/\S+)",
        message.text
    )

    if match:
        url = match.group(1)
        await send_instagram_media(message, url)
