from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn
import time
import os
from typing import Optional

# Import our modules
from app.models.database import get_db, create_tables, User, AuditLog
from app.auth.firebase_auth import initialize_firebase, get_current_user, log_audit, AuthUser

# Initialize Firebase
initialize_firebase()

# Create database tables
create_tables()

app = FastAPI(
    title="Smart Personal Finance Planner - Phase 1",
    description="Auth + Database + Audit Logging",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://*.vercel.app"  # For deployment
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    phase: str = "1"
    user: Optional[str] = None

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """Health check with database connection test"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "phase": "1 - Auth + Database + Audit",
        "features": ["firebase_auth", "neon_database", "audit_logging"],
        "database": db_status,
        "message": "Phase 1 backend with authentication and database!"
    }

@app.post("/chat/command")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Chat endpoint with authentication and audit logging"""
    
    message = chat_request.message.lower()
    user_display = current_user.display_name if current_user else "Anonymous"
    
    # Generate response (same logic as Phase 0)
    if "dashboard" in message or "overview" in message:
        response = f"Hello {user_display}! Here's your financial dashboard with key metrics and spending trends."
    elif "save" in message and ("december" in message or "vacation" in message or any(c.isdigit() for c in message)):
        response = f"Great savings goal, {user_display}! Once you import transaction data, I'll help you create a realistic plan to reach it."
    elif "import" in message or "upload" in message or "csv" in message:
        response = f"Ready to import your data, {user_display}! Upload your bank CSV in the Transactions tab for automatic categorization."
    elif "balance" in message or "spend" in message or "expense" in message:
        response = f"I'd love to analyze your spending, {user_display}, but I need your transaction data first. Please upload a CSV file!"
    elif "auth" in message or "login" in message:
        if current_user:
            response = f"You're already authenticated as {user_display} ({current_user.email})! 🎉"
        else:
            response = "Please sign in using the authentication system to access personalized features."
    elif "help" in message or "what can" in message:
        response = f"Hi {user_display}! I can help with goal setting, transaction analysis, and financial planning. Try: 'Import transactions', 'Save 3000 by December', or sign in for personalized features!"
    else:
        response = f"I understand, {user_display}! '{chat_request.message}' - I'm getting smarter with each phase. Try uploading transaction data or setting a savings goal!"
    
    # Log chat interaction to audit trail
    await log_audit(
        db=db,
        firebase_uid=current_user.firebase_uid if current_user else None,
        entity="chat",
        action="message",
        details={
            "request": chat_request.message,
            "response": response,
            "user_authenticated": current_user is not None
        },
        request=request
    )
    
    return ChatResponse(
        response=response,
        timestamp=time.strftime("%H:%M:%S"),
        user=user_display
    )

@app.get("/auth/me")
async def get_current_user_info(
    current_user: AuthUser = Depends(get_current_user)
):
    """Get current user information"""
    if not current_user:
        return {"authenticated": False}
    
    return {
        "authenticated": True,
        "firebase_uid": current_user.firebase_uid,
        "email": current_user.email,
        "display_name": current_user.display_name
    }

@app.get("/admin/audit")
async def get_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: AuthUser = Depends(get_current_user)
):
    """Get recent audit logs (admin endpoint)"""
    if not current_user:
        return {"error": "Authentication required"}
    
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(logs),
        "logs": [
            {
                "id": str(log.id),
                "entity": log.entity,
                "action": log.action,
                "firebase_uid": log.firebase_uid,
                "details": log.details,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    }

if __name__ == "__main__":
    uvicorn.run("server_v2:app", host="0.0.0.0", port=8001, reload=True)