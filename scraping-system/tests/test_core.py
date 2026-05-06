import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.scraping_system.schemas.scraping import ScrapingTask, ScrapingMethod, Priority
from src.scraping_system.schemas.data import ScrapedData, DataSourceType
from src.scraping_system.services.parser_engine import ParserEngine
from src.scraping_system.services.data_processor import DataProcessor

class TestParserEngine:
    """Test ParserEngine functionality"""
    
    def setup_method(self):
        self.parser = ParserEngine()
        self.task = ScrapingTask(
            url="https://example.com",
            method=ScrapingMethod.HTTP,
            priority=Priority.NORMAL
        )
    
    def test_parse_html_content(self):
        """Test parsing HTML content"""
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Article Title</h1>
                <div class="content">This is the article content.</div>
                <img src="image.jpg" alt="Test Image">
                <a href="https://example.com/link">Link</a>
            </body>
        </html>
        """
        
        result = self.parser.parse(html, self.task)
        
        # Parser prioritizes h1 over title tag
        assert result.title == "Article Title"
        assert result.content is not None
        assert len(result.images) == 1
        assert len(result.links) == 1
        assert result.source_type == DataSourceType.HTML
    
    def test_parse_json_content(self):
        """Test parsing JSON/API content"""
        json_content = '{"title": "API Response", "content": "API data"}'
        
        result = self.parser.parse(json_content, self.task)
        
        assert result.source_type == DataSourceType.API
        assert result.structured_data is not None
    
    def test_extract_with_custom_selectors(self):
        """Test extraction with custom selectors"""
        html = """
        <html>
            <body>
                <h1 class="custom-title">Custom Title</h1>
                <div class="custom-content">Custom Content</div>
            </body>
        </html>
        """
        
        self.task.custom_selectors = {
            "title": ".custom-title",
            "content": ".custom-content"
        }
        
        result = self.parser.parse(html, self.task)
        
        assert result.title == "Custom Title"

class TestDataProcessor:
    """Test DataProcessor functionality"""
    
    def setup_method(self):
        self.processor = DataProcessor()
    
    def test_clean_text(self):
        """Test text cleaning"""
        dirty_text = "  Hello   World  \n\n  "
        clean = self.processor._clean_text(dirty_text)
        
        assert clean == "Hello World"
    
    def test_generate_hash(self):
        """Test hash generation"""
        data = ScrapedData(
            id="test",
            source_url="https://example.com",
            source_type=DataSourceType.HTML,
            title="Test",
            content="Test content"
        )
        
        hash1 = self.processor._generate_hash(data)
        hash2 = self.processor._generate_hash(data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length
    
    def test_deduplicate(self):
        """Test deduplication"""
        item1 = ScrapedData(
            id="1",
            source_url="https://example.com/1",
            source_type=DataSourceType.HTML,
            hash="hash1"
        )
        item2 = ScrapedData(
            id="2",
            source_url="https://example.com/2",
            source_type=DataSourceType.HTML,
            hash="hash1"  # Duplicate hash
        )
        item3 = ScrapedData(
            id="3",
            source_url="https://example.com/3",
            source_type=DataSourceType.HTML,
            hash="hash2"
        )
        
        items = [item1, item2, item3]
        unique = self.processor.deduplicate(items)
        
        assert len(unique) == 2
        assert unique[0].hash == "hash1"
        assert unique[1].hash == "hash2"
    
    def test_extract_entities(self):
        """Test entity extraction"""
        data = ScrapedData(
            id="test",
            source_url="https://example.com",
            source_type=DataSourceType.HTML,
            content="Contact us at email@example.com or visit https://example.com"
        )
        
        processed = self.processor._extract_entities(data)
        
        assert "entities" in processed.structured_data
        assert len(processed.structured_data["entities"]["emails"]) == 1
        assert len(processed.structured_data["entities"]["urls"]) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
