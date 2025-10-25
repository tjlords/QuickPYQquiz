import os
import tempfile
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pdf_parser import PDFParser
from qa_processor import QAProcessor
from config import TELEGRAM_BOT_TOKEN, MAX_QUESTIONS_PER_REQUEST

class QABot:
    def __init__(self):
        self.parser = PDFParser()
        self.processor = QAProcessor()
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = """
🤖 Welcome to the Q&A Explanation Bot!

Send me a PDF or text file with multiple-choice questions.

Use /help for more information.
        """
        await update.message.reply_text(welcome_text)
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
📚 How to use:

1. Send a PDF/TXT file with questions like:
   1. Question text?
   a) Option A
   b) Option B  
   c) Option C
   d) Option D
   Ex: Explanation

2. I'll extract questions and generate explanations

Commands:
/start - Welcome
/help - This help
/about - About bot
        """
        await update.message.reply_text(help_text)
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        about_text = """
🎓 Q&A Explanation Bot

Extracts questions from files and provides explanations.
        """
        await update.message.reply_text(about_text)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            processing_msg = await update.message.reply_text("📥 Processing file...")
            
            document = update.message.document
            file = await context.bot.get_file(document.file_id)
            
            file_extension = os.path.splitext(document.file_name)[1].lower()
            
            if file_extension not in ['.pdf', '.txt']:
                await processing_msg.edit_text("❌ Please send PDF or TXT file.")
                return
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                file_path = tmp_file.name
            
            await file.download_to_drive(file_path)
            
            await processing_msg.edit_text("🔍 Extracting questions...")
            questions = self.parser.parse_file(file_path)
            
            if not questions:
                await processing_msg.edit_text("❌ No questions found. Check format.")
                os.unlink(file_path)
                return
            
            await processing_msg.edit_text(f"📚 Found {len(questions)} questions. Generating explanations...")
            
            processed_questions = self.processor.process_questions(
                questions, 
                max_questions=min(MAX_QUESTIONS_PER_REQUEST, len(questions))
            )
            
            await self.send_results(update, context, processed_questions)
            
            os.unlink(file_path)
            await processing_msg.delete()
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            await update.message.reply_text(error_msg)
            print(f"Error: {e}")
    
    async def send_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, questions):
        for i, question in enumerate(questions, 1):
            response = self.format_question_response(question, i)
            
            if len(response) > 4000:
                parts = self.split_message(response)
                for part in parts:
                    await update.message.reply_text(part)
            else:
                await update.message.reply_text(response)
            
            await asyncio.sleep(1)
        
        summary = f"✅ Processed {len(questions)} questions!"
        await update.message.reply_text(summary)
    
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
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("about", self.about))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        print("Bot starting...")
        self.application.run_polling()