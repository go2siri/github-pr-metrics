import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import traceback

# Import existing modules
import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from github_client import GitHubClient, GitHubAPIError, RateLimitError
from pr_analyzer import PRAnalyzer
from backend.models import (
    AnalysisRequest, AnalysisResponse, TaskStatus, WebSocketMessage, 
    ProgressUpdate, DeveloperMetrics, RepositoryMetrics, GlobalInsights,
    AnalysisMetadata, PRMetrics
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for handling PR analysis tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskStatus] = {}
        self.results: Dict[str, AnalysisResponse] = {}
        self.websocket_connections: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def create_analysis_task(self, request: AnalysisRequest) -> str:
        """Create a new analysis task"""
        task_id = str(uuid.uuid4())
        
        task_status = TaskStatus(
            task_id=task_id,
            status="pending",
            progress=0,
            message="Task created, waiting to start",
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task_status
        
        # Start the analysis in the background
        asyncio.create_task(self._run_analysis(task_id, request))
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        return self.tasks.get(task_id)
    
    async def get_analysis_result(self, task_id: str) -> Optional[AnalysisResponse]:
        """Get the complete analysis result"""
        return self.results.get(task_id)
    
    async def register_websocket(self, task_id: str, websocket):
        """Register a WebSocket connection for task updates"""
        self.websocket_connections[task_id] = websocket
        logger.info(f"WebSocket registered for task {task_id}")
    
    async def unregister_websocket(self, task_id: str):
        """Unregister a WebSocket connection"""
        if task_id in self.websocket_connections:
            del self.websocket_connections[task_id]
            logger.info(f"WebSocket unregistered for task {task_id}")
    
    async def _send_websocket_message(self, task_id: str, message: WebSocketMessage):
        """Send a message via WebSocket if connected"""
        if task_id in self.websocket_connections:
            try:
                websocket = self.websocket_connections[task_id]
                await websocket.send_text(message.json())
                logger.debug(f"Sent WebSocket message for task {task_id}: {message.message_type}")
            except Exception as e:
                logger.error(f"Error sending WebSocket message for task {task_id}: {e}")
                # Remove broken connection
                await self.unregister_websocket(task_id)
    
    async def _update_task_status(self, task_id: str, status: str, progress: int = None, 
                                 message: str = None, error: str = None):
        """Update task status and notify via WebSocket"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.status = status
        if progress is not None:
            task.progress = progress
        if message is not None:
            task.message = message
        if error is not None:
            task.error = error
        
        if status == "running" and not task.started_at:
            task.started_at = datetime.now()
        elif status in ["completed", "failed"]:
            task.completed_at = datetime.now()
        
        # Send WebSocket update
        ws_message = WebSocketMessage(
            task_id=task_id,
            message_type="progress" if status == "running" else "status",
            data={
                "status": status,
                "progress": task.progress,
                "message": message or "",
                "error": error
            }
        )
        await self._send_websocket_message(task_id, ws_message)
    
    async def _run_analysis(self, task_id: str, request: AnalysisRequest):
        """Run the PR analysis in a background thread"""
        try:
            await self._update_task_status(task_id, "running", 0, "Starting analysis...")
            
            # Run the actual analysis in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._perform_analysis, 
                task_id, 
                request
            )
            
            # Store the result
            self.results[task_id] = result
            
            await self._update_task_status(task_id, "completed", 100, "Analysis completed successfully")
            
            # Send completion message via WebSocket
            completion_message = WebSocketMessage(
                task_id=task_id,
                message_type="complete",
                data={"result": result.dict()}
            )
            await self._send_websocket_message(task_id, completion_message)
            
        except Exception as e:
            logger.error(f"Analysis failed for task {task_id}: {e}")
            error_msg = str(e)
            await self._update_task_status(task_id, "failed", None, "Analysis failed", error_msg)
            
            # Send error message via WebSocket
            error_message = WebSocketMessage(
                task_id=task_id,
                message_type="error",
                data={"error": error_msg, "traceback": traceback.format_exc()}
            )
            await self._send_websocket_message(task_id, error_message)
    
    def _perform_analysis(self, task_id: str, request: AnalysisRequest) -> AnalysisResponse:
        """Perform the actual analysis (runs in thread pool)"""
        try:
            # Initialize GitHub client
            self._send_progress_sync(task_id, 10, "Initializing GitHub client...")
            github_client = GitHubClient(token=request.github_token)
            
            # Validate repository access
            self._send_progress_sync(task_id, 20, "Validating repository access...")
            try:
                # Test repository access by fetching basic info
                github_client._make_request(f"repos/{request.owner}/{request.repo}")
            except GitHubAPIError as e:
                if e.status_code == 404:
                    raise Exception(f"Repository {request.owner}/{request.repo} not found or not accessible")
                raise Exception(f"Repository access error: {e.message}")
            
            # Fetch pull requests
            self._send_progress_sync(task_id, 30, "Fetching pull requests...")
            try:
                logger.info(f"Starting PR fetch for {request.owner}/{request.repo}")
                pull_requests = github_client.get_pull_requests(
                    owner=request.owner,
                    repo=request.repo,
                    state='all',
                    since=request.since,
                    until=request.until
                )
                logger.info(f"Successfully fetched {len(pull_requests)} PRs")
            except RateLimitError as e:
                raise Exception(f"GitHub API rate limit exceeded. {e.message}")
            except GitHubAPIError as e:
                raise Exception(f"Error fetching pull requests: {e.message}")
            
            if not pull_requests:
                raise Exception("No pull requests found for the specified criteria")
            
            self._send_progress_sync(task_id, 50, f"Found {len(pull_requests)} pull requests. Analyzing...")
            
            # Initialize analyzer
            analyzer = PRAnalyzer(verbose=False)
            
            # Analyze pull requests
            self._send_progress_sync(task_id, 70, "Analyzing pull request metrics...")
            repo_name = f"{request.owner}/{request.repo}"
            metrics = analyzer.analyze_pull_requests(
                pull_requests=pull_requests,
                repository=repo_name,
                since=request.since,
                until=request.until
            )
            
            # Generate comprehensive report
            self._send_progress_sync(task_id, 90, "Generating analysis report...")
            summary = analyzer.generate_summary_report()
            
            # Convert to response format
            analysis_response = self._convert_to_response_format(
                task_id=task_id,
                metrics=metrics,
                summary=summary,
                request=request
            )
            
            self._send_progress_sync(task_id, 95, "Finalizing results...")
            
            return analysis_response
            
        except Exception as e:
            logger.error(f"Analysis error for task {task_id}: {e}")
            raise
    
    def _send_progress_sync(self, task_id: str, progress: int, message: str):
        """Send progress update synchronously (for use in thread pool)"""
        try:
            # Update the task status synchronously
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.progress = progress
                task.message = message
                
            # Log progress
            logger.info(f"Task {task_id} progress: {progress}% - {message}")
        except Exception as e:
            logger.error(f"Error sending progress for task {task_id}: {e}")
    
    def _convert_to_response_format(self, task_id: str, metrics: Dict, summary: Dict, 
                                  request: AnalysisRequest) -> AnalysisResponse:
        """Convert analysis results to response format"""
        
        # Convert repository metrics
        repository_metrics_list = []
        
        for repo, developers in metrics.items():
            repo_metrics = RepositoryMetrics(
                repository=repo,
                total_prs=0,
                developers={},
                summary={'total': 0, 'open': 0, 'merged': 0, 'closed': 0, 'draft': 0}
            )
            
            for dev, dev_metrics in developers.items():
                # Convert PR data
                prs_data = []
                for pr_data in dev_metrics.get('prs_data', []):
                    pr_metrics = PRMetrics(
                        number=pr_data['number'],
                        title=pr_data['title'],
                        state=pr_data['state'],
                        created_at=pr_data['created_at'],
                        merged_at=pr_data.get('merged_at'),
                        closed_at=pr_data.get('closed_at'),
                        additions=pr_data.get('additions', 0),
                        deletions=pr_data.get('deletions', 0),
                        changed_files=pr_data.get('changed_files', 0),
                        commits=pr_data.get('commits', 0),
                        url=pr_data.get('url', '')
                    )
                    prs_data.append(pr_metrics)
                
                # Calculate time and size metrics
                time_to_merge_list = dev_metrics.get('time_to_merge', [])
                time_to_close_list = dev_metrics.get('time_to_close', [])
                lines_added_list = dev_metrics.get('lines_added', [])
                lines_deleted_list = dev_metrics.get('lines_deleted', [])
                files_changed_list = dev_metrics.get('files_changed', [])
                commits_list = dev_metrics.get('commits_count', [])
                
                time_metrics = {
                    'time_to_merge': self._calculate_stats(time_to_merge_list),
                    'time_to_close': self._calculate_stats(time_to_close_list)
                }
                
                size_metrics = {
                    'lines_added': self._calculate_stats(lines_added_list),
                    'lines_deleted': self._calculate_stats(lines_deleted_list),
                    'files_changed': self._calculate_stats(files_changed_list),
                    'commits_count': self._calculate_stats(commits_list)
                }
                
                # Calculate productivity metrics
                total_prs = dev_metrics.get('total', 0)
                merged_prs = dev_metrics.get('merged', 0)
                merge_rate = (merged_prs / total_prs * 100) if total_prs > 0 else 0
                avg_pr_size = (sum(lines_added_list) + sum(lines_deleted_list)) / len(lines_added_list + lines_deleted_list) if (lines_added_list + lines_deleted_list) else 0
                
                productivity_metrics = {
                    'merge_rate_percent': round(merge_rate, 1),
                    'average_pr_size': round(avg_pr_size, 0),
                    'prs_per_week': 0  # Would need date range calculation
                }
                
                developer_metrics = DeveloperMetrics(
                    developer=dev,
                    basic_metrics={
                        'total': dev_metrics.get('total', 0),
                        'open': dev_metrics.get('open', 0),
                        'merged': dev_metrics.get('merged', 0),
                        'closed': dev_metrics.get('closed', 0),
                        'draft': dev_metrics.get('draft', 0)
                    },
                    time_metrics=time_metrics,
                    size_metrics=size_metrics,
                    productivity_metrics=productivity_metrics,
                    prs_data=prs_data
                )
                
                repo_metrics.developers[dev] = developer_metrics
                
                # Update repository totals
                repo_metrics.total_prs += dev_metrics.get('total', 0)
                repo_metrics.summary['total'] += dev_metrics.get('total', 0)
                repo_metrics.summary['open'] += dev_metrics.get('open', 0)
                repo_metrics.summary['merged'] += dev_metrics.get('merged', 0)
                repo_metrics.summary['closed'] += dev_metrics.get('closed', 0)
                repo_metrics.summary['draft'] += dev_metrics.get('draft', 0)
            
            repository_metrics_list.append(repo_metrics)
        
        # Create global insights
        insights = summary.get('global_insights', {})
        global_insights = GlobalInsights(
            average_time_to_merge_hours=insights.get('average_time_to_merge_hours', 0),
            median_time_to_merge_hours=insights.get('median_time_to_merge_hours', 0),
            average_pr_size_lines=insights.get('average_pr_size_lines', 0),
            most_active_developer=insights.get('most_active_developer'),
            total_repositories=summary.get('analysis_metadata', {}).get('total_repositories', 0),
            total_developers=summary.get('analysis_metadata', {}).get('total_developers', 0),
            total_prs_processed=summary.get('analysis_metadata', {}).get('total_prs_processed', 0)
        )
        
        # Create analysis metadata
        metadata_dict = summary.get('analysis_metadata', {})
        analysis_metadata = AnalysisMetadata(
            total_repositories=metadata_dict.get('total_repositories', 0),
            total_developers=metadata_dict.get('total_developers', 0),
            total_prs_processed=metadata_dict.get('total_prs_processed', 0),
            analysis_duration=metadata_dict.get('analysis_duration', 0),
            date_range=metadata_dict.get('date_range', {'since': None, 'until': None})
        )
        
        # Create the final response
        response = AnalysisResponse(
            task_id=task_id,
            status="completed",
            analysis_metadata=analysis_metadata,
            repository_metrics=repository_metrics_list,
            global_insights=global_insights,
            created_at=self.tasks[task_id].created_at,
            completed_at=datetime.now()
        )
        
        return response
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical measures for a list of values"""
        if not values:
            return {
                'count': 0,
                'mean': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0,
                'std_dev': 0.0
            }
        
        import statistics
        return {
            'count': len(values),
            'mean': round(statistics.mean(values), 2),
            'median': round(statistics.median(values), 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'std_dev': round(statistics.stdev(values) if len(values) > 1 else 0, 2)
        }


# Global service instance
analysis_service = AnalysisService()