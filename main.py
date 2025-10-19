import os
import asyncio
from pyrogram import Client, filters, idle
from db import Database

# ----------------------
# Config from environment
# ----------------------
def get_env_int(key, default=0):
    val = os.environ.get(key)
    if val is None:
        print(f"⚠️ Environment variable {key} not set, using default {default}")
        return default
    return int(val)

API_ID = get_env_int("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = get_env_int("OWNER_ID")
DATABASE_URL = os.environ.get("DATABASE_URL")

PORT = int(os.environ.get("PORT", 10000))
HOST = "0.0.0.0"

# ----------------------
# Environment debug
# ----------------------
print("🔹 Environment Variables:")
print(f"API_ID = {API_ID}")
print(f"API_HASH = {'SET' if API_HASH else 'NOT SET'}")
print(f"BOT_TOKEN = {'SET' if BOT_TOKEN else 'NOT SET'}")
print(f"OWNER_ID = {OWNER_ID}")
print(f"DATABASE_URL = {'SET' if DATABASE_URL else 'NOT SET'}")
print(f"PORT = {PORT}")

if not BOT_TOKEN or not API_HASH or API_ID == 0 or OWNER_ID == 0 or not DATABASE_URL:
    raise ValueError("❌ One or more required environment variables are missing or invalid!")

# ----------------------
# Database
# ----------------------
db = Database(DATABASE_URL)

# ----------------------
# Bot setup
# ----------------------
bot = Client(
    "quizbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ----------------------
# Command Handlers
# ----------------------
@bot.on_message(filters.private & filters.command("start"))
async def start(_, msg):
    await msg.reply("✅ Bot is alive! This is a test response.")
    print(f"📩 Received /start from chat_id={msg.chat.id}")

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
# Healthcheck Server
# ----------------------
async def healthcheck(reader, writer):
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n✅ Quiz Bot is running!"
    )
    writer.write(response.encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def start_healthcheck_server():
    server = await asyncio.start_server(healthcheck, HOST, PORT)
    print(f"🌐 Healthcheck server running on {HOST}:{PORT}")
    async with server:
        await server.serve_forever()

# ----------------------
# Main
# ----------------------
async def main():
    await db.connect()
    print("✅ Database connected")

    await bot.start()
    print("🤖 Bot started and ready")

    # Start healthcheck server in background
    asyncio.create_task(start_healthcheck_server())

    # Keep bot running
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
