#!/usr/bin/env python3
"""
MongoDB Index Setup Script

Creates all necessary indexes for optimal query performance.
Run this script after initial database setup.

Usage:
    python setup_indexes.py
"""

import asyncio
import logging
from datetime import datetime

from src.scraping_system.services.database_service import DatabaseService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def setup_indexes():
    """Create all database indexes."""
    
    db_service = DatabaseService()
    
    try:
        # Connect to database
        await db_service.connect()
        logger.info("Connected to MongoDB")
        
        # Create indexes using the database service
        await db_service.create_indexes()
        
        logger.info("=" * 60)
        logger.info("All indexes created successfully!")
        logger.info("=" * 60)
        
        # List all collections and their indexes
        collections = await db_service.db.list_collection_names()
        
        for collection_name in collections:
            collection = db_service.db[collection_name]
            indexes = await collection.index_information()
            
            logger.info(f"\nCollection: {collection_name}")
            logger.info(f"Number of indexes: {len(indexes)}")
            
            for index_name, index_info in indexes.items():
                logger.info(f"  - {index_name}: {index_info.get('key', 'N/A')}")
        
        # Get index statistics
        for collection_name in collections:
            collection = db_service.db[collection_name]
            
            # Get collection stats
            stats = await db_service.db.command('collstats', collection_name)
            
            logger.info(f"\n{collection_name} Statistics:")
            logger.info(f"  - Document count: {stats.get('count', 0)}")
            logger.info(f"  - Storage size: {stats.get('storageSize', 0) / 1024:.2f} KB")
            logger.info(f"  - Index size: {stats.get('totalIndexSize', 0) / 1024:.2f} KB")
            logger.info(f"  - Average document size: {stats.get('avgObjSize', 0)} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup indexes: {e}")
        return False
        
    finally:
        # Disconnect from database
        await db_service.disconnect()
        logger.info("Disconnected from MongoDB")


async def verify_indexes():
    """Verify that all required indexes exist."""
    
    db_service = DatabaseService()
    
    try:
        await db_service.connect()
        
        # Required indexes
        required_indexes = {
            'scraped_content': [
                'hash_1',  # Unique hash index
                'source_url_1',
                'scraped_at_-1',
                'status_1',
                'title_text_description_text'  # Text search index
            ],
            'scrape_logs': [
                'timestamp_1',
                'status_1',
                'status_1_timestamp_-1'
            ],
            'scraper_jobs': [
                'job_id_1',  # Unique job ID index
                'status_1',
                'target_site_1',
                'status_1_started_at_-1'
            ],
            'users': [
                'username_1',  # Unique username index
                'email_1',  # Unique email index
                'role_1'
            ]
        }
        
        all_good = True
        
        for collection_name, expected_indexes in required_indexes.items():
            collection = db_service.db[collection_name]
            indexes = await collection.index_information()
            
            logger.info(f"\nVerifying indexes for {collection_name}:")
            
            for expected_index in expected_indexes:
                # Check if index exists (partial match)
                found = any(expected_index in index_name 
                          for index_name in indexes.keys())
                
                if found:
                    logger.info(f"  ✓ {expected_index}")
                else:
                    logger.warning(f"  ✗ {expected_index} (MISSING)")
                    all_good = False
        
        return all_good
        
    except Exception as e:
        logger.error(f"Failed to verify indexes: {e}")
        return False
        
    finally:
        await db_service.disconnect()


async def drop_indexes():
    """Drop all indexes (use with caution!)."""
    
    db_service = DatabaseService()
    
    try:
        await db_service.connect()
        
        collections = await db_service.db.list_collection_names()
        
        for collection_name in collections:
            collection = db_service.db[collection_name]
            
            # Drop all indexes except _id_
            indexes = await collection.index_information()
            
            for index_name in indexes.keys():
                if index_name != '_id_':
                    await collection.drop_index(index_name)
                    logger.info(f"Dropped index {index_name} from {collection_name}")
        
        logger.info("All indexes dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop indexes: {e}")
        return False
        
    finally:
        await db_service.disconnect()


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    action = "setup"
    if len(sys.argv) > 1:
        action = sys.argv[1]
    
    logger.info(f"Starting index management: {action}")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("-" * 60)
    
    if action == "setup":
        # Setup indexes
        success = asyncio.run(setup_indexes())
        
        if success:
            logger.info("\nVerifying indexes...")
            asyncio.run(verify_indexes())
        
    elif action == "verify":
        # Verify indexes
        success = asyncio.run(verify_indexes())
        
        if success:
            logger.info("\nAll required indexes are present!")
        else:
            logger.warning("\nSome indexes are missing. Run 'setup' to create them.")
        
    elif action == "drop":
        # Drop indexes (confirmation required)
        confirm = input("Are you sure you want to drop all indexes? (yes/no): ")
        
        if confirm.lower() == "yes":
            success = asyncio.run(drop_indexes())
            
            if success:
                logger.info("Indexes dropped successfully")
        else:
            logger.info("Operation cancelled")
        
    elif action == "rebuild":
        # Rebuild indexes
        logger.info("Dropping existing indexes...")
        asyncio.run(drop_indexes())
        
        logger.info("\nCreating new indexes...")
        success = asyncio.run(setup_indexes())
        
        if success:
            logger.info("\nVerifying indexes...")
            asyncio.run(verify_indexes())
        
    else:
        logger.error(f"Unknown action: {action}")
        logger.info("Usage: python setup_indexes.py [setup|verify|drop|rebuild]")
        sys.exit(1)
    
    logger.info("\nIndex management complete!")
