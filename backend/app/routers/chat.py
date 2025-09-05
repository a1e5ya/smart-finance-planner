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
    
    # Check for financial intents first
    financial_intent = parse_financial_intent(message)
    if financial_intent:
        if financial_intent["type"] == "savings_goal":
            return f"Great goal, {user_name}! Saving ${financial_intent['amount']} for {financial_intent['purpose']} by {financial_intent['deadline']} is achievable with the right plan. Upload your transaction data and I'll help you create a realistic savings strategy!"
        elif financial_intent["type"] == "budget":
            return f"Setting a ${financial_intent['amount']} budget for {financial_intent['category']} is smart planning! Once you upload your transaction history, I can analyze if this budget aligns with your spending patterns."
    
    # AI/Language model questions
    if any(phrase in message_lower for phrase in ["language model", "ai", "artificial intelligence", "what are you", "who are you"]):
        return f"I'm your AI finance assistant powered by GPT-2! I help with budgeting, savings goals, and financial planning. I'm currently in Phase 1 with authentication working. Upload your transaction data to unlock my full potential, {user_name}!"
    
    # Greetings
    if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        if user:
            return f"Hello {user_name}! 👋 I'm your AI finance assistant. Your authentication is working perfectly! Ready to help with budgeting and savings goals. Try asking me to help you save money or upload your transaction CSV!"
        else:
            return "Hello! 👋 I'm your AI finance assistant. Sign in to access personalized features, then upload your transaction data to get started with smart financial planning!"
    
    # Data import questions
    if any(word in message_lower for word in ["import", "upload", "csv", "transactions", "bank data", "file"]):
        return f"To import your financial data, {user_name}, click 'Upload CSV File' in the Transactions tab. I support most bank CSV formats and will automatically categorize your spending once that feature is ready in Phase 2!"
    
    # Financial analysis questions
    if any(word in message_lower for word in ["balance", "money", "spend", "spending", "analyze", "budget"]):
        return f"I'd love to analyze your finances, {user_name}! First, upload your transaction CSV in the Transactions tab, then I can provide insights on spending patterns, suggest budgets, and help with financial planning."
    
    # Help and capabilities
    if any(word in message_lower for word in ["help", "what can", "capabilities", "features"]):
        if user:
            return f"Hi {user_name}! I'm your GPT-2 powered finance assistant. ✨ Current features: ✅ Authentication ✅ Personalized chat ✅ Goal parsing. Coming soon: 🔜 Transaction import 🔜 ML categorization 🔜 Prophet forecasting. Try: 'Save $3000 by December' or 'Help me budget'!"
        else:
            return "I'm a GPT-2 powered finance assistant! 🤖 Sign in first, then upload transaction data for personalized insights. Try asking: 'Save $3000 by December' or 'Help me budget for groceries'."
    
    # Authentication testing
    if any(word in message_lower for word in ["auth", "login", "sign in", "account", "test auth"]):
        if user:
            return f"🎉 Authentication test successful! You're signed in as {user.email}. Your Firebase token is working perfectly with the backend. All systems ready for Phase 2 features!"
        else:
            return "❌ Not authenticated. Please sign in using the login button to test personalized features and secure data storage!"
    
    # System status questions
    if any(word in message_lower for word in ["status", "working", "online", "backend", "server"]):
        return f"✅ System Status: Backend online, GPT-2 AI active, authentication working! {f'Signed in as {user_name}' if user else 'Anonymous user'}. Phase 1 complete - ready for transaction imports in Phase 2!"
    
    # Forecasting and predictions
    if any(word in message_lower for word in ["forecast", "predict", "future", "will i", "can i afford"]):
        return f"I'll be able to forecast your spending and predict financial outcomes using Prophet ML once you upload transaction data, {user_name}! The forecasting engine will help you plan for the future with confidence."
    
    # Categories and organization
    if any(word in message_lower for word in ["categor", "organize", "sort", "group"]):
        return f"I can automatically categorize your transactions using machine learning once you upload your data, {user_name}! The system learns from your spending patterns to organize everything intelligently."
    
    # Short responses for simple inputs
    if len(message_lower.strip()) <= 3:
        if message_lower in ["y", "yes", "ok", "k"]:
            return f"Great! What would you like to work on, {user_name}? Try: 'Save money for vacation' or 'Help me budget' or 'Import transactions'."
        elif message_lower in ["n", "no"]:
            return f"No problem, {user_name}! Is there something else I can help you with? I'm here for budgeting, savings goals, and financial planning!"
    
    # Default response with more personality
    return f"I understand you said '{message}'. I'm your GPT-2 powered finance assistant ready to help with budgeting, savings goals, and financial planning! ✨ Try asking me to help you save money or upload your transaction data in the Transactions tab, {user_name}."

def build_gpt2_prompt(message: str, user: Optional[User]) -> str:
    """Build a well-structured prompt for GPT-2 to generate finance-focused responses"""
    
    # User context
    user_context = ""
    if user:
        user_name = user.display_name or user.email.split('@')[0]
        user_context = f"The user {user_name} is signed in and authenticated. "
    else:
        user_context = "The user is anonymous and should be encouraged to sign in. "
    
    # Check for specific financial intents
    financial_intent = parse_financial_intent(message)
    intent_context = ""
    
    if financial_intent:
        if financial_intent["type"] == "savings_goal":
            intent_context = f"The user wants to save ${financial_intent['amount']} for {financial_intent['purpose']} by {financial_intent['deadline']}. "
        elif financial_intent["type"] == "budget":
            intent_context = f"The user wants to budget ${financial_intent['amount']} for {financial_intent['category']}. "
    
    # Build the complete prompt
    prompt = f"""You are a helpful personal finance assistant. {user_context}{intent_context}Respond to the user's message: "{message}"

Keep your response:
- Under 100 words
- Friendly and encouraging
- Focused on personal finance
- Practical and actionable

Response:"""
    
    return prompt

@router.post("/command", response_model=ChatResponse)
async def chat_command(
    request_data: ChatRequest, 
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """GPT-2 powered chat with intelligent fallbacks"""
    
    message = request_data.message.strip()
    user_context = "authenticated" if current_user else "anonymous"
    ai_powered = False
    fallback_used = False
    model_info = None
    
    # Build GPT-2 specific prompt
    gpt2_prompt = build_gpt2_prompt(message, current_user)
    
    print(f"🎯 Attempting GPT-2 query for: {message}")
    
    # Try GPT-2 first
    try:
        llm_result = await llm_client.query(gpt2_prompt, max_tokens=80)
        print(f"📊 GPT-2 result: {llm_result['status']}")
        
        if llm_result["status"] == "success" and llm_result["text"]:
            response = llm_result["text"]
            ai_powered = True
            model_info = llm_result.get("meta", {}).get("model", "gpt2")
            print(f"✅ Using GPT-2 AI response")
        else:
            response = get_smart_fallback_response(message, current_user)
            fallback_used = True
            model_info = "fallback"
            print(f"🔄 Using enhanced fallback: {llm_result.get('text', 'unknown error')}")
            
    except Exception as e:
        print(f"❌ GPT-2 error: {e}")
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
        "ai_model": "gpt2"
    }