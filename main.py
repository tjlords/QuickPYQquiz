from flask import Flask, request
import telebot
import os
from config import TELEGRAM_BOT_TOKEN

# Initialize Flask app
app = Flask(__name__)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@app.route('/')
def index():
    return "🤖 Q&A Bot is running! Send PDF files to your Telegram bot."

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return ''

# Import and setup bot handlers
from telegram_bot import setup_bot_handlers
setup_bot_handlers(bot)

if __name__ == '__main__':
    # For production with webhook
    if os.environ.get('RENDER'):
        bot.remove_webhook()
        # You'll need to set your actual Render URL here
        bot.set_webhook(url=f"https://quickpyqquiz-0bxc.onrender.com")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)