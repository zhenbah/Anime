"""
MongoDB Database Connection Module

Provides async MongoDB connection with connection pooling,
reconnection logic, and error handling.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextlib import asynccontextmanager
import asyncio

from src.scraping_system.core.config import settings
from src.scraping_system.utils.error_handler import (
    DatabaseErrorHandler,
    DatabaseTransaction,
    DatabaseHealthChecker
)

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Manages MongoDB connection with pooling and reconnection."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connection_lock = asyncio.Lock()
        self._is_connected = False
        self.error_handler = DatabaseErrorHandler()
        self.health_checker = DatabaseHealthChecker(self)
    
    async def connect(self) -> None:
        """Establish MongoDB connection with retry logic."""
        async with self._connection_lock:
            if self._is_connected:
                logger.warning("MongoDB connection already established")
                return
                
            max_retries = 5
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Connecting to MongoDB (attempt {attempt + 1}/{max_retries})...")
                    
                    # Create MongoDB client with connection pooling options
                    self.client = AsyncIOMotorClient(
                        settings.MONGODB_URL,
                        maxPoolSize=50,  # Maximum number of connections in pool
                        minPoolSize=10,   # Minimum number of connections to maintain
                        maxIdleTimeMS=45000,  # Close idle connections after 45 seconds
                        waitQueueTimeoutMS=5000,  # Wait up to 5 seconds for connection
                        serverSelectionTimeoutMS=5000,  # Timeout for server selection
                        socketTimeoutMS=45000,  # Socket timeout
                        connectTimeoutMS=10000,  # Connection timeout
                        retryWrites=True,
                        w="majority",  # Write concern
                        readPreference="primaryPreferred",
                        uuidRepresentation="standard",
                        appname="scraping-platform"
                    )
                    
                    # Get database instance
                    self.db = self.client[settings.MONGODB_DB]
                    
                    # Test connection
                    await self.client.admin.command('ping')
                    
                    # Create indexes
                    await self._create_indexes()
                    
                    self._is_connected = True
                    logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DB}")
                    return
                    
                except Exception as e:
                    logger.error(f"MongoDB connection attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error("Failed to connect to MongoDB after all retries")
                        raise ConnectionError(f"Could not connect to MongoDB: {e}")
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        async with self._connection_lock:
            if self.client:
                self.client.close()
                self._is_connected = False
                logger.info("MongoDB connection closed")
    
    async def _create_indexes(self) -> None:
        """Create indexes for optimized query performance."""
        try:
            # Scraped Content Collection Indexes
            await self.db.scraped_content.create_index(
                [("title", "text"), ("description", "text")],
                name="text_search_index",
                default_language="english"
            )
            await self.db.scraped_content.create_index(
                "created_at",
                name="created_at_index",
                expireAfterSeconds=7776000  # Auto-delete after 90 days (optional)
            )
            await self.db.scraped_content.create_index(
                "source",
                name="source_index"
            )
            await self.db.scraped_content.create_index(
                [("title", 1), ("created_at", -1)],
                name="title_created_at_index"
            )
            
            # Scrape Logs Collection Indexes
            await self.db.scrape_logs.create_index(
                "timestamp",
                name="timestamp_index",
                expireAfterSeconds=2592000  # Auto-delete logs after 30 days
            )
            await self.db.scrape_logs.create_index(
                "status",
                name="status_index"
            )
            await self.db.scrape_logs.create_index(
                [("status", 1), ("timestamp", -1)],
                name="status_timestamp_index"
            )
            
            # Scraper Jobs Collection Indexes
            await self.db.scraper_jobs.create_index(
                "job_id",
                name="job_id_index",
                unique=True
            )
            await self.db.scraper_jobs.create_index(
                "status",
                name="jobs_status_index"
            )
            await self.db.scraper_jobs.create_index(
                "target_site",
                name="target_site_index"
            )
            await self.db.scraper_jobs.create_index(
                [("status", 1), ("started_at", -1)],
                name="jobs_status_started_index"
            )
            
            # Users Collection Indexes
            await self.db.users.create_index(
                "username",
                name="username_index",
                unique=True
            )
            await self.db.users.create_index(
                "email",
                name="email_index",
                unique=True
            )
            await self.db.users.create_index(
                "role",
                name="role_index"
            )
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    async def is_connected(self) -> bool:
        """Check if MongoDB connection is active."""
        if not self._is_connected or not self.client:
            return False
        try:
            # Check connection by running a simple command
            await self.client.admin.command('ping')
            return True
        except Exception:
            self._is_connected = False
            return False
    
    @asynccontextmanager
    async def get_session():
        """Get MongoDB session for transactions."""
        if not self.client:
            raise ConnectionError("MongoDB client not initialized")
        
        async with await self.client.start_session() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Session error: {e}")
                raise
    
    async def transaction(self):
        """Get a transaction context manager."""
        return DatabaseTransaction(self)
    
    async def insert_scraped_data(self, data: dict) -> str:
        """Insert scraped data with deduplication."""
        from bson import ObjectId
        
        # Check for duplicates
        existing = await self.db.scraped_data.find_one({"hash": data["hash"]})
        if existing:
            data["duplicate_of"] = str(existing["_id"])
            data["status"] = "duplicate"
        
        result = await self.db.scraped_data.insert_one(data)
        return str(result.inserted_id)
    
    async def get_scraped_data(self, data_id: str) -> Optional[dict]:
        """Get scraped data by ID."""
        from bson import ObjectId
        return await self.db.scraped_data.find_one({"_id": ObjectId(data_id)})
    
    async def search_scraped_data(self, query: str, limit: int = 50) -> list:
        """Full-text search on scraped data."""
        cursor = await self.db.scraped_data.find(
            {"$text": {"$search": query}}
        ).limit(limit)
        return await cursor.to_list(length=limit)


# Global database connection instance
db_connection = MongoDBConnection()

# Alias for backward compatibility
DatabaseService = MongoDBConnection


def get_db() -> MongoDBConnection:
    """Get database connection instance."""
    return db_connection


async def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    if not db_connection.db:
        raise ConnectionError("Database not connected")
    return db_connection.db


async def health_check() -> dict:
    """Perform database health check."""
    return await db_connection.health_checker.check_connection()
