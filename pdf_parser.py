import PyPDF2
import re

class PDFParser:
    def extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PDF error: {e}")
            raise
        return text
    
    def extract_qa_from_text(self, text):
        questions = []
        
        pattern = r'(\d+)\.\s*(.*?)\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)\s*Ex:\s*(.*?)(?=\n\d+\.|\Z)'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                q_num, question, opt_a, opt_b, opt_c, opt_d, explanation = match
                
                question = self.clean_text(question)
                opt_a = self.clean_text(opt_a)
                opt_b = self.clean_text(opt_b)
                opt_c = self.clean_text(opt_c)
                opt_d = self.clean_text(opt_d)
                explanation = self.clean_text(explanation)
                
                correct_answer = self.find_correct_answer(opt_a, opt_b, opt_c, opt_d)
                
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
        
        return questions
    
    def clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    
    def find_correct_answer(self, opt_a, opt_b, opt_c, opt_d):
        options = {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d}
        
        for key, value in options.items():
            if '✅' in value:
                return key
        
        return 'A'
    
    def parse_file(self, file_path):
        if file_path.endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError("Unsupported file type")
        
        return self.extract_qa_from_text(text)