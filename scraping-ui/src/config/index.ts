export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export const REFRESH_INTERVALS = {
  metrics: 5000,
  logs: 2000,
  status: 10000,
} as const;

export const MAX_RETRIES = 3;
export const RETRY_DELAY = 1000;

export const ITEMS_PER_PAGE = 20;

export const DATE_FORMAT = 'yyyy-MM-dd HH:mm:ss';
