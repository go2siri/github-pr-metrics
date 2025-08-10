import axios from 'axios';
import { AnalysisRequest, AnalysisResponse, PRMetric, MetricsSummary } from '../types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'Server error occurred';
      throw new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Unable to connect to server. Please check if the backend is running.');
    } else {
      // Something else happened
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

export const apiService = {
  // Start PR analysis
  async startAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await api.post<AnalysisResponse>('/api/analyze', request);
    return response.data;
  },

  // Get analysis status
  async getAnalysisStatus(analysisId: string): Promise<AnalysisResponse> {
    const response = await api.get<AnalysisResponse>(`/api/analysis/${analysisId}`);
    return response.data;
  },

  // Get analysis results
  async getAnalysisResults(analysisId: string): Promise<PRMetric[]> {
    const response = await api.get<PRMetric[]>(`/analysis/${analysisId}/results`);
    return response.data;
  },

  // Get metrics summary
  async getMetricsSummary(analysisId: string): Promise<MetricsSummary> {
    const response = await api.get<MetricsSummary>(`/analysis/${analysisId}/summary`);
    return response.data;
  },

  // Export data as CSV
  async exportCSV(analysisId: string): Promise<Blob> {
    const response = await api.get(`/analysis/${analysisId}/export/csv`, {
      responseType: 'blob',
      headers: {
        'Accept': 'text/csv',
      },
    });
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await api.get('/api/health');
    return response.data;
  },

  // Test GitHub token
  async testGitHubToken(token: string, repoUrl: string): Promise<{ valid: boolean; message: string }> {
    const response = await api.post('/test-token', {
      github_token: token,
      github_url: repoUrl,
    });
    return response.data;
  },

  // Validate GitHub URL
  validateGitHubUrl(url: string): { valid: boolean; message: string } {
    const githubUrlPattern = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
    
    if (!url) {
      return { valid: false, message: 'GitHub URL is required' };
    }
    
    if (!githubUrlPattern.test(url)) {
      return { valid: false, message: 'Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)' };
    }
    
    return { valid: true, message: 'Valid GitHub URL' };
  },

  // Validate date range
  validateDateRange(startDate?: string, endDate?: string): { valid: boolean; message: string } {
    if (!startDate && !endDate) {
      return { valid: true, message: 'Date range is optional' };
    }
    
    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      
      if (start > end) {
        return { valid: false, message: 'Start date must be before end date' };
      }
      
      const now = new Date();
      if (end > now) {
        return { valid: false, message: 'End date cannot be in the future' };
      }
      
      // Check if range is reasonable (not too far back)
      const oneYearAgo = new Date();
      oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
      
      if (start < oneYearAgo) {
        return { valid: false, message: 'Start date should not be more than one year ago for performance reasons' };
      }
    }
    
    return { valid: true, message: 'Valid date range' };
  },
};

export default apiService;