from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime

from src.scraping_system.schemas.data import ScrapedData, DataSourceType
from src.scraping_system.schemas.scraping import ScrapingTask

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    title: Optional[str]
    content: Optional[str]
    metadata: Dict[str, Any]
    media: List[Dict[str, Any]]
    links: List[Dict[str, Any]]

class ParserEngine:
    """Intelligent parser with fallback strategies"""
    
    def __init__(self):
        self.selectors = {
            "title": [
                "h1", ".title", "[class*='title']", 
                "h2", "h3", "head title"
            ],
            "content": [
                "article", ".content", "[class*='content']",
                "main", ".post", ".article",
                "[class*='article']", "[class*='post']"
            ],
            "author": [
                ".author", "[class*='author']",
                "[class*='writer']", "[rel='author']"
            ],
            "date": [
                "[class*='date']", "[class*='time']",
                "time", "[datetime]", ".timestamp"
            ],
            "image": [
                "img", "figure img", ".image",
                "[class*='image']", "picture img"
            ],
            "link": [
                "a[href]"
            ]
        }
        
    def parse(self, content: str, task: ScrapingTask) -> ScrapedData:
        """Main parsing method with fallback strategies"""
        start_time = datetime.utcnow()
        
        # Try to detect if content is JSON/API response
        api_data = self._try_parse_api(content)
        if api_data:
            return self._process_api_data(api_data, task, start_time)
        
        # Parse HTML
        soup = BeautifulSoup(content, 'lxml')
        
        # Extract with multiple strategies
        extraction = self._extract_with_fallbacks(soup, task)
        
        # Calculate hash for deduplication
        content_hash = self._calculate_hash(content)
        
        # Clean and normalize
        cleaned_content = self._clean_content(extraction.content)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return ScrapedData(
            id=content_hash[:20],
            source_url=str(task.url),
            source_type=DataSourceType.HTML,
            title=extraction.title,
            content=cleaned_content,
            raw_content=content[:50000],  # Store first 50KB
            images=extraction.media,
            videos=[],
            links=extraction.links,
            author=extraction.metadata.get("author"),
            publish_date=extraction.metadata.get("date"),
            language=self._detect_language(cleaned_content),
            tags=[],
            categories=[],
            word_count=len(cleaned_content.split()) if cleaned_content else 0,
            reading_time=self._calculate_reading_time(cleaned_content),
            status="completed",
            processing_time=processing_time,
            confidence_score=self._calculate_confidence(extraction),
            hash=content_hash,
            duplicate_of=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            structured_data=extraction.metadata
        )
    
    def _try_parse_api(self, content: str) -> Optional[Dict]:
        """Try to parse as JSON/API response"""
        try:
            # Try JSON
            data = json.loads(content)
            return {"type": "json", "data": data}
        except:
            pass
        
        # Try to find JSON in HTML
        json_pattern = r'<script[^>+]*type\s*=\s*["\']application/json["\'][^>]*>([^<]+)</script>'
        matches = re.findall(json_pattern, content, re.IGNORECASE)
        for match in matches:
            try:
                data = json.loads(match.strip())
                return {"type": "json_in_html", "data": data}
            except:
                continue
        
        return None
    
    def _process_api_data(self, api_data: Dict, task: ScrapingTask, start_time: datetime) -> ScrapedData:
        """Process API/JSON data"""
        data = api_data["data"]
        
        # Extract common fields from API responses
        title = None
        content = None
        
        # Try common API patterns
        for key in ["title", "name", "headline"]:
            if key in data:
                title = str(data[key])
                break
        
        for key in ["content", "body", "description", "text"]:
            if key in data:
                content = str(data[key])
                break
        
        # Handle list responses
        if isinstance(data, list) and len(data) > 0:
            content = json.dumps(data[:10], indent=2)  # Store first 10 items
        
        content_hash = self._calculate_hash(json.dumps(data))
        
        return ScrapedData(
            id=content_hash[:20],
            source_url=str(task.url),
            source_type=DataSourceType.API,
            title=title,
            content=content,
            raw_content=json.dumps(data)[:50000],
            images=self._extract_images_from_data(data),
            videos=[],
            links=self._extract_links_from_data(data),
            language="en",
            status="completed",
            processing_time=(datetime.utcnow() - start_time).total_seconds(),
            confidence_score=0.9,
            hash=content_hash,
            duplicate_of=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
            structured_data=data if isinstance(data, dict) else {"data": data}
        )
    
    def _extract_with_fallbacks(self, soup: BeautifulSoup, task: ScrapingTask) -> ExtractionResult:
        """Extract data with multiple fallback strategies"""
        
        # Strategy 1: Custom selectors
        if task.custom_selectors:
            result = self._extract_with_custom_selectors(soup, task.custom_selectors)
            if result.title or result.content:
                return result
        
        # Strategy 2: Semantic selectors
        result = self._extract_with_semantic_selectors(soup)
        if result.title and result.content:
            return result
        
        # Strategy 3: Generic extraction
        result = self._extract_generic(soup)
        
        return result
    
    def _extract_with_custom_selectors(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> ExtractionResult:
        """Extract using custom CSS selectors"""
        title = None
        content = None
        metadata = {}
        media = []
        links = []
        
        for field, selector in selectors.items():
            element = soup.select_one(selector)
            if element:
                if field == "title":
                    title = element.get_text(strip=True)
                elif field == "content":
                    content = element.get_text(strip=True)
                elif field == "author":
                    metadata["author"] = element.get_text(strip=True)
                elif field == "date":
                    metadata["date"] = element.get_text(strip=True)
        
        return ExtractionResult(title, content, metadata, media, links)
    
    def _extract_with_semantic_selectors(self, soup: BeautifulSoup) -> ExtractionResult:
        """Extract using semantic HTML5 elements and common class patterns"""
        title = self._extract_first_match(soup, self.selectors["title"])
        content = self._extract_first_match(soup, self.selectors["content"], extract_text=True)
        
        metadata = {}
        author = self._extract_first_match(soup, self.selectors["author"])
        if author:
            metadata["author"] = author
        
        date = self._extract_date(soup)
        if date:
            metadata["date"] = date
        
        media = self._extract_media(soup)
        links = self._extract_links(soup)
        
        return ExtractionResult(title, content, metadata, media, links)
    
    def _extract_generic(self, soup: BeautifulSoup) -> ExtractionResult:
        """Generic extraction as last resort"""
        # Remove script and style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        # Get title
        title = soup.title.string if soup.title else None
        
        # Get main text content
        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
        
        if not content:
            # Fallback to all text
            content = soup.get_text(separator="\n", strip=True)
        
        media = self._extract_media(soup)
        links = self._extract_links(soup)
        
        return ExtractionResult(title, content, {}, media, links)
    
    def _extract_first_match(self, soup: BeautifulSoup, selectors: List[str], extract_text: bool = False) -> Optional[str]:
        """Try multiple selectors and return first match"""
        for selector in selectors:
            if selector.startswith("head "):
                element = soup.head.find(selector.replace("head ", "")) if soup.head else None
            else:
                element = soup.select_one(selector)
            
            if element:
                if extract_text:
                    text = element.get_text(strip=True)
                    if text and len(text) > 5:
                        return text
                else:
                    return element.get_text(strip=True)
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date from various formats"""
        # Try time element with datetime attribute
        time_elem = soup.find("time", {"datetime": True})
        if time_elem:
            return time_elem.get("datetime")
        
        # Try common date patterns
        date_elem = self._extract_first_match(soup, self.selectors["date"])
        if date_elem:
            return date_elem
        
        return None
    
    def _extract_media(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract media URLs"""
        media = []
        
        for selector in self.selectors["image"]:
            for img in soup.select(selector):
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if src:
                    media.append({
                        "type": "image",
                        "url": src,
                        "alt": img.get("alt", ""),
                        "width": img.get("width"),
                        "height": img.get("height")
                    })
        
        # Extract videos
        for video in soup.find_all("video"):
            sources = video.find_all("source")
            for source in sources:
                media.append({
                    "type": "video",
                    "url": source.get("src"),
                    "mime_type": source.get("type")
                })
        
        return media
    
    def _extract_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all links"""
        links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href")
            if href and not href.startswith(("#", "javascript:", "mailto:")):
                links.append({
                    "url": href,
                    "text": a.get_text(strip=True),
                    "title": a.get("title", "")
                })
        return links
    
    def _clean_content(self, content: Optional[str]) -> Optional[str]:
        """Clean and normalize content"""
        if not content:
            return content
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove special characters but keep punctuation
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', content)
        
        return content.strip()
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _detect_language(self, text: Optional[str]) -> Optional[str]:
        """Detect language of text"""
        if not text:
            return None
        
        # Simple heuristic based on common words
        english_words = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'I']
        text_lower = text.lower()
        
        count = sum(1 for word in english_words if word in text_lower)
        
        return "en" if count > 3 else "unknown"
    
    def _calculate_reading_time(self, content: Optional[str]) -> Optional[float]:
        """Calculate reading time in minutes"""
        if not content:
            return None
        
        words = len(content.split())
        return round(words / 200, 2)  # Average 200 words per minute
    
    def _calculate_confidence(self, extraction: ExtractionResult) -> float:
        """Calculate confidence score for extraction"""
        score = 0.0
        
        if extraction.title:
            score += 0.3
        if extraction.content and len(extraction.content) > 100:
            score += 0.4
        if extraction.metadata:
            score += 0.2
        if extraction.media:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_images_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """Extract images from nested data structure"""
        images = []
        
        def extract(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in ["image", "img", "picture", "thumbnail", "photo"]:
                        if isinstance(value, str):
                            images.append({"url": value, "field": f"{path}.{key}"})
                    elif isinstance(value, (dict, list)):
                        extract(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract(item, f"{path}[{i}]")
        
        extract(data)
        return images
    
    def _extract_links_from_data(self, data: Any) -> List[Dict[str, Any]]:
        """Extract links from nested data structure"""
        links = []
        
        def extract(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in ["url", "link", "href"]:
                        if isinstance(value, str) and value.startswith("http"):
                            links.append({"url": value, "field": f"{path}.{key}"})
                    elif isinstance(value, (dict, list)):
                        extract(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract(item, f"{path}[{i}]")
        
        extract(data)
        return links
