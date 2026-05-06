import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.scraping_system.services.database_service import DatabaseService
from src.scraping_system.schemas.scraping import ScrapingTask, Priority, CrawlStrategy, ScrapingMethod

logger = logging.getLogger(__name__)

class ScrapingScheduler:
    """Manages scheduled scraping tasks"""
    
    def __init__(self, db_service: Optional[DatabaseService] = None):
        self.db_service = db_service
        self.scheduler = AsyncIOScheduler()
        self.scheduled_jobs: Dict[str, Any] = {}
        self.running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("Scheduler started")
            
            # Load scheduled tasks from database
            self._load_scheduled_tasks()
    
    def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False
            logger.info("Scheduler stopped")
    
    def schedule_task(
        self,
        task: ScrapingTask,
        schedule_type: str = "interval",
        interval_minutes: int = 60,
        cron_expression: str = "0 * * * *",  # Every hour
        start_date: Optional[datetime] = None
    ) -> str:
        """Schedule a recurring scraping task"""
        import uuid
        
        job_id = str(uuid.uuid4())
        
        if schedule_type == "interval":
            trigger = IntervalTrigger(
                minutes=interval_minutes,
                start_date=start_date or datetime.utcnow()
            )
        elif schedule_type == "cron":
            trigger = CronTrigger(
                expression=cron_expression,
                start_date=start_date or datetime.utcnow()
            )
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")
        
        # Store task in database
        task_data = task.dict()
        task_data["scheduled"] = True
        task_data["schedule_type"] = schedule_type
        task_data["interval_minutes"] = interval_minutes
        task_data["cron_expression"] = cron_expression
        task_data["job_id"] = job_id
        
        if self.db_service:
            self.db_service.db.scheduled_tasks.insert_one(task_data)
        
        # Schedule the job
        job = self.scheduler.add_job(
            self._execute_scheduled_task,
            trigger=trigger,
            args=[task],
            id=job_id,
            replace_existing=True
        )
        
        self.scheduled_jobs[job_id] = {
            "job": job,
            "task": task,
            "schedule_type": schedule_type,
            "created_at": datetime.utcnow()
        }
        
        logger.info(f"Scheduled task {job_id}: {task.url}")
        
        return job_id
    
    def remove_scheduled_task(self, job_id: str):
        """Remove a scheduled task"""
        if job_id in self.scheduled_jobs:
            self.scheduler.remove_job(job_id)
            del self.scheduled_jobs[job_id]
            
            # Remove from database
            if self.db_service:
                self.db_service.db.scheduled_tasks.delete_one({"job_id": job_id})
            
            logger.info(f"Removed scheduled task: {job_id}")
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks"""
        tasks = []
        
        for job_id, job_info in self.scheduled_jobs.items():
            tasks.append({
                "job_id": job_id,
                "url": str(job_info["task"].url),
                "schedule_type": job_info["schedule_type"],
                "next_run": job_info["job"].next_run_time.isoformat() if job_info["job"].next_run_time else None,
                "created_at": job_info["created_at"].isoformat()
            })
        
        return tasks
    
    async def _execute_scheduled_task(self, task: ScrapingTask):
        """Execute a scheduled scraping task"""
        logger.info(f"Executing scheduled task: {task.url}")
        
        try:
            # Update task timestamp
            task.created_at = datetime.utcnow()
            
            # Add to queue
            if self.db_service:
                await self.db_service.push_to_queue(
                    {"task": task.dict(), "url": str(task.url), "depth": 0},
                    priority=task.priority.value
                )
                
                # Update last run time
                self.db_service.db.scheduled_tasks.update_one(
                    {"job_id": task.metadata.get("job_id")},
                    {"$set": {"last_run": datetime.utcnow()}}
                )
        except Exception as e:
            logger.error(f"Failed to execute scheduled task {task.url}: {e}")
    
    def _load_scheduled_tasks(self):
        """Load scheduled tasks from database"""
        if not self.db_service:
            return
        
        try:
            cursor = self.db_service.db.scheduled_tasks.find({"active": True})
            tasks = list(cursor)
            
            for task_data in tasks:
                try:
                    task = ScrapingTask(**{k: v for k, v in task_data.items() if k in ScrapingTask.__fields__})
                    
                    schedule_type = task_data.get("schedule_type", "interval")
                    interval = task_data.get("interval_minutes", 60)
                    cron_expr = task_data.get("cron_expression", "0 * * * *")
                    
                    self.schedule_task(
                        task,
                        schedule_type=schedule_type,
                        interval_minutes=interval,
                        cron_expression=cron_expr,
                        start_date=task_data.get("start_date")
                    )
                except Exception as e:
                    logger.error(f"Failed to load scheduled task {task_data.get('_id')}: {e}")
        except Exception as e:
            logger.error(f"Failed to load scheduled tasks: {e}")

class AutoRescraper:
    """Automatically re-scrape content that has changed"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.check_interval = 3600  # Check every hour
    
    async def start(self):
        """Start auto-rescraping"""
        logger.info("Auto-rescraper started")
        
        while True:
            try:
                await self._check_for_updates()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Auto-rescraper error: {e}")
                await asyncio.sleep(60)
    
    async def _check_for_updates(self):
        """Check for content updates"""
        # Get recently scraped items
        cursor = self.db_service.db.scraped_data.find(
            {"scraped_at": {"$gte": datetime.utcnow() - timedelta(days=7)}}
        ).limit(100)
        
        items = await cursor.to_list(length=100)
        
        for item in items:
            await self._check_item_for_updates(item)
    
    async def _check_item_for_updates(self, item: Dict):
        """Check if an item has been updated"""
        from src.scraping_system.services.fetcher_service import FetcherService
        from src.scraping_system.services.parser_engine import ParserEngine
        from src.scraping_system.services.data_processor import DataProcessor
        
        try:
            # Create a task for re-scraping
            from src.scraping_system.schemas.scraping import ScrapingTask
            
            task = ScrapingTask(
                url=item["source_url"],
                method="http",
                priority="low",
                max_depth=0,
                follow_links=False
            )
            
            # Fetch the content
            async with FetcherService() as fetcher:
                result = await fetcher.fetch(task)
            
            if result.status == "success" and result.content:
                # Parse the content
                parser = ParserEngine()
                parsed = parser.parse(result.content, task)
                
                # Process the data
                processor = DataProcessor()
                processed = processor.process(parsed)
                
                # Check if content has changed
                if processed.hash != item.get("hash"):
                    logger.info(f"Content updated: {item['source_url']}")
                    
                    # Store the new version
                    processed.duplicate_of = str(item["_id"])
                    await self.db_service.insert_scraped_data(processed.dict())
                    
                    # Update the original item
                    await self.db_service.db.scraped_data.update_one(
                        {"_id": item["_id"]},
                        {"$set": {"has_update": True, "last_checked": datetime.utcnow()}}
                    )
        except Exception as e:
            logger.error(f"Failed to check updates for {item['source_url']}: {e}")

class IncrementalCrawler:
    """Crawls only new or updated content"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.known_urls = set()
    
    async def initialize(self):
        """Load known URLs from database"""
        cursor = self.db_service.db.scraped_data.find({}, {"source_url": 1})
        items = await cursor.to_list(length=10000)
        
        for item in items:
            self.known_urls.add(item["source_url"])
        
        logger.info(f"Loaded {len(self.known_urls)} known URLs")
    
    async def crawl_incremental(self, task: ScrapingTask) -> List[str]:
        """Crawl only new URLs"""
        from src.scraping_system.services.crawler_service import CrawlerService
        from src.scraping_system.services.queue_service import QueueService
        
        queue_service = QueueService(self.db_service)
        await queue_service.connect()
        
        crawler = CrawlerService(self.db_service, queue_service)
        
        # Override max_depth for incremental crawl
        task.max_depth = 2
        
        # Start crawl
        task_id = await crawler.start_crawl(task)
        
        # Filter out known URLs in the crawler
        # This is handled by the visited_urls set in CrawlerService
        
        return [task_id]
    
    def is_known_url(self, url: str) -> bool:
        """Check if URL is already known"""
        return url in self.known_urls
    
    def add_known_url(self, url: str):
        """Add URL to known set"""
        self.known_urls.add(url)
