import os
import requests
import logging

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"
        self.logger = logging.getLogger(__name__)

    def get_ai_response(self, user_message, context=None):
        """
        Fetches a response from Groq.
        """
        system_prompt = (
            "You are the Senior IPv6 Intelligence Analyst for the APAC region. "
            "Your goal is to provide technically accurate, professional, and actionable advice "
            "on IPv6 deployment, internet standards (IETF), and network security. "
            "Use a helpful, industry-grade tone. If provided with scan results, explain them clearly."
        )

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if context:
            messages.append({"role": "system", "content": f"Context for this query: {context}"})
        
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            self.logger.info(f"Sending request to Groq for model {self.model}")
            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            self.logger.error(f"Groq API Error: {str(e)}")
            return f"I apologize, but I encountered a technical error: {str(e)}. Please try again later."

ai_service = AIService()
