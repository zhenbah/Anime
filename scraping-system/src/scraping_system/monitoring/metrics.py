import logging
from typing import Optional, Dict, Any
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge
import time

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and exposes system metrics"""
    
    def __init__(self):
        # Request metrics
        self.requests_total = Counter(
            'scraping_requests_total',
            'Total number of scraping requests',
            ['method', 'status']
        )
        
        self.request_duration = Histogram(
            'scraping_request_duration_seconds',
            'Request duration in seconds',
            ['method']
        )
        
        # Data metrics
        self.data_extracted_total = Counter(
            'scraping_data_extracted_total',
            'Total amount of data extracted',
            ['type']
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'scraping_queue_size',
            'Current queue size',
            ['priority']
        )
        
        # System metrics
        self.active_workers = Gauge(
            'scraping_active_workers',
            'Number of active workers'
        )
        
        self.errors_total = Counter(
            'scraping_errors_total',
            'Total number of errors',
            ['type']
        )
        
        # Custom metrics storage
        self.custom_metrics: Dict[str, Any] = {}
    
    def record_request(self, method: str, status: str, duration: float):
        """Record a scraping request"""
        self.requests_total.labels(method=method, status=status).inc()
        self.request_duration.labels(method=method).observe(duration)
    
    def record_data_extracted(self, data_type: str, count: int = 1):
        """Record extracted data"""
        self.data_extracted_total.labels(type=data_type).inc(count)
    
    def record_error(self, error_type: str):
        """Record an error"""
        self.errors_total.labels(type=error_type).inc()
    
    def set_queue_size(self, priority: str, size: int):
        """Set queue size metric"""
        self.queue_size.labels(priority=priority).set(size)
    
    def set_active_workers(self, count: int):
        """Set active workers count"""
        self.active_workers.set(count)
    
    def set_custom_metric(self, name: str, value: Any):
        """Set custom metric"""
        self.custom_metrics[name] = {
            "value": value,
            "timestamp": datetime.utcnow()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            "requests": {
                "total": self.requests_total._metrics,
                "duration": self.request_duration._metrics
            },
            "data": {
                "extracted": self.data_extracted_total._metrics
            },
            "queue": {
                "size": self.queue_size._metrics
            },
            "workers": {
                "active": self.active_workers._value.get()
            },
            "errors": {
                "total": self.errors_total._metrics
            },
            "custom": self.custom_metrics
        }

class Logger:
    """Custom logger with structured logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log("DEBUG", message, **kwargs)
    
    def _log(self, level: str, message: str, **kwargs):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        }
        
        if kwargs:
            log_data.update(kwargs)
        
        log_message = json.dumps(log_data)
        
        if level == "ERROR":
            self.logger.error(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "DEBUG":
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alerts: list = []
        self.thresholds = {
            "error_rate": 0.1,  # 10% error rate
            "queue_size": 1000,  # 1000 items in queue
            "response_time": 30  # 30 seconds
        }
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> list:
        """Check if any thresholds are exceeded"""
        alerts = []
        
        # Check error rate
        total_requests = sum(
            m._value.get() for m in metrics.get("requests", {}).get("total", [])
        )
        total_errors = sum(
            m._value.get() for m in metrics.get("errors", {}).get("total", [])
        )
        
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > self.thresholds["error_rate"]:
                alerts.append({
                    "type": "error_rate",
                    "message": f"Error rate exceeded: {error_rate:.2%}",
                    "severity": "high",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Check queue size
        queue_sizes = metrics.get("queue", {}).get("size", [])
        for queue_metric in queue_sizes:
            if queue_metric._value.get() > self.thresholds["queue_size"]:
                alerts.append({
                    "type": "queue_size",
                    "message": f"Queue size exceeded: {queue_metric._value.get()}",
                    "severity": "medium",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        return alerts
    
    def add_alert(self, alert: Dict[str, Any]):
        """Add alert to list"""
        self.alerts.append(alert)
        logger.warning(f"Alert: {alert['message']}")
    
    def get_recent_alerts(self, limit: int = 10) -> list:
        """Get recent alerts"""
        return self.alerts[-limit:]

def setup_logging():
    """Setup structured logging"""
    import json_log_formatter
    
    formatter = json_log_formatter.JSONFormatter()
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger
