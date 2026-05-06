export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

export interface ScrapingTask {
  id: string;
  url: string;
  method: 'http' | 'browser' | 'auto';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  createdAt: string;
  completedAt?: string;
}

export interface ScrapedData {
  id: string;
  title: string;
  url: string;
  content: string;
  images: string[];
  metadata: {
    author?: string;
    date?: string;
    language?: string;
  };
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: string;
}

export interface SystemMetrics {
  totalScraped: number;
  activeScrapers: number;
  successRate: number;
  errorRate: number;
  queueSize: number;
  requestsPerMinute: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
  details?: string;
}

export interface Proxy {
  id: string;
  url: string;
  type: 'residential' | 'datacenter';
  status: 'active' | 'inactive' | 'failed';
  lastUsed?: string;
  failureCount: number;
}
