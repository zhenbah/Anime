"""
MongoDB API Routes

Provides REST API endpoints for all MongoDB collections
with full CRUD operations, search, and filtering.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from src.scraping_system.schemas.database_models import (
    ScrapedContentCreate, ScrapedContentUpdate, ScrapedContent,
    ScrapeLogCreate, ScrapeLogUpdate, ScrapeLog,
    ScraperJobCreate, ScraperJobUpdate, ScraperJob,
    UserCreate, UserUpdate, User,
    ContentListResponse, SearchRequest, BulkInsertRequest, FilterParams,
    DatabaseStats, JobStats
)
from src.scraping_system.services.crud_service import crud
from src.scraping_system.security.auth import get_current_user

router = APIRouter()

# ============================================
# Scraped Content Routes
# ============================================

@router.post("/content", response_model=ScrapedContent)
async def create_content(
    content: ScrapedContentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new scraped content."""
    try:
        return await crud.create_content(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create content: {str(e)}")


@router.post("/content/bulk", response_model=list[ScrapedContent])
async def bulk_insert_content(
    request: BulkInsertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Bulk insert scraped content."""
    try:
        return await crud.bulk_insert_content(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk insert: {str(e)}")


@router.get("/content/{content_id}", response_model=ScrapedContent)
async def get_content(content_id: str):
    """Get scraped content by ID."""
    try:
        content = await crud.get_content(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content: {str(e)}")


@router.put("/content/{content_id}", response_model=ScrapedContent)
async def update_content(
    content_id: str,
    update: ScrapedContentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update scraped content."""
    try:
        content = await crud.update_content(content_id, update)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update content: {str(e)}")


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete scraped content."""
    try:
        success = await crud.delete_content(content_id)
        if not success:
            raise HTTPException(status_code=404, detail="Content not found")
        return {"message": "Content deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete content: {str(e)}")


@router.get("/content", response_model=ContentListResponse)
async def list_content(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source: Optional[str] = Query(None, description="Filter by source")
):
    """List scraped content with pagination and filtering."""
    try:
        from src.scraping_system.schemas.database_models import ScrapedContentStatus
        
        status_enum = None
        if status:
            try:
                status_enum = ScrapedContentStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        return await crud.list_content(
            page=page,
            page_size=page_size,
            status=status_enum,
            source=source
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list content: {str(e)}")


@router.post("/search", response_model=ContentListResponse)
async def search_content(request: SearchRequest):
    """Search scraped content using full-text search."""
    try:
        return await crud.search_content(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search: {str(e)}")


@router.post("/filter", response_model=ContentListResponse)
async def filter_content(request: FilterParams):
    """Filter content by various criteria."""
    try:
        return await crud.filter_content(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to filter: {str(e)}")


# ============================================
# Scrape Log Routes
# ============================================

@router.post("/logs", response_model=ScrapeLog)
async def create_log(
    log: ScrapeLogCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new scrape log."""
    try:
        return await crud.create_log(log)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create log: {str(e)}")


@router.get("/logs", response_model=ContentListResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    hours: Optional[int] = 24
):
    """Get recent scrape logs."""
    try:
        from src.scraping_system.schemas.database_models import ScrapeLogStatus
        
        status_enum = None
        if status:
            try:
                status_enum = ScrapeLogStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        return await crud.get_logs(
            page=page,
            page_size=page_size,
            status=status_enum,
            hours=hours
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.delete("/logs/cleanup")
async def cleanup_logs(
    days: int = Query(30, ge=1, description="Delete logs older than this many days"),
    current_user: dict = Depends(get_current_user)
):
    """Delete old logs."""
    try:
        deleted = await crud.cleanup_old_logs(days)
        return {"message": f"Deleted {deleted} old logs"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup logs: {str(e)}")


# ============================================
# Scraper Job Routes
# ============================================

@router.post("/jobs", response_model=ScraperJob)
async def create_job(
    job: ScraperJobCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new scraper job."""
    try:
        return await crud.create_job(job)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=ScraperJob)
async def get_job(job_id: str):
    """Get scraper job by ID."""
    try:
        job = await crud.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.put("/jobs/{job_id}/status", response_model=ScraperJob)
async def update_job_status(
    job_id: str,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """Update scraper job status."""
    try:
        from src.scraping_system.schemas.database_models import ScraperJobStatus
        
        try:
            status_enum = ScraperJobStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        job = await crud.update_job_status(job_id, status_enum)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")


@router.get("/jobs", response_model=ContentListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    target_site: Optional[str] = None
):
    """List scraper jobs with pagination and filtering."""
    try:
        from src.scraping_system.schemas.database_models import ScraperJobStatus
        
        status_enum = None
        if status:
            try:
                status_enum = ScraperJobStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        return await crud.list_jobs(
            page=page,
            page_size=page_size,
            status=status_enum,
            target_site=target_site
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/jobs/stats", response_model=JobStats)
async def get_job_stats():
    """Get scraper job statistics."""
    try:
        return await crud.get_job_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job stats: {str(e)}")


# ============================================
# User Routes
# ============================================

@router.post("/users", response_model=User)
async def create_user(user: UserCreate):
    """Create new user."""
    try:
        return await crud.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.post("/auth/login")
async def login(username: str, password: str):
    """Authenticate user and return token."""
    try:
        from passlib.context import CryptContext
        from jose import jwt
        from src.scraping_system.core.config import settings
        
        user = await crud.authenticate_user(username, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create JWT token
        token_data = {"sub": user.username, "role": user.role}
        token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to login: {str(e)}")


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get user by ID."""
    try:
        user = await crud.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user."""
    try:
        user = await crud.update_user(user_id, update)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.get("/users", response_model=ContentListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List users with pagination and filtering."""
    try:
        from src.scraping_system.schemas.database_models import UserRole
        
        role_enum = None
        if role:
            try:
                role_enum = UserRole(role)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
        
        return await crud.list_users(
            page=page,
            page_size=page_size,
            role=role_enum
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


# ============================================
# Database Stats Routes
# ============================================

@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats():
    """Get comprehensive database statistics."""
    try:
        return await crud.get_database_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/health")
async def database_health():
    """Check database health."""
    try:
        from src.scraping_system.services.database_service import health_check
        return await health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
