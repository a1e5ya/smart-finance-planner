from sqlalchemy import Column, String, DateTime, Text, JSON, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL and convert to async
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables. Check your .env file.")

# Convert NeonDB SSL parameters for asyncpg
def convert_url_for_asyncpg(url: str) -> str:
    """Convert psycopg2 URL to asyncpg compatible URL"""
    async_url = url.replace("postgresql://", "postgresql+asyncpg://")
    
    # Handle NeonDB SSL parameters
    if "sslmode=require" in async_url:
        async_url = async_url.replace("sslmode=require", "ssl=require")
    
    if "channel_binding=require" in async_url:
        # Remove channel_binding as asyncpg doesn't support it
        async_url = async_url.replace("&channel_binding=require", "")
        async_url = async_url.replace("?channel_binding=require&", "?")
        async_url = async_url.replace("?channel_binding=require", "")
    
    return async_url

ASYNC_DATABASE_URL = convert_url_for_asyncpg(DATABASE_URL)

print(f"Original URL: {DATABASE_URL[:80]}...")
print(f"Async URL: {ASYNC_DATABASE_URL[:80]}...")

# Async engine for production
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Sync engine for table creation (Alembic compatibility)
sync_engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # FK to users.id
    firebase_uid = Column(String, nullable=True)  # Backup identifier
    entity = Column(String, nullable=False)  # 'chat', 'auth', 'system'
    action = Column(String, nullable=False)  # 'message', 'login', 'signup', 'error'
    details = Column(JSON, nullable=True)    # Store request/response data
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Sync version for initialization
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables (sync - for startup)
def create_tables():
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("✅ Database tables created successfully!")

# Initialize database
async def init_database():
    """Initialize database connection and create tables if needed"""
    try:
        # Test connection
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
        
        # Create tables (sync operation)
        create_tables()
        
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False