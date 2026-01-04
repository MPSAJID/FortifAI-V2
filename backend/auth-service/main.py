"""
FortifAI Authentication Service
Enhanced version with API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic Models
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = []

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "viewer"

class UserResponse(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    disabled: bool = False

class UserInDB(UserResponse):
    hashed_password: str

# In-memory user store (replace with database in production)
fake_users_db = {}

# Role permissions
ROLE_PERMISSIONS = {
    'admin': ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_alerts', 'configure_system'],
    'analyst': ['read', 'write', 'view_logs', 'manage_alerts'],
    'viewer': ['read', 'view_logs'],
    'api': ['read', 'write']
}

class AuthService:
    """Authentication and Authorization service"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            role = payload.get("role")
            
            if username is None:
                return None
            
            permissions = ROLE_PERMISSIONS.get(role, [])
            return TokenData(username=username, role=role, permissions=permissions)
        except JWTError:
            return None
    
    @staticmethod
    def get_user(username: str) -> Optional[UserInDB]:
        if username in fake_users_db:
            user_data = fake_users_db[username]
            return UserInDB(**user_data)
        return None
    
    @staticmethod
    def create_user(user_data: UserCreate) -> UserInDB:
        hashed_password = AuthService.get_password_hash(user_data.password)
        user = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "disabled": False,
            "hashed_password": hashed_password
        }
        fake_users_db[user_data.username] = user
        return UserInDB(**user)
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
        user = AuthService.get_user(username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user


# FastAPI Application
app = FastAPI(title="FortifAI Auth Service", version="1.0.0")
auth_service = AuthService()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = auth_service.decode_token(token)
    if token_data is None:
        raise credentials_exception
    return token_data

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}

@app.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    if user_data.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    user = auth_service.create_user(user_data)
    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        disabled=user.disabled
    )

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user.username, "role": user.role}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@app.get("/me", response_model=UserResponse)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    user = auth_service.get_user(current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        disabled=user.disabled
    )

@app.post("/verify")
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    return {
        "valid": True,
        "username": current_user.username,
        "role": current_user.role,
        "permissions": current_user.permissions
    }

# Create default admin user on startup
@app.on_event("startup")
async def create_default_admin():
    if "admin" not in fake_users_db:
        auth_service.create_user(UserCreate(
            username="admin",
            email="admin@fortifai.io",
            password="admin123",  # Change in production!
            full_name="System Administrator",
            role="admin"
        ))
        print("Default admin user created")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)
