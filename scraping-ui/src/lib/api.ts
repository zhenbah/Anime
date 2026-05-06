import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Scraping endpoints
export const scraperApi = {
  scrape: (data: any) => api.post('/scrape', data),
  scrapeBatch: (data: any) => api.post('/scrape/batch', data),
  startCrawl: (data: any) => api.post('/crawl', data),
  startDistributedCrawl: (data: any, params?: any) => 
    api.post('/crawl/distributed', data, { params }),
  getQueueStatus: () => api.get('/queue/status'),
};

// Data endpoints
export const dataApi = {
  getData: (params?: any) => api.get('/data', { params }),
  searchData: (query: string) => api.get(`/data/search?query=${query}`),
  getDataById: (id: string) => api.get(`/data/${id}`),
};

// Auth endpoints
export const authApi = {
  login: (data: any) => api.post('/auth/token', data),
  register: (data: any) => api.post('/auth/register', data),
  createApiKey: (data: any) => api.post('/auth/api-key', data),
};

// System endpoints
export const systemApi = {
  getMetrics: () => api.get('/metrics'),
  getHealth: () => api.get('/health'),
};
