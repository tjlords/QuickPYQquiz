import PyPDF2
import re
import os
import tempfile
import base64
import requests
from config import GEMINI_API_KEY

class PDFParser:
    def extract_text_from_pdf(self, pdf_path):
        # First try regular extraction
        text = self.try_regular_extraction(pdf_path)
        
        # If regular extraction doesn't work well, use Gemini OCR
        if not self.has_questions(text):
            print("Regular extraction failed, using Gemini OCR...")
            text = self.extract_text_with_gemini_ocr(pdf_path)
        
        return text
    
    def try_regular_extraction(self, pdf_path):
        """Try regular PDF text extraction first"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Regular extraction error: {e}")
        
        return text
    
    def extract_text_with_gemini_ocr(self, pdf_path):
        """Use Gemini API for OCR on PDF"""
        if not GEMINI_API_KEY:
            print("Gemini API key not available for OCR")
            return ""
        
        try:
            # Convert PDF to base64
            with open(pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Gemini API request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GEMINI_API_KEY}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": "Extract all text from this PDF document. Include all questions, options, and explanations exactly as they appear. Preserve the numbering and formatting."
                        },
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": pdf_base64
                            }
                        }
                    ]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                print("Gemini OCR successful")
                return text
            else:
                print(f"Gemini OCR failed: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"Gemini OCR error: {e}")
            return ""
    
    def has_questions(self, text):
        """Check if text contains questions in expected format"""
        if not text:
            return False
        
        # Check for common question patterns
        patterns = [
            r'\d+\.\s+.*?\?',  # Numbered questions with question mark
            r'\d+\.\s+.*?a\)',  # Numbered questions with options
            r'Question\s*\d+',  # "Question 1" format
            r'\(A\).*?\(B\)',   # Options in parentheses
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
    def extract_qa_from_text(self, text):
        """Extract Q&A pairs from text"""
        questions = []
        
        print("Raw text sample:", text[:500])  # Debug: show first 500 chars
        
        # Multiple patterns to handle different formats
        patterns = [
            # Pattern for: 1. Question? a) optA b) optB c) optC d) optD Ex: explanation
            r'(\d+)\.\s*(.*?)\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)\s*Ex:\s*(.*?)(?=\n\d+\.|\Z)',
            # Pattern without "Ex:"
            r'(\d+)\.\s*(.*?)\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)(?=\n\d+\.|\Z)',
            # Pattern with (A), (B), (C), (D)
            r'(\d+)\.\s*(.*?)\s*\(A\)\s*(.*?)\s*\(B\)\s*(.*?)\s*\(C\)\s*(.*?)\s*\(D\)\s*(.*?)\s*Ex:\s*(.*?)(?=\n\d+\.|\Z)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            print(f"Pattern found {len(matches)} matches")  # Debug
            
            for match in matches:
                try:
                    if len(match) == 8:
                        q_num, question, opt_a, opt_b, opt_c, opt_d, explanation = match
                    elif len(match) == 7:
                        q_num, question, opt_a, opt_b, opt_c, opt_d = match
                        explanation = ""
                    else:
                        continue
                    
                    # Clean the text
                    question = self.clean_text(question)
                    opt_a = self.clean_text(opt_a)
                    opt_b = self.clean_text(opt_b)
                    opt_c = self.clean_text(opt_c)
                    opt_d = self.clean_text(opt_d)
                    explanation = self.clean_text(explanation)
                    
                    # Find correct answer
                    correct_answer = self.find_correct_answer(opt_a, opt_b, opt_c, opt_d, explanation)
                    
                    questions.append({
                        'number': int(q_num.strip('.')),
                        'question': question,
                        'options': {
                            'A': opt_a,
                            'B': opt_b,
                            'C': opt_c,
                            'D': opt_d
                        },
                        'correct_answer': correct_answer,
                        'original_explanation': explanation
                    })
                    
                    print(f"Extracted Q{q_num}: {question[:50]}...")  # Debug
                    
                except Exception as e:
                    print(f"Error processing question: {e}")
                    continue
            
            if questions:  # If we found questions with this pattern, break
                break
        
        return questions
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace but preserve content
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def find_correct_answer(self, opt_a, opt_b, opt_c, opt_d, explanation):
        """Find the correct answer from options"""
        options = {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d}
        
        # Look for indicators
        for key, value in options.items():
            if '✅' in value or 'correct' in value.lower() or 'right' in value.lower():
                return key
        
        # Check explanation for correct answer hints
        if 'option a' in explanation.lower() or 'answer a' in explanation.lower():
            return 'A'
        elif 'option b' in explanation.lower() or 'answer b' in explanation.lower():
            return 'B'
        elif 'option c' in explanation.lower() or 'answer c' in explanation.lower():
            return 'C'
        elif 'option d' in explanation.lower() or 'answer d' in explanation.lower():
            return 'D'
        
        # Default fallback
        return 'A'
    
    def parse_file(self, file_path):
        """Main method to parse file and extract Q&A"""
        if file_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError("Unsupported file type")
        
        print(f"Extracted text length: {len(text)}")
        return self.extract_qa_from_text(text)