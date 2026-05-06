#!/usr/bin/env python3
"""
Example Scraper: News Article Scraper
Demonstrates how to use the scraping system for a real-world scenario
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraping_system.schemas.scraping import ScrapingTask, ScrapingMethod, Priority, CrawlStrategy
from scraping_system.services.fetcher_service import FetcherService
from scraping_system.services.parser_engine import ParserEngine
from scraping_system.services.data_processor import DataProcessor
from scraping_system.services.database_service import DatabaseService

async def example_news_scraper():
    """Example: Scrape news articles from a website"""
    
    print("=" * 60)
    print("News Article Scraper Example")
    print("=" * 60)
    
    # Initialize services
    db_service = DatabaseService()
    await db_service.connect()
    
    async with FetcherService() as fetcher:
        parser = ParserEngine()
        processor = DataProcessor()
        
        # Example 1: Scrape a single article
        print("\n1. Scraping single article...")
        
        task = ScrapingTask(
            url="https://example-news.com/article/123",
            method=ScrapingMethod.AUTO,
            priority=Priority.NORMAL,
            extract_media=True,
            extract_metadata=True
        )
        
        try:
            result = await fetcher.fetch(task)
            
            if result.status == "success":
                print(f"   ✓ Fetched: {result.url}")
                print(f"   ✓ Method: {result.method_used}")
                print(f"   ✓ Response time: {result.response_time:.2f}s")
                
                # Parse the content
                parsed = parser.parse(result.content, task)
                print(f"   ✓ Title: {parsed.title}")
                print(f"   ✓ Author: {parsed.author}")
                print(f"   ✓ Images found: {len(parsed.images)}")
                
                # Process and store
                processed = processor.process(parsed)
                data_id = await db_service.insert_scraped_data(processed.dict())
                print(f"   ✓ Stored with ID: {data_id}")
            else:
                print(f"   ✗ Failed: {result.error}")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Example 2: Batch scraping
        print("\n2. Batch scraping multiple articles...")
        
        tasks = [
            ScrapingTask(
                url=f"https://example-news.com/article/{i}",
                method=ScrapingMethod.HTTP,
                priority=Priority.NORMAL
            )
            for i in range(1, 6)
        ]
        
        try:
            results = await fetcher.fetch_batch(tasks)
            
            successful = [r for r in results if not isinstance(r, Exception) and r.status == "success"]
            print(f"   ✓ Successfully fetched: {len(successful)}/{len(tasks)}")
            
            # Process all results
            for result in successful:
                if result.content:
                    parsed = parser.parse(result.content, task)
                    processed = processor.process(parsed)
                    await db_service.insert_scraped_data(processed.dict())
            
            print(f"   ✓ All articles processed and stored")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Example 3: Crawl with pagination
        print("\n3. Crawling paginated articles...")
        
        from scraping_system.services.crawler_service import CrawlerService
        
        crawler_task = ScrapingTask(
            url="https://example-news.com/articles",
            method=ScrapingMethod.HTTP,
            priority=Priority.NORMAL,
            strategy=CrawlStrategy.PAGINATION,
            max_depth=3
        )
        
        crawler = CrawlerService(db_service)
        task_id = await crawler.start_crawl(crawler_task)
        print(f"   ✓ Crawl started: {task_id}")
        
        # Process some items from queue
        for _ in range(5):
            item = await db_service.pop_from_queue()
            if item:
                print(f"   ✓ Processing: {item.get('url')}")
        
        # Example 4: Scrape with JavaScript rendering
        print("\n4. Scraping JavaScript-heavy page...")
        
        js_task = ScrapingTask(
            url="https://example-spa.com/article",
            method=ScrapingMethod.BROWSER,
            priority=Priority.HIGH
        )
        
        try:
            result = await fetcher.fetch(js_task)
            
            if result.status == "success":
                print(f"   ✓ Fetched with browser: {result.url}")
                
                parsed = parser.parse(result.content, js_task)
                print(f"   ✓ Title: {parsed.title}")
                
                processed = processor.process(parsed)
                await db_service.insert_scraped_data(processed.dict())
                print(f"   ✓ Stored successfully")
                
        except Exception as e:
            print(f"   ✗ Error (browser may not be available): {e}")
        
        # Example 5: Custom selectors
        print("\n5. Scraping with custom selectors...")
        
        custom_task = ScrapingTask(
            url="https://example-news.com/special-article",
            method=ScrapingMethod.HTTP,
            priority=Priority.NORMAL,
            custom_selectors={
                "title": ".article-title",
                "content": ".article-body",
                "author": ".author-name",
                "date": ".publish-date"
            }
        )
        
        try:
            result = await fetcher.fetch(custom_task)
            
            if result.status == "success":
                parsed = parser.parse(result.content, custom_task)
                print(f"   ✓ Title: {parsed.title}")
                print(f"   ✓ Author: {parsed.author}")
                
                processed = processor.process(parsed)
                await db_service.insert_scraped_data(processed.dict())
                print(f"   ✓ Stored with custom extraction")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("Scraping Summary")
        print("=" * 60)
        
        queue_sizes = await db_service.get_queue_size()
        print(f"Queue sizes: {queue_sizes}")
        
        recent_data = await db_service.get_recent_data(5)
        print(f"Recent items scraped: {len(recent_data)}")
        
        for item in recent_data[:3]:
            print(f"  - {item.get('source_url', 'N/A')}")
        
        await db_service.disconnect()
        print("\n✓ Example completed successfully!")

if __name__ == "__main__":
    asyncio.run(example_news_scraper())
