from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class AnalysisRequest(BaseModel):
    """Request model for PR analysis"""
    owner: Optional[str] = Field(None, description="Repository owner")
    repo: Optional[str] = Field(None, description="Repository name")
    github_token: str = Field(..., description="GitHub API token")
    since: Optional[datetime] = Field(None, description="Start date for analysis (ISO format)")
    until: Optional[datetime] = Field(None, description="End date for analysis (ISO format)")
    github_url: Optional[str] = Field(None, description="Full GitHub repository URL (alternative to owner/repo)")
    
    @field_validator('owner')
    @classmethod
    def validate_owner(cls, v):
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("Owner cannot be empty")
        # Basic GitHub username/org validation
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', v.strip()):
            raise ValueError("Invalid owner format")
        return v.strip()
    
    @field_validator('repo')
    @classmethod
    def validate_repo(cls, v):
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError("Repository name cannot be empty")
        # Basic GitHub repo name validation
        if not re.match(r'^[a-zA-Z0-9._-]+$', v.strip()):
            raise ValueError("Invalid repository name format")
        return v.strip()
    
    @field_validator('github_token')
    @classmethod
    def validate_token(cls, v):
        if not v or not v.strip():
            raise ValueError("GitHub token cannot be empty")
        # Basic token format validation (GitHub tokens are typically 40 chars)
        if len(v.strip()) < 20:
            raise ValueError("GitHub token appears to be too short")
        return v.strip()
    
    @model_validator(mode='after')
    def validate_github_url_or_owner_repo(self):
        if self.github_url:
            # Parse GitHub URL to extract owner and repo
            github_url_pattern = r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
            match = re.match(github_url_pattern, self.github_url.strip())
            if match:
                self.owner = match.group(1)
                self.repo = match.group(2).rstrip('.git')
            else:
                raise ValueError("Invalid GitHub URL format. Expected: https://github.com/owner/repo")
        elif not (self.owner and self.repo):
            raise ValueError("Either github_url or both owner and repo must be provided")
        
        return self
    
    @model_validator(mode='after')
    def validate_date_range(self):
        if self.since and self.until and self.since >= self.until:
            raise ValueError("'since' date must be before 'until' date")
        
        return self


class TaskStatus(BaseModel):
    """Task status model"""
    task_id: str
    status: str = Field(..., description="Task status: pending, running, completed, failed")
    progress: int = Field(0, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Current status message")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class PRMetrics(BaseModel):
    """Individual PR metrics"""
    number: int
    title: str
    state: str
    created_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits: int = 0
    url: str


class DeveloperMetrics(BaseModel):
    """Metrics for a single developer"""
    developer: str
    basic_metrics: Dict[str, int] = Field(default_factory=lambda: {
        'total': 0, 'open': 0, 'merged': 0, 'closed': 0, 'draft': 0
    })
    time_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    size_metrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    productivity_metrics: Dict[str, float] = Field(default_factory=dict)
    prs_data: List[PRMetrics] = Field(default_factory=list)


class RepositoryMetrics(BaseModel):
    """Metrics for a repository"""
    repository: str
    total_prs: int = 0
    developers: Dict[str, DeveloperMetrics] = Field(default_factory=dict)
    summary: Dict[str, int] = Field(default_factory=lambda: {
        'total': 0, 'open': 0, 'merged': 0, 'closed': 0, 'draft': 0
    })


class GlobalInsights(BaseModel):
    """Global insights across all repositories"""
    average_time_to_merge_hours: float = 0.0
    median_time_to_merge_hours: float = 0.0
    average_pr_size_lines: float = 0.0
    most_active_developer: Optional[str] = None
    total_repositories: int = 0
    total_developers: int = 0
    total_prs_processed: int = 0


class AnalysisMetadata(BaseModel):
    """Analysis metadata"""
    total_repositories: int
    total_developers: int
    total_prs_processed: int
    analysis_duration: float
    date_range: Dict[str, Optional[datetime]]


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    task_id: str
    status: str
    analysis_metadata: AnalysisMetadata
    repository_metrics: List[RepositoryMetrics] = Field(default_factory=list)
    global_insights: GlobalInsights
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    task_id: str
    message_type: str = Field(..., description="Message type: progress, status, error, complete")
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v):
        allowed_types = ['progress', 'status', 'error', 'complete', 'started']
        if v not in allowed_types:
            raise ValueError(f"Message type must be one of: {allowed_types}")
        return v


class ProgressUpdate(BaseModel):
    """Progress update model"""
    task_id: str
    progress: int = Field(..., ge=0, le=100)
    message: str
    current_step: str
    total_steps: int = 0
    current_step_number: int = 0


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    uptime_seconds: float
    github_api_accessible: bool = False


class AnalysisTaskCreate(BaseModel):
    """Model for creating a new analysis task"""
    request_data: AnalysisRequest
    task_id: Optional[str] = None


class AnalysisTaskResponse(BaseModel):
    """Response when creating a new analysis task"""
    task_id: str
    status: str = "pending"
    message: str = "Analysis task created successfully"
    websocket_url: str
    status_url: str
    created_at: datetime = Field(default_factory=datetime.now)