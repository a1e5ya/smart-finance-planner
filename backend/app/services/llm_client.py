import requests
import os
from typing import Dict, Optional, Any

class HuggingFaceLLM:
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY")
        self.model_id = os.getenv("HF_MODEL_ID", "gpt2")  # Changed to GPT-2
        self.base_url = "https://api-inference.huggingface.co/models"
        
    async def query(self, prompt: str, max_tokens: int = 100) -> Dict[str, Any]:
        """Query Hugging Face Inference API with GPT-2"""
        if not self.api_key:
            return {
                "status": "error",
                "text": "LLM service not configured",
                "meta": {"fallback": True}
            }
        
        url = f"{self.base_url}/{self.model_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # GPT-2 format - simpler than Mistral's instruction format
        # Add context to make responses more finance-focused
        finance_context = "As a helpful personal finance assistant, respond to: "
        formatted_prompt = f"{finance_context}{prompt}"
        
        payload = {
            "inputs": formatted_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "return_full_text": False,  # Only return the generated part
                "do_sample": True,
                "top_p": 0.9,
                "repetition_penalty": 1.1,  # Avoid repetitive text
                "stop": ["\n\n", "User:", "Assistant:", "Question:"]  # Stop sequences
            }
        }
        
        try:
            print(f"🤖 Querying GPT-2: {self.model_id}")
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
                
                # Post-process GPT-2 output to make it more concise and relevant
                cleaned_text = self._post_process_gpt2_response(cleaned_text, prompt)
                
                if not cleaned_text:
                    cleaned_text = "I'm here to help with your personal finances!"
                
                print(f"✅ GPT-2 Response: {cleaned_text[:100]}...")
                return {
                    "status": "success",
                    "text": cleaned_text,
                    "meta": {"model": self.model_id, "length": len(cleaned_text)}
                }
            
            elif response.status_code == 503:
                # Model is loading
                print("⏳ GPT-2 model is loading...")
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
    
    def _post_process_gpt2_response(self, text: str, original_prompt: str) -> str:
        """Post-process GPT-2 response to make it more suitable for chat"""
        # Remove the context prefix if it appears in the response
        text = text.replace("As a helpful personal finance assistant, respond to:", "").strip()
        
        # Split by sentences and take the first few that make sense
        sentences = text.split('. ')
        
        # Filter out incomplete or very long sentences
        good_sentences = []
        for sentence in sentences[:3]:  # Take max 3 sentences
            sentence = sentence.strip()
            if len(sentence) > 10 and len(sentence) < 200:  # Reasonable length
                if not sentence.endswith('.'):
                    sentence += '.'
                good_sentences.append(sentence)
        
        result = ' '.join(good_sentences)
        
        # If result is empty or too short, provide a default response
        if len(result) < 20:
            # Create a contextual fallback based on the prompt
            if "goal" in original_prompt.lower() or "save" in original_prompt.lower():
                result = "That's a great financial goal! I'd love to help you create a savings plan once you upload your transaction data."
            elif "hello" in original_prompt.lower() or "hi" in original_prompt.lower():
                result = "Hello! I'm your AI finance assistant, ready to help with budgeting and financial planning."
            else:
                result = "I'm here to help with your personal finances! Try asking about savings goals or uploading transaction data."
        
        # Ensure response is not too long
        if len(result) > 300:
            result = result[:297] + "..."
        
        return result

# Initialize singleton
llm_client = HuggingFaceLLM()