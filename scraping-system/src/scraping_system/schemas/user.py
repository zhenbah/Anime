from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["read"]

class APIKey(BaseModel):
    id: str
    name: str
    key: str
    permissions: List[str]
    is_active: bool = True
    created_at: datetime
    last_used: Optional[datetime] = None

class RateLimitConfig(BaseModel):
    requests_per_minute: int = 100
    burst_allowance: int = 10
    
class UserScrapingStats(BaseModel):
    user_id: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    data_extracted: int
    api_calls_made: int
    last_activity: Optional[datetime] = None