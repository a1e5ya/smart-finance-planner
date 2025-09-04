#!/usr/bin/env python3
"""
Database initialization script for Smart Finance Planner
Run this once to set up your NeonDB tables
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

# Check if DATABASE_URL is available
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not found in environment variables")
    print("🔍 Make sure you have a .env file with DATABASE_URL set")
    print("📁 Your .env file should be in the backend/ directory")
    sys.exit(1)

print(f"📍 Found DATABASE_URL: {DATABASE_URL[:50]}...")

try:
    from app.models.database import init_database, async_engine
    from app.core.config import settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔍 Make sure you're running this from the backend/ directory")
    sys.exit(1)

async def main():
    print("🚀 Initializing Smart Finance Planner Database...")
    print(f"📍 Database: {settings.DATABASE_URL[:50]}...")
    
    # Initialize database
    success = await init_database()
    
    if success:
        print("✅ Database initialization complete!")
        print("\n📋 Tables created:")
        print("  - users (id, firebase_uid, email, display_name, created_at)")
        print("  - audit_log (id, user_id, entity, action, details, created_at)")
        print("\n🎯 Next steps:")
        print("  1. Start your backend: python main.py")
        print("  2. Test auth: POST /auth/verify with Firebase token")
        print("  3. Test chat: POST /chat/command")
        
    else:
        print("❌ Database initialization failed!")
        print("🔍 Check your DATABASE_URL in .env file")
        sys.exit(1)
    
    # Close the engine
    await async_engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())