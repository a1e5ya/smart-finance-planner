# Save as backend/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import time

app = FastAPI(title="Smart Personal Finance Planner - Phase 0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    phase: str = "0"

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "phase": "0 - Chat Skeleton",
        "features": ["chat", "fallback_responses"],
        "message": "Phase 0 backend working!"
    }

@app.post("/chat/command")
def chat(request: ChatRequest):
    """Phase 0 chat with intelligent fallback responses"""
    message = request.message.lower()
    
    # Smart responses based on your design
    if "dashboard" in message or "overview" in message:
        response = "Here's your financial dashboard with key metrics, spending trends, and goal progress. This gives you a complete overview of your financial health at a glance."
    elif "save" in message and ("december" in message or "vacation" in message or any(c.isdigit() for c in message)):
        response = "I can see you want to create a savings goal! I can't create goals yet since you haven't imported any transaction data. Please upload a CSV in the Transactions tab first, then I'll help you set up realistic savings targets."
    elif "import" in message or "upload" in message or "csv" in message:
        response = "Great! Click 'Upload CSV File' in the Transactions tab to import your bank data. I support most common bank CSV formats and will help categorize everything automatically."
    elif "balance" in message or "spend" in message or "expense" in message:
        response = "I can't analyze your transactions yet — please upload a CSV in the Transactions tab to get started with personalized insights and forecasting."
    elif "forecast" in message or "predict" in message:
        response = "Forecasting with Prophet ML will be available once you have transaction history. Upload your bank CSV first, and I'll predict your spending patterns and goal achievement probability."
    elif "categor" in message:
        response = "I've opened the Categories tab. You can create, split, and merge spending categories here. The system will auto-categorize transactions using ML once you have data imported."
    elif "timeline" in message or "chart" in message or "visual" in message:
        response = "Here's your financial timeline view! Once you import transactions, you'll see spending trends, income patterns, and goal progress. The timeline extends 5 years into the future with ML forecasts."
    elif "help" in message or "what can" in message:
        response = "I'm your AI finance assistant! Right now I can guide you through the app, but I need transaction data to provide insights. Try: 'Import transactions', 'Save 3000 by December', or 'Show categories'. Everything starts with uploading your bank CSV!"
    else:
        response = f"I understand you said '{request.message}'. I can't fully analyze that yet since this is Phase 0. Try uploading transaction data first, or ask me to 'Save money for a goal' or 'Show categories'. I'll be much more helpful once you have financial data imported!"
    
    return ChatResponse(
        response=response,
        timestamp=time.strftime("%H:%M:%S")
    )

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)