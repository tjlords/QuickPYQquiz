import os
import tempfile
import telebot
from pdf_parser import PDFParser
from qa_processor import QAProcessor
from config import TELEGRAM_BOT_TOKEN, MAX_QUESTIONS_PER_REQUEST

class QABot:
    def __init__(self):
        self.bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        self.parser = PDFParser()
        self.processor = QAProcessor()
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = """
🤖 Welcome to the Q&A Explanation Bot!

Send me a PDF or text file with multiple-choice questions.

Format should be:
1. Question text?
a) Option A
b) Option B  
c) Option C
d) Option D
Ex: Explanation

I'll extract questions and generate AI explanations!
            """
            self.bot.reply_to(message, welcome_text)

        @self.bot.message_handler(commands=['about'])
        def send_about(message):
            about_text = "🎓 Q&A Bot - Extracts questions from files and provides explanations"
            self.bot.reply_to(message, about_text)

        @self.bot.message_handler(content_types=['document'])
        def handle_document(message):
            try:
                # Check file type
                file_info = self.bot.get_file(message.document.file_id)
                file_extension = os.path.splitext(message.document.file_name)[1].lower()
                
                if file_extension not in ['.pdf', '.txt']:
                    self.bot.reply_to(message, "❌ Please send a PDF or TXT file.")
                    return
                
                # Download file
                downloaded_file = self.bot.download_file(file_info.file_path)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    tmp_file.write(downloaded_file)
                    file_path = tmp_file.name
                
                # Process file
                processing_msg = self.bot.reply_to(message, "📥 Processing file...")
                
                questions = self.parser.parse_file(file_path)
                
                if not questions:
                    self.bot.edit_message_text(
                        "❌ No questions found. Please check the file format.",
                        chat_id=message.chat.id,
                        message_id=processing_msg.message_id
                    )
                    os.unlink(file_path)
                    return
                
                self.bot.edit_message_text(
                    f"📚 Found {len(questions)} questions. Generating explanations...",
                    chat_id=message.chat.id,
                    message_id=processing_msg.message_id
                )
                
                processed_questions = self.processor.process_questions(
                    questions, 
                    max_questions=min(MAX_QUESTIONS_PER_REQUEST, len(questions))
                )
                
                self.send_results(message, processed_questions)
                
                os.unlink(file_path)
                self.bot.delete_message(message.chat.id, processing_msg.message_id)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                self.bot.reply_to(message, error_msg)
                print(f"Error: {e}")
    
    def send_results(self, message, questions):
        for i, question in enumerate(questions, 1):
            response = self.format_question_response(question, i)
            
            # Split long messages
            if len(response) > 4000:
                parts = self.split_message(response)
                for part in parts:
                    self.bot.send_message(message.chat.id, part)
            else:
                self.bot.send_message(message.chat.id, response)
        
        summary = f"✅ Processed {len(questions)} questions!"
        self.bot.send_message(message.chat.id, summary)
    
    def format_question_response(self, question, index):
        response = f"""
Question {index}

Q: {question['question']}

Options:
A) {question['options']['A']}
B) {question['options']['B']}
C) {question['options']['C']}
D) {question['options']['D']}

Correct Answer: {question['correct_answer']}

Explanation:
{question.get('ai_explanation', 'No explanation generated.')}
        """
        
        if question.get('original_explanation'):
            response += f"\n\nOriginal Explanation:\n{question['original_explanation']}"
        
        return response
    
    def split_message(self, text, max_length=4000):
        parts = []
        while len(text) > max_length:
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            parts.append(text[:split_pos])
            text = text[split_pos:].lstrip()
        parts.append(text)
        return parts
    
    def run(self):
        print("Bot is running...")
        self.bot.infinity_polling()

# Webhook version for production (optional)
class QABotWebhook:
    def __init__(self):
        self.bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        self.parser = PDFParser()
        self.processor = QAProcessor()
        self.setup_handlers()
    
    def setup_handlers(self):
        # Same handlers as above
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            welcome_text = "🤖 Q&A Bot - Send me PDF/TXT files with questions!"
            self.bot.reply_to(message, welcome_text)

        @self.bot.message_handler(content_types=['document'])
        def handle_document(message):
            try:
                file_info = self.bot.get_file(message.document.file_id)
                file_extension = os.path.splitext(message.document.file_name)[1].lower()
                
                if file_extension not in ['.pdf', '.txt']:
                    self.bot.reply_to(message, "❌ Please send PDF or TXT file.")
                    return
                
                downloaded_file = self.bot.download_file(file_info.file_path)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                    tmp_file.write(downloaded_file)
                    file_path = tmp_file.name
                
                self.bot.reply_to(message, "📥 Processing file...")
                
                questions = self.parser.parse_file(file_path)
                
                if not questions:
                    self.bot.reply_to(message, "❌ No questions found.")
                    os.unlink(file_path)
                    return
                
                processed_questions = self.processor.process_questions(
                    questions, 
                    max_questions=min(MAX_QUESTIONS_PER_REQUEST, len(questions))
                )
                
                for i, question in enumerate(processed_questions, 1):
                    response = f"Q{i}: {question['question']}\nAns: {question['correct_answer']}"
                    self.bot.send_message(message.chat.id, response)
                
                os.unlink(file_path)
                
            except Exception as e:
                self.bot.reply_to(message, f"❌ Error: {str(e)}")