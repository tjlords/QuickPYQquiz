import os

# Loaded from Render environment
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")  # Render PostgreSQL external URL

OWNER_ID = int(os.getenv("OWNER_ID"))  # your Telegram user ID
