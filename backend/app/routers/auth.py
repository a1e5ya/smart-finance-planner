from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class AuthResponse(BaseModel):
    message: str
    phase: str = "0"

@router.post("/verify")
async def verify_user():
    """Phase 0 auth placeholder"""
    return AuthResponse(
        message="Auth will be connected to Firebase in next phase"
    )