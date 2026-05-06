"""
MongoDB CRUD Operations Service

Provides full CRUD operations for all database collections
with error handling, logging, and performance optimization.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.scraping_system.schemas.database_models import (
    ScrapedContentCreate, ScrapedContentUpdate, ScrapedContent, ScrapedContentStatus,
    ScrapeLogCreate, ScrapeLogUpdate, ScrapeLog, ScrapeLogStatus,
    ScraperJobCreate, ScraperJobUpdate, ScraperJob, ScraperJobStatus,
    UserCreate, UserUpdate, User, UserRole,
    ContentListResponse, SearchRequest, BulkInsertRequest, FilterParams,
    DatabaseStats, JobStats
)
from src.scraping_system.services.database_service import get_database

logger = logging.getLogger(__name__)


class MongoDBCRUD:
    """CRUD operations for MongoDB collections."""
    
    def __init__(self):
        self.db = None
        self._collections_initialized = False
    
    async def _ensure_db(self):
        """Ensure database connection is available."""
        if not self.db:
            self.db = await get_database()
    
    async def _get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get collection by name."""
        await self._ensure_db()
        return self.db[collection_name]
    
    # ============================================
    # Scraped Content Operations
    # ============================================
    
    async def create_content(self, content: ScrapedContentCreate) -> ScrapedContent:
        """Create new scraped content."""
        try:
            collection = await self._get_collection("scraped_content")
            
            # Check for duplicates
            existing = await collection.find_one({
                "title": content.title,
                "source": content.source
            })
            
            if existing:
                logger.info(f"Duplicate content found: {content.title}")
                content_dict = content.dict()
                content_dict["status"] = ScrapedContentStatus.DUPLICATE
            else:
                content_dict = content.dict()
            
            # Insert document
            result = await collection.insert_one(content_dict)
            
            # Fetch inserted document
            inserted = await collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Created content: {content.title} (ID: {result.inserted_id})")
            
            return self._parse_scraped_content(inserted)
            
        except Exception as e:
            logger.error(f"Failed to create content: {e}")
            raise
    
    async def bulk_insert_content(self, request: BulkInsertRequest) -> List[ScrapedContent]:
        """Bulk insert scraped content."""
        try:
            collection = await self._get_collection("scraped_content")
            
            # Prepare documents
            documents = []
            for item in request.items:
                # Check for duplicates
                existing = await collection.find_one({
                    "title": item.title,
                    "source": item.source
                })
                
                if existing:
                    item_dict = item.dict()
                    item_dict["status"] = ScrapedContentStatus.DUPLICATE
                else:
                    item_dict = item.dict()
                
                documents.append(item_dict)
            
            # Bulk insert
            if documents:
                result = await collection.insert_many(documents)
                
                # Fetch inserted documents
                inserted_ids = result.inserted_ids
                inserted = await collection.find({
                    "_id": {"$in": inserted_ids}
                }).to_list(length=len(inserted_ids))
                
                logger.info(f"Bulk inserted {len(inserted)} content items")
                
                return [self._parse_scraped_content(doc) for doc in inserted]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to bulk insert content: {e}")
            raise
    
    async def get_content(self, content_id: str) -> Optional[ScrapedContent]:
        """Get scraped content by ID."""
        try:
            collection = await self._get_collection("scraped_content")
            
            document = await collection.find_one({"_id": ObjectId(content_id)})
            
            if document:
                return self._parse_scraped_content(document)
            
            logger.warning(f"Content not found: {content_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get content {content_id}: {e}")
            raise
    
    async def update_content(self, content_id: str, update: ScrapedContentUpdate) -> Optional[ScrapedContent]:
        """Update scraped content."""
        try:
            collection = await self._get_collection("scraped_content")
            
            # Build update document
            update_dict = {k: v for k, v in update.dict(exclude_unset=True).items() if v is not None}
            
            if not update_dict:
                logger.warning(f"No valid fields to update for content {content_id}")
                return None
            
            # Add updated_at timestamp
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(content_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated content: {content_id}")
                return self._parse_scraped_content(result)
            
            logger.warning(f"Content not found for update: {content_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to update content {content_id}: {e}")
            raise
    
    async def delete_content(self, content_id: str) -> bool:
        """Delete scraped content."""
        try:
            collection = await self._get_collection("scraped_content")
            
            result = await collection.delete_one({"_id": ObjectId(content_id)})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted content: {content_id}")
                return True
            
            logger.warning(f"Content not found for deletion: {content_id}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete content {content_id}: {e}")
            raise
    
    async def list_content(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ScrapedContentStatus] = None,
        source: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> ContentListResponse:
        """List scraped content with pagination and filtering."""
        try:
            collection = await self._get_collection("scraped_content")
            
            # Build query
            query = {}
            if status:
                query["status"] = status
            if source:
                query["source"] = source
            
            # Get total count
            total = await collection.count_documents(query)
            
            # Calculate pagination
            total_pages = (total + page_size - 1) // page_size
            skip = (page - 1) * page_size
            
            # Fetch documents
            cursor = collection.find(query).sort(sort_by, sort_order).skip(skip).limit(page_size)
            documents = await cursor.to_list(length=page_size)
            
            items = [self._parse_scraped_content(doc) for doc in documents]
            
            return ContentListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list content: {e}")
            raise
    
    async def search_content(self, request: SearchRequest) -> ContentListResponse:
        """Search scraped content using full-text search."""
        try:
            collection = await self._get_collection("scraped_content")
            
            # Build search query
            query = {"$text": {"$search": request.query}}
            
            if request.status:
                query["status"] = request.status
            if request.source:
                query["source"] = request.source
            
            # Get total count
            total = await collection.count_documents(query)
            
            # Calculate pagination
            total_pages = (total + request.page_size - 1) // request.page_size
            skip = (request.page - 1) * request.page_size
            
            # Fetch documents with text score
            cursor = collection.find(
                query,
                {"score": {"$meta": "textScore"}}
            ).sort(
                [("score", {"$meta": "textScore"})]
            ).skip(skip).limit(request.page_size)
            
            documents = await cursor.to_list(length=request.page_size)
            
            items = [self._parse_scraped_content(doc) for doc in documents]
            
            logger.info(f"Search for '{request.query}' returned {len(items)} results")
            
            return ContentListResponse(
                items=items,
                total=total,
                page=request.page,
                page_size=request.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to search content: {e}")
            raise
    
    async def filter_content(self, params: FilterParams) -> ContentListResponse:
        """Filter content by various criteria."""
        try:
            collection = await self._get_collection("scraped_content")
            
            # Build query
            query = {}
            if params.status:
                query["status"] = params.status
            if params.source:
                query["source"] = params.source
            if params.start_date or params.end_date:
                date_query = {}
                if params.start_date:
                    date_query["$gte"] = params.start_date
                if params.end_date:
                    date_query["$lte"] = params.end_date
                query["created_at"] = date_query
            
            # Get total count
            total = await collection.count_documents(query)
            
            # Calculate pagination
            total_pages = (total + params.page_size - 1) // params.page_size
            skip = (params.page - 1) * params.page_size
            
            # Fetch documents
            cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(params.page_size)
            documents = await cursor.to_list(length=params.page_size)
            
            items = [self._parse_scraped_content(doc) for doc in documents]
            
            return ContentListResponse(
                items=items,
                total=total,
                page=params.page,
                page_size=params.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to filter content: {e}")
            raise
    
    async def get_content_stats(self) -> Dict[str, Any]:
        """Get statistics about scraped content."""
        try:
            collection = await self._get_collection("scraped_content")
            
            # Count by status
            pipeline = [
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            stats = {result["_id"]: result["count"] for result in results}
            total = sum(stats.values())
            
            return {
                "total": total,
                "by_status": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get content stats: {e}")
            raise
    
    # ============================================
    # Scrape Log Operations
    # ============================================
    
    async def create_log(self, log: ScrapeLogCreate) -> ScrapeLog:
        """Create new scrape log."""
        try:
            collection = await self._get_collection("scrape_logs")
            
            log_dict = log.dict()
            result = await collection.insert_one(log_dict)
            
            inserted = await collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Created log: {log.status} - {log.error_message or 'Success'}")
            
            return self._parse_scrape_log(inserted)
            
        except Exception as e:
            logger.error(f"Failed to create log: {e}")
            raise
    
    async def get_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[ScrapeLogStatus] = None,
        hours: Optional[int] = 24
    ) -> ContentListResponse:
        """Get recent scrape logs."""
        try:
            collection = await self._get_collection("scrape_logs")
            
            # Build query
            query = {}
            if status:
                query["status"] = status
            if hours:
                query["timestamp"] = {"$gte": datetime.utcnow() - timedelta(hours=hours)}
            
            # Get total count
            total = await collection.count_documents(query)
            
            # Calculate pagination
            total_pages = (total + page_size - 1) // page_size
            skip = (page - 1) * page_size
            
            # Fetch documents
            cursor = collection.find(query).sort("timestamp", -1).skip(skip).limit(page_size)
            documents = await cursor.to_list(length=page_size)
            
            items = [self._parse_scrape_log(doc) for doc in documents]
            
            return ContentListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            raise
    
    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days."""
        try:
            collection = await self._get_collection("scrape_logs")
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old logs")
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup logs: {e}")
            raise
    
    # ============================================
    # Scraper Job Operations
    # ============================================
    
    async def create_job(self, job: ScraperJobCreate) -> ScraperJob:
        """Create new scraper job."""
        try:
            collection = await self._get_collection("scraper_jobs")
            
            job_dict = job.dict()
            result = await collection.insert_one(job_dict)
            
            inserted = await collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Created job: {job.target_site} (ID: {result.inserted_id})")
            
            return self._parse_scraper_job(inserted)
            
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            raise
    
    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create a new scraping task from task data.
        
        Converts ScrapingTask to ScraperJob and creates it in the database.
        
        Args:
            task_data: Dictionary containing task data
            
        Returns:
            Job ID
        """
        try:
            # Convert task data to ScraperJobCreate
            from src.scraping_system.schemas.database_models import ScraperJobCreate
            from src.scraping_system.schemas.scraping import ScrapingTask
            
            # Extract task if it's in the data
            task_dict = task_data.get("task", task_data)
            
            # Create ScraperJob from ScrapingTask
            job_create = ScraperJobCreate(
                target_site=task_dict.get("url", ""),
                status="pending",
                config={
                    "task": task_dict,
                    "original_data": task_data
                }
            )
            
            return await self.create_job(job_create)
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def update_job_status(self, job_id: str, status: ScraperJobStatus) -> Optional[ScraperJob]:
        """Update scraper job status."""
        try:
            collection = await self._get_collection("scraper_jobs")
            
            update_dict = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if status == ScraperJobStatus.RUNNING:
                update_dict["started_at"] = datetime.utcnow()
            elif status in [ScraperJobStatus.COMPLETED, ScraperJobStatus.FAILED, ScraperJobStatus.STOPPED]:
                update_dict["finished_at"] = datetime.utcnow()
            
            result = await collection.find_one_and_update(
                {"job_id": job_id},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated job {job_id} status to {status}")
                return self._parse_scraper_job(result)
            
            logger.warning(f"Job not found: {job_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[ScraperJob]:
        """Get scraper job by ID."""
        try:
            collection = await self._get_collection("scraper_jobs")
            
            document = await collection.find_one({"job_id": job_id})
            
            if document:
                return self._parse_scraper_job(document)
            
            logger.warning(f"Job not found: {job_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            raise
    
    async def list_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ScraperJobStatus] = None,
        target_site: Optional[str] = None
    ) -> ContentListResponse:
        """List scraper jobs with pagination and filtering."""
        try:
            collection = await self._get_collection("scraper_jobs")
            
            # Build query
            query = {}
            if status:
                query["status"] = status
            if target_site:
                query["target_site"] = target_site
            
            # Get total count
            total = await collection.count_documents(query)
            
            # Calculate pagination
            total_pages = (total + page_size - 1) // page_size
            skip = (page - 1) * page_size
            
            # Fetch documents
            cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(page_size)
            documents = await cursor.to_list(length=page_size)
            
            items = [self._parse_scraper_job(doc) for doc in documents]
            
            return ContentListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            raise
    
    async def get_job_stats(self) -> JobStats:
        """Get statistics about scraper jobs."""
        try:
            collection = await self._get_collection("scraper_jobs")
            
            # Count by status
            pipeline = [
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            stats = {result["_id"]: result["count"] for result in results}
            
            return JobStats(
                total_jobs=sum(stats.values()),
                pending_jobs=stats.get(ScraperJobStatus.PENDING, 0),
                running_jobs=stats.get(ScraperJobStatus.RUNNING, 0),
                completed_jobs=stats.get(ScraperJobStatus.COMPLETED, 0),
                failed_jobs=stats.get(ScraperJobStatus.FAILED, 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get job stats: {e}")
            raise
    
    # ============================================
    # User Operations
    # ============================================
    
    async def create_user(self, user: UserCreate) -> User:
        """Create new user with hashed password."""
        try:
            from passlib.context import CryptContext
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            collection = await self._get_collection("users")
            
            # Check if user already exists
            existing = await collection.find_one({
                "$or": [
                    {"username": user.username},
                    {"email": user.email}
                ]
            })
            
            if existing:
                raise ValueError("User with this username or email already exists")
            
            # Hash password
            hashed_password = pwd_context.hash(user.password)
            
            user_dict = user.dict()
            user_dict["hashed_password"] = hashed_password
            user_dict.pop("password")
            
            result = await collection.insert_one(user_dict)
            
            inserted = await collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"Created user: {user.username}")
            
            return self._parse_user(inserted)
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object if successful."""
        try:
            from passlib.context import CryptContext
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            collection = await self._get_collection("users")
            
            user = await collection.find_one({"username": username})
            
            if not user:
                return None
            
            if not pwd_context.verify(password, user["hashed_password"]):
                return None
            
            return self._parse_user(user)
            
        except Exception as e:
            logger.error(f"Failed to authenticate user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        try:
            collection = await self._get_collection("users")
            
            document = await collection.find_one({"_id": ObjectId(user_id)})
            
            if document:
                return self._parse_user(document)
            
            logger.warning(f"User not found: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    async def update_user(self, user_id: str, update: UserUpdate) -> Optional[User]:
        """Update user."""
        try:
            collection = await self._get_collection("users")
            
            update_dict = {k: v for k, v in update.dict(exclude_unset=True).items() if v is not None}
            
            if not update_dict:
                logger.warning(f"No valid fields to update for user {user_id}")
                return None
            
            result = await collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated user: {user_id}")
                return self._parse_user(result)
            
            logger.warning(f"User not found for update: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None
    ) -> ContentListResponse:
        """List users with pagination and filtering."""
        try:
            collection = await self._get_collection("users")
            
            # Build query
            query = {}
            if role:
                query["role"] = role
            
            # Get total count
            total = await collection.count_documents(query)
            
            # Calculate pagination
            total_pages = (total + page_size - 1) // page_size
            skip = (page - 1) * page_size
            
            # Fetch documents
            cursor = collection.find(query).skip(skip).limit(page_size)
            documents = await cursor.to_list(length=page_size)
            
            items = [self._parse_user(doc) for doc in documents]
            
            return ContentListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise
    
    async def get_database_stats(self) -> DatabaseStats:
        """Get comprehensive database statistics."""
        try:
            job_stats = await self.get_job_stats()
            
            collection = await self._get_collection("scraped_content")
            content_count = await collection.count_documents({})
            
            collection = await self._get_collection("scrape_logs")
            log_count = await collection.count_documents({})
            
            collection = await self._get_collection("scraper_jobs")
            job_count = await collection.count_documents({})
            
            collection = await self._get_collection("users")
            user_count = await collection.count_documents({})
            
            return DatabaseStats(
                content_count=content_count,
                log_count=log_count,
                job_count=job_count,
                user_count=user_count,
                job_stats=job_stats
            )
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise
    
    # ============================================
    # Helper Methods
    # ============================================
    
    def _parse_scraped_content(self, document: Dict) -> ScrapedContent:
        """Parse MongoDB document to ScrapedContent model."""
        document["id"] = str(document["_id"])
        document.pop("_id", None)
        return ScrapedContent(**document)
    
    def _parse_scrape_log(self, document: Dict) -> ScrapeLog:
        """Parse MongoDB document to ScrapeLog model."""
        document["id"] = str(document["_id"])
        document.pop("_id", None)
        return ScrapeLog(**document)
    
    def _parse_scraper_job(self, document: Dict) -> ScraperJob:
        """Parse MongoDB document to ScraperJob model."""
        document["id"] = str(document["_id"])
        document.pop("_id", None)
        return ScraperJob(**document)
    
    def _parse_user(self, document: Dict) -> User:
        """Parse MongoDB document to User model."""
        document["id"] = str(document["_id"])
        document.pop("_id", None)
        document.pop("hashed_password", None)
        return User(**document)


# Global CRUD instance
crud = MongoDBCRUD()
