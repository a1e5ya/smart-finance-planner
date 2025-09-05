import requests
import os
from typing import Dict, Optional, Any

class HuggingFaceLLM:
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        self.model_id = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")
        self.base_url = "https://api-inference.huggingface.co/models"
        
    async def query(self, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
        """Query Hugging Face Inference API with Mistral"""
        if not self.api_key:
            return {
                "status": "error",
                "text": "LLM service not configured",
                "meta": {"fallback": True}
            }
        
        url = f"{self.base_url}/{self.model_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Mistral instruction format
        formatted_prompt = f"[INST] You are a helpful AI assistant for a personal finance app called Smart Personal Finance Planner.\n\nBe concise, helpful, and encouraging. Keep responses under 100 words. If a feature isn't implemented yet, guide users to what they can do now.\n\nUser: {prompt} [/INST]"
        
        payload = {
            "inputs": formatted_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "return_full_text": False,
                "do_sample": True,
                "top_p": 0.9
            }
        }
        
        try:
            print(f"🤖 Querying Mistral: {self.model_id}")
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=20
            )
            
            print(f"HF API Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"HF API Result Type: {type(result)}")
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict) and "generated_text" in result:
                    generated_text = result["generated_text"]
                else:
                    print(f"Unexpected response format: {result}")
                    return {
                        "status": "error",
                        "text": "Unexpected API response format",
                        "meta": {"fallback": True}
                    }
                
                # Clean the response
                cleaned_text = generated_text.strip()
                if not cleaned_text:
                    cleaned_text = "I'm here to help with your personal finances!"
                
                print(f"✅ Mistral Response: {cleaned_text[:100]}...")
                return {
                    "status": "success",
                    "text": cleaned_text,
                    "meta": {"model": self.model_id, "length": len(cleaned_text)}
                }
            
            elif response.status_code == 503:
                # Model is loading
                print("⏳ Mistral model is loading...")
                return {
                    "status": "error",
                    "text": "AI model is starting up, please try again in a moment...",
                    "meta": {"fallback": True, "loading": True}
                }
            
            else:
                error_text = response.text
                print(f"❌ HF API Error {response.status_code}: {error_text}")
                return {
                    "status": "error",
                    "text": f"AI service temporarily unavailable ({response.status_code})",
                    "meta": {"fallback": True, "status_code": response.status_code}
                }
            
        except requests.exceptions.Timeout:
            print("⏰ Request timeout")
            return {
                "status": "error", 
                "text": "AI response took too long, please try again",
                "meta": {"fallback": True, "timeout": True}
            }
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {
                "status": "error", 
                "text": "AI service temporarily unavailable",
                "meta": {"fallback": True, "error": str(e)}
            }

# Initialize singleton
llm_client = HuggingFaceLLM()