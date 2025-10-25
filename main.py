from telegram_bot import QABot
from config import TELEGRAM_BOT_TOKEN

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is required")
        return
    
    bot = QABot()
    bot.run()

if __name__ == "__main__":
    main()