import requests
from pyrogram import filters
from pyrogram.types import Message
from YourBot import app   # apna main app

API_URL = "https://bot.lyo.su/quote/generate"


def generate_quote(text, user):
    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": "#1c1c1c",
        "width": 512,
        "height": 512,
        "scale": 2,
        "messages": [
            {
                "entities": [],
                "avatar": True,
                "from": {
                    "id": user.id,
                    "name": user.first_name,
                    "username": user.username
                },
                "text": text
            }
        ]
    }
    return requests.post(API_URL, json=payload).content


@app.on_message(filters.command("qt"))
async def qt_handler(_, message: Message):

    reply = message.reply_to_message
    cmd = message.command

    # 🔥 /qt -r (reply auto text)
    if len(cmd) == 2 and cmd[1] == "-r":
        if not reply or not (reply.text or reply.caption):
            return await message.reply("❌ Reply to a text message")

        quote_text = reply.text or reply.caption
        quote_user = reply.from_user

    # 🔥 /qt hello
    elif len(cmd) > 1:
        quote_text = message.text.split(None, 1)[1]

        # reply hai → samne wala
        if reply and reply.from_user:
            quote_user = reply.from_user
        else:
            quote_user = message.from_user

    else:
        return await message.reply(
            "❌ Usage:\n"
            "`/qt text`\n"
            "`/qt -r` (reply required)`"
        )

    img = generate_quote(quote_text, quote_user)

    await message.reply_photo(
        photo=img,
        caption="✨ Quotely"
    )
