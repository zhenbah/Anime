from typing import Optional, Dict, Any, List
import logging
import asyncio
from datetime import datetime, timedelta
import random
import time

from src.scraping_system.services.database_service import DatabaseService
from src.scraping_system.services.queue_service import QueueService
from src.scraping_system.services.crud_service import crud
from src.scraping_system.schemas.scraping import ScrapingTask, Priority, CrawlStrategy

logger = logging.getLogger(__name__)


class CrawlerService:
    """Distributed crawler with queue-based architecture"""
    
    def __init__(self, db_service: DatabaseService, queue_service: Optional[QueueService] = None):
        self.db_service = db_service
        self.queue_service = queue_service or QueueService(db_service)
        self.visited_urls = set()
        self.max_depth = 3
        self.domain_limits = {}  # Rate limiting per domain
        
    async def _ensure_queue_service(self):
        """Ensure queue service is connected."""
        if not self.queue_service._is_connected:
            await self.queue_service.connect()
        
    async def start_crawl(self, task: ScrapingTask) -> str:
        """Start a new crawling job"""
        # Ensure queue service is connected
        await self._ensure_queue_service()
        
        # Create task in database
        task_id = await crud.create_task(task.dict())
        
        # Add initial URL to queue
        await self.queue_service.push_to_queue(
            {"task": task.dict(), "url": str(task.url), "depth": 0, "task_id": task_id},
            priority=task.priority.value
        )
        
        logger.info(f"Crawl started: {task.url} (ID: {task_id})")
        return task_id
    
    async def process_queue(self, worker_id: str):
        """Process items from the queue"""
        # Ensure queue service is connected
        await self._ensure_queue_service()
        
        logger.info(f"Worker {worker_id} started processing queue")
        
        while True:
            try:
                # Get next item from queue
                item = await self.queue_service.pop_from_queue()
                
                if not item:
                    await asyncio.sleep(1)
                    continue
                
                # Process the item
                await self._process_queue_item(item, worker_id)
                
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)
    
    async def _process_queue_item(self, item: Dict, worker_id: str):
        """Process a single queue item"""
        task_data = item.get("task")
        url = item.get("url")
        depth = item.get("depth", 0)
        
        if not task_data or not url:
            logger.warning(f"Invalid queue item: {item}")
            return
        
        # Check if already visited
        if url in self.visited_urls:
            logger.info(f"URL already visited: {url}")
            return
        
        self.visited_urls.add(url)
        
        # Apply rate limiting
        await self._apply_rate_limit(url)
        
        # Create scraping task
        task = ScrapingTask(**task_data)
        task.url = url
        
        logger.info(f"Worker {worker_id} processing: {url} (depth: {depth})")
        
        # Check if we should continue crawling
        if depth < task.max_depth:
            # Discover new links
            new_links = await self._discover_links(task)
            
            for link in new_links:
                await self.queue_service.push_to_queue(
                    {
                        "task": task_data,
                        "url": link,
                        "depth": depth + 1,
                        "parent_url": url,
                        "task_id": task_data.get("task_id", task_id)
                    },
                    priority=task.priority.value
                )
    
    async def _discover_links(self, task: ScrapingTask) -> List[str]:
        """Discover new links based on crawl strategy"""
        links = []
        
        if task.strategy == CrawlStrategy.SITEMAP:
            links = await self._crawl_sitemap(task.url)
        elif task.strategy == CrawlStrategy.PAGINATION:
            links = await self._crawl_pagination(task.url)
        elif task.strategy == CrawlStrategy.LINK_DISCOVERY:
            links = await self._discover_links_from_page(task)
        elif task.strategy == CrawlStrategy.CUSTOM:
            links = await self._custom_crawl(task)
        
        # Filter and normalize links
        links = self._filter_links(links, task.url)
        
        return links
    
    async def _crawl_sitemap(self, base_url: str) -> List[str]:
        """Crawl sitemap.xml"""
        from urllib.parse import urljoin
        
        sitemap_url = urljoin(base_url, "/sitemap.xml")
        links = []
        
        try:
            # This would use the fetcher service
            # For now, return empty list
            logger.info(f"Would crawl sitemap: {sitemap_url}")
        except Exception as e:
            logger.error(f"Sitemap crawl failed: {e}")
        
        return links
    
    async def _crawl_pagination(self, base_url: str) -> List[str]:
        """Crawl paginated pages"""
        links = []
        
        # Generate pagination URLs
        for page in range(1, 11):  # First 10 pages
            if "?" in base_url:
                paginated_url = f"{base_url}&page={page}"
            else:
                paginated_url = f"{base_url}?page={page}"
            
            links.append(paginated_url)
        
        return links
    
    async def _discover_links_from_page(self, task: ScrapingTask) -> List[str]:
        """Discover links from page content"""
        # This would use the fetcher and parser services
        # For now, return empty list
        return []
    
    async def _custom_crawl(self, task: ScrapingTask) -> List[str]:
        """Custom crawling logic"""
        # Implement custom crawling logic based on task parameters
        return []
    
    def _filter_links(self, links: List[str], base_url: str) -> List[str]:
        """Filter and normalize discovered links"""
        from urllib.parse import urljoin, urlparse
        
        base_domain = urlparse(base_url).netloc
        filtered = []
        
        for link in links:
            # Normalize URL
            normalized = urljoin(base_url, link)
            
            # Check if same domain
            if urlparse(normalized).netloc == base_domain:
                # Check if already visited
                if normalized not in self.visited_urls:
                    filtered.append(normalized)
        
        return filtered
    
    async def _apply_rate_limit(self, url: str):
        """Apply rate limiting per domain"""
        from urllib.parse import urlparse
        
        domain = urlparse(url).netloc
        
        if domain not in self.domain_limits:
            self.domain_limits[domain] = {
                "last_request": 0,
                "delay": 1.0  # 1 second between requests
            }
        
        limit = self.domain_limits[domain]
        elapsed = time.time() - limit["last_request"]
        
        if elapsed < limit["delay"]:
            sleep_time = limit["delay"] - elapsed
            await asyncio.sleep(sleep_time)
        
        limit["last_request"] = time.time()
    
    async def get_crawl_stats(self) -> Dict[str, Any]:
        """Get crawling statistics"""
        # Ensure queue service is connected
        await self._ensure_queue_service()
        
        return {
            "visited_urls": len(self.visited_urls),
            "queue_sizes": await self.queue_service.get_queue_size(),
            "domain_limits": len(self.domain_limits)
        }

class DistributedCrawler:
    """Manages multiple crawler workers"""
    
    def __init__(self, db_service: DatabaseService, queue_service: Optional[QueueService] = None, num_workers: int = 5):
        self.db_service = db_service
        self.queue_service = queue_service or QueueService(db_service)
        self.num_workers = num_workers
        self.workers = []
        self.running = False
        
    async def start(self):
        """Start all crawler workers"""
        # Ensure queue service is connected
        await self.queue_service.connect()
        
        self.running = True
        
        for i in range(self.num_workers):
            worker = CrawlerService(self.db_service, self.queue_service)
            self.workers.append(worker)
            
            # Start worker task
            task = asyncio.create_task(
                worker.process_queue(f"worker-{i}")
            )
            self.workers.append(task)
        
        logger.info(f"Started {self.num_workers} crawler workers")
    
    async def stop(self):
        """Stop all crawler workers"""
        self.running = False
        logger.info("Stopping crawler workers")
    
    async def add_task(self, task: ScrapingTask):
        """Add a new crawling task"""
        crawler = CrawlerService(self.db_service, self.queue_service)
        await crawler.start_crawl(task)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get overall crawler statistics"""
        total_visited = 0
        
        for worker in self.workers:
            if isinstance(worker, CrawlerService):
                stats = await worker.get_crawl_stats()
                total_visited += stats["visited_urls"]
        
        return {
            "total_visited_urls": total_visited,
            "num_workers": self.num_workers,
            "running": self.running
        }
