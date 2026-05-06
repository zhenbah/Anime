from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.redis: Optional[Redis] = None
        
    async def connect(self):
        """Connect to MongoDB and Redis"""
        from src.scraping_system.core.config import settings
        
        try:
            # MongoDB connection
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[settings.MONGODB_DB]
            
            # Test MongoDB connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        
        try:
            # Redis connection
            self.redis = Redis.from_url(settings.REDIS_URL)
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
        
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def create_indexes(self):
        """Create optimized indexes for collections"""
        # Scraped data indexes
        await self.db.scraped_data.create_index("hash", unique=True)
        await self.db.scraped_data.create_index("source_url")
        await self.db.scraped_data.create_index("scraped_at")
        await self.db.scraped_data.create_index("status")
        await self.db.scraped_data.create_index([("title", "text"), ("content", "text")])
        
        # Scraping tasks indexes
        await self.db.scraping_tasks.create_index("status")
        await self.db.scraping_tasks.create_index("created_at")
        await self.db.scraping_tasks.create_index("scheduled_at")
        await self.db.scraping_tasks.create_index("priority")
        
        # Queue items indexes
        await self.db.queue_items.create_index("status")
        await self.db.queue_items.create_index("worker_id")
        await self.db.queue_items.create_index("created_at")
        
        # Users indexes
        await self.db.users.create_index("username", unique=True)
        await self.db.users.create_index("email", unique=True)
        
        # API keys indexes
        await self.db.api_keys.create_index("key", unique=True)
        
        logger.info("Database indexes created successfully")
    
    # Scraped Data Operations
    async def insert_scraped_data(self, data: dict) -> str:
        """Insert scraped data with deduplication"""
        from bson import ObjectId
        
        # Check for duplicates
        existing = await self.db.scraped_data.find_one({"hash": data["hash"]})
        if existing:
            data["duplicate_of"] = str(existing["_id"])
            data["status"] = "duplicate"
        
        result = await self.db.scraped_data.insert_one(data)
        return str(result.inserted_id)
    
    async def get_scraped_data(self, data_id: str) -> Optional[dict]:
        """Get scraped data by ID"""
        from bson import ObjectId
        return await self.db.scraped_data.find_one({"_id": ObjectId(data_id)})
    
    async def get_scraped_data_by_url(self, url: str, limit: int = 100) -> list:
        """Get scraped data by URL"""
        cursor = self.db.scraped_data.find({"source_url": url}).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def search_scraped_data(self, query: str, limit: int = 50) -> list:
        """Full-text search on scraped data"""
        cursor = await self.db.scraped_data.find(
            {"$text": {"$search": query}}
        ).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_recent_data(self, limit: int = 100) -> list:
        """Get most recent scraped data"""
        cursor = self.db.scraped_data.find().sort("scraped_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    # Queue Operations
    async def push_to_queue(self, task: dict, priority: str = "normal") -> str:
        """Push task to Redis queue"""
        from src.scraping_system.schemas.scraping import ScrapingTask
        from datetime import datetime
        import uuid
        
        queue_name = f"scraping_queue:{priority}"
        item = {
            "id": str(uuid.uuid4()),
            "task": task.dict() if hasattr(task, "dict") else task,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "priority": priority
        }
        
        # Store in Redis
        await self.redis.lpush(queue_name, str(item))
        
        # Also store in MongoDB for persistence
        result = await self.db.queue_items.insert_one(item)
        return item["id"]
    
    async def pop_from_queue(self, priority: str = "high") -> Optional[dict]:
        """Pop task from Redis queue"""
        # Try high priority first, then normal, then low
        priorities = ["critical", "high", "normal", "low"]
        
        for pri in priorities:
            queue_name = f"scraping_queue:{pri}"
            item = await self.redis.rpop(queue_name)
            if item:
                import json
                return json.loads(item)
        
        return None
    
    async def get_queue_size(self) -> dict:
        """Get queue sizes for all priorities"""
        sizes = {}
        for priority in ["critical", "high", "normal", "low"]:
            queue_name = f"scraping_queue:{priority}"
            sizes[priority] = await self.redis.llen(queue_name)
        return sizes
    
    # Task Operations
    async def create_task(self, task: dict) -> str:
        """Create a new scraping task"""
        result = await self.db.scraping_tasks.insert_one(task)
        return str(result.inserted_id)
    
    async def update_task_status(self, task_id: str, status: str):
        """Update task status"""
        from bson import ObjectId
        await self.db.scraping_tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
    
    # Cache Operations
    async def set_cache(self, key: str, value: str, ttl: int = 3600):
        """Set cache value with TTL"""
        await self.redis.setex(key, ttl, value)
    
    async def get_cache(self, key: str) -> Optional[str]:
        """Get cache value"""
        return await self.redis.get(key)
    
    async def delete_cache(self, key: str):
        """Delete cache value"""
        await self.redis.delete(key)
    
    # Metrics
    async def increment_metric(self, metric_name: str, value: int = 1):
        """Increment a metric counter"""
        await self.redis.hincrby("metrics", metric_name, value)
    
    async def get_metrics(self) -> dict:
        """Get all metrics"""
        metrics = await self.redis.hgetall("metrics")
        return {k.decode(): int(v.decode()) for k, v in metrics.items()}
