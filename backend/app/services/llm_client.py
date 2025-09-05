import requests
import os
from typing import Dict, Optional, Any

class HuggingFaceLLM:
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        # Updated to use google/flan-t5-large model
        self.model_id = os.getenv("HF_MODEL_ID", "google/flan-t5-base")
        self.base_url = "https://api-inference.huggingface.co/models"
        
    async def query(self, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
        """Query Hugging Face Inference API with FLAN-T5"""
        if not self.api_key:
            return {
                "status": "error",
                "text": "LLM service not configured",
                "meta": {"fallback": True}
            }
        
        url = f"{self.base_url}/{self.model_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # FLAN-T5 format - simpler than Mistral, no special tokens needed
        formatted_prompt = f"You are a helpful AI assistant for a personal finance app called Smart Personal Finance Planner. Be concise, helpful, and encouraging. Keep responses under 100 words. If a feature isn't implemented yet, guide users to what they can do now.\n\nUser: {prompt}\nAssistant:"
        
        payload = {
            "inputs": formatted_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "do_sample": True,
                "top_p": 0.9,
                "repetition_penalty": 1.03
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False
            }
        }
        
        try:
            print(f"🤖 Querying FLAN-T5: {self.model_id}")
            print(f"🔗 URL: {url}")
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=30  # Increased timeout for model loading
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
                
                # Clean the response - remove the original prompt if it's included
                if formatted_prompt in generated_text:
                    cleaned_text = generated_text.replace(formatted_prompt, "").strip()
                else:
                    cleaned_text = generated_text.strip()
                
                # Remove common artifacts
                if cleaned_text.startswith("Assistant:"):
                    cleaned_text = cleaned_text[10:].strip()
                
                if not cleaned_text:
                    cleaned_text = "I'm here to help with your personal finances!"
                
                print(f"✅ FLAN-T5 Response: {cleaned_text[:100]}...")
                return {
                    "status": "success",
                    "text": cleaned_text,
                    "meta": {"model": self.model_id, "length": len(cleaned_text)}
                }
            
            elif response.status_code == 503:
                # Model is loading
                print("⏳ FLAN-T5 model is loading...")
                return {
                    "status": "error",
                    "text": "AI model is starting up, please try again in a moment...",
                    "meta": {"fallback": True, "loading": True}
                }
            
            elif response.status_code == 404:
                print(f"❌ Model not found: {self.model_id}")
                print(f"❌ Full URL attempted: {url}")
                return {
                    "status": "error",
                    "text": f"Model {self.model_id} not found. Please check the model name.",
                    "meta": {"fallback": True, "status_code": response.status_code}
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