from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class DataSourceType(str, Enum):
    HTML = "html"
    JSON = "json"
    XML = "xml"
    API = "api"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"

class ScrapedData(BaseModel):
    id: str
    source_url: str
    source_type: DataSourceType
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    raw_content: Optional[str] = None
    
    # Media extraction
    images: List[Dict[str, Any]] = []
    videos: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []
    
    # Metadata
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    language: Optional[str] = None
    tags: List[str] = []
    categories: List[str] = []
    
    # Technical
    word_count: Optional[int] = None
    reading_time: Optional[float] = None
    
    # Processing
    status: ProcessingStatus = ProcessingStatus.PENDING
    processing_time: Optional[float] = None
    confidence_score: float = 0.0
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Deduplication
    hash: Optional[str] = None
    duplicate_of: Optional[str] = None
    
    # Additional structured data
    structured_data: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "id": "abc123",
                "source_url": "https://example.com/article",
                "source_type": "html",
                "title": "Example Article",
                "content": "This is the extracted content...",
                "images": [{"url": "https://example.com/image.jpg", "alt": "Example"}],
                "author": "John Doe",
                "publish_date": "2024-01-01T00:00:00",
                "status": "completed",
                "hash": "sha256_hash_value"
            }
        }

class BatchProcessingResult(BaseModel):
    total: int
    completed: int
    failed: int
    duplicates: int
    processing_time: float
    results: List[ScrapedData]

class DataQualityMetrics(BaseModel):
    total_processed: int
    successful_extractions: int
    failed_extractions: int
    duplicate_count: int
    average_confidence: float
    extraction_rate: float