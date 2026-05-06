from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.scraping_system.schemas.scraping import ScrapingTask, ScrapingResult, ScrapingMethod, Priority, CrawlStrategy
from src.scraping_system.schemas.data import ScrapedData, BatchProcessingResult, DataSourceType
from src.scraping_system.services.database_service import DatabaseService
from src.scraping_system.services.fetcher_service import FetcherService
from src.scraping_system.services.parser_engine import ParserEngine
from src.scraping_system.services.data_processor import DataProcessor
from src.scraping_system.services.crawler_service import CrawlerService, DistributedCrawler
from src.scraping_system.services.proxy_service import ProxyManager
from src.scraping_system.services.queue_service import QueueService
from src.scraping_system.services.crud_service import crud
from src.scraping_system.security.auth import get_current_user, SecurityManager
from src.scraping_system.security.rate_limiter import RateLimiter
from src.scraping_system.monitoring.metrics import MetricsCollector

router = APIRouter()

# Initialize services
security_manager = SecurityManager()
rate_limiter = RateLimiter()
metrics_collector = MetricsCollector()

# Import database routes
from src.scraping_system.api.v1.database_routes import router as db_router

# Include database routes under /api/v1
router.include_router(db_router, prefix="", tags=["database"])

@router.post("/scrape", response_model=ScrapingResult)
async def scrape_url(
    task: ScrapingTask,
    user: dict = Depends(get_current_user)
):
    """Scrape a single URL"""
    # Check rate limit
    if not await rate_limiter.is_allowed(user["username"]):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    try:
        # Fetch content
        result = await fetcher_service.fetch(task)
        
        if result.status == "success" and result.content:
            # Parse content
            parsed = parser_engine.parse(result.content, task)
            
            # Process data
            processed = data_processor.process(parsed)
            
            # Store in database
            data_id = await db_service.insert_scraped_data(processed.dict())
            
            # Update metrics
            metrics_collector.record_request(task.method.value, "success", result.response_time)
            metrics_collector.record_data_extracted(processed.source_type.value)
            
            # Add structured data to result
            result.structured_data = processed.structured_data
            result.media_urls = [img["url"] for img in processed.images]
            
        return result
        
    except Exception as e:
        metrics_collector.record_request(task.method.value, "error", 0)
        metrics_collector.record_error(type(e).__name__)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/batch", response_model=BatchProcessingResult)
async def scrape_batch(
    tasks: List[ScrapingTask],
    user: dict = Depends(get_current_user)
):
    """Scrape multiple URLs concurrently"""
    # Check rate limit
    if not await rate_limiter.is_allowed(user["username"], limit=1000):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    try:
        # Fetch all URLs concurrently
        results = await fetcher_service.fetch_batch(tasks)
        
        # Process successful results
        processed_items = []
        for result in results:
            if isinstance(result, Exception):
                continue
            
            if result.status == "success" and result.content:
                try:
                    parsed = parser_engine.parse(result.content, tasks[0])  # Use first task as template
                    processed = data_processor.process(parsed)
                    processed_items.append(processed)
                except Exception as e:
                    print(f"Processing error: {e}")
        
        # Deduplicate and store
        unique_items = data_processor.deduplicate(processed_items)
        
        for item in unique_items:
            await db_service.insert_scraped_data(item.dict())
        
        # Update metrics
        metrics_collector.record_request("batch", "success", 0)
        metrics_collector.record_data_extracted("batch", len(unique_items))
        
        return BatchProcessingResult(
            total=len(tasks),
            completed=len(unique_items),
            failed=len(tasks) - len(processed_items),
            duplicates=len(processed_items) - len(unique_items),
            processing_time=0,
            results=unique_items
        )
        
    except Exception as e:
        metrics_collector.record_error("batch_processing")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl", response_model=Dict[str, str])
async def start_crawl(
    task: ScrapingTask,
    queue_service: QueueService = Depends(lambda: QueueService(db_service)),
    user: dict = Depends(get_current_user)
):
    """Start a crawling job"""
    try:
        # Ensure queue service is connected
        await queue_service.connect()
        
        crawler = CrawlerService(db_service, queue_service)
        task_id = await crawler.start_crawl(task)
        
        return {"task_id": task_id, "status": "started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/crawl/distributed", response_model=Dict[str, str])
