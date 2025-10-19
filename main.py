import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Update
from pyrogram.methods import SetWebhook
from db import Database

# ----------------------
# Config from environment
# ----------------------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
DATABASE_URL = os.environ.get("DATABASE_URL")

WEBHOOK_PATH = "/" + BOT_TOKEN  # unique path for Telegram
PORT = int(os.environ.get("PORT", 10000))  # Render port
HOST = "0.0.0.0"

db = Database(DATABASE_URL)

# ----------------------
# Bot setup
# ----------------------
bot = Client(
    "quizbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="./"  # optional
)

# ----------------------
# Command Handlers
# ----------------------
@bot.on_message(filters.private & filters.command("start"))
async def start(_, msg):
    await msg.reply(
        "👋 Hello! I am your Quiz Bot.\n"
        "Commands:\n"
        "/add - Add question (Owner only)\n"
        "/groupsave - Save group (Owner only)\n"
        "/startquiz FolderName - Start a quiz"
    )

@bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command("add"))
async def add_question(_, msg):
    await msg.reply("Send me the folder name (e.g., Gujarati Grammar):")
    folder_msg = await bot.listen(msg.chat.id)
    folder = folder_msg.text.strip()

    await msg.reply(
        "Now send the question and options in this format:\n\n"
        "'Question text'\nOption1 ✅\nOption2\nOption3\nOption4\nExplain: Reason text"
    )

    q_msg = await bot.listen(msg.chat.id)
    text = q_msg.text.strip().splitlines()
    question = text[0].strip("'\" ")
    options = []
    correct = None
    explanation = None

    for line in text[1:]:
        if line.startswith("Explain:"):
            explanation = line.replace("Explain:", "").strip()
        elif "✅" in line:
            correct = line.replace("✅", "").strip()
            options.append(correct)
        else:
            options.append(line.strip())

    await db.add_question(folder, question, options, correct, explanation)
    await msg.reply(f"✅ Question added under folder: {folder}")

@bot.on_message(filters.private & filters.user(OWNER_ID) & filters.command("groupsave"))
async def save_group(_, msg):
    await msg.reply("Send me the group ID or forward a message from the group.")
    g_msg = await bot.listen(msg.chat.id)
    if g_msg.forward_from_chat:
        group_id = g_msg.forward_from_chat.id
        title = g_msg.forward_from_chat.title
    else:
        group_id = int(g_msg.text)
        title = "Custom Group"

    await db.add_group(group_id, title)
    await msg.reply(f"✅ Group '{title}' saved.")

@bot.on_message(filters.private & filters.command("startquiz"))
async def start_quiz(_, msg):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.reply("Usage: /startquiz FolderName")
        return

    folder = args[1].strip()
    q = await db.get_random_question(folder)
    if not q:
        await msg.reply("❌ No questions found in this folder.")
        return

    options = q["options"]
    await bot.send_poll(
        chat_id=msg.chat.id,
        question=q["question"],
        options=options,
        type="quiz",
        correct_option_id=options.index(q["correct"]),
        explanation=q["explanation"] or "No explanation provided.",
        is_anonymous=True
    )
    await msg.reply(f"✅ Quiz started from folder: {folder}")

# ----------------------
# Health Check HTTP Server
# ----------------------
async def healthcheck(reader, writer):
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n✅ Quiz Bot is running!"
    writer.write(response.encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

# ----------------------
# Main
# ----------------------
async def main():
    await db.connect()
    print("✅ Database connected.")

    await bot.start()
    print("🤖 Bot started")

    # Set webhook with public URL
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_URL')}{WEBHOOK_PATH}"
    await bot.set_webhook(WEBHOOK_URL)
    print(f"🌐 Webhook set to: {WEBHOOK_URL}")

    # Start simple async web server for Render port
    server = await asyncio.start_server(healthcheck, HOST, PORT)
    print(f"🌐 Web server listening on port {PORT}")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
    
