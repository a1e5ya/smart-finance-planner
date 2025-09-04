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

# Dependency to get current user from Firebase token
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    request: Request = None
) -> Optional[User]:
    """Extract user from Firebase JWT token"""
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Get Firebase app
        app = get_firebase_app()
        
        # Verify the token
        decoded_token = firebase_auth.verify_id_token(token, app=app)
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')
        display_name = decoded_token.get('name', '')
        
        # Check if user exists in our database
        result = await db.execute(
            select(User).where(User.firebase_uid == firebase_uid)
        )
        user = result.scalar_one_or_none()
        
        # Create user if doesn't exist
        if not user:
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Log user creation
            audit = AuditLog(
                user_id=user.id,
                firebase_uid=firebase_uid,
                entity="auth",
                action="signup",
                details={
                    "email": email,
                    "display_name": display_name,
                    "method": "firebase"
                },
                ip_address=getattr(request, 'client', {}).get('host') if request else None,
                user_agent=getattr(request, 'headers', {}).get('user-agent') if request else None
            )
            db.add(audit)
            await db.commit()
            
            print(f"👤 New user created: {email} ({firebase_uid[:8]}...)")
        else:
            # Update user info if changed
            updated = False
            if user.email != email:
                user.email = email
                updated = True
            if user.display_name != display_name:
                user.display_name = display_name
                updated = True
                
            if updated:
                await db.commit()
                await db.refresh(user)
        
        return user
        
    except Exception as e:
        print(f"❌ Auth error: {e}")
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
            "name": decoded_token.get('name')
        }
    except Exception as e:
        return {"error": str(e)}