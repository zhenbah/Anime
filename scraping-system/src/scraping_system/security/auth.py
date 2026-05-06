import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.scraping_system.core.config import settings
from src.scraping_system.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class SecurityManager:
    """Handles authentication, authorization, and security"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password"""
        return pwd_context.verify(password, hashed)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            
            if username is None:
                return None
            
            return {"username": username}
        except JWTError:
            logger.error("Invalid token")
            return None
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user"""
        user = await self.db_service.db.users.find_one({"username": username})
        
        if not user:
            return None
        
        if not self.verify_password(password, user["password"]):
            return None
        
        return {"username": user["username"], "id": str(user["_id"])}
    
    async def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Create new user"""
        # Check if user exists
        existing = await self.db_service.db.users.find_one({"$or": [{"username": username}, {"email": email}]})
        
        if existing:
            raise ValueError("User already exists")
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        result = await self.db_service.db.users.insert_one(user_data)
        
        return {
            "id": str(result.inserted_id),
            "username": username,
            "email": email
        }
    
    async def create_api_key(self, user_id: str, name: str, permissions: list) -> Dict[str, Any]:
        """Create API key for user"""
        import secrets
        
        key = secrets.token_urlsafe(32)
        
        api_key_data = {
            "user_id": user_id,
            "name": name,
            "key": key,
            "permissions": permissions,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_used": None
        }
        
        result = await self.db_service.db.api_keys.insert_one(api_key_data)
        
        return {
            "id": str(result.inserted_id),
            "key": key,
            "name": name,
            "permissions": permissions
        }
    
    async def verify_api_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Verify API key"""
        api_key = await self.db_service.db.api_keys.find_one({"key": key, "is_active": True})
        
        if not api_key:
            return None
        
        # Update last used
        await self.db_service.db.api_keys.update_one(
            {"key": key},
            {"$set": {"last_used": datetime.utcnow()}}
        )
        
        return {
            "user_id": str(api_key["user_id"]),
            "permissions": api_key["permissions"]
        }
    
    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has permission"""
        user = await self.db_service.db.users.find_one({"_id": user_id})
        
        if not user:
            return False
        
        # Admin has all permissions
        if user.get("is_admin", False):
            return True
        
        # Check user permissions
        user_permissions = user.get("permissions", [])
        
        return permission in user_permissions

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.requests: Dict[str, list] = {}
    
    async def is_allowed(self, key: str, limit: int = 100, window: int = 60) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).total_seconds() < window
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        
        # Store in Redis for persistence
        await self._store_in_redis(key, len(self.requests[key]), window)
        
        return True
    
    async def _store_in_redis(self, key: str, count: int, window: int):
        """Store rate limit in Redis"""
        try:
            redis_key = f"rate_limit:{key}"
            await self.db_service.redis.setex(redis_key, window, count)
        except Exception as e:
            logger.error(f"Failed to store rate limit in Redis: {e}")
    
    async def get_remaining(self, key: str, limit: int = 100, window: int = 60) -> int:
        """Get remaining requests"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            return limit
        
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).total_seconds() < window
        ]
        
        return max(0, limit - len(self.requests[key]))

# Dependency
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_service: DatabaseService = Depends(lambda: DatabaseService())
) -> Dict[str, Any]:
    """Get current user from token"""
    security_manager = SecurityManager(db_service)
    
    token = credentials.credentials
    payload = security_manager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return payload

def get_current_user_with_api_key(
    api_key: str = None,
    db_service: DatabaseService = Depends(lambda: DatabaseService())
) -> Dict[str, Any]:
    """Get current user from API key"""
    security_manager = SecurityManager(db_service)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    user = security_manager.verify_api_key(api_key)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user
