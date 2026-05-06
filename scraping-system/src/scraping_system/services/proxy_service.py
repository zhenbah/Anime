from typing import Optional, Dict, Any, List
import logging
import random
import asyncio
from datetime import datetime

from src.scraping_system.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages rotating proxies with failover"""
    
    def __init__(self, db_service: Optional[DatabaseService] = None):
        self.db_service = db_service
        self.proxies: List[Dict[str, Any]] = []
        self.current_index = 0
        self.failed_proxies: Dict[str, int] = {}
        self.max_failures = 3
        
    async def initialize(self):
        """Initialize proxy list from database or config"""
        from src.scraping_system.core.config import settings
        
        # Load from config
        if settings.PROXY_LIST:
            for proxy_url in settings.PROXY_LIST:
                self.proxies.append({
                    "url": proxy_url,
                    "type": "datacenter",
                    "failures": 0,
                    "last_used": None,
                    "is_active": True
                })
        
        # Load from database if available
        if self.db_service:
            await self._load_proxies_from_db()
        
        logger.info(f"Loaded {len(self.proxies)} proxies")
    
    async def _load_proxies_from_db(self):
        """Load proxies from database"""
        try:
            cursor = self.db_service.db.proxies.find({"is_active": True})
            db_proxies = await cursor.to_list(length=100)
            
            for proxy in db_proxies:
                self.proxies.append({
                    "url": proxy["url"],
                    "type": proxy.get("type", "datacenter"),
                    "failures": proxy.get("failures", 0),
                    "last_used": proxy.get("last_used"),
                    "is_active": True
                })
        except Exception as e:
            logger.error(f"Failed to load proxies from DB: {e}")
    
    async def get_proxy(self) -> Optional[str]:
        """Get next available proxy using round-robin"""
        if not self.proxies:
            return None
        
        # Try to find an active proxy
        for _ in range(len(self.proxies)):
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy["is_active"] and proxy["failures"] < self.max_failures:
                proxy["last_used"] = datetime.utcnow()
                return proxy["url"]
        
        return None
    
    async def mark_proxy_failed(self, proxy_url: str):
        """Mark proxy as failed"""
        for proxy in self.proxies:
            if proxy["url"] == proxy_url:
                proxy["failures"] += 1
                
                if proxy["failures"] >= self.max_failures:
                    proxy["is_active"] = False
                    logger.warning(f"Proxy disabled after {self.max_failures} failures: {proxy_url}")
                
                # Update in database
                if self.db_service:
                    await self._update_proxy_in_db(proxy_url, proxy)
                
                break
    
    async def mark_proxy_success(self, proxy_url: str):
        """Mark proxy as successful"""
        for proxy in self.proxies:
            if proxy["url"] == proxy_url:
                if proxy["failures"] > 0:
                    proxy["failures"] = max(0, proxy["failures"] - 1)
                
                if not proxy["is_active"] and proxy["failures"] < self.max_failures:
                    proxy["is_active"] = True
                    logger.info(f"Proxy reactivated: {proxy_url}")
                
                break
    
    async def _update_proxy_in_db(self, proxy_url: str, proxy_data: Dict):
        """Update proxy status in database"""
        try:
            await self.db_service.db.proxies.update_one(
                {"url": proxy_url},
                {"$set": {
                    "failures": proxy_data["failures"],
                    "is_active": proxy_data["is_active"],
                    "last_used": proxy_data["last_used"]
                }}
            )
        except Exception as e:
            logger.error(f"Failed to update proxy in DB: {e}")
    
    async def add_proxy(self, proxy_url: str, proxy_type: str = "datacenter"):
        """Add new proxy"""
        proxy = {
            "url": proxy_url,
            "type": proxy_type,
            "failures": 0,
            "last_used": None,
            "is_active": True,
            "added_at": datetime.utcnow()
        }
        
        self.proxies.append(proxy)
        
        # Save to database
        if self.db_service:
            try:
                await self.db_service.db.proxies.insert_one(proxy)
            except Exception as e:
                logger.error(f"Failed to save proxy to DB: {e}")
    
    async def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        active = sum(1 for p in self.proxies if p["is_active"])
        total = len(self.proxies)
        
        return {
            "total_proxies": total,
            "active_proxies": active,
            "failed_proxies": total - active,
            "proxies": self.proxies
        }

class UserAgentRotator:
    """Rotates user agents to avoid detection"""
    
    def __init__(self):
        try:
            from fake_useragent import UserAgent
            self.ua = UserAgent()
            self.use_fake_ua = True
        except:
            self.use_fake_ua = False
            self.manual_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ]
    
    def get_random(self) -> str:
        """Get random user agent"""
        if self.use_fake_ua:
            return self.ua.random
        else:
            return random.choice(self.manual_agents)
    
    def get_browser_specific(self, browser: str = "chrome") -> str:
        """Get user agent for specific browser"""
        if self.use_fake_ua:
            try:
                if browser == "chrome":
                    return self.ua.chrome
                elif browser == "firefox":
                    return self.ua.firefox
                elif browser == "safari":
                    return self.ua.safari
            except:
                pass
        
        return self.get_random()

class RequestThrottler:
    """Manages request rate limiting"""
    
    def __init__(self, requests_per_minute: int = 100):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make request"""
        async with self.lock:
            now = datetime.utcnow()
            
            # Remove old requests
            self.requests = [
                req_time for req_time in self.requests
                if (now - req_time).total_seconds() < 60
            ]
            
            # Check if we can make request
            if len(self.requests) >= self.requests_per_minute:
                # Wait until oldest request expires
                oldest = min(self.requests)
                wait_time = 60 - (now - oldest).total_seconds()
                await asyncio.sleep(wait_time)
            
            # Add current request
            self.requests.append(now)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get throttler status"""
        now = datetime.utcnow()
        recent = [
            req_time for req_time in self.requests
            if (now - req_time).total_seconds() < 60
        ]
        
        return {
            "requests_per_minute": self.requests_per_minute,
            "current_requests": len(recent),
            "available": len(recent) < self.requests_per_minute
        }
