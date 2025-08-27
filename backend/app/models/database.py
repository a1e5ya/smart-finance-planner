from sqlalchemy import create_engine, Column, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Can be null for anonymous users
    firebase_uid = Column(String, nullable=True)
    entity = Column(String, nullable=False)  # 'chat', 'auth', 'system'
    action = Column(String, nullable=False)  # 'message', 'login', 'error'
    details = Column(JSON, nullable=True)    # Store request/response data
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()