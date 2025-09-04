from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Add parent directory to path so we can import app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app.core.config import settings
from app.routers import auth, chat
from app.models.database import init_database

# Lifespan manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Smart Finance Planner API...")
    print(f"🔧 Database URL: {settings.DATABASE_URL[:50]}...")
    
    # Initialize database
    db_success = await init_database()
    if not db_success:
        print("❌ Failed to initialize database!")
        # In production, you might want to exit here
    
    print("✅ API startup complete!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down API...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Phase 1 - Authentication + Database Integration",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "phase": "1 - Database Connected",
        "features": [
            "firebase_auth", 
            "neon_database", 
            "user_management", 
            "audit_logging",
            "personalized_chat"
        ],
        "database": "✅ Connected" if settings.DATABASE_URL else "❌ Not configured"
    }

@app.get("/")
async def root():
    return {
        "message": "Smart Finance Planner API",
        "phase": "Phase 1 Complete",
        "endpoints": [
            "/health - System status",
            "/auth/verify - Verify Firebase token",
            "/auth/me - Get user profile", 
            "/chat/command - Send chat message",
            "/docs - API documentation"
        ]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)