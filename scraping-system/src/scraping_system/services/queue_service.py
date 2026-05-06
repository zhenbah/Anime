"""
Redis Queue Service

Provides queue operations for distributed task processing
using Redis as a message broker.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.scraping_system.services.database_service import DatabaseService

logger = logging.getLogger(__name__)


class QueueService:
    """Redis-based queue service for distributed task processing."""
    
    def __init__(self, db_service: Optional[DatabaseService] = None):
        self.db_service = db_service
        self.redis = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Connect to Redis."""
        if self.db_service and self.db_service.redis:
            self.redis = self.db_service.redis
            self._is_connected = True
            logger.info("Queue service connected to Redis")
        else:
            raise ConnectionError("Database service not connected or Redis not available")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        # Redis is managed by DatabaseService, so we don't close it here
        self._is_connected = False
        logger.info("Queue service disconnected")
    
    async def push_to_queue(self, task: Dict[str, Any], priority: str = "normal") -> str:
        """Push task to Redis queue with priority.
        
        Args:
            task: Task data to push to queue
            priority: Task priority (critical, high, normal, low)
            
        Returns:
            Task ID
        """
        if not self._is_connected:
            raise ConnectionError("Queue service not connected")
        
        # Validate priority
        valid_priorities = ["critical", "high", "normal", "low"]
        if priority not in valid_priorities:
            priority = "normal"
        
        # Add metadata
        task_data = {
            **task,
            "queued_at": datetime.utcnow().isoformat(),
            "priority": priority
        }
        
        # Push to appropriate queue
        queue_name = f"scraping_queue:{priority}"
        await self.redis.lpush(queue_name, json.dumps(task_data))
        
        logger.debug(f"Task pushed to queue '{priority}': {task.get('url', 'N/A')}")
        return task.get("task_id", "unknown")
    
    async def pop_from_queue(self, priority: str = "high") -> Optional[Dict[str, Any]]:
        """Pop task from Redis queue.
        
        Tries to pop from queues in priority order.
        
        Args:
            priority: Starting priority level
            
        Returns:
            Task data or None if queue is empty
        """
        if not self._is_connected:
            raise ConnectionError("Queue service not connected")
        
        # Define priority order
        if priority == "critical":
            priorities = ["critical", "high", "normal", "low"]
        elif priority == "high":
            priorities = ["critical", "high", "normal", "low"]
        elif priority == "normal":
            priorities = ["critical", "high", "normal", "low"]
        else:
            priorities = ["critical", "high", "normal", "low"]
        
        # Try each priority queue
        for pri in priorities:
            queue_name = f"scraping_queue:{pri}"
            result = await self.redis.rpop(queue_name)
            
            if result:
                task_data = json.loads(result)
                logger.debug(f"Task popped from queue '{pri}': {task_data.get('url', 'N/A')}")
                return task_data
        
        return None
    
    async def get_queue_size(self) -> Dict[str, int]:
        """Get queue sizes for all priorities.
        
        Returns:
            Dictionary with queue sizes for each priority
        """
        if not self._is_connected:
            raise ConnectionError("Queue service not connected")
        
        sizes = {}
        for priority in ["critical", "high", "normal", "low"]:
            queue_name = f"scraping_queue:{priority}"
            sizes[priority] = await self.redis.llen(queue_name)
        
        return sizes
    
    async def clear_queue(self, priority: Optional[str] = None) -> None:
        """Clear queue(s).
        
        Args:
            priority: Specific priority to clear, or all if None
        """
        if not self._is_connected:
            raise ConnectionError("Queue service not connected")
        
        if priority:
            queue_name = f"scraping_queue:{priority}"
            await self.redis.delete(queue_name)
            logger.info(f"Cleared queue '{priority}'")
        else:
            for pri in ["critical", "high", "normal", "low"]:
                queue_name = f"scraping_queue:{pri}"
                await self.redis.delete(queue_name)
            logger.info("Cleared all queues")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get detailed queue statistics.
        
        Returns:
            Dictionary with queue statistics
        """
        sizes = await self.get_queue_size()
        total = sum(sizes.values())
        
        return {
            "sizes": sizes,
            "total": total,
            "timestamp": datetime.utcnow().isoformat()
        }