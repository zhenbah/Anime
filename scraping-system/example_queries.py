#!/usr/bin/env python3
"""
Example MongoDB Queries

Demonstrates common database operations for the scraping platform.
Run after the database is populated with data.

Usage:
    python example_queries.py
"""

import asyncio
from datetime import datetime, timedelta
from bson import ObjectId

from src.scraping_system.services.database_service import DatabaseService
from src.scraping_system.services.crud_service import crud


async def example_queries():
    """Run example database queries."""
    
    db_service = DatabaseService()
    
    try:
        # Connect to database
        await db_service.connect()
        print("✓ Connected to MongoDB\n")
        
        # ============================================
        # Example 1: Insert Scraped Content
        # ============================================
        print("=" * 60)
        print("Example 1: Insert Scraped Content")
        print("=" * 60)
        
        from src.scraping_system.schemas.database_models import ScrapedContentCreate
        
        content = ScrapedContentCreate(
            title="Example Article Title",
            description="This is an example description of scraped content.",
            media_url="https://example.com/image.jpg",
            source="https://example.com"
        )
        
        inserted = await crud.create_content(content)
        print(f"✓ Inserted content: {inserted.title}")
        print(f"  ID: {inserted.id}")
        print(f"  Status: {inserted.status}")
        print(f"  Created at: {inserted.created_at}\n")
        
        # ============================================
        # Example 2: Bulk Insert
        # ============================================
        print("=" * 60)
        print("Example 2: Bulk Insert Content")
        print("=" * 60)
        
        from src.scraping_system.schemas.database_models import BulkInsertRequest
        
        bulk_request = BulkInsertRequest(
            items=[
                ScrapedContentCreate(
                    title=f"Bulk Article {i}",
                    description=f"Description for article {i}",
                    source="https://bulk-example.com"
                )
                for i in range(1, 6)
            ]
        )
        
        bulk_inserted = await crud.bulk_insert_content(bulk_request)
        print(f"✓ Bulk inserted {len(bulk_inserted)} items\n")
        
        # ============================================
        # Example 3: Query with Pagination
        # ============================================
        print("=" * 60)
        print("Example 3: Query with Pagination")
        print("=" * 60)
        
        content_list = await crud.list_content(
            page=1,
            page_size=10,
            status=None
        )
        
        print(f"✓ Retrieved page {content_list.page} of {content_list.total_pages}")
        print(f"  Total items: {content_list.total}")
        print(f"  Items on page: {len(content_list.items)}")
        
        for item in content_list.items[:3]:  # Show first 3
            print(f"  - {item.title} (from {item.source})")
        print()
        
        # ============================================
        # Example 4: Full-Text Search
        # ============================================
        print("=" * 60)
        print("Example 4: Full-Text Search")
        print("=" * 60)
        
        from src.scraping_system.schemas.database_models import SearchRequest
        
        search_request = SearchRequest(
            query="example",
            page=1,
            page_size=10
        )
        
        search_results = await crud.search_content(search_request)
        print(f"✓ Found {search_results.total} results for 'example'")
        
        for item in search_results.items[:3]:
            print(f"  - {item.title}")
        print()
        
        # ============================================
        # Example 5: Filter by Date Range
        # ============================================
        print("=" * 60)
        print("Example 5: Filter by Date Range")
        print("=" * 60)
        
        from src.scraping_system.schemas.database_models import FilterParams
        
        filter_params = FilterParams(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            page=1,
            page_size=10
        )
        
        filtered = await crud.filter_content(filter_params)
        print(f"✓ Found {filtered.total} items in the last 24 hours\n")
        
        # ============================================
        # Example 6: Create Scrape Log
        # ============================================
        print("=" * 60)
        print("Example 6: Create Scrape Log")
        print("=" * 60)
        
        from src.scraping_system.schemas.database_models import ScrapeLogCreate, ScrapeLogStatus
        
        log = ScrapeLogCreate(
            status=ScrapeLogStatus.SUCCESS,
            target_url="https://example.com",
            metadata={
                "response_time": 0.5,
                "status_code": 200
            }
        )
        
        created_log = await crud.create_log(log)
        print(f"✓ Created log: {created_log.status}")
        print(f"  Timestamp: {created_log.timestamp}\n")
        
        # ============================================
        # Example 7: Get Recent Logs
        # ============================================
        print("=" * 60)
        print("Example 7: Get Recent Logs")
        print("=" * 60)
        
        logs = await crud.get_logs(hours=24, page=1, page_size=5)
        print(f"✓ Retrieved {logs.total} logs from last 24 hours")
        
        for log in logs.items[:3]:
            print(f"  - [{log.status}] {log.target_url or 'N/A'}")
        print()
        
        # ============================================
        # Example 8: Create Scraper Job
        # ============================================
        print("=" * 60)
        print("Example 8: Create Scraper Job")
        print("=" * 60)
        
        from src.scraping_system.schemas.database_models import ScraperJobCreate, ScraperJobStatus
        
        job = ScraperJobCreate(
            target_url="https://example.com",
            status=ScraperJobStatus.PENDING,
            config={
                "max_depth": 3,
                "follow_links": True
            }
        )
        
        created_job = await crud.create_job(job)
        print(f"✓ Created job: {created_job.job_id}")
        print(f"  Status: {created_job.status}")
        print(f"  Target: {created_job.target_site}\n")
        
        # ============================================
        # Example 9: Update Job Status
        # ============================================
        print("=" * 60)
        print("Example 9: Update Job Status")
        print("=" * 60)
        
        updated_job = await crud.update_job_status(
            created_job.job_id,
            ScraperJobStatus.RUNNING
        )
        print(f"✓ Updated job status to: {updated_job.status}\n")
        
        # ============================================
        # Example 10: Get Job Statistics
        # ============================================
        print("=" * 60)
        print("Example 10: Get Job Statistics")
        print("=" * 60)
        
        job_stats = await crud.get_job_stats()
        print(f"✓ Total jobs: {job_stats.total_jobs}")
        print(f"  Pending: {job_stats.pending_jobs}")
        print(f"  Running: {job_stats.running_jobs}")
        print(f"  Completed: {job_stats.completed_jobs}")
        print(f"  Failed: {job_stats.failed_jobs}\n")
        
        # ============================================
        # Example 11: Create User
        # ============================================
        print("=" * 60)
        print("Example 11: Create User")
        print("=" * 60)
        
        from src.scraping_system.schemas.database_models import UserCreate, UserRole
        
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePassword123!",
            role=UserRole.USER
        )
        
        created_user = await crud.create_user(user)
        print(f"✓ Created user: {created_user.username}")
        print(f"  Role: {created_user.role}")
        print(f"  Email: {created_user.email}\n")
        
        # ============================================
        # Example 12: Authenticate User
        # ============================================
        print("=" * 60)
        print("Example 12: Authenticate User")
        print("=" * 60)
        
        authenticated = await crud.authenticate_user(
            "testuser",
            "SecurePassword123!"
        )
        
        if authenticated:
            print(f"✓ Authentication successful for: {authenticated.username}\n")
        else:
            print("✗ Authentication failed\n")
        
        # ============================================
        # Example 13: Get Database Statistics
        # ============================================
        print("=" * 60)
        print("Example 13: Get Database Statistics")
        print("=" * 60)
        
        db_stats = await crud.get_database_stats()
        print(f"✓ Content items: {db_stats.content_count}")
        print(f"  Log entries: {db_stats.log_count}")
        print(f"  Jobs: {db_stats.job_count}")
        print(f"  Users: {db_stats.user_count}\n")
        
        # ============================================
        # Example 14: Direct MongoDB Query
        # ============================================
        print("=" * 60)
        print("Example 14: Direct MongoDB Query")
        print("=" * 60)
        
        collection = db_service.db.scraped_content
        
        # Find items with specific criteria
        cursor = collection.find({
            "status": "completed",
            "created_at": {"$gte": datetime.utcnow() - timedelta(hours=1)}
        }).limit(5)
        
        items = await cursor.to_list(length=5)
        print(f"✓ Found {len(items)} completed items in last hour\n")
        
        # ============================================
        # Example 15: Aggregation Pipeline
        # ============================================
        print("=" * 60)
        print("Example 15: Aggregation Pipeline")
        print("=" * 60)
        
        pipeline = [
            {
                "$match": {
                    "status": "completed"
                }
            },
            {
                "$group": {
                    "_id": "$source",
                    "count": {"$sum": 1},
                    "avg_title_length": {"$avg": {"$strLenCP": "$title"}}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 5
            }
        ]
        
        agg_cursor = collection.aggregate(pipeline)
        agg_results = await agg_cursor.to_list(length=5)
        
        print(f"✓ Top sources by content count:")
        for result in agg_results:
            print(f"  - {result['_id']}: {result['count']} items")
        print()
        
        # ============================================
        # Summary
        # ============================================
        print("=" * 60)
        print("All Examples Completed Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Disconnect from database
        await db_service.disconnect()
        print("\n✓ Disconnected from MongoDB")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MongoDB Example Queries")
    print("=" * 60 + "\n")
    
    asyncio.run(example_queries())
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60 + "\n")
