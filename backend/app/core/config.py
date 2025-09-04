import os
import json
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Simple settings class without pydantic complexity"""
    
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        
        # Firebase
        self.FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "{}")
        
        # App
        self.APP_NAME = "Smart Finance Planner API"
        self.VERSION = "1.0.0"
        self.DEBUG = True
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse CORS origins from environment"""
        cors_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,https://your-app.vercel.app")
        return [origin.strip() for origin in cors_env.split(",")]
    
    @property
    def firebase_credentials(self) -> dict:
        """Parse Firebase service account JSON"""
        try:
            return json.loads(self.FIREBASE_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError:
            print("Warning: Could not parse Firebase credentials")
            return {}

settings = Settings()