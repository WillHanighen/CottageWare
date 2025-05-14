"""
Authentication module for CottageWare
Handles user authentication, JWT tokens, and Google OAuth
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
from fastapi_sso.sso.google import GoogleSSO
from models import User
from database import SessionLocal

# Load environment variables
load_dotenv()

# Constants
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key_replace_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Google SSO setup
google_sso = GoogleSSO(
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", ""),
    allow_insecure_http=True
)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password verification
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Password hashing
def get_password_hash(password):
    return pwd_context.hash(password)

# Get user by username
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

# Get user by email
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Get user by OAuth ID
def get_user_by_oauth(db: Session, oauth_provider: str, oauth_id: str):
    return db.query(User).filter(
        User.oauth_provider == oauth_provider,
        User.oauth_id == oauth_id
    ).first()

# Authenticate user
def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not user.hashed_password:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user

# Get current active user
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Create new user
def create_user(db: Session, username: str, email: str, password: Optional[str] = None, 
                oauth_provider: Optional[str] = None, oauth_id: Optional[str] = None,
                avatar_url: Optional[str] = None):
    hashed_password = get_password_hash(password) if password else None
    is_oauth = oauth_provider is not None and oauth_id is not None
    
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_oauth=is_oauth,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        avatar_url=avatar_url
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Get or create OAuth user
def get_or_create_oauth_user(db: Session, oauth_provider: str, oauth_id: str, 
                            email: str, username: str, avatar_url: Optional[str] = None):
    # Check if user exists by OAuth ID
    user = get_user_by_oauth(db, oauth_provider, oauth_id)
    if user:
        return user
    
    # Check if user exists by email
    user = get_user_by_email(db, email)
    if user:
        # Update OAuth info for existing user
        user.is_oauth = True
        user.oauth_provider = oauth_provider
        user.oauth_id = oauth_id
        if avatar_url:
            user.avatar_url = avatar_url
        db.commit()
        db.refresh(user)
        return user
    
    # Create new user
    return create_user(
        db=db,
        username=username,
        email=email,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        avatar_url=avatar_url
    )

# Optional current user (for templates)
async def get_optional_user(request: Request, db: Session = Depends(get_db)):
    """Get the current user if logged in, otherwise return None"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        
        user = get_user_by_username(db, username)
        if user is None:
            return None
        
        return user
    except JWTError:
        return None

# Admin required dependency
def admin_required():
    """Dependency to check if user is an admin (tier 4 or higher)"""
    async def _admin_required(current_user: User = Depends(get_current_active_user)):
        # Check if user has admin privileges (tier 4 or higher)
        if not current_user or not current_user.profile or current_user.profile.account_tier < 4:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough privileges",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return current_user
    return _admin_required
