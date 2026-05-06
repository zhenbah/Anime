import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
from fake_useragent import UserAgent
import random
import time
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

from src.scraping_system.core.config import settings
from src.scraping_system.schemas.scraping import ScrapingTask, ScrapingResult
from src.scraping_system.services.proxy_service import ProxyManager

logger = logging.getLogger(__name__)

@dataclass
class FetchResult:
    content: Optional[str]
    status_code: int
    response_time: float
    method_used: str
    error: Optional[str] = None

class FetcherService:
    """High-performance async fetcher with HTTP and browser support"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.proxy_manager = ProxyManager()
        self.ua = UserAgent()
        self.active_sessions = 0
        self.max_concurrent = settings.MAX_CONCURRENT_REQUESTS
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def initialize(self):
        """Initialize aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent,
            limit_per_host=10,
            ttl_dns_cache=300
        )
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector
        )
        logger.info(f"Fetcher service initialized with {self.max_concurrent} max concurrent requests")
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            logger.info("Fetcher service closed")
    
    async def fetch(self, task: ScrapingTask) -> ScrapingResult:
        """Main fetch method with automatic method detection"""
        start_time = time.time()
        method = task.method
        
        # Auto-detect method if not specified
        if method == "auto":
            method = await self._detect_method(task.url)
        
        result = None
        
        try:
            if method == "browser":
                result = await self._fetch_with_browser(task)
            else:
                result = await self._fetch_with_http(task)
            
            response_time = time.time() - start_time
            
            return ScrapingResult(
                task_id=str(hash(task.url + str(time.time()))),
                url=str(task.url),
                status="success",
                method_used=method,
                content=result.content,
                response_time=response_time,
                retry_count=0,
                created_at=task.created_at,
                completed_at=time.time()
            )
            
        except Exception as e:
            logger.error(f"Fetch failed for {task.url}: {e}")
            
            # Retry logic
            if task.retry_count and task.retry_count > 0:
                return await self._retry_fetch(task, method, task.retry_count)
            
            response_time = time.time() - start_time
            return ScrapingResult(
                task_id=str(hash(task.url + str(time.time()))),
                url=str(task.url),
                status="failed",
                method_used=method,
                error=str(e),
                response_time=response_time,
                retry_count=0,
                created_at=task.created_at,
                completed_at=time.time()
            )
    
    async def _detect_method(self, url: str) -> str:
        """Detect if page requires JavaScript rendering"""
        # Quick check for common SPA patterns
        spa_indicators = [
            "/app/", "/spa/", "/react/", "/vue/",
            "?_escaped_fragment_", "#!"
        ]
        
        for indicator in spa_indicators:
            if indicator in str(url):
                return "browser"
        
        # Check URL extension
        static_extensions = ['.pdf', '.jpg', '.png', '.css', '.js', '.json', '.xml']
        if any(str(url).endswith(ext) for ext in static_extensions):
            return "http"
        
        # Default to HTTP for speed
        return "http"
    
    async def _fetch_with_http(self, task: ScrapingTask) -> FetchResult:
        """Fetch using aiohttp (fast mode)"""
        async with self.semaphore:
            headers = await self._build_headers(task)
            proxy = await self._get_proxy(task)
            
            try:
                async with self.session.get(
                    str(task.url),
                    headers=headers,
                    proxy=proxy,
                    cookies=task.cookies,
                    ssl=False
                ) as response:
                    content = await response.text()
                    
                    return FetchResult(
                        content=content,
                        status_code=response.status,
                        response_time=response.request_info.real_time,
                        method_used="http"
                    )
                    
            except aiohttp.ClientError as e:
                logger.error(f"HTTP fetch error: {e}")
                raise
    
    async def _fetch_with_browser(self, task: ScrapingTask) -> FetchResult:
        """Fetch using Playwright (JavaScript rendering)"""
        async with self.semaphore:
            proxy = await self._get_proxy(task)
            
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=settings.HEADLESS,
                        proxy={"server": proxy} if proxy else None
                    )
                    
                    context = await browser.new_context(
                        user_agent=task.user_agent or self.ua.random,
                        viewport={"width": 1920, "height": 1080}
                    )
                    
                    page = await context.new_page()
                    
                    # Set extra headers
                    if task.headers:
                        await page.set_extra_http_headers(task.headers)
                    
                    # Navigate with timeout
                    timeout = task.timeout or settings.BROWSER_TIMEOUT * 1000
                    await page.goto(str(task.url), wait_until="networkidle", timeout=timeout)
                    
                    # Handle infinite scroll if needed
                    if task.strategy and "infinite" in str(task.strategy).lower():
                        await self._handle_infinite_scroll(page)
                    
                    # Wait for lazy loading
                    await asyncio.sleep(2)
                    
                    content = await page.content()
                    
                    await browser.close()
                    
                    return FetchResult(
                        content=content,
                        status_code=200,
                        response_time=0,  # Will be calculated in main method
                        method_used="browser"
                    )
                    
            except Exception as e:
                logger.error(f"Browser fetch error: {e}")
                raise
    
    async def _handle_infinite_scroll(self, page):
        """Handle infinite scroll pages"""
        scroll_pause_time = 2
        last_height = await page.evaluate("document.body.scrollHeight")
        
        for _ in range(10):  # Max 10 scrolls
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(scroll_pause_time)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    async def _build_headers(self, task: ScrapingTask) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        if task.user_agent:
            headers["User-Agent"] = task.user_agent
        else:
            headers["User-Agent"] = self.ua.random
        
        if task.headers:
            headers.update(task.headers)
        
        return headers
    
    async def _get_proxy(self, task: ScrapingTask) -> Optional[str]:
        """Get proxy for request"""
        if task.proxy:
            return task.proxy
        
        if settings.PROXY_ENABLED:
            return await self.proxy_manager.get_proxy()
        
        return None
    
    async def _retry_fetch(self, task: ScrapingTask, method: str, retries: int) -> ScrapingResult:
        """Retry fetch with exponential backoff"""
        for attempt in range(retries):
            try:
                # Exponential backoff
                delay = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
                
                if method == "browser":
                    result = await self._fetch_with_browser(task)
                else:
                    result = await self._fetch_with_http(task)
                
                if result.status_code == 200:
                    return ScrapingResult(
                        task_id=str(hash(task.url + str(time.time()))),
                        url=str(task.url),
                        status="success",
                        method_used=method,
                        content=result.content,
                        response_time=result.response_time,
                        retry_count=attempt + 1,
                        created_at=task.created_at,
                        completed_at=time.time()
                    )
                    
            except Exception as e:
                logger.warning(f"Retry {attempt + 1} failed: {e}")
                continue
        
        raise Exception(f"All {retries} retries failed")
    
    async def fetch_batch(self, tasks: List[ScrapingTask]) -> List[ScrapingResult]:
        """Fetch multiple URLs concurrently"""
        tasks = [self.fetch(task) for task in tasks]
        return await asyncio.gather(*tasks, return_exceptions=True)
