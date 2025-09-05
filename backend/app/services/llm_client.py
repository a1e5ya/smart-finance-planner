import requests
import os
from typing import Dict, Optional, Any

class HuggingFaceLLM:
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        self.model_id = os.getenv("HF_MODEL_ID", "gpt2")
        self.base_url = "https://api-inference.huggingface.co/models"
        
        # Debug logging
        print(f"🔧 HF Client initialized:")
        print(f"   API Key: {'✅ Set' if self.api_key else '❌ Missing'}")
        print(f"   Model ID: {self.model_id}")
        print(f"   Full URL: {self.base_url}/{self.model_id}")
        
    async def query(self, prompt: str, max_tokens: int = 50) -> Dict[str, Any]:
        """Query Hugging Face Inference API with extensive debugging"""
        
        if not self.api_key:
            print("❌ No HF API key found")
            return {
                "status": "error",
                "text": "Hugging Face API key not configured",
                "meta": {"fallback": True, "error": "no_api_key"}
            }
        
        # Try a simpler approach first
        url = f"{self.base_url}/{self.model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Simplified payload for debugging
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        print(f"🔍 Debug Info:")
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        print(f"   Payload: {payload}")
        print(f"   Prompt length: {len(prompt)}")
        
        try:
            print(f"🚀 Making request to HF API...")
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=30
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📊 Response Headers: {dict(response.headers)}")
            
            # Log the raw response for debugging
            try:
                response_text = response.text
                print(f"📊 Raw Response: {response_text[:500]}...")
            except:
                print("📊 Could not read response text")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"✅ JSON Response Type: {type(result)}")
                    print(f"✅ JSON Response Keys: {result.keys() if isinstance(result, dict) else 'List response'}")
                    
                    # Handle different response formats
                    generated_text = ""
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                    elif isinstance(result, dict) and "generated_text" in result:
                        generated_text = result["generated_text"]
                    else:
                        print(f"❓ Unexpected response format: {result}")
                        return {
                            "status": "error",
                            "text": "Unexpected API response format",
                            "meta": {"fallback": True, "response": str(result)[:200]}
                        }
                    
                    # Clean the response
                    cleaned_text = generated_text.strip()
                    if len(cleaned_text) > 200:
                        cleaned_text = cleaned_text[:197] + "..."
                    
                    if not cleaned_text:
                        cleaned_text = "I'm here to help with your finances!"
                    
                    print(f"✅ Final Response: {cleaned_text}")
                    return {
                        "status": "success",
                        "text": cleaned_text,
                        "meta": {"model": self.model_id, "length": len(cleaned_text)}
                    }
                    
                except Exception as json_error:
                    print(f"❌ JSON parsing error: {json_error}")
                    return {
                        "status": "error",
                        "text": "Failed to parse API response",
                        "meta": {"fallback": True, "json_error": str(json_error)}
                    }
            
            elif response.status_code == 401:
                print("❌ Authentication failed - check your HF API key")
                return {
                    "status": "error",
                    "text": "Hugging Face authentication failed",
                    "meta": {"fallback": True, "status_code": 401}
                }
            
            elif response.status_code == 404:
                print(f"❌ Model not found: {self.model_id}")
                print("💡 Trying fallback to a different model...")
                
                # Try with distilgpt2 as fallback
                fallback_url = f"{self.base_url}/distilgpt2"
                print(f"🔄 Trying fallback URL: {fallback_url}")
                
                fallback_response = requests.post(
                    fallback_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if fallback_response.status_code == 200:
                    print("✅ Fallback model worked!")
                    result = fallback_response.json()
                    generated_text = ""
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                    
                    cleaned_text = generated_text.strip()
                    if len(cleaned_text) > 200:
                        cleaned_text = cleaned_text[:197] + "..."
                    
                    return {
                        "status": "success",
                        "text": cleaned_text or "I'm here to help with your finances!",
                        "meta": {"model": "distilgpt2", "fallback": True}
                    }
                
                return {
                    "status": "error",
                    "text": f"Model '{self.model_id}' not found on Hugging Face",
                    "meta": {"fallback": True, "status_code": 404}
                }
            
            elif response.status_code == 503:
                print("⏳ Model is loading...")
                return {
                    "status": "error",
                    "text": "AI model is starting up, please try again in a moment...",
                    "meta": {"fallback": True, "loading": True}
                }
            
            else:
                error_text = response.text
                print(f"❌ HTTP Error {response.status_code}: {error_text}")
                return {
                    "status": "error",
                    "text": f"AI service error ({response.status_code})",
                    "meta": {"fallback": True, "status_code": response.status_code, "error_text": error_text[:200]}
                }
            
        except requests.exceptions.Timeout:
            print("⏰ Request timeout")
            return {
                "status": "error", 
                "text": "AI request timed out, please try again",
                "meta": {"fallback": True, "timeout": True}
            }
        except requests.exceptions.ConnectionError as e:
            print(f"🌐 Connection error: {e}")
            return {
                "status": "error", 
                "text": "Cannot connect to AI service",
                "meta": {"fallback": True, "connection_error": str(e)}
            }
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return {
                "status": "error", 
                "text": "AI service temporarily unavailable",
                "meta": {"fallback": True, "error": str(e)}
            }

# Test function to verify the API key and connection
async def test_hugging_face_connection():
    """Test function to debug HF API connection"""
    client = HuggingFaceLLM()
    
    print("🧪 Testing Hugging Face API Connection...")
    
    # Test with a simple prompt
    result = await client.query("Hello, I am a", max_tokens=10)
    
    print(f"🧪 Test Result: {result}")
    return result

# Initialize singleton
llm_client = HuggingFaceLLM()