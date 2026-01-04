from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: list = []

class User(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    disabled: bool = False

class UserInDB(User):
    hashed_password: str

class AuthService:
    """
    Authentication and Authorization service with RBAC
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        
        # Role-based permissions
        self.role_permissions = {
            'admin': ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_alerts', 'configure_system'],
            'analyst': ['read', 'write', 'view_logs', 'manage_alerts'],
            'viewer': ['read', 'view_logs'],
            'api': ['read', 'write']
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            
            if username is None:
                return None
            
            permissions = self.role_permissions.get(role, [])
            
            return TokenData(username=username, role=role, permissions=permissions)
        
        except JWTError:
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password"""
        # In production, fetch from database
        user = self._get_user_from_db(username)
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def _get_user_from_db(self, username: str) -> Optional[UserInDB]:
        """Get user from database (mock implementation)"""
        # Mock users - replace with actual database query
        mock_users = {
            "admin": UserInDB(
                username="admin",
                email="admin@fortifai.com",
                full_name="System Administrator",
                role="admin",
                hashed_password=self.get_password_hash("admin123")
            ),
            "analyst": UserInDB(
                username="analyst",
                email="analyst@fortifai.com",
                full_name="Security Analyst",
                role="analyst",
                hashed_password=self.get_password_hash("analyst123")
            )
        }
        
        return mock_users.get(username)
    
    def check_permission(self, token_data: TokenData, required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in token_data.permissions
    
    def login(self, username: str, password: str) -> Optional[Token]:
        """Login and return tokens"""
        user = self.authenticate_user(username, password)
        
        if not user:
            return None
        
        access_token = self.create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        refresh_token = self.create_refresh_token(
            data={"sub": user.username, "role": user.role}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token"""
        token_data = self.decode_token(refresh_token)
        
        if not token_data:
            return None
        
        new_access_token = self.create_access_token(
            data={"sub": token_data.username, "role": token_data.role}
        )
        
        return new_access_token


# Dependency for protected routes
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Dependency to get current authenticated user"""
    auth_service = AuthService()
    token_data = auth_service.decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

def require_permission(permission: str):
    """Decorator to require specific permission"""
    async def permission_checker(current_user: TokenData = Depends(get_current_user)):
        auth_service = AuthService()
        
        if not auth_service.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        
        return current_user
    
    return permission_checker
