import requests
from config import GEMINI_API_KEY

class QAProcessor:
    def generate_explanation(self, question_data):
        prompt = self.create_prompt(question_data)
        explanation = self.try_gemini(prompt)
        
        if explanation:
            return explanation
        else:
            return "Explanation: The correct answer is option " + question_data['correct_answer']
    
    def create_prompt(self, question_data):
        question = question_data['question']
        options = question_data['options']
        correct_answer = question_data['correct_answer']
        
        prompt = f"""
Explain this multiple-choice question:

Question: {question}

Options:
A) {options['A']}
B) {options['B']}
C) {options['C']}
D) {options['D']}

Correct Answer: {correct_answer}

Provide a brief explanation.
        """
        
        return prompt
    
    def try_gemini(self, prompt):
        if not GEMINI_API_KEY:
            return None
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini API error: {e}")
        
        return None
    
    def process_questions(self, questions, max_questions=3):
        processed = []
        
        for i, question in enumerate(questions[:max_questions]):
            print(f"Processing question {i+1}")
            
            ai_explanation = self.generate_explanation(question)
            
            processed_question = question.copy()
            processed_question['ai_explanation'] = ai_explanation
            
            processed.append(processed_question)
        
        return processed