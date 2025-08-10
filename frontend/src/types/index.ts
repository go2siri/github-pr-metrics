export interface PRMetric {
  id: number;
  pr_number: number;
  title: string;
  author: string;
  created_at: string;
  merged_at: string | null;
  closed_at: string | null;
  state: string;
  review_time_hours: number | null;
  time_to_merge_hours: number | null;
  lines_added: number;
  lines_deleted: number;
  files_changed: number;
  commits: number;
  reviews_count: number;
  review_comments: number;
}

export interface AnalysisRequest {
  github_url: string;
  github_token: string;
  start_date?: string;
  end_date?: string;
}

export interface AnalysisResponse {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message?: string;
  progress?: number;
  analysis_metadata?: {
    total_repositories: number;
    total_developers: number;
    total_prs_processed: number;
    analysis_duration: number;
  };
  repository_metrics?: Array<{
    repository: string;
    total_prs: number;
    developers: Record<string, {
      developer: string;
      basic_metrics: {
        total: number;
        open: number;
        merged: number;
        closed: number;
        draft: number;
      };
      productivity_metrics: {
        merge_rate_percent: number;
      };
    }>;
  }>;
  global_insights?: any;
  error?: string;
}

export interface WebSocketMessage {
  type: 'progress' | 'completed' | 'error';
  analysis_id: string;
  progress?: number;
  message?: string;
  data?: PRMetric[];
  error?: string;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }[];
}

export interface MetricsSummary {
  total_prs: number;
  avg_review_time: number;
  avg_merge_time: number;
  avg_lines_changed: number;
  top_contributors: {
    author: string;
    pr_count: number;
  }[];
  monthly_trends: {
    month: string;
    pr_count: number;
    avg_review_time: number;
  }[];
}

export interface FilterOptions {
  author?: string;
  state?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  minReviewTime?: number;
  maxReviewTime?: number;
}

export interface SortOption {
  field: keyof PRMetric;
  direction: 'asc' | 'desc';
}

export interface ThemeMode {
  mode: 'light' | 'dark';
}