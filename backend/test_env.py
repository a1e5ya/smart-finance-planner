#!/usr/bin/env python3
"""
Test script to check if environment variables are loading correctly
"""

import os
from dotenv import load_dotenv

print("Testing environment variable loading...")

# Check if .env file exists
env_path = ".env"
if os.path.exists(env_path):
    print(f"✅ Found .env file at: {os.path.abspath(env_path)}")
else:
    print(f"❌ .env file not found at: {os.path.abspath(env_path)}")
    print("Make sure your .env file is in the backend/ directory")
    exit(1)

# Load environment variables
load_dotenv()

# Test DATABASE_URL
database_url = os.getenv("DATABASE_URL")
if database_url:
    print(f"✅ DATABASE_URL loaded: {database_url[:50]}...")
else:
    print("❌ DATABASE_URL not found in environment")

# Test Firebase credentials
firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
if firebase_json and len(firebase_json) > 10:
    print("✅ FIREBASE_SERVICE_ACCOUNT_JSON loaded")
else:
    print("❌ FIREBASE_SERVICE_ACCOUNT_JSON not found or empty")

# Test CORS origins
cors_origins = os.getenv("ALLOWED_ORIGINS")
if cors_origins:
    print(f"✅ ALLOWED_ORIGINS loaded: {cors_origins}")
else:
    print("❌ ALLOWED_ORIGINS not found")

print("\n--- Summary ---")
print("If all variables show ✅, your environment is configured correctly")
print("If any show ❌, check your .env file content and location")