import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Other APIs (fallback options)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

# Bot Settings
MAX_QUESTIONS_PER_REQUEST = 5  # Reduced for better performance
SUPPORTED_FILE_TYPES = ['.pdf', '.txt']