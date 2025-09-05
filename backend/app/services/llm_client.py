import requests
import os
from typing import Dict, Optional, Any

class HuggingFaceLLM:
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        self.model_id = os.getenv("HF_MODEL_ID", "microsoft/DialoGPT-medium")
        self.base_url = "https://api-inference.huggingface.co/models"
        
    async def query(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        """Query Hugging Face Inference API"""
        if not self.api_key:
            return {
                "status": "error",
                "text": "LLM service not configured",
                "meta": {"fallback": True}
            }
        
        url = f"{self.base_url}/{self.model_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=15
            )
            
            print(f"HF API Status: {response.status_code}")  # Debug log
            
            if response.status_code == 200:
                result = response.json()
                print(f"HF API Result: {result}")  # Debug log
                
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                    # Clean up the response - remove the original prompt
                    cleaned_text = generated_text.replace(prompt, "").strip()
                    return {
                        "status": "success",
                        "text": cleaned_text or "I'm here to help with your finances!",
                        "meta": {"model": self.model_id}
                    }
            
            print(f"HF API Error: {response.text}")  # Debug log
            return {
                "status": "error",
                "text": f"LLM API error: {response.status_code}",
                "meta": {"fallback": True}
            }
            
        except Exception as e:
            print(f"HF API Exception: {e}")  # Debug log
            return {
                "status": "error", 
                "text": f"LLM connection failed: {str(e)}",
                "meta": {"fallback": True}
            }

# Initialize singleton
llm_client = HuggingFaceLLM()