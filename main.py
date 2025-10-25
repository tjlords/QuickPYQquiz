from telegram_bot import QABot
from config import TELEGRAM_BOT_TOKEN

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set")
        return
    
    try:
        bot = QABot()
        print("Starting Telegram Bot with pyTelegramBotAPI...")
        bot.run()
    except Exception as e:
        print(f"Failed to start: {e}")

if __name__ == "__main__":
    main()