import google.generativeai as genai
import requests
import json
from typing import Dict, List, Optional
from config import GEMINI_API_KEY, OPENROUTER_API_KEY, HUGGINGFACE_API_KEY

class QAProcessor:
    def __init__(self):
        self.gemini_client = None
        self.setup_clients()
    
    def setup_clients(self):
        """Setup AI clients"""
        # Gemini
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_client = genai.GenerativeModel('gemini-pro')
        
        self.openrouter_headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        } if OPENROUTER_API_KEY else None
        
        self.huggingface_headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
        } if HUGGINGFACE_API_KEY else None
    
    def generate_explanation(self, question_data: Dict) -> str:
        """Generate explanation using AI"""
        prompt = self._create_prompt(question_data)
        
        # Try Gemini first
        explanation = self._try_gemini(prompt)
        if explanation:
            return explanation
        
        # Try OpenRouter as fallback
        explanation = self._try_openrouter(prompt)
        if explanation:
            return explanation
        
        # Try HuggingFace as last resort
        explanation = self._try_huggingface(prompt)
        if explanation:
            return explanation
        
        return "Could not generate explanation at this time. Please try again later."
    
    def _create_prompt(self, question_data: Dict) -> str:
        """Create prompt for AI"""
        question = question_data['question']
        options = question_data['options']
        correct_answer = question_data['correct_answer']
        original_explanation = question_data.get('original_explanation', '')
        
        prompt = f"""
        Please provide a clear and educational explanation for this multiple-choice question:
        
        Question: {question}
        
        Options:
        A) {options['A']}
        B) {options['B']}
        C) {options['C']}
        D) {options['D']}
        
        Correct Answer: {correct_answer}
        
        Original Explanation: {original_explanation}
        
        Please provide:
        1. A clear explanation of why the correct answer is right
        2. Brief explanation of why other options are wrong (if applicable)
        3. Additional context or examples to help understand the concept
        4. Keep the explanation concise but informative
        
        Format your response in a clear, easy-to-read way.
        """
        
        return prompt
    
    def _try_gemini(self, prompt: str) -> Optional[str]:
        """Try generating with Gemini"""
        if not self.gemini_client:
            return None
        
        try:
            response = self.gemini_client.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            return None
    
    def _try_openrouter(self, prompt: str) -> Optional[str]:
        """Try generating with OpenRouter"""
        if not self.openrouter_headers:
            return None
        
        try:
            payload = {
                "model": "google/gemini-pro",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=self.openrouter_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"OpenRouter error: {e}")
        
        return None
    
    def _try_huggingface(self, prompt: str) -> Optional[str]:
        """Try generating with HuggingFace"""
        if not self.huggingface_headers:
            return None
        
        try:
            # Using a general purpose model
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            response = requests.post(
                "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large",
                headers=self.huggingface_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
        except Exception as e:
            print(f"HuggingFace error: {e}")
        
        return None
    
    def process_questions(self, questions: List[Dict], max_questions: int = 5) -> List[Dict]:
        """Process multiple questions with AI explanations"""
        processed = []
        
        for i, question in enumerate(questions[:max_questions]):
            print(f"Processing question {i+1}/{min(len(questions), max_questions)}")
            
            # Generate AI explanation
            ai_explanation = self.generate_explanation(question)
            
            processed_question = question.copy()
            processed_question['ai_explanation'] = ai_explanation
            
            processed.append(processed_question)
        
        return processed