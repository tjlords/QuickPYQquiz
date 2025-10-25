import os
import tempfile
import asyncio
from typing import Dict, List
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
        """Send welcome message"""
        welcome_text = """
🤖 Welcome to the Q&A Explanation Bot!

Send me a PDF or text file containing multiple-choice questions, and I'll:
• Extract all questions and answers
• Generate AI-powered explanations
• Provide detailed insights

Supported formats: PDF, TXT

Use /help for more information.
        """
        await update.message.reply_text(welcome_text)
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help message"""
        help_text = """
📚 How to use this bot:

1. Send a PDF or text file containing multiple-choice questions
2. The file should have questions in this format:
   1. Question text?
   a) Option A
   b) Option B  
   c) Option C
   d) Option D
   Ex: Explanation

3. I'll extract questions and generate AI explanations

Commands:
/start - Welcome message
/help - This help message
/about - About this bot

Note: Large files may take some time to process.
        """
        await update.message.reply_text(help_text)
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show about information"""
        about_text = """
🎓 Q&A Explanation Bot

This bot uses AI to generate detailed explanations for multiple-choice questions.

Features:
• PDF and text file parsing
• AI-powered explanations (Gemini/OpenRouter/HuggingFace)
• Clear, educational responses
• Support for various question formats

Built with Python and love for education! 💫
        """
        await update.message.reply_text(about_text)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        try:
            # Send processing message
            processing_msg = await update.message.reply_text("📥 File received! Processing...")
            
            # Get file
            document = update.message.document
            file = await context.bot.get_file(document.file_id)
            
            # Get file extension
            file_extension = os.path.splitext(document.file_name)[1].lower()
            
            if file_extension not in ['.pdf', '.txt']:
                await processing_msg.edit_text("❌ Unsupported file type. Please send a PDF or TXT file.")
                return
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                file_path = tmp_file.name
            
            # Download file
            await file.download_to_drive(file_path)
            
            # Parse file
            await processing_msg.edit_text("🔍 Extracting questions from file...")
            questions = self.parser.parse_file(file_path)
            
            if not questions:
                await processing_msg.edit_text("❌ No questions found in the file. Please check the format.")
                os.unlink(file_path)
                return
            
            await processing_msg.edit_text(f"📚 Found {len(questions)} questions. Generating AI explanations...")
            
            # Process questions with AI
            processed_questions = self.processor.process_questions(
                questions, 
                max_questions=min(MAX_QUESTIONS_PER_REQUEST, len(questions))
            )
            
            # Send results
            await self.send_results(update, context, processed_questions)
            
            # Cleanup
            os.unlink(file_path)
            await processing_msg.delete()
            
        except Exception as e:
            error_msg = f"❌ Error processing file: {str(e)}"
            await update.message.reply_text(error_msg)
            print(f"Error: {e}")
    
    async def send_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, questions: List[Dict]):
        """Send processed questions to user"""
        for i, question in enumerate(questions, 1):
            response = self.format_question_response(question, i)
            
            # Split long messages if needed
            if len(response) > 4000:
                parts = self.split_message(response)
                for part in parts:
                    await update.message.reply_text(part, parse_mode='HTML')
            else:
                await update.message.reply_text(response, parse_mode='HTML')
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        summary = f"""
✅ Processing complete!

Total questions processed: {len(questions)}

Need more explanations? Send another file!
        """
        await update.message.reply_text(summary)
    
    def format_question_response(self, question: Dict, index: int) -> str:
        """Format question response with HTML"""
        response = f"""
<b>Question {index}</b>

<b>Q:</b> {question['question']}

<b>Options:</b>
A) {question['options']['A']}
B) {question['options']['B']}
C) {question['options']['C']}
D) {question['options']['D']}

<b>Correct Answer:</b> {question['correct_answer']}

<b>🤖 AI Explanation:</b>
{question.get('ai_explanation', 'No explanation generated.')}
        """
        
        if question.get('original_explanation'):
            response += f"\n\n<b>Original Explanation:</b>\n{question['original_explanation']}"
        
        return response
    
    def split_message(self, text: str, max_length: int = 4000) -> List[str]:
        """Split long message into parts"""
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
        """Start the bot"""
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("about", self.about))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        
        # Start bot
        print("Bot is running...")
        self.application.run_polling()