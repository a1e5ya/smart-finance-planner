# backend/app/core/database.py
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
import os

# Use SQLite for Phase 0 (simple, no external dependencies)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finance_app.db")

# Create engine with proper SQLite settings
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Phase 0 Models - Simple but functional
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="demo-user")
    user_message = Column(Text)
    bot_response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Initialize database
def init_database():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test connection function
def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        # Try a simple query
        result = db.execute("SELECT 1").fetchone()
        db.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False