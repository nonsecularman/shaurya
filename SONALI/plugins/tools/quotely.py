from pyrogram import filters
from pyrogram.types import Message
from SONALI import app
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
from io import BytesIO

print("🔥 LOCAL QT PLUGIN LOADED (100% WORKING) 🔥")


def create_quote_image(text, author, profile_photo=None):
    width, height = 800, 400
    bg_color = (30, 30, 30)
    text_color = (255, 255, 255)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    text_margin = 160 if profile_photo else 60
    max_text_width = width - text_margin - 80

    # Add profile photo if available
    if profile_photo:
        profile_size = 110
        profile_x = 40
        profile_y = (height - profile_size) // 2
        
        try:
            profile_img = Image.open(profile_photo).convert("RGBA")
            profile_img = profile_img.resize((profile_size, profile_size), Image.Resampling.LANCZOS)
            
            # Create perfect circular mask
            mask = Image.new('L', (profile_size, profile_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, profile_size, profile_size), fill=255)
            
            profile_img.putalpha(mask)
            img.paste(profile_img, (profile_x, profile_y), profile_img)
            
        except Exception as e:
            print(f"Profile photo error: {e}")

    # Wrap text properly
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + word + " "
        if draw.textsize(test_line, font=font)[0] < max_text_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    
    if not lines:
        lines = [text[:100]]

    # Calculate text position
    total_text_height = len(lines) * 40
    text_y = max(80, (height - total_text_height) // 2)
    text_x = text_margin

    # Draw text lines
    y_offset = text_y
    for line in lines:
        w, h = draw.textsize(line, font=font)
        draw.text((text_x, y_offset), line, fill=text_color, font=font)
        y_offset += 42

    # Draw author name
    author_text = f"— {author}"
    author_w, author_h = draw.textsize(author_text, font=small_font)
    draw.text((width - 60, height - 50), author_text, fill=(220, 220, 220), font=small_font)

    # Add subtle border around profile photo
    if profile_photo:
        draw.ellipse([profile_x-3, profile_y-3, profile_x+profile_size+3, profile_y+profile_size+3], 
                    outline=(100, 100, 100), width=2)

    file = io.BytesIO()
    img.save(file, "PNG")
    file.name = "quote.png"
    file.seek(0)
    return file


@app.on_message(filters.command("qt") & filters.group)
async def qt_handler(_, message: Message):
    try:
        cmd = message.command
        
        if len(cmd) < 2:
            return await message.reply(
                "❌ Usage:\n"
                "/qt Text here\n"
                "/qt @username Text here\n"
                "/qt -r (reply mode)"
            )

        text = " ".join(cmd[1:])
        author = None
        profile_photo = None
        user_id = None

        # Reply mode (-r)
        if cmd[1] == "-r":
            reply = message.reply_to_message
            if not reply or not reply.from_user:
                return await message.reply("❌ Reply to a user message!")
            
            user = reply.from_user
            author = user.first_name or user.first_name or "User"
            user_id = user.id
            text = reply.text or reply.caption or "💬"

𝐼ꪜ𝛢𝚴, [19-01-2026 20:43]
# Mention username mode (@username)
        elif cmd[1].startswith("@"):
            username = cmd[1][1:]
            try:
                user = await app.get_users(username)
                author = user.first_name or username
                user_id = user.id
                text = " ".join(cmd[2:]) if len(cmd) > 2 else "💬"
            except:
                return await message.reply(f"❌ User @{username} not found!")

        # Default mode (sender)
        else:
            user = message.from_user
            author = user.first_name or "User"
            user_id = user.id

        # Get profile photo
        if user_id:
            try:
                photos = await app.get_chat_photos(user_id, limit=1)
                if photos:
                    photo = await app.download_media(photos[0].file_id)
                    profile_photo = BytesIO(photo.getvalue())
                    photo.close()
            except Exception:
                pass

        if not author:
            author = "User"

        img = create_quote_image(text[:200], author, profile_photo)  # Limit text length
        await message.reply_photo(img, caption="✨ Quotely ✨")
        
    except Exception as e:
        print(f"QT Error: {e}")
        await message.reply("❌ Something went wrong! Try again.")


@app.on_message(filters.command("qt") & ~filters.group)
async def qt_pm_handler(_, message: Message):
    await message.reply("❌ Use this command in groups only!")
