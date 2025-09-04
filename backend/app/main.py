from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Add this after your imports and before the lifespan function:

print("🔧 CORS Debug Information:")
print(f"   ALLOWED_ORIGINS env var: {os.getenv('ALLOWED_ORIGINS', 'NOT SET')}")
print(f"   Parsed origins: {settings.ALLOWED_ORIGINS}")

# Update your CORS middleware configuration:
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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
        "database": "✅ Connected" if settings.DATABASE_URL else "❌ Not configured",
        "port": os.getenv("PORT", "8001"),
        "host": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
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
        ],
        "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    }

if __name__ == "__main__":
    # Use Railway's PORT environment variable, fallback to 8001
    port = int(os.getenv("PORT", 8001))
    host = "0.0.0.0"
    
    print(f"🚀 Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)