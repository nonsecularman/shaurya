@app.on_message(filters.group)
async def test(client, message):
    await message.reply_text("I am working in group ✅")
