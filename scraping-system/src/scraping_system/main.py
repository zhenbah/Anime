from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
from src.scraping_system.core.config import settings
from src.scraping_system.monitoring.logger import setup_logging
from src.scraping_system.monitoring.metrics import MetricsCollector
from src.scraping_system.security.rate_limiter import RateLimiter
from src.scraping_system.api.v1.api import api_router
from src.scraping_system.automation.scheduler import ScrapingScheduler
from src.scraping_system.services.queue_service import QueueService
from src.scraping_system.services.database_service import DatabaseService

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Web Scraping System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up scraping system...")
    
    # Initialize database connections
    db_service = DatabaseService()
    await db_service.connect()
    app.state.db_service = db_service
    
    # Initialize queue service
    queue_service = QueueService()
    await queue_service.connect()
    app.state.queue_service = queue_service
    
    # Initialize metrics collector
    metrics = MetricsCollector()
    app.state.metrics = metrics
    
    # Initialize rate limiter
    rate_limiter = RateLimiter()
    app.state.rate_limiter = rate_limiter
    
    # Start scheduler
    scheduler = ScrapingScheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    
    logger.info("Scraping system started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down scraping system...")
    
    # Close database connections
    if hasattr(app.state, 'db_service'):
        await app.state.db_service.disconnect()
    
    # Close queue connections
    if hasattr(app.state, 'queue_service'):
        await app.state.queue_service.disconnect()
    
    # Stop scheduler
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.stop()
    
    logger.info("Scraping system shut down successfully")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)