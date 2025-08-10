import { format, parseISO, differenceInHours, differenceInDays } from 'date-fns';
import { DATE_FORMATS, GITHUB_PATTERNS } from './constants';

/**
 * Format a date string or Date object for display
 */
export const formatDate = (
  date: string | Date | null,
  formatString: string = DATE_FORMATS.DISPLAY
): string => {
  if (!date) return 'N/A';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatString);
  } catch {
    return 'Invalid Date';
  }
};

/**
 * Format hours into a human-readable duration
 */
export const formatDuration = (hours: number | null): string => {
  if (hours === null || hours === undefined) return 'N/A';
  
  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes}m`;
  } else if (hours < 24) {
    return `${hours.toFixed(1)}h`;
  } else {
    const days = Math.floor(hours / 24);
    const remainingHours = Math.round(hours % 24);
    
    if (remainingHours === 0) {
      return `${days}d`;
    }
    return `${days}d ${remainingHours}h`;
  }
};

/**
 * Calculate time difference between two dates in hours
 */
export const calculateHoursDifference = (
  start: string | Date,
  end: string | Date
): number => {
  const startDate = typeof start === 'string' ? parseISO(start) : start;
  const endDate = typeof end === 'string' ? parseISO(end) : end;
  
  return differenceInHours(endDate, startDate);
};

/**
 * Validate GitHub repository URL
 */
export const validateGitHubUrl = (url: string): { valid: boolean; message: string } => {
  if (!url) {
    return { valid: false, message: 'GitHub URL is required' };
  }
  
  if (!GITHUB_PATTERNS.REPO_URL.test(url)) {
    return { 
      valid: false, 
      message: 'Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)' 
    };
  }
  
  return { valid: true, message: 'Valid GitHub URL' };
};

/**
 * Extract owner and repository name from GitHub URL
 */
export const parseGitHubUrl = (url: string): { owner: string; repo: string } | null => {
  const match = url.match(GITHUB_PATTERNS.OWNER_REPO);
  
  if (match) {
    return {
      owner: match[1],
      repo: match[2],
    };
  }
  
  return null;
};

/**
 * Format file size in bytes to human-readable format
 */
export const formatFileSize = (bytes: number): string => {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  
  if (bytes === 0) return '0 Bytes';
  
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const formattedSize = (bytes / Math.pow(1024, i)).toFixed(1);
  
  return `${formattedSize} ${sizes[i]}`;
};

/**
 * Generate a random color for charts
 */
export const generateRandomColor = (opacity: number = 1): string => {
  const r = Math.floor(Math.random() * 255);
  const g = Math.floor(Math.random() * 255);
  const b = Math.floor(Math.random() * 255);
  
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
};

/**
 * Download data as JSON file
 */
export const downloadJSON = (data: any, filename: string): void => {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename.endsWith('.json') ? filename : `${filename}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
};

/**
 * Download data as CSV file
 */
export const downloadCSV = (data: any[], filename: string): void => {
  if (data.length === 0) return;
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escape commas and quotes in CSV
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename.endsWith('.csv') ? filename : `${filename}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
};

/**
 * Debounce function to limit frequent calls
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

/**
 * Throttle function to limit call frequency
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Check if a value is empty (null, undefined, empty string, empty array, empty object)
 */
export const isEmpty = (value: any): boolean => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim().length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

/**
 * Deep clone an object
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as any;
  if (Array.isArray(obj)) return obj.map(deepClone) as any;
  
  const cloned = {} as T;
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key]);
    }
  }
  
  return cloned;
};

/**
 * Safe JSON parse with fallback
 */
export const safeJSONParse = <T>(str: string, fallback: T): T => {
  try {
    return JSON.parse(str);
  } catch {
    return fallback;
  }
};

export default {
  formatDate,
  formatDuration,
  calculateHoursDifference,
  validateGitHubUrl,
  parseGitHubUrl,
  formatFileSize,
  generateRandomColor,
  downloadJSON,
  downloadCSV,
  debounce,
  throttle,
  isEmpty,
  deepClone,
  safeJSONParse,
};