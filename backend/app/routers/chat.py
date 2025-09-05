from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import time
import re

from ..models.database import get_db, User, AuditLog
from .auth import get_current_user
from ..services.groq_client import llm_client  # Updated import

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
    model_info: Optional[str] = None

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

def parse_financial_intent(message: str) -> Optional[dict]:
    """Parse financial intents with regex fallback"""
    message_lower = message.lower()
    
    # Goal setting patterns
    goal_patterns = [
        r"save\s+\$?(\d+[,\d]*)\s+by\s+(\w+)\s+for\s+(.+)",
        r"save\s+\$?(\d+[,\d]*)\s+for\s+(.+)\s+by\s+(\w+)",
        r"need\s+\$?(\d+[,\d]*)\s+by\s+(\w+)\s+for\s+(.+)",
        r"\$?(\d+[,\d]*)\s+by\s+(\w+)\s+for\s+(.+)"
    ]
    
    for pattern in goal_patterns:
        match = re.search(pattern, message_lower)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                return {
                    "type": "savings_goal",
                    "amount": groups[0],
                    "deadline": groups[1] if "by" in pattern else groups[2],
                    "purpose": groups[2] if "by" in pattern else groups[1]
                }
    
    # Budget patterns
    budget_patterns = [
        r"budget\s+\$?(\d+[,\d]*)\s+for\s+(.+)",
        r"spend\s+\$?(\d+[,\d]*)\s+on\s+(.+)",
        r"limit\s+(.+)\s+to\s+\$?(\d+[,\d]*)"
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, message_lower)
        if match:
            return {
                "type": "budget",
                "amount": match.group(1) if "limit" not in pattern else match.group(2),
                "category": match.group(2) if "limit" not in pattern else match.group(1)
            }
    
    return None

def get_smart_fallback_response(message: str, user: Optional[User]) -> str:
    """Enhanced fallback responses with financial context"""
    message_lower = message.lower()
    user_name = user.display_name or user.email.split('@')[0] if user else "there"
    
    # Check for financial intents
    financial_intent = parse_financial_intent(message)
    if financial_intent:
        if financial_intent["type"] == "savings_goal":
            return f"I can see you want to save ${financial_intent['amount']} for {financial_intent['purpose']} by {financial_intent['deadline']}! That's a great goal, {user_name}. Once you upload your transaction data, I'll help you create a realistic savings plan and track your progress."
        elif financial_intent["type"] == "budget":
            return f"Setting a ${financial_intent['amount']} budget for {financial_intent['category']} is smart planning! Upload your transaction history and I'll help you see if this budget is realistic based on your spending patterns."
    
    # AI/Language model questions
    if any(phrase in message_lower for phrase in ["language model", "ai", "artificial intelligence", "what are you", "who are you"]):
        return f"I'm an AI assistant powered by Groq's Llama models, specifically designed for personal finance! I can help with budgeting, savings goals, and financial planning. Right now I'm in Phase 1, so I can chat with you, but I'll be much more powerful once you upload your transaction data, {user_name}!"
    
    # Greetings
    if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        if user:
            return f"Hello {user_name}! I'm your AI finance assistant powered by Groq. I'm ready to help with budgeting and savings goals. Upload your transaction CSV to unlock my full potential!"
        else:
            return "Hello! I'm your AI finance assistant powered by Groq's fast language models. Sign in to access personalized features, then upload your transaction data to get started with smart financial planning!"
    
    # Data import
    elif any(word in message_lower for word in ["import", "upload", "csv", "transactions", "bank data"]):
        return f"To import your financial data, {user_name}, click 'Upload CSV File' in the Transactions tab. I support most bank CSV formats and will automatically categorize your spending once the feature is ready!"
    
    # Financial analysis
    elif any(word in message_lower for word in ["balance", "money", "spend", "spending", "analyze", "budget"]):
        return f"I'd love to analyze your finances, {user_name}! First, upload your transaction CSV in the Transactions tab, then I can provide insights on spending patterns, suggest budgets, and help with financial planning."
    
    # Help and capabilities
    elif any(word in message_lower for word in ["help", "what can", "capabilities", "features"]):
        if user:
            return f"Hi {user_name}! I'm your AI-powered finance assistant running on Groq for super-fast responses. I can help with savings goals, budgeting, and financial planning. Currently in Phase 1 - upload your bank CSV to unlock features like spending analysis and goal tracking!"
        else:
            return "I'm an AI finance assistant powered by Groq's lightning-fast language models! Sign in first, then upload transaction data for personalized insights. Try asking: 'Save $3000 by December' or 'Help me budget for groceries'."
    
    # Authentication
    elif any(word in message_lower for word in ["auth", "login", "sign in", "account"]):
        if user:
            return f"You're successfully signed in as {user.email}! Your authentication is working perfectly. Now upload some transaction data and I can provide personalized financial insights!"
        else:
            return "Please sign in using the login button to access personalized financial features and secure data storage!"
    
    # Forecasting and predictions
    elif any(word in message_lower for word in ["forecast", "predict", "future", "will i", "can i afford"]):
        return f"I'll be able to forecast your spending and predict financial outcomes once you upload transaction data, {user_name}! The forecasting engine uses machine learning to help you plan for the future."
    
    # Categories and organization
    elif any(word in message_lower for word in ["categor", "organize", "sort", "group"]):
        return f"I can automatically categorize your transactions using ML once you upload your data, {user_name}! The system learns from your spending patterns to organize everything intelligently."
    
    # Default response
    else:
        return f"I understand you said '{message}'. I'm an AI finance assistant powered by Groq's fast language models, ready to help with budgeting, savings goals, and financial planning! Try uploading your transaction data in the Transactions tab to get started, {user_name}."

