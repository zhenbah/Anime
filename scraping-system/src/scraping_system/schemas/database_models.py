"""
Pydantic Models for MongoDB Data Validation

Defines schemas for all database collections with validation rules.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic validation."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid ObjectId')
        return str(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class ScrapedContentStatus(str, Enum):
    """Status of scraped content."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class ScrapeLogStatus(str, Enum):
    """Status of scrape log."""
    SUCCESS = "success"
    FAILURE = "failure"


class ScraperJobStatus(str, Enum):
    """Status of scraper job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    USER = "user"


# ============================================
# Scraped Content Models
# ============================================

class ScrapedContentBase(BaseModel):
    """Base model for scraped content."""
    title: str = Field(..., min_length=1, max_length=500, description="Title of the content")
    description: Optional[str] = Field(None, max_length=2000, description="Description of the content")
    media_url: Optional[HttpUrl] = Field(None, description="URL of media content")
    source: str = Field(..., min_length=1, max_length=200, description="Source of the content")
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title must not be empty')
        return v.strip()
    
    @validator('source')
    def source_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Source must not be empty')
        return v.strip()


class ScrapedContentCreate(ScrapedContentBase):
    """Model for creating new scraped content."""
    pass


class ScrapedContentUpdate(BaseModel):
    """Model for updating scraped content."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    media_url: Optional[HttpUrl] = None
    source: Optional[str] = Field(None, min_length=1, max_length=200)
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Title must not be empty')
        return v.strip() if v else v


class ScrapedContentInDBBase(ScrapedContentBase):
    """Base model for scraped content in database."""
    id: str = Field(default_factory=lambda: str(ObjectId()), description="Unique ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    status: ScrapedContentStatus = Field(
        default=ScrapedContentStatus.COMPLETED,
        description="Status of the content"
    )
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "Example Article Title",
                "description": "This is an example description of the scraped content.",
                "media_url": "https://example.com/image.jpg",
                "source": "https://example.com",
                "created_at": "2024-01-01T00:00:00",
                "status": "completed"
            }
        }


class ScrapedContent(ScrapedContentInDBBase):
    """Model for scraped content returned from API."""
    pass


class ScrapedContentInDB(ScrapedContentInDBBase):
    """Model for scraped content stored in MongoDB."""
    
    class Config(ScrapedContentInDBBase.Config):
        allow_population_by_field_name = True


# ============================================
# Scrape Log Models
# ============================================

class ScrapeLogBase(BaseModel):
    """Base model for scrape logs."""
    status: ScrapeLogStatus = Field(..., description="Status of the scrape operation")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if failed")
    target_url: Optional[HttpUrl] = Field(None, description="URL that was scraped")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ScrapeLogCreate(ScrapeLogBase):
    """Model for creating a scrape log."""
    pass


class ScrapeLogUpdate(BaseModel):
    """Model for updating a scrape log."""
    status: Optional[ScrapeLogStatus] = None
    error_message: Optional[str] = Field(None, max_length=1000)


class ScrapeLogInDBBase(ScrapeLogBase):
    """Base model for scrape log in database."""
    id: str = Field(default_factory=lambda: str(ObjectId()), description="Unique ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ScrapeLog(ScrapeLogInDBBase):
    """Model for scrape log returned from API."""
    pass


class ScrapeLogInDB(ScrapeLogInDBBase):
    """Model for scrape log stored in MongoDB."""
    pass


# ============================================
# Scraper Job Models
# ============================================

class ScraperJobBase(BaseModel):
    """Base model for scraper jobs."""
    target_site: HttpUrl = Field(..., description="Target website URL")
    status: ScraperJobStatus = Field(
        default=ScraperJobStatus.PENDING,
        description="Current status of the job"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Job configuration parameters"
    )


class ScraperJobCreate(ScraperJobBase):
    """Model for creating a scraper job."""
    pass


class ScraperJobUpdate(BaseModel):
    """Model for updating a scraper job."""
    status: Optional[ScraperJobStatus] = None
    config: Optional[Dict[str, Any]] = None


class ScraperJobInDBBase(ScraperJobBase):
    """Base model for scraper job in database."""
    job_id: str = Field(default_factory=lambda: str(ObjectId()), description="Unique job ID")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    finished_at: Optional[datetime] = Field(None, description="Job completion time")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ScraperJob(ScraperJobInDBBase):
    """Model for scraper job returned from API."""
    pass


class ScraperJobInDB(ScraperJobInDBBase):
    """Model for scraper job stored in MongoDB."""
    pass


# ============================================
# User Models
# ============================================

class UserBase(BaseModel):
    """Base model for users."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    role: UserRole = Field(default=UserRole.USER, description="User role")


class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8, description="Password")


class UserUpdate(BaseModel):
    """Model for updating a user."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    role: Optional[UserRole] = None


class UserInDBBase(UserBase):
    """Base model for user in database."""
    id: str = Field(default_factory=lambda: str(ObjectId()), description="Unique ID")
    hashed_password: str = Field(..., description="Hashed password")
    is_active: bool = Field(default=True, description="Whether user is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class User(UserInDBBase):
    """Model for user returned from API."""
    pass


class UserInDB(UserInDBBase):
    """Model for user stored in MongoDB."""
    pass


# ============================================
# Response Models
# ============================================

class ContentListResponse(BaseModel):
    """Response model for paginated content list."""
    items: List[ScrapedContent]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobStats(BaseModel):
    """Statistics for scraper jobs."""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int


class DatabaseStats(BaseModel):
    """Database statistics."""
    content_count: int
    log_count: int
    job_count: int
    user_count: int
    job_stats: JobStats


# ============================================
# Request/Response Models
# ============================================

class SearchRequest(BaseModel):
    """Model for search requests."""
    query: str = Field(..., min_length=1, description="Search query")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    status: Optional[ScrapedContentStatus] = None
    source: Optional[str] = None


class BulkInsertRequest(BaseModel):
    """Model for bulk insert requests."""
    items: List[ScrapedContentCreate] = Field(..., min_items=1, max_items=1000)


class FilterParams(BaseModel):
    """Model for filtering parameters."""
    status: Optional[ScrapedContentStatus] = None
    source: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
