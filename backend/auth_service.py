"""
Authentication Service - JWT Token Management
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
import bcrypt
import jwt
from sqlalchemy import select
from config import settings
from database import SessionLocal
from models import User

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user authentication, JWT tokens, and password management"""
    
    ALGORITHM = settings.JWT_ALGORITHM
    SECRET_KEY = settings.JWT_SECRET_KEY
    EXPIRATION_HOURS = settings.JWT_EXPIRATION_HOURS

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_access_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """Create a JWT access token"""
        now = datetime.utcnow()
        expire = now + timedelta(hours=AuthService.EXPIRATION_HOURS)
        
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expire,
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, AuthService.SECRET_KEY, algorithm=AuthService.ALGORITHM)
        logger.info(f"✅ Access token created for user {user_id}")
        return token

    @staticmethod
    def verify_access_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT access token"""
        try:
            payload = jwt.decode(token, AuthService.SECRET_KEY, algorithms=[AuthService.ALGORITHM])
            if payload.get("type") != "access":
                raise ValueError("Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise ValueError("Invalid token")

    @staticmethod
    def register_user(username: str, password: str, email: Optional[str] = None) -> User:
        """Register a new user"""
        session = SessionLocal()
        try:
            # Check if user already exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                raise ValueError("Username already taken")
            
            if email:
                existing_email = session.query(User).filter(User.email == email).first()
                if existing_email:
                    raise ValueError("Email already registered")
            
            # Create new user
            hashed_pwd = AuthService.hash_password(password)
            user = User(
                id=uuid4(),
                username=username,
                password_hash=hashed_pwd,
                email=email,
                created_at=datetime.utcnow()
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info(f"✅ User registered: {username}")
            return user
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Registration failed: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def login_user(username: str, password: str) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.username == username).first()
            
            if not user:
                logger.warning(f"⚠️ Login attempt with non-existent user: {username}")
                raise ValueError("Invalid credentials")
            
            if not AuthService.verify_password(password, user.password_hash):
                logger.warning(f"⚠️ Failed login attempt for user: {username}")
                raise ValueError("Invalid credentials")
            
            # Generate tokens
            access_token = AuthService.create_access_token(str(user.id))
            
            logger.info(f"✅ User logged in: {username}")
            return {
                "access_token": access_token,
                "user_id": str(user.id),
                "username": user.username,
                "email": user.email,
                "token_type": "bearer"
            }
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID"""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == UUID(user_id)).first()
            return user
        finally:
            session.close()

    @staticmethod
    def change_password(user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == UUID(user_id)).first()
            
            if not user:
                raise ValueError("User not found")
            
            if not AuthService.verify_password(old_password, user.password_hash):
                raise ValueError("Current password is incorrect")
            
            user.password_hash = AuthService.hash_password(new_password)
            session.commit()
            
            logger.info(f"✅ Password changed for user {user_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Password change failed: {e}")
            raise
        finally:
            session.close()