@router.post("/command", response_model=ChatResponse)
async def chat_command(
    request_data: ChatRequest, 
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Groq-powered chat with intelligent fallbacks"""
    
    message = request_data.message
    user_context = "authenticated" if current_user else "anonymous"
    ai_powered = False
    fallback_used = False
    model_info = None
    
    # Build context for Groq
    context_parts = [
        "You are having a natural conversation about personal finance.",
        "The user is using Smart Personal Finance Planner app.",
        "Be conversational and helpful, like chatting with a friend about money."
    ]
    
    if current_user:
        context_parts.append(f"User {current_user.email} is signed in.")
    else:
        context_parts.append("User is anonymous - encourage sign in for personalized features.")
    
    context_parts.extend([
        "This is Phase 1: auth works, transaction import coming soon.",
        "If asked about unimplemented features, guide to current capabilities.",
        f"User question: {message}"
    ])
    
    full_prompt = " ".join(context_parts)
    
    # Try Groq LLM first
    print(f"🎯 Attempting Groq query for: {message}")
    try:
        llm_result = await llm_client.query(full_prompt, max_tokens=150)
        print(f"📊 Groq result: {llm_result['status']}")
        
        if llm_result["status"] == "success" and llm_result["text"]:
            response = llm_result["text"]
            ai_powered = True
            model_info = llm_result.get("meta", {}).get("model", "groq")
            print(f"✅ Using Groq AI response")
        else:
            response = get_smart_fallback_response(message, current_user)
            fallback_used = True
            model_info = "fallback"
            print(f"🔄 Using enhanced fallback: {llm_result.get('text', 'unknown error')}")
            
    except Exception as e:
        print(f"❌ Groq error: {e}")
        response = get_smart_fallback_response(message, current_user)
        fallback_used = True
        model_info = "fallback"
    
    # Create response object
    chat_response = ChatResponse(
        response=response,
        timestamp=time.strftime("%H:%M:%S"),
        user_context=user_context,
        ai_powered=ai_powered,
        fallback_used=fallback_used,
        model_info=model_info
    )
    
    # Log the interaction
    await log_chat_interaction(db, current_user, message, response, ai_powered, request)
    
    # Console logging for development
    status_emoji = "🤖" if ai_powered else "🔄"
    model_tag = f"[{model_info}]" if model_info else ""
    print(f"{status_emoji} {model_tag} {user_context}: {message[:50]}...")
    print(f"   Response: {response[:80]}...")
    
    return chat_response

@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's recent chat history (requires auth)"""
    
    if not current_user:
        return {"error": "Authentication required"}
    
    return {
        "message": f"Chat history for {current_user.email} - coming in Phase 2!",
        "user_id": str(current_user.id),
        "ai_model": "groq-llama-models"
    }