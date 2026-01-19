from pyrogram import filters
from pyrogram.types import Message
from SONALI import app

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import io

print("🔥 QT PLUGIN LOADED (FIXED VERSION) 🔥")


# ================= IMAGE CREATOR ================= #

def create_quote_image(text, author, profile_photo=None):
    width, height = 800, 400
    bg_color = (30, 30, 30)
    text_color = (255, 255, 255)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    text_margin = 160 if profile_photo else 60
    max_text_width = width - text_margin - 80

    # ===== PROFILE PHOTO ===== #
    if profile_photo:
        try:
            size = 110
            x = 40
            y = (height - size) // 2

            pimg = Image.open(profile_photo).convert("RGBA")
            pimg = pimg.resize((size, size), Image.Resampling.LANCZOS)

            mask = Image.new("L", (size, size), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse((0, 0, size, size), fill=255)

            pimg.putalpha(mask)
            img.paste(pimg, (x, y), pimg)

            draw.ellipse(
                (x - 3, y - 3, x + size + 3, y + size + 3),
                outline=(120, 120, 120),
                width=2
            )
        except Exception as e:
            print("Profile error:", e)

    # ===== TEXT WRAP ===== #
    lines = []
    words = text.split()
    current = ""

    for word in words:
        test = current + word + " "
        w, _ = draw.textsize(test, font=font)
        if w <= max_text_width:
            current = test
        else:
            lines.append(current.strip())
            current = word + " "

    if current:
        lines.append(current.strip())

    total_height = len(lines) * 42
    start_y = max(80, (height - total_height) // 2)
    x = text_margin

    for line in lines:
        draw.text((x, start_y), line, fill=text_color, font=font)
        start_y += 42

    # ===== AUTHOR ===== #
    author_text = f"— {author}"
    aw, ah = draw.textsize(author_text, font=small_font)
    draw.text(
        (width - aw - 40, height - ah - 30),
        author_text,
        fill=(200, 200, 200),
        font=small_font
    )

    output = io.BytesIO()
    img.save(output, "PNG")
    output.name = "quote.png"
    output.seek(0)

    return output


# ================= GROUP HANDLER ================= #

@app.on_message(filters.command("qt") & filters.group)
async def qt_handler(_, message: Message):
    try:
        cmd = message.command

        if len(cmd) < 2:
            return await message.reply(
                "❌ Usage:\n"
                "/qt Text\n"
                "/qt @username Text\n"
                "/qt -r (reply mode)"
            )

        text = ""
        author = "User"
        user_id = None
        profile_photo = None

        # ===== REPLY MODE ===== #
        if cmd[1] == "-r":
            reply = message.reply_to_message
            if not reply or not reply.from_user:
                return await message.reply("❌ Kisi user ke message par reply karo")

            user = reply.from_user
            author = user.first_name or "User"
            user_id = user.id
            text = reply.text or reply.caption or "💬"

        # ===== USERNAME MODE ===== #
        elif cmd[1].startswith("@"):
            username = cmd[1][1:]
            try:
                user = await app.get_users(username)
                author = user.first_name or username
                user_id = user.id
                text = " ".join(cmd[2:]) or "💬"
            except:
                return await message.reply(f"❌ @{username} nahi mila")

        # ===== NORMAL MODE ===== #
        else:
            user = message.from_user
            author = user.first_name or "User"
            user_id = user.id
            text = " ".join(cmd[1:])

        # ===== PROFILE PHOTO ===== #
        try:
            photos = await app.get_chat_photos(user_id, limit=1)
            if photos:
                bio = await app.download_media(photos[0].file_id, in_memory=True)
                profile_photo = BytesIO(bio.getvalue())
        except:
            pass

        img = create_quote_image(text[:200], author, profile_photo)
        await message.reply_photo(img, caption="✨ Quotely ✨")

    except Exception as e:
        print("QT ERROR:", e)
        await message.reply("❌ Error aa gaya, dobara try karo")


# ================= PM BLOCK ================= #

@app.on_message(filters.command("qt") & filters.private)
async def qt_pm(_, message: Message):
    await message.reply("❌ Ye command sirf groups me kaam karti hai")
