import requests
import os
from typing import Dict, Optional, Any

class GroqLLM:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_id = os.getenv("GROQ_MODEL_ID", "llama-3.3-70b-versatile")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    async def query(self, prompt: str, max_tokens: int = 200) -> Dict[str, Any]:
        """Query Groq API with Llama or other models"""
        if not self.api_key:
            return {
                "status": "error",
                "text": "LLM service not configured - missing GROQ_API_KEY",
                "meta": {"fallback": True}
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Format messages for OpenAI-compatible API
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant for a personal finance app called Smart Personal Finance Planner. Be concise, helpful, and encouraging. Keep responses under 100 words. If a feature isn't implemented yet, guide users to what they can do now."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            print(f"🤖 Querying Groq: {self.model_id}")
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=payload, 
                timeout=20
            )
            
            print(f"Groq API Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Groq API Result: {result}")
                
                # Extract the response from OpenAI-compatible format
                if "choices" in result and len(result["choices"]) > 0:
                    generated_text = result["choices"][0]["message"]["content"]
                    
                    print(f"✅ Groq Response: {generated_text[:100]}...")
                    return {
                        "status": "success",
                        "text": generated_text,
                        "meta": {
                            "model": self.model_id, 
                            "length": len(generated_text),
                            "usage": result.get("usage", {})
                        }
                    }
                else:
                    print(f"Unexpected response format: {result}")
                    return {
                        "status": "error",
                        "text": "Unexpected API response format",
                        "meta": {"fallback": True}
                    }
            
            elif response.status_code == 401:
                print("🔐 Groq API Authentication Error")
                return {
                    "status": "error",
                    "text": "AI service authentication failed",
                    "meta": {"fallback": True, "auth_error": True}
                }
            
            elif response.status_code == 429:
                print("⏳ Groq API Rate Limited")
                return {
                    "status": "error",
                    "text": "AI service is busy, please try again in a moment",
                    "meta": {"fallback": True, "rate_limited": True}
                }
            
            else:
                error_text = response.text
                print(f"❌ Groq API Error {response.status_code}: {error_text}")
                return {
                    "status": "error",
                    "text": f"AI service temporarily unavailable ({response.status_code})",
                    "meta": {"fallback": True, "status_code": response.status_code}
                }
            
        except requests.exceptions.Timeout:
            print("⏰ Groq Request timeout")
            return {
                "status": "error", 
                "text": "AI response took too long, please try again",
                "meta": {"fallback": True, "timeout": True}
            }
        except Exception as e:
            print(f"❌ Groq Exception: {e}")
            return {
                "status": "error", 
                "text": "AI service temporarily unavailable",
                "meta": {"fallback": True, "error": str(e)}
            }

# Initialize singleton
llm_client = GroqLLM()