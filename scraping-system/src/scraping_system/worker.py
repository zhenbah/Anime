#!/usr/bin/env python3
"""
Worker script for distributed scraping
"""

import asyncio
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraping_system.services.database_service import DatabaseService
from scraping_system.services.queue_service import QueueService
from scraping_system.services.crawler_service import CrawlerService
from scraping_system.services.fetcher_service import FetcherService
from scraping_system.services.parser_engine import ParserEngine
from scraping_system.services.data_processor import DataProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def worker_main():
    """Main worker loop"""
    
    print("Starting scraping worker...")
    
    # Initialize services
    db_service = DatabaseService()
    await db_service.connect()
    
    queue_service = QueueService(db_service)
    await queue_service.connect()
    
    fetcher = FetcherService()
    await fetcher.initialize()
    
    parser = ParserEngine()
    processor = DataProcessor()
    crawler = CrawlerService(db_service, queue_service)
    
    worker_id = os.environ.get('WORKER_ID', 'worker-1')
    
    logger.info(f"Worker {worker_id} started")
    
    try:
        while True:
            try:
                # Get next item from queue
                item = await queue_service.pop_from_queue()
                
                if not item:
                    await asyncio.sleep(1)
                    continue
                
                task_data = item.get('task')
                url = item.get('url')
                
                if not task_data or not url:
                    logger.warning(f"Invalid queue item: {item}")
                    continue
                
                logger.info(f"Worker {worker_id} processing: {url}")
                
                # Create scraping task
                from scraping_system.schemas.scraping import ScrapingTask
                task = ScrapingTask(**task_data)
                task.url = url
                
                # Fetch content
                result = await fetcher.fetch(task)
                
                if result.status == "success" and result.content:
                    # Parse content
                    parsed = parser.parse(result.content, task)
                    
                    # Process data
                    processed = processor.process(parsed)
                    
                    # Store in database
                    await db_service.insert_scraped_data(processed.dict())
                    
                    logger.info(f"Successfully processed: {url}")
                    
                    # Discover new links if crawling
                    if task.follow_links and task.max_depth > 0:
                        # This would extract links from the content
                        # and add them to the queue
                        pass
                        
                else:
                    logger.error(f"Failed to fetch {url}: {result.error}")
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)
                
    except KeyboardInterrupt:
        logger.info("Worker shutting down...")
    finally:
        await fetcher.close()
        await db_service.disconnect()
        logger.info("Worker stopped")

if __name__ == "__main__":
    asyncio.run(worker_main())
