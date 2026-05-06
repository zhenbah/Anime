from typing import Optional, Dict, Any, List
import logging
import hashlib
from datetime import datetime

from src.scraping_system.schemas.data import ScrapedData

logger = logging.getLogger(__name__)

class DataProcessor:
    """Data cleaning, normalization, and deduplication"""
    
    def __init__(self):
        self.stop_words = set([
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with'
        ])
    
    def process(self, data: ScrapedData) -> ScrapedData:
        """Process scraped data through the pipeline"""
        logger.info(f"Processing data from {data.source_url}")
        
        # Step 1: Clean and normalize
        data = self._clean_data(data)
        
        # Step 2: Extract entities
        data = self._extract_entities(data)
        
        # Step 3: Generate hash for deduplication
        data.hash = self._generate_hash(data)
        
        # Step 4: Validate schema
        self._validate_schema(data)
        
        # Step 5: Enrich data
        data = self._enrich_data(data)
        
        logger.info(f"Data processing completed for {data.source_url}")
        return data
    
    def _clean_data(self, data: ScrapedData) -> ScrapedData:
        """Clean and normalize data fields"""
        # Clean title
        if data.title:
            data.title = self._clean_text(data.title)
        
        # Clean content
        if data.content:
            data.content = self._clean_text(data.content)
            # Remove excessive whitespace
            data.content = ' '.join(data.content.split())
        
        # Clean author
        if data.author:
            data.author = self._clean_text(data.author)
        
        # Clean media URLs
        for media in data.images:
            if 'url' in media:
                media['url'] = media['url'].strip()
        
        for media in data.videos:
            if 'url' in media:
                media['url'] = media['url'].strip()
        
        # Normalize URLs in links
        for link in data.links:
            if 'url' in link:
                link['url'] = self._normalize_url(link['url'], data.source_url)
        
        return data
    
    def _clean_text(self, text: str) -> str:
        """Clean text content"""
        if not text:
            return text
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common boilerplate
        boilerplate = [
            "Advertisement", "Ad", "Sponsored", "Promoted",
            "Related Articles", "You might also like",
            "Subscribe", "Newsletter", "Copyright",
            "All rights reserved", "Terms of Service",
            "Privacy Policy", "Cookie Policy"
        ]
        
        for phrase in boilerplate:
            text = text.replace(phrase, '')
        
        return text.strip()
    
    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize URL to absolute form"""
        from urllib.parse import urljoin
        
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return urljoin(base_url, url)
        elif not url.startswith('http'):
            return urljoin(base_url, url)
        
        return url
    
    def _extract_entities(self, data: ScrapedData) -> ScrapedData:
        """Extract named entities from content"""
        if not data.content:
            return data
        
        # Simple entity extraction (can be enhanced with NLP libraries)
        entities = {
            'emails': self._extract_emails(data.content),
            'phone_numbers': self._extract_phone_numbers(data.content),
            'urls': self._extract_urls(data.content),
            'hashtags': self._extract_hashtags(data.content),
        }
        
        data.structured_data['entities'] = entities
        return data
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        import re
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers"""
        import re
        pattern = r'\+?[\d\s\-\(\)]{10,}'
        return re.findall(pattern, text)
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        import re
        pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
        return re.findall(pattern, text)
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags"""
        import re
        pattern = r'#\w+'
        return re.findall(pattern, text)
    
    def _generate_hash(self, data: ScrapedData) -> str:
        """Generate hash for deduplication"""
        content_to_hash = ""
        
        if data.title:
            content_to_hash += data.title
        if data.content:
            content_to_hash += data.content[:1000]  # Use first 1000 chars
        
        return hashlib.sha256(content_to_hash.encode()).hexdigest()
    
    def _validate_schema(self, data: ScrapedData):
        """Validate data schema"""
        errors = []
        
        # Check required fields
        if not data.source_url:
            errors.append("source_url is required")
        
        if not data.hash:
            errors.append("hash is required")
        
        # Validate URL format
        if data.source_url:
            from urllib.parse import urlparse
            try:
                result = urlparse(data.source_url)
                if not all([result.scheme, result.netloc]):
                    errors.append(f"Invalid URL: {data.source_url}")
            except:
                errors.append(f"Invalid URL format: {data.source_url}")
        
        if errors:
            logger.warning(f"Schema validation errors: {errors}")
            # Don't raise exception, just log for now
    
    def _enrich_data(self, data: ScrapedData) -> ScrapedData:
        """Enrich data with additional information"""
        # Add processing timestamp
        data.processed_at = datetime.utcnow()
        
        # Calculate content statistics
        if data.content:
            data.word_count = len(data.content.split())
            data.reading_time = self._calculate_reading_time(data.content)
        
        # Detect content type
        data.content_type = self._detect_content_type(data)
        
        # Add quality metrics
        data.quality_score = self._calculate_quality_score(data)
        
        return data
    
    def _detect_content_type(self, data: ScrapedData) -> str:
        """Detect content type"""
        if data.source_type == "api":
            return "api_data"
        
        if data.word_count and data.word_count > 500:
            return "long_form"
        elif data.word_count and data.word_count > 100:
            return "article"
        else:
            return "short_content"
    
    def _calculate_quality_score(self, data: ScrapedData) -> float:
        """Calculate data quality score"""
        score = 0.0
        
        # Content completeness
        if data.content and len(data.content) > 100:
            score += 0.3
        
        # Metadata completeness
        if data.author:
            score += 0.1
        if data.publish_date:
            score += 0.1
        if data.language:
            score += 0.1
        
        # Media presence
        if data.images:
            score += 0.1
        
        # Structure
        if data.structured_data:
            score += 0.2
        
        # Confidence from parser
        score += data.confidence_score * 0.1
        
        return min(score, 1.0)
    
    def _calculate_reading_time(self, content: str) -> float:
        """Calculate reading time in minutes"""
        words = len(content.split())
        return round(words / 200, 2)
    
    def deduplicate(self, items: List[ScrapedData]) -> List[ScrapedData]:
        """Remove duplicate items"""
        seen_hashes = set()
        unique_items = []
        
        for item in items:
            if item.hash not in seen_hashes:
                seen_hashes.add(item.hash)
                unique_items.append(item)
            else:
                logger.info(f"Duplicate detected: {item.source_url}")
                item.status = "duplicate"
        
        return unique_items
    
    def batch_process(self, items: List[ScrapedData]) -> List[ScrapedData]:
        """Process multiple items"""
        processed = []
        
        for item in items:
            try:
                processed_item = self.process(item)
                processed.append(processed_item)
            except Exception as e:
                logger.error(f"Failed to process item {item.source_url}: {e}")
                item.status = "failed"
                processed.append(item)
        
        # Deduplicate
        processed = self.deduplicate(processed)
        
        return processed
