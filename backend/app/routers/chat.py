from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import time
import re

from ..models.database import get_db, User, AuditLog
from .auth import get_current_user
from ..services.llm_client import llm_client

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    user_context: str
    phase: str = "1"
    ai_powered: bool = False
    fallback_used: bool = False

async def log_chat_interaction(
    db: AsyncSession,
    user: Optional[User],
    message: str,
    response: str,
    ai_powered: bool,
    request: Request
):
    """Log chat interaction to audit table"""
    audit = AuditLog(
        user_id=user.id if user else None,
        firebase_uid=user.firebase_uid if user else None,
        entity="chat",
        action="message",
        details={
            "user_message": message,
            "bot_response": response,
            "ai_powered": ai_powered,
            "authenticated": user is not None,
            "user_email": user.email if user else None
        },
        ip_address=getattr(request.client, 'host', None) if hasattr(request, 'client') else None,
        user_agent=request.headers.get('user-agent', None) if hasattr(request, 'headers') else None
    )
    
    db.add(audit)
    await db.commit()

def parse_goal_intent(message: str) -> Optional[dict]:
    """Regex fallback for goal parsing"""
    patterns = [
        r"save\s+(\d+)\s+by\s+(\w+)\s+for\s+(.+)",
        r"save\s+(\d+)\s+for\s+(.+)\s+by\s+(\w+)",
        r"(\d+)\s+by\s+(\w+)\s+for\s+(.+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return {
                "type": "goal",
                "amount": match.group(1),
                "deadline": match.group(2) if len(match.groups()) == 3 else match.group(3),
                "purpose": match.group(3) if len(match.groups()) == 3 else match.group(2)
            }
    return None

def get_fallback_response(message: str, user: Optional[User]) -> str:
    """Fallback responses when LLM unavailable"""
    message_lower = message.lower()
    user_name = user.display_name or user.email.split('@')[0] if user else "there"
    
    # Check for goal setting
    goal_intent = parse_goal_intent(message)
    if goal_intent:
        return f"I can see you want to save ${goal_intent['amount']} for {goal_intent['purpose']} by {goal_intent['deadline']}. I can't create goals yet - please import your transactions first, then I'll help you set realistic savings targets!"
    
    # Keyword-based responses
    if any(word in message_lower for word in ["hello", "hi", "hey"]):
        if user:
            return f"Hello {user_name}! I'm your AI finance assistant. Right now I can chat with you, but I'll be much more helpful once you upload your transaction data!"
        else:
            return "Hello! I'm your AI finance assistant. Sign in to unlock personalized features, then upload your transaction data to get started!"
    
    elif "language model" in message_lower or "ai" in message_lower:
        return f"Yes, I'm an AI assistant powered by machine learning! I'm specifically designed to help with personal finance, budgeting, and savings goals. While I can chat naturally, I'll be most useful once you upload your transaction data, {user_name}!"
    
    elif any(word in message_lower for word in ["import", "upload", "csv", "transactions"]):
        return f"To import transactions, {user_name}, click 'Upload CSV File' in the Transactions tab. I support most bank CSV formats and will help categorize everything automatically once that feature is ready!"
    
    elif any(word in message_lower for word in ["balance", "money", "spend", "spending"]):
        return "I can't analyze your spending yet since you haven't uploaded any transaction data. Upload a CSV in the Transactions tab first!"
    
    elif any(word in message_lower for word in ["help", "what can"]):
        if user:
            return f"Hi {user_name}! I'm still learning, but I can chat with you about finances. Try asking me to 'save money for vacation' or 'import transactions'. Upload your bank CSV to unlock my full potential!"
        else:
            return "I'm your AI finance assistant! Sign in first, then upload transaction data to get personalized insights. Try: 'Save 3000 by December' or 'Import transactions'."
    
    elif "auth" in message_lower or "login" in message_lower:
        if user:
            return f"You're already signed in as {user.email}! Your authentication is working perfectly. Now upload some transaction data and I can really help you!"
        else:
            return "Please sign in using the login button to access personalized features!"
    
    else:
        return f"I understand you said '{message}'. I'm still learning about finance features. Right now, try uploading transaction data in the Transactions tab, or ask me about saving goals!"

@router.post("/command", response_model=ChatResponse)
async def chat_command(
    request_data: ChatRequest, 
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enhanced chat with Hugging Face LLM proxy and fallbacks"""
    
    message = request_data.message
    user_context = "authenticated" if current_user else "anonymous"
    ai_powered = False
    fallback_used = False
    
    # Build context for LLM
    context_prompt = f"You are a helpful AI assistant for a personal finance app called Smart Personal Finance Planner. Be concise and helpful. "
    
    if current_user:
        context_prompt += f"The user {current_user.email} is signed in. "
    else:
        context_prompt += "The user is anonymous (encourage them to sign in). "
    
    context_prompt += "This is Phase 1 - features like transaction import and categorization are coming soon. User question: "
    
    full_prompt = context_prompt + message
    
    # Try LLM first
    print(f"Attempting LLM query for: {message}")
    try:
        llm_result = await llm_client.query(full_prompt)
        print(f"LLM result: {llm_result}")
        
        if llm_result["status"] == "success" and llm_result["text"]:
            response = llm_result["text"]
            ai_powered = True
            print("Using AI response")
        else:
            response = get_fallback_response(message, current_user)
            fallback_used = True
            print("Using fallback response")
            
    except Exception as e:
        print(f"LLM error: {e}")
        response = get_fallback_response(message, current_user)
        fallback_used = True
    
    # Create response object
    chat_response = ChatResponse(
        response=response,
        timestamp=time.strftime("%H:%M:%S"),
        user_context=user_context,
        ai_powered=ai_powered,
        fallback_used=fallback_used
    )
    
    # Log the interaction
    await log_chat_interaction(db, current_user, message, response, ai_powered, request)
    
    # Console logging for development
    status_emoji = "🤖" if ai_powered else "🔄"
    print(f"{status_emoji} {user_context}: {message[:50]}...")
    print(f"   Response: {response[:50]}...")
    
    return chat_response