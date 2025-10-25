#!/usr/bin/env python3
import logging
from telegram_bot import QABot
from config import TELEGRAM_BOT_TOKEN

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is required")
        return
    
    try:
        bot = QABot()
        print("Starting Telegram Q&A Bot...")
        bot.run()
    except Exception as e:
        print(f"Failed to start bot: {e}")
        logging.error(f"Bot startup error: {e}")

if __name__ == "__main__":
    main()