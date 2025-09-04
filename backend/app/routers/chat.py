from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import time

from ..models.database import get_db, User, AuditLog
from .auth import get_current_user

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    user_context: str
    phase: str = "1"

async def log_chat_interaction(
    db: AsyncSession,
    user: Optional[User],
    message: str,
    response: str,
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
            "authenticated": user is not None,
            "user_email": user.email if user else None
        },
        ip_address=getattr(request.client, 'host', None) if hasattr(request, 'client') else None,
        user_agent=request.headers.get('user-agent', None) if hasattr(request, 'headers') else None
    )
    
    db.add(audit)
    await db.commit()

@router.post("/command", response_model=ChatResponse)
async def chat_command(
    request_data: ChatRequest, 
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enhanced chat with user context and database logging"""
    
    message = request_data.message.lower()
    user_context = "authenticated" if current_user else "anonymous"
    
    # Personalized responses based on authentication
    if current_user:
        user_name = current_user.display_name or current_user.email.split('@')[0] if current_user.email else "there"
        user_greeting = f"Hello {user_name}! 👋"
    else:
        user_name = "there"
        user_greeting = "Hello there! 👋"
    
    # Enhanced response logic with user context
    if "hello" in message or "hi" in message:
        if current_user:
            response = f"{user_greeting} Great to see you signed in. Your Firebase authentication is working perfectly!"
        else:
            response = f"{user_greeting} You're chatting as an anonymous user. Sign in to unlock personalized features!"
            
    elif "test auth" in message:
        if current_user:
            response = f"🔐 Authentication Test PASSED ✅\nUser: {current_user.email}\nUID: {current_user.firebase_uid[:12]}...\nDatabase: Connected\nAll systems operational!"
        else:
            response = "🔐 Authentication Test: You're not signed in. Please sign in to test the auth flow."
            
    elif "dashboard" in message or "overview" in message:
        if current_user:
            response = f"Here's your personalized financial dashboard, {user_name}! Ready to load your spending trends and goal progress."
        else:
            response = "Here's the financial dashboard overview. Sign in to see your personalized metrics and spending trends."
            
    elif "save" in message and ("december" in message or "vacation" in message or any(c.isdigit() for c in message)):
        if current_user:
            response = f"I can see you want to create a savings goal, {user_name}! Goal parsing is working. I'll need your transaction history first - please upload a CSV to get started."
        else:
            response = "I understand you want to create a savings goal! Please sign in first, then upload your transaction data to create personalized financial goals."
            
    elif "import" in message or "upload" in message or "csv" in message:
        if current_user:
            response = f"Great, {user_name}! Click 'Upload CSV File' in the Transactions tab. Your imported data will be securely linked to your account."
        else:
            response = "CSV import is available! Please sign in first so I can securely save your financial data to your account."
            
    elif "balance" in message or "spend" in message or "expense" in message:
        if current_user:
            response = f"I'd love to analyze your spending patterns, {user_name}! Please upload your transaction CSV first so I can give you personalized insights."
        else:
            response = "I can't analyze transactions for anonymous users. Please sign in and upload a CSV to get personalized spending insights."
            
    elif "help" in message:
        if current_user:
            response = f"Hi {user_name}! I'm your personal AI finance assistant. Try: 'Import transactions', 'Save 3000 by December', or 'Show categories'. Your data is securely stored in your account."
        else:
            response = "I'm your AI finance assistant! Sign in to unlock personalized features. Then try: 'Import transactions', 'Save 3000 by December', or 'Show categories'."
            
    else:
        # Generic response with context awareness
        if current_user:
            response = f"I understand you said '{request_data.message}', {user_name}. I'm ready to help with your finances once you upload transaction data!"
        else:
            response = f"I understand you said '{request_data.message}'. Sign in first, then upload transaction data to get personalized financial insights!"
    
    # Create response object
    chat_response = ChatResponse(
        response=response,
        timestamp=time.strftime("%H:%M:%S"),
        user_context=user_context
    )
    
    # Log the interaction to database
    await log_chat_interaction(db, current_user, request_data.message, response, request)
    
    # Console logging for development
    if current_user:
        print(f"💬 {user_name}: {request_data.message}")
        print(f"🤖 Response: {response[:50]}...")
    else:
        print(f"💬 Anonymous: {request_data.message}")
        print(f"🤖 Response: {response[:50]}...")
    
    return chat_response

@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's recent chat history (requires auth)"""
    
    if not current_user:
        return {"error": "Authentication required"}
    
    # This will be implemented in later phases
    return {
        "message": f"Chat history for {current_user.email} - coming in Phase 2!",
        "user_id": str(current_user.id)
    }