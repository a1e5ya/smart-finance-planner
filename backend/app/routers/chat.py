from fastapi import APIRouter
from pydantic import BaseModel
import time

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    phase: str = "0"

@router.post("/command", response_model=ChatResponse)
async def chat_command(request: ChatRequest):
    """Phase 0 chat with fallback responses"""
    
    message = request.message.lower()
    
    # Phase 0 response logic (from your design)
    if "dashboard" in message or "overview" in message:
        response = "Here's your financial dashboard with key metrics, spending trends, and goal progress."
    elif "save" in message and ("december" in message or "vacation" in message or any(c.isdigit() for c in message)):
        response = "I can see you want to create a savings goal! I can't create goals yet since you haven't imported any transaction data. Please upload a CSV first."
    elif "import" in message or "upload" in message or "csv" in message:
        response = "Great! Click 'Upload CSV File' in the Transactions tab to import your bank data. I support most common bank CSV formats."
    elif "balance" in message or "spend" in message or "expense" in message:
        response = "I can't analyze your transactions yet — please upload a CSV in the Transactions tab to get started."
    elif "help" in message:
        response = "I'm your AI finance assistant! Try: 'Import transactions', 'Save 3000 by December', or 'Show categories'. Everything starts with uploading your bank CSV!"
    else:
        response = f"I understand you said '{request.message}'. I can't fully analyze that yet since this is Phase 0. Try uploading transaction data first!"
    
    return ChatResponse(
        response=response,
        timestamp=time.strftime("%H:%M:%S")
    )