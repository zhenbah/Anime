# Enterprise Web Scraping System

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the system
python -m src.scraping_system.main
```

## Project Structure

```
scraping-system/
├── src/
│   └── scraping_system/
│       ├── main.py              # FastAPI application
│       ├── core/
│       │   └── config.py        # Configuration
│       ├── services/
│       │   ├── database_service.py    # MongoDB + Redis
│       │   ├── fetcher_service.py     # HTTP + Browser fetching
│       │   ├── parser_engine.py       # Content extraction
│       │   ├── data_processor.py      # Data cleaning
│       │   ├── crawler_service.py     # URL discovery
│       │   ├── proxy_service.py       # Proxy rotation
│       │   └── queue_service.py       # Queue management
│       ├── models/              # Database models
│       ├── schemas/             # Pydantic schemas
│       ├── security/            # Auth & encryption
│       ├── monitoring/          # Metrics & logging
│       ├── automation/          # Scheduling
│       └── api/                 # REST API
├── docker/                     # Docker configuration
├── examples/                   # Example scrapers
└── docs/                       # Documentation
```

## Features

### Distributed Crawling
- Queue-based architecture
- Worker nodes
- Horizontal scaling

### High Performance
- Async/await
- Connection pooling
- Batch processing

### Security
- JWT authentication
- Rate limiting
- Proxy rotation
- Encryption

### Intelligence
- Auto-detection
- Fallback strategies
- Deduplication

## API Usage

### Scrape URL
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Authorization: Bearer TOKEN" \
  -d '{"url": "https://example.com"}'
```

### Batch Scrape
```bash
curl -X POST http://localhost:8000/api/v1/scrape/batch \
  -H "Authorization: Bearer TOKEN" \
  -d '[{"url": "https://example.com/1"}]'
```

### Distributed Crawl
```bash
curl -X POST http://localhost:8000/api/v1/crawl/distributed \
  -H "Authorization: Bearer TOKEN" \
  -d '{"url": "https://example.com"}'
```

## Configuration

Edit `.env` file:

```bash
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
MAX_CONCURRENT_REQUESTS=100
```

## Docker Deployment

```bash
docker-compose up -d
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run worker
python -m src.scraping_system.worker
```

## Documentation

See [Deployment Guide](docs/deployment-guide.md) for detailed deployment instructions.
