# Initialize MongoDB with custom settings

db = db.getSiblingDB('scraping_db');

# Create users
db.createUser({
  user: "admin",
  pwd: "password",
  roles: ["readWrite", "dbAdmin"]
});

# Create indexes for better performance
db.scraped_data.createIndex({ "hash": 1 }, { unique: true });
db.scraped_data.createIndex({ "source_url": 1 });
db.scraped_data.createIndex({ "scraped_at": -1 });
db.scraped_data.createIndex({ "status": 1 });
db.scraped_data.createIndex({ "title": "text", "content": "text" });

db.scraping_tasks.createIndex({ "status": 1 });
db.scraping_tasks.createIndex({ "created_at": -1 });
db.scraping_tasks.createIndex({ "scheduled_at": 1 });
db.scraping_tasks.createIndex({ "priority": 1 });

db.queue_items.createIndex({ "status": 1 });
db.queue_items.createIndex({ "worker_id": 1 });
db.queue_items.createIndex({ "created_at": -1 });

db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });

db.api_keys.createIndex({ "key": 1 }, { unique: true });
db.api_keys.createIndex({ "user_id": 1 });

db.proxies.createIndex({ "url": 1 }, { unique: true });
db.proxies.createIndex({ "is_active": 1 });

db.scheduled_tasks.createIndex({ "active": 1 });
db.scheduled_tasks.createIndex({ "next_run": 1 });

print("MongoDB initialized successfully");