import pdfplumber
import PyPDF2
import re
import fitz  # PyMuPDF
from typing import List, Dict

class PDFParser:
    def __init__(self):
        self.qa_patterns = [
            r'(\d+)\.\s*(.*?)\s*\n\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)(?=\n\d+\.|\n\s*Ex:|\Z)',
            r'(\d+)\.\s*(.*?)\s*\([A-D]\)\s*(.*?)\s*\([A-D]\)\s*(.*?)\s*\([A-D]\)\s*(.*?)\s*\([A-D]\)\s*(.*?)(?=\n\d+\.|\Z)'
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file using multiple methods"""
        text = ""
        
        # Try PyMuPDF first (most reliable)
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            if text.strip():
                return text
        except Exception as e:
            print(f"PyMuPDF error: {e}")
        
        # Try pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            if text.strip():
                return text
        except Exception as e:
            print(f"pdfplumber error: {e}")
        
        # Try PyPDF2 as last resort
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PyPDF2 error: {e}")
            raise Exception("Could not extract text from PDF using any method")
        
        return text
    
    def extract_qa_from_text(self, text: str) -> List[Dict]:
        """Extract Q&A pairs from text"""
        questions = []
        
        # Multiple patterns to catch different formats
        patterns = [
            r'(\d+)\.\s*(.*?)\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)\s*Ex:\s*(.*?)(?=\n\d+\.|\Z)',
            r'(\d+)\.\s*(.*?)\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)\s*Ex:\s*(.*)',
            r'(\d+)\.\s*(.*?)\s*\(A\)\s*(.*?)\s*\(B\)\s*(.*?)\s*\(C\)\s*(.*?)\s*\(D\)\s*(.*?)\s*Ex:\s*(.*?)(?=\n\d+\.|\Z)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
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
                    except Exception as e:
                        print(f"Error processing question: {e}")
                        continue
                break  # Use first pattern that matches
        
        return questions
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters but keep essential ones
        text = re.sub(r'[^\w\s\.\?\!\-\:\,\/\\(\)]', '', text)
        return text
    
    def find_correct_answer(self, opt_a: str, opt_b: str, opt_c: str, opt_d: str, explanation: str) -> str:
        """Find the correct answer from options"""
        # Look for ✅ emoji or similar indicators
        options = {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d}
        
        for key, value in options.items():
            if '✅' in value or 'correct' in value.lower() or 'right' in value.lower():
                return key
        
        # If no indicator found, return the first option as fallback
        return 'A'
    
    def parse_file(self, file_path: str) -> List[Dict]:
        """Main method to parse file and extract Q&A"""
        if file_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError("Unsupported file type")
        
        return self.extract_qa_from_text(text)