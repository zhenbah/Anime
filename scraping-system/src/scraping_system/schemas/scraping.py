from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum

class ScrapingMethod(str, Enum):
    HTTP = "http"
    BROWSER = "browser"
    AUTO = "auto"

class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class CrawlStrategy(str, Enum):
    SITEMAP = "sitemap"
    PAGINATION = "pagination"
    LINK_DISCOVERY = "link_discovery"
    CUSTOM = "custom"

class ScrapingTask(BaseModel):
    url: HttpUrl
    method: ScrapingMethod = ScrapingMethod.AUTO
    priority: Priority = Priority.NORMAL
    strategy: CrawlStrategy = CrawlStrategy.LINK_DISCOVERY
    max_depth: int = Field(default=3, ge=0, le=10)
    follow_links: bool = True
    extract_media: bool = True
    extract_metadata: bool = True
    custom_selectors: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    delay: Optional[float] = None
    timeout: Optional[int] = None
    retry_count: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ScrapingResult(BaseModel):
    task_id: str
    url: str
    status: str
    method_used: ScrapingMethod
    content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    media_urls: List[str] = []
    metadata: Dict[str, Any] = {}
    response_time: float
    retry_count: int = 0
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class CrawledLink(BaseModel):
    url: str
    depth: int
    parent_url: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

class QueueItem(BaseModel):
    id: str
    task: ScrapingTask
    status: str = "pending"
    worker_id: Optional[str] = None
    attempts: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)