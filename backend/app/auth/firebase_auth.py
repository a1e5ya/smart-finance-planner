import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import json

from app.models.database import get_db, User, AuditLog

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Try to load from file first
        service_account_path = "firebase-service-account.json"
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
        else:
            # Fallback to environment variable (for deployment)
            service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            if service_account_json:
                service_account_dict = json.loads(service_account_json)
                cred = credentials.Certificate(service_account_dict)
            else:
                raise ValueError("No Firebase service account found. Add firebase-service-account.json or FIREBASE_SERVICE_ACCOUNT_JSON env var.")
        
        firebase_admin.initialize_app(cred)

security = HTTPBearer(auto_error=False)

class AuthUser:
    def __init__(self, firebase_uid: str, email: str, display_name: str = None):
        self.firebase_uid = firebase_uid
        self.email = email
        self.display_name = display_name

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None
) -> AuthUser:
    """
    Extract user from Firebase JWT token and ensure user exists in database
    """
    if not credentials:
        # For Phase 1, allow anonymous users but log them
        await log_audit(
            db=db, 
            entity="auth", 
            action="anonymous_access",
            request=request
        )
        return None
    
    try:
        # Verify Firebase token
        decoded_token = auth.verify_id_token(credentials.credentials)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email")
        display_name = decoded_token.get("name")
        
        # Get or create user in database
        db_user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
        if not db_user:
            db_user = User(
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Log new user creation
            await log_audit(
                db=db,
                firebase_uid=firebase_uid,
                user_id=str(db_user.id),
                entity="auth",
                action="user_created",
                details={"email": email, "display_name": display_name},
                request=request
            )
        
        # Log successful authentication
        await log_audit(
            db=db,
            firebase_uid=firebase_uid,
            user_id=str(db_user.id),
            entity="auth",
            action="authenticated",
            request=request
        )
        
        return AuthUser(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name or db_user.display_name
        )
        
    except Exception as e:
        # Log authentication failure
        await log_audit(
            db=db,
            entity="auth",
            action="auth_failed",
            details={"error": str(e)},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

async def log_audit(
    db: Session,
    entity: str,
    action: str,
    firebase_uid: str = None,
    user_id: str = None,
    details: dict = None,
    request: Request = None
):
    """Log audit events to database"""
    audit_entry = AuditLog(
        firebase_uid=firebase_uid,
        user_id=user_id,
        entity=entity,
        action=action,
        details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(audit_entry)
    db.commit()