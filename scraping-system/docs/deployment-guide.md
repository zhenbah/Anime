# Enterprise Web Scraping System - Deployment Guide

## Overview

This guide covers deploying the Enterprise Web Scraping System in production environments.

## System Requirements

### Minimum Requirements
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space
- Docker 20.10+
- Docker Compose 2.0+

### Recommended Requirements
- 8+ CPU cores
- 16+ GB RAM
- 100+ GB SSD storage
- 1 Gbps network connection

## Deployment Options

### Option 1: Docker Compose (Recommended for Small/Medium)

```bash
# Clone repository
git clone <repository-url>
cd scraping-system

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings

# Start services
docker-compose up -d

# Verify services
docker-compose ps

# View logs
docker-compose logs -f scraping-api
```

### Option 2: Kubernetes (Recommended for Large Scale)

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraping-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scraping-api
  template:
    metadata:
      labels:
        app: scraping-api
    spec:
      containers:
      - name: api
        image: scraping-system:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: scraping-config
        - secretRef:
            name: scraping-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Option 3: Cloud Deployment

#### AWS ECS
```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name scraping-cluster

# Deploy services using task definitions
aws ecs create-service --cluster scraping-cluster \
  --service-name scraping-api \
  --task-definition scraping-api:1 \
  --desired-count 3
```

#### Google Cloud Run
```bash
gcloud run deploy scraping-api \
  --image gcr.io/project/scraping-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 10
```

## Database Configuration

### MongoDB

#### Standalone
```bash
# Enable authentication
echo "security:\n  authorization: enabled" >> /etc/mongod.conf

# Create admin user
use admin
db.createUser({
  user: "admin",
  pwd: "strong-password",
  roles: ["root"]
})
```

#### Replica Set (Production)
```bash
# Initiate replica set
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27017" },
    { _id: 2, host: "mongo3:27017" }
  ]
})
```

#### MongoDB Atlas
```bash
# Use connection string
MONGODB_URL="mongodb+srv://user:password@cluster.mongodb.net/scraping_db"
```

### Redis

#### Configuration
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### Redis Sentinel (High Availability)
```bash
sentinel monitor scraping-redis redis-master 6379 2
sentinel down-after-milliseconds scraping-redis 5000
sentinel failover-timeout scraping-redis 10000
```

## Load Balancing

### Nginx Configuration
```nginx
upstream scraping_api {
    least_conn;
    server api1:8000 weight=3;
    server api2:8000 weight=3;
    server api3:8000 weight=2;
}

server {
    listen 80;
    server_name scraping.example.com;

    location / {
        proxy_pass http://scraping_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api_rate burst=20 nodelay;
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}
```

## SSL/TLS Configuration

### Using Let's Encrypt
```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d scraping.example.com

# Auto-renewal
certbot renew --dry-run
```

## Monitoring Setup

### Prometheus
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'scraping-api'
    static_configs:
      - targets: ['api1:8000', 'api2:8000', 'api3:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Scraping System",
    "panels": [
      {
        "title": "Requests per Second",
        "targets": [{"expr": "rate(scraping_requests_total[5m])"}]
      },
      {
        "title": "Error Rate",
        "targets": [{"expr": "rate(scraping_errors_total[5m])"}]
      },
      {
        "title": "Queue Size",
        "targets": [{"expr": "scraping_queue_size"}]
      }
    ]
  }
}
```

## Backup Strategy

### MongoDB Backups
```bash
#!/bin/bash
# Daily backup
mongodump --host localhost:27017 \
  --username admin \
  --password password \
  --db scraping_db \
  --out /backup/mongodb/$(date +%Y%m%d)

# Compress
tar -czf /backup/mongodb/$(date +%Y%m%d).tar.gz \
  /backup/mongodb/$(date +%Y%m%d)

# Remove old backups (keep 30 days)
find /backup/mongodb -name "*.tar.gz" -mtime +30 -delete
```

### Redis Backups
```bash
# RDB snapshot
redis-cli BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/redis/dump-$(date +%Y%m%d).rdb
```

## Security Hardening

### Network Security
```bash
# Firewall rules
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 27017/tcp # MongoDB (internal only)
ufw allow 6379/tcp  # Redis (internal only)
ufw enable
```

### Application Security
```python
# Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

## Performance Tuning

### MongoDB Optimization
```javascript
// Index optimization
db.scraped_data.createIndex({ 
  "source_url": 1, 
  "scraped_at": -1 
}, { 
  background: true 
})

// Query optimization
db.scraped_data.find(
  { "scraped_at": { $gte: ISODate("2024-01-01") } }
).hint("source_url_1_scraped_at_-1")
```

### Redis Optimization
```bash
# redis.conf
tcp-backlog 511
timeout 0
tcp-keepalive 300
maxmemory-policy allkeys-lru
```

## Scaling Guidelines

### Vertical Scaling
- Increase CPU/RAM for API instances
- Upgrade MongoDB to higher tier
- Use Redis Enterprise

### Horizontal Scaling
- Add more API replicas
- Implement MongoDB sharding
- Use Redis Cluster
- Deploy in multiple regions

### Auto-scaling (Cloud)
```yaml
# AWS Auto Scaling Policy
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ASGAverageCPUUtilization"
  },
  "ScaleOutCooldown": 60,
  "ScaleInCooldown": 300
}
```

## Disaster Recovery

### RTO/RPO Planning
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 15 minutes

### Recovery Procedures
```bash
# Restore MongoDB
mongorestore --host new-host:27017 \
  --username admin \
  --password password \
  /backup/mongodb/latest

# Restore Redis
cp /backup/redis/latest.rdb /var/lib/redis/dump.rdb
redis-cli SHUTDOWN NOSAVE
redis-server /etc/redis/redis.conf
```

## Compliance

### GDPR Compliance
- Anonymize personal data
- Implement right to deletion
- Data retention policies
- Encryption at rest and in transit

### CCPA Compliance
- Do Not Sell mechanism
- Data access requests
- Deletion requests

## Maintenance

### Regular Tasks
```bash
# Daily
- Check backup status
- Review error logs
- Monitor disk space

# Weekly
- Review performance metrics
- Update security patches
- Test disaster recovery

# Monthly
- Rotate secrets and keys
- Review access logs
- Optimize database indexes
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory
free -h
docker stats

# Solutions
# 1. Reduce MAX_CONCURRENT_REQUESTS
# 2. Limit batch sizes
# 3. Enable Redis persistence
```

#### Slow Performance
```bash
# Check slow queries
mongotop
mongostat

# Check Redis
redis-cli SLOWLOG GET
```

#### Connection Issues
```bash
# Test connectivity
telnet mongodb 27017
telnet redis 6379

# Check DNS
docker-compose exec scraping-api nslookup mongodb
```

## Production Checklist

- [ ] SSL/TLS configured
- [ ] Authentication enabled
- [ ] Rate limiting active
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Logging centralized
- [ ] Alerts configured
- [ ] Security headers set
- [ ] CORS configured
- [ ] Database indexed
- [ ] Redis configured
- [ ] Load balancer setup
- [ ] Auto-scaling enabled
- [ ] Disaster recovery tested
- [ ] Documentation updated

## Support

For production issues:
1. Check monitoring dashboards
2. Review application logs
3. Verify database connectivity
4. Check resource utilization
5. Contact support team
