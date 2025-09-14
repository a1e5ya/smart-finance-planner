from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import sys
import os

# Add parent directory to path so we can import app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import settings FIRST
from app.core.config import settings

# NOW we can use settings for debug output
print("🔧 CORS Debug Information:")
print(f"   ALLOWED_ORIGINS env var: {os.getenv('ALLOWED_ORIGINS', 'NOT SET')}")
print(f"   Parsed origins: {settings.ALLOWED_ORIGINS}")

# Import other modules after settings
from app.routers import auth, chat
from app.routers import transactions_router, transaction_import_router, transaction_analytics_router
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
    description="Phase 1 - Transaction Management Complete",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware with debug info
print(f"🌐 Setting up CORS with origins: {settings.ALLOWED_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers - Updated to use new separated routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

# Transaction routers - separated by functionality
app.include_router(transactions_router.router, prefix="/transactions", tags=["transactions"])
app.include_router(transaction_import_router.router, prefix="/transactions", tags=["transaction-import"])
app.include_router(transaction_analytics_router.router, prefix="/transactions/analytics", tags=["transaction-analytics"])

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "phase": "1 - Transaction Management Complete",
        "features": [
            "firebase_auth", 
            "neon_database", 
            "user_management", 
            "audit_logging",
            "personalized_chat",
            "csv_import",
            "auto_categorization",
            "transaction_crud",
            "transaction_analytics",
            "bulk_operations",
            "import_management"
        ],
        "database": "✅ Connected" if settings.DATABASE_URL else "❌ Not configured",
        "cors_origins": settings.ALLOWED_ORIGINS,
        "port": os.getenv("PORT", "8001"),
        "host": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local",
        "transaction_endpoints": [
            "/transactions/list - Get transactions with filters",
            "/transactions/summary - Get transaction statistics", 
            "/transactions/review - Get transactions needing review",
            "/transactions/categorize/{id} - Categorize transaction",
            "/transactions/bulk-categorize - Bulk categorize transactions",
            "/transactions/{id} - Update/Delete transaction",
            "/transactions/import - Upload CSV files",
            "/transactions/create-default-mappings - Create category mappings",
            "/transactions/import-history - View import history",
            "/transactions/batch/{id} - Manage import batches",
            "/transactions/analytics/spending-trends - Spending analysis",
            "/transactions/analytics/merchant-analysis - Merchant patterns",
            "/transactions/analytics/category-breakdown - Category analysis",
            "/transactions/analytics/monthly-summary - Monthly reports",
            "/transactions/analytics/financial-health - Health metrics",
            "/transactions/analytics/compare-periods - Period comparison"
        ]
    }

@app.get("/")
async def root():
    return {
        "message": "Smart Finance Planner API",
        "phase": "Phase 1 - Transaction Management Complete",
        "endpoints": [
            "/health - System status",
            "/auth/verify - Verify Firebase token",
            "/auth/me - Get user profile", 
            "/chat/command - Send chat message",
            "/transactions/* - Transaction management endpoints",
            "/docs - API documentation"
        ],
        "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local",
        "features_completed": [
            "✅ User authentication with Firebase",
            "✅ Chat interface with Groq AI",
            "✅ CSV transaction import with auto-categorization",
            "✅ Transaction CRUD operations",
            "✅ Bulk categorization and management", 
            "✅ Advanced analytics and reporting",
            "✅ Import batch management",
            "✅ Financial health metrics",
            "✅ Audit logging for all operations"
        ]
    }

if __name__ == "__main__":
    # Use Railway's PORT environment variable, fallback to 8001
    port = int(os.getenv("PORT", 8001))
    host = "0.0.0.0"
    
    print(f"🚀 Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)