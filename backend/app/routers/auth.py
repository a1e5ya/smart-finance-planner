from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
import json
import os

from ..models.database import get_db, User, AuditLog
from ..core.config import settings

router = APIRouter()

# Initialize Firebase Admin (singleton pattern)
_firebase_app = None

def get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        try:
            # Try to get existing app
            _firebase_app = firebase_admin.get_app()
        except ValueError:
            # App doesn't exist, create it
            cred_dict = settings.firebase_credentials
            if not cred_dict:
                raise ValueError("Firebase credentials not found in environment")
            
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized!")
    
    return _firebase_app

# Pydantic models
class AuthResponse(BaseModel):
    message: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    phase: str = "1"

class UserResponse(BaseModel):
    id: str
    firebase_uid: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: str

# Simplified dependency to get current user from Firebase token
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Extract user from Firebase JWT token - simplified version"""
    
    # Allow anonymous access for now - just log it
    if not authorization or not authorization.startswith("Bearer "):
        print("⚠️ No authorization header - allowing anonymous access")
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        print(f"🔑 Verifying Firebase token: {token[:20]}...")
        
        # Get Firebase app
        app = get_firebase_app()
        
        # Verify the token
        decoded_token = firebase_auth.verify_id_token(token, app=app)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')
        display_name = decoded_token.get('name', '')
        
        print(f"✅ Token verified for user: {email} ({firebase_uid[:8]}...)")
        
        # Check if user exists in our database
        result = await db.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        user = result.scalar_one_or_none()
        
        # Create user if doesn't exist
        if not user:
            print(f"👤 Creating new user: {email}")
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"✅ User created with ID: {user.id}")
        else:
            # Update user info if changed
            if user.email != email or user.display_name != display_name:
                print(f"📝 Updating user info for: {email}")
                user.email = email
                user.display_name = display_name
                await db.commit()
                await db.refresh(user)
        
        return user
        
    except Exception as e:
        print(f"❌ Firebase token verification failed: {e}")
        # Don't raise exception - just return None for anonymous access
        return None

@router.post("/verify", response_model=AuthResponse)
async def verify_user(
    current_user: Optional[User] = Depends(get_current_user)
):
    """Verify Firebase token and return user info"""
    
    if not current_user:
        return AuthResponse(
            message="No valid authentication token provided"
        )
    
    return AuthResponse(
        message=f"✅ Authenticated as {current_user.email}",
        user_id=str(current_user.id),
        email=current_user.email
    )

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return UserResponse(
        id=str(current_user.id),
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at.isoformat()
    )

@router.post("/debug")
async def debug_auth(authorization: Optional[str] = Header(None)):
    """Debug endpoint to test Firebase token"""
    
    if not authorization:
        return {"error": "No Authorization header"}
    
    if not authorization.startswith("Bearer "):
        return {"error": "Invalid Authorization format"}
    
    token = authorization.replace("Bearer ", "")
    
    try:
        app = get_firebase_app()
        decoded_token = firebase_auth.verify_id_token(token, app=app)
        return {
            "success": True,
            "uid": decoded_token['uid'],
            "email": decoded_token.get('email'),
            "name": decoded_token.get('name'),
            "token_preview": token[:20] + "..."
        }
    except Exception as e:
        return {"error": str(e), "token_preview": token[:20] + "..."}