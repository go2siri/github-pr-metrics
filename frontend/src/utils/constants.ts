// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  WS_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
  TIMEOUT: 30000, // 30 seconds
};

// Application Constants
export const APP_CONFIG = {
  NAME: 'GitHub PR Metrics Analyzer',
  VERSION: '1.0.0',
  DESCRIPTION: 'Analyze pull request performance and team productivity',
};

// Chart Colors (consistent with Material-UI theme)
export const CHART_COLORS = {
  LIGHT: {
    PRIMARY: '#1976d2',
    SECONDARY: '#dc004e',
    SUCCESS: '#2e7d32',
    WARNING: '#ed6c02',
    ERROR: '#d32f2f',
    INFO: '#0288d1',
  },
  DARK: {
    PRIMARY: '#90caf9',
    SECONDARY: '#f48fb1',
    SUCCESS: '#4caf50',
    WARNING: '#ff9800',
    ERROR: '#f44336',
    INFO: '#29b6f6',
  },
};

// Date Formats
export const DATE_FORMATS = {
  DISPLAY: 'MMM dd, yyyy',
  DISPLAY_WITH_TIME: 'MMM dd, yyyy HH:mm',
  API: 'yyyy-MM-dd',
  ISO: "yyyy-MM-dd'T'HH:mm:ss.SSSxxx",
};

// GitHub URL Patterns
export const GITHUB_PATTERNS = {
  REPO_URL: /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/,
  OWNER_REPO: /^https:\/\/github\.com\/([a-zA-Z0-9_.-]+)\/([a-zA-Z0-9_.-]+)\/?$/,
};

// Default Values
export const DEFAULTS = {
  PAGE_SIZE: 25,
  MAX_CONTRIBUTORS_CHART: 10,
  MAX_RECONNECT_ATTEMPTS: 5,
  RECONNECT_INTERVAL: 3000,
  MAX_DATE_RANGE_MONTHS: 12,
};

// WebSocket Event Types
export const WS_EVENTS = {
  PROGRESS: 'progress',
  COMPLETED: 'completed',
  ERROR: 'error',
} as const;

// Analysis Statuses
export const ANALYSIS_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const;

// PR States
export const PR_STATES = {
  OPEN: 'open',
  CLOSED: 'closed',
  MERGED: 'merged',
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  THEME_MODE: 'darkMode',
  LAST_ANALYSIS: 'lastAnalysis',
  USER_PREFERENCES: 'userPreferences',
};

export default {
  API_CONFIG,
  APP_CONFIG,
  CHART_COLORS,
  DATE_FORMATS,
  GITHUB_PATTERNS,
  DEFAULTS,
  WS_EVENTS,
  ANALYSIS_STATUS,
  PR_STATES,
  STORAGE_KEYS,
};