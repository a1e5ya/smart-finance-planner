import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Basic app settings
    APP_NAME: str = "Smart Finance Planner"
    DEBUG: bool = True
    
    # API settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
    
    # LLM settings (optional for Phase 0)
    HF_API_KEY: str = ""
    HF_MODEL_ID: str = "microsoft/DialoGPT-medium"
    
    class Config:
        env_file = ".env"

settings = Settings()