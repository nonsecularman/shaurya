from pyrogram import filters
from pyrogram.types import Message

from SONALI import app
from config import OWNER_ID

GMUTED_USERS = set()


# ✅ GMUTE Command
@app.on_message(filters.command("gmute") & filters.group)
async def gmute_user(_, message: Message):

    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only Owner can gmute!")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to user then /gmute")

    user_id = message.reply_to_message.from_user.id
    GMUTED_USERS.add(user_id)

    await message.reply_text(f"✅ GMUTED!\nUser: `{user_id}`")


# ✅ UNGMUTE Command
@app.on_message(filters.command("ungmute") & filters.group)
async def ungmute_user(_, message: Message):

    if message.from_user.id != OWNER_ID:
        return await message.reply_text("❌ Only Owner can ungmute!")

    if not message.reply_to_message:
        return await message.reply_text("⚠️ Reply to user then /ungmute")

    user_id = message.reply_to_message.from_user.id
    GMUTED_USERS.discard(user_id)

    await message.reply_text("✅ UNGMUTED!")


# ✅ Delete Muted User Messages (SAFE MODE)
# group=999 → सबसे last में चलेगा
@app.on_message(filters.group, group=999)
async def delete_gmuted(_, message: Message):

    if not message.from_user:
        return

    # अगर user muted है
    if message.from_user.id in GMUTED_USERS:

        # ✅ Commands को touch मत करो (/ping /stats safe)
        if message.text and message.text.startswith("/"):
            return

        try:
            await message.delete()
        except:
            pass