async def start_distributed_crawl(
    task: ScrapingTask,
    num_workers: int = Query(5, ge=1, le=20),
    queue_service: QueueService = Depends(lambda: QueueService(db_service)),
    user: dict = Depends(get_current_user)
):
    """Start a distributed crawling job"""
    try:
        # Ensure queue service is connected
        await queue_service.connect()
        
        crawler = DistributedCrawler(db_service, queue_service, num_workers=num_workers)
        await crawler.start()
        await crawler.add_task(task)
        
        return {
            "task_id": "distributed-" + task.url.path,
            "status": "started",
            "workers": num_workers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data", response_model=List[ScrapedData])
async def get_scraped_data(
    limit: int = Query(100, le=1000),
    offset: int = 0,
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get scraped data with pagination"""
    try:
        query = {}
        if status:
            query["status"] = status
        
        cursor = db_service.db.scraped_data.find(query).skip(offset).limit(limit).sort("scraped_at", -1)
        items = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for item in items:
            item["id"] = str(item["_id"])
            del item["_id"]
        
        return items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/search", response_model=List[ScrapedData])
async def search_data(
    query: str = Query(..., min_length=1),
    limit: int = Query(50, le=500),
    user: dict = Depends(get_current_user)
):
    """Search scraped data using full-text search"""
    try:
        results = await db_service.search_scraped_data(query, limit)
        
        for item in results:
            item["id"] = str(item["_id"])
            del item["_id"]
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{data_id}", response_model=ScrapedData)
async def get_data_item(
    data_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific data item"""
    try:
        from bson import ObjectId
        item = await db_service.get_scraped_data(data_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        item["id"] = str(item["_id"])
        del item["_id"]
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue/status")
async def get_queue_status(
    queue_service: QueueService = Depends(lambda: QueueService(db_service)),
    user: dict = Depends(get_current_user)
):
    """Get queue status"""
    try:
        # Ensure queue service is connected
        await queue_service.connect()
        
        sizes = await queue_service.get_queue_size()
        return sizes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics(
    queue_service: QueueService = Depends(lambda: QueueService(db_service)),
    user: dict = Depends(get_current_user)
):
    """Get system metrics"""
    try:
        # Ensure queue service is connected
        await queue_service.connect()
        
        queue_sizes = await queue_service.get_queue_size()
        metrics_collector.set_queue_size("high", queue_sizes.get("high", 0))
        metrics_collector.set_queue_size("normal", queue_sizes.get("normal", 0))
        metrics_collector.set_queue_size("low", queue_sizes.get("low", 0))
        
        return metrics_collector.get_metrics()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await db_service.db.admin.command('ping')
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    try:
        # Check Redis connection
        await db_service.redis.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy"
    
    return {
        "status": overall_status,
        "database": db_status,
        "cache": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Authentication endpoints
@router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await security_manager.create_user(
            user_data.username,
            user_data.email,
            user_data.password
        )
        
        access_token = security_manager.create_access_token(
            data={"sub": user["username"]}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/token", response_model=Token)
async def login(
    username: str,
    password: str
):
    """Login and get access token"""
    user = await security_manager.authenticate_user(username, password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = security_manager.create_access_token(
        data={"sub": user["username"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/api-key", response_model=Dict[str, str])
async def create_api_key(
    api_key_data: APIKeyCreate,
    user: dict = Depends(get_current_user)
):
    """Create API key for programmatic access"""
    try:
        api_key = await security_manager.create_api_key(
            user["id"],
            api_key_data.name,
            api_key_data.permissions
        )
        
        return api_key
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Public endpoints (no authentication required)
@router.get("/public/robots.txt")
async def get_robots_txt():
    """Return robots.txt"""
    return {
        "content": "User-agent: *\nDisallow: /admin/\nDisallow: /api/v1/scrape\nCrawl-delay: 10"
    }

@router.get("/public/stats")
async def get_public_stats():
    """Get public statistics"""
    try:
        total_data = await db_service.db.scraped_data.count_documents({})
        recent_data = await db_service.db.scraped_data.count_documents({
            "scraped_at": {"$gte": datetime.utcnow().timestamp() - 86400}
        })
        
        return {
            "total_scraped": total_data,
            "scraped_today": recent_data,
            "status": "operational"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
