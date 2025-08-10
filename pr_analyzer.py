from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pandas as pd
import statistics
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns
from rich import box

class PRAnalyzer:
    """
    Advanced Pull Request analyzer with comprehensive metrics calculation.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.console = Console()
        
        # Enhanced metrics storage
        self.metrics = defaultdict(lambda: defaultdict(lambda: {
            'total': 0,
            'open': 0,
            'merged': 0,
            'closed': 0,
            'draft': 0,
            'time_to_merge': [],
            'time_to_first_review': [],
            'time_to_close': [],
            'lines_added': [],
            'lines_deleted': [],
            'files_changed': [],
            'commits_count': [],
            'prs_data': []  # Store raw PR data for advanced analytics
        }))
        
        # Global statistics
        self.global_stats = {
            'analysis_start_time': datetime.now(),
            'total_prs_processed': 0,
            'total_api_calls': 0,
            'date_range': {'since': None, 'until': None}
        }
    
    def analyze_pull_requests(self, pull_requests: List[Dict], 
                            repository: str, 
                            since: datetime = None, 
                            until: datetime = None) -> Dict:
        """
        Enhanced pull request analysis with advanced metrics calculation
        
        Args:
            pull_requests: List of PR data from GitHub API
            repository: Repository name
            since: Start date filter
            until: End date filter
            
        Returns:
            Dictionary containing analyzed metrics
        """
        
        if not pull_requests:
            if self.verbose:
                self.console.print(f"No pull requests found for {repository}", style="yellow dim")
            return dict(self.metrics)
        
        # Update global stats
        if since:
            self.global_stats['date_range']['since'] = since
        if until:
            self.global_stats['date_range']['until'] = until
            
        self.global_stats['total_prs_processed'] += len(pull_requests)
        
        for pr in pull_requests:
            try:
                self._analyze_single_pr(pr, repository, since, until)
            except Exception as e:
                if self.verbose:
                    self.console.print(f"Error analyzing PR #{pr.get('number', 'unknown')}: {e}", style="red dim")
                continue
        
        return dict(self.metrics)
    
    def _analyze_single_pr(self, pr: Dict, repository: str, since: datetime, until: datetime):
        """Analyze a single pull request and extract all metrics"""
        
        # Extract basic PR info
        author = pr['user']['login']
        created_at = self._parse_datetime(pr['created_at'])
        
        # Skip if outside date range
        if since and created_at < since:
            return
        if until and created_at > until:
            return
        
        # Initialize author metrics if needed
        author_metrics = self.metrics[repository][author]
        
        # Basic state tracking
        state = self._get_pr_state(pr)
        author_metrics['total'] += 1
        author_metrics[state] += 1
        
        # Time-based metrics
        self._calculate_time_metrics(pr, author_metrics)
        
        # Size metrics
        self._calculate_size_metrics(pr, author_metrics)
        
        # Store PR data for advanced analytics
        pr_data = {
            'number': pr['number'],
            'title': pr['title'],
            'state': state,
            'created_at': created_at,
            'merged_at': self._parse_datetime(pr.get('merged_at')),
            'closed_at': self._parse_datetime(pr.get('closed_at')),
            'additions': pr.get('additions', 0),
            'deletions': pr.get('deletions', 0),
            'changed_files': pr.get('changed_files', 0),
            'commits': pr.get('commits', 0),
            'url': pr.get('html_url', '')
        }
        author_metrics['prs_data'].append(pr_data)
    
    def _calculate_time_metrics(self, pr: Dict, author_metrics: Dict):
        """Calculate time-based metrics for a PR"""
        created_at = self._parse_datetime(pr['created_at'])
        
        # Time to merge
        if pr.get('merged_at'):
            merged_at = self._parse_datetime(pr['merged_at'])
            time_to_merge = (merged_at - created_at).total_seconds() / 3600  # hours
            author_metrics['time_to_merge'].append(time_to_merge)
        
        # Time to close (for closed PRs)
        if pr.get('closed_at'):
            closed_at = self._parse_datetime(pr['closed_at'])
            time_to_close = (closed_at - created_at).total_seconds() / 3600  # hours
            author_metrics['time_to_close'].append(time_to_close)
    
    def _calculate_size_metrics(self, pr: Dict, author_metrics: Dict):
        """Calculate size-related metrics for a PR"""
        
        # Lines of code changed
        additions = pr.get('additions', 0)
        deletions = pr.get('deletions', 0)
        changed_files = pr.get('changed_files', 0)
        commits = pr.get('commits', 0)
        
        if additions > 0:
            author_metrics['lines_added'].append(additions)
        if deletions > 0:
            author_metrics['lines_deleted'].append(deletions)
        if changed_files > 0:
            author_metrics['files_changed'].append(changed_files)
        if commits > 0:
            author_metrics['commits_count'].append(commits)
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string with error handling"""
        if not date_str:
            return None
        try:
            if date_str.endswith('Z'):
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(date_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        except (ValueError, AttributeError):
            return None
    
    def _get_pr_state(self, pr: Dict) -> str:
        """Determine the actual state of a PR"""
        if pr.get('draft', False):
            return 'draft'
        elif pr['state'] == 'open':
            return 'open'
        elif pr['state'] == 'closed':
            if pr.get('merged_at'):
                return 'merged'
            else:
                return 'closed'  # closed without merge
        else:
            return pr['state']
    
    def _calculate_statistics(self, values: List[float]) -> Dict:
        """Calculate statistical measures for a list of values"""
        if not values:
            return {
                'count': 0,
                'mean': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'std_dev': 0
            }
        
        return {
            'count': len(values),
            'mean': round(statistics.mean(values), 2),
            'median': round(statistics.median(values), 2),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'std_dev': round(statistics.stdev(values) if len(values) > 1 else 0, 2)
        }
    
    def generate_summary_report(self) -> Dict:
        """Generate comprehensive summary report with advanced metrics"""
        
        summary = {
            'analysis_metadata': {
                'total_repositories': len(self.metrics),
                'total_developers': len(set(dev for repo_metrics in self.metrics.values() 
                                         for dev in repo_metrics.keys())),
                'total_prs_processed': self.global_stats['total_prs_processed'],
                'analysis_duration': (datetime.now() - self.global_stats['analysis_start_time']).total_seconds(),
                'date_range': self.global_stats['date_range']
            },
            'repository_summary': {},
            'developer_summary': defaultdict(lambda: {
                'basic_metrics': {'total': 0, 'open': 0, 'merged': 0, 'closed': 0, 'draft': 0},
                'time_metrics': {},
                'size_metrics': {},
                'productivity_metrics': {}
            }),
            'global_insights': {}
        }
        
        # Calculate repository and developer summaries
        all_time_to_merge = []
        all_lines_changed = []
        
        for repo, developers in self.metrics.items():
            repo_totals = {'total': 0, 'open': 0, 'merged': 0, 'closed': 0, 'draft': 0}
            repo_time_metrics = []
            repo_size_metrics = []
            
            for dev, metrics in developers.items():
                # Basic metrics
                dev_summary = summary['developer_summary'][dev]
                for key in ['total', 'open', 'merged', 'closed', 'draft']:
                    repo_totals[key] += metrics[key]
                    dev_summary['basic_metrics'][key] += metrics[key]
                
                # Time metrics
                time_to_merge_stats = self._calculate_statistics(metrics['time_to_merge'])
                time_to_close_stats = self._calculate_statistics(metrics['time_to_close'])
                
                dev_summary['time_metrics'] = {
                    'time_to_merge': time_to_merge_stats,
                    'time_to_close': time_to_close_stats
                }
                
                # Size metrics
                dev_summary['size_metrics'] = {
                    'lines_added': self._calculate_statistics(metrics['lines_added']),
                    'lines_deleted': self._calculate_statistics(metrics['lines_deleted']),
                    'files_changed': self._calculate_statistics(metrics['files_changed']),
                    'commits_count': self._calculate_statistics(metrics['commits_count'])
                }
                
                # Productivity metrics
                merge_rate = (metrics['merged'] / metrics['total'] * 100) if metrics['total'] > 0 else 0
                avg_pr_size = statistics.mean(metrics['lines_added'] + metrics['lines_deleted']) if metrics['lines_added'] or metrics['lines_deleted'] else 0
                
                dev_summary['productivity_metrics'] = {
                    'merge_rate_percent': round(merge_rate, 1),
                    'average_pr_size': round(avg_pr_size, 0),
                    'prs_per_week': 0  # Would need date range to calculate accurately
                }
                
                # Collect data for global insights
                all_time_to_merge.extend(metrics['time_to_merge'])
                all_lines_changed.extend([sum(x) for x in zip(metrics['lines_added'], metrics['lines_deleted']) if x])
            
            summary['repository_summary'][repo] = repo_totals
        
        # Global insights
        summary['global_insights'] = {
            'average_time_to_merge_hours': round(statistics.mean(all_time_to_merge), 1) if all_time_to_merge else 0,
            'median_time_to_merge_hours': round(statistics.median(all_time_to_merge), 1) if all_time_to_merge else 0,
            'average_pr_size_lines': round(statistics.mean(all_lines_changed), 0) if all_lines_changed else 0,
            'most_active_developer': max(summary['developer_summary'].keys(), 
                                       key=lambda x: summary['developer_summary'][x]['basic_metrics']['total']) if summary['developer_summary'] else None
        }
        
        summary['developer_summary'] = dict(summary['developer_summary'])
        return summary
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to pandas DataFrame with enhanced columns"""
        data = []
        
        for repo, developers in self.metrics.items():
            for dev, metrics in developers.items():
                
                # Calculate statistics for time metrics
                time_to_merge_stats = self._calculate_statistics(metrics['time_to_merge'])
                time_to_close_stats = self._calculate_statistics(metrics['time_to_close'])
                
                # Calculate statistics for size metrics
                lines_added_stats = self._calculate_statistics(metrics['lines_added'])
                lines_deleted_stats = self._calculate_statistics(metrics['lines_deleted'])
                files_changed_stats = self._calculate_statistics(metrics['files_changed'])
                
                # Calculate productivity metrics
                merge_rate = (metrics['merged'] / metrics['total'] * 100) if metrics['total'] > 0 else 0
                
                row = {
                    'repository': repo,
                    'developer': dev,
                    'total_prs': metrics['total'],
                    'open_prs': metrics['open'],
                    'merged_prs': metrics['merged'],
                    'closed_prs': metrics['closed'],
                    'draft_prs': metrics['draft'],
                    'merge_rate_percent': round(merge_rate, 1),
                    'avg_time_to_merge_hours': time_to_merge_stats['mean'],
                    'median_time_to_merge_hours': time_to_merge_stats['median'],
                    'avg_time_to_close_hours': time_to_close_stats['mean'],
                    'avg_lines_added': lines_added_stats['mean'],
                    'avg_lines_deleted': lines_deleted_stats['mean'],
                    'avg_files_changed': files_changed_stats['mean'],
                    'total_lines_added': sum(metrics['lines_added']),
                    'total_lines_deleted': sum(metrics['lines_deleted']),
                    'max_pr_size_lines': max(metrics['lines_added'] + metrics['lines_deleted']) if metrics['lines_added'] or metrics['lines_deleted'] else 0
                }
                data.append(row)
        
        return pd.DataFrame(data)
    
    def export_to_csv(self, filename: str) -> None:
        """Export enhanced metrics to CSV file"""
        try:
            df = self.to_dataframe()
            df.to_csv(filename, index=False)
            
            # Print summary of exported data
            if not df.empty:
                self.console.print(f"[green]Successfully exported {len(df)} rows to {filename}[/green]")
                
                # Show column summary
                if self.verbose:
                    self.console.print(f"Columns exported: {', '.join(df.columns.tolist())}", style="dim")
            else:
                self.console.print("[yellow]Warning: No data to export[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Error exporting to CSV: {e}[/red]")
            raise
    
    def print_detailed_report(self) -> None:
        """Print comprehensive metrics report using Rich formatting"""
        
        summary = self.generate_summary_report()
        
        # Header
        self.console.print("\n" + "="*80, style="blue")
        header_text = Text("GITHUB PULL REQUEST METRICS REPORT", style="bold blue")
        self.console.print(Panel(header_text, expand=False))
        
        # Analysis metadata
        metadata = summary['analysis_metadata']
        self.console.print(f"\n📊 Analysis Overview", style="bold green")
        overview_table = Table(show_header=False, box=box.SIMPLE)
        overview_table.add_column("Metric", style="cyan")
        overview_table.add_column("Value", style="white")
        
        overview_table.add_row("Total Repositories", str(metadata['total_repositories']))
        overview_table.add_row("Total Developers", str(metadata['total_developers']))
        overview_table.add_row("Total PRs Processed", str(metadata['total_prs_processed']))
        overview_table.add_row("Analysis Duration", f"{metadata['analysis_duration']:.1f} seconds")
        
        if metadata['date_range']['since']:
            overview_table.add_row("Date Range (Since)", metadata['date_range']['since'].strftime('%Y-%m-%d'))
        if metadata['date_range']['until']:
            overview_table.add_row("Date Range (Until)", metadata['date_range']['until'].strftime('%Y-%m-%d'))
            
        self.console.print(overview_table)
        
        # Global insights
        insights = summary['global_insights']
        if insights.get('most_active_developer'):
            self.console.print(f"\n🏆 Key Insights", style="bold yellow")
            insights_table = Table(show_header=False, box=box.SIMPLE)
            insights_table.add_column("Insight", style="yellow")
            insights_table.add_column("Value", style="white")
            
            insights_table.add_row("Most Active Developer", insights['most_active_developer'])
            insights_table.add_row("Average Time to Merge", f"{insights['average_time_to_merge_hours']:.1f} hours")
            insights_table.add_row("Median Time to Merge", f"{insights['median_time_to_merge_hours']:.1f} hours")
            insights_table.add_row("Average PR Size", f"{insights['average_pr_size_lines']:.0f} lines")
            
            self.console.print(insights_table)
        
        # Repository summary
        self.console.print(f"\n📁 Repository Summary", style="bold green")
        repo_table = Table(box=box.ROUNDED)
        repo_table.add_column("Repository", style="cyan", no_wrap=True)
        repo_table.add_column("Total PRs", justify="right", style="white")
        repo_table.add_column("Open", justify="right", style="yellow")
        repo_table.add_column("Merged", justify="right", style="green")
        repo_table.add_column("Closed", justify="right", style="red")
        repo_table.add_column("Draft", justify="right", style="dim white")
        
        for repo, metrics in summary['repository_summary'].items():
            repo_table.add_row(
                repo,
                str(metrics['total']),
                str(metrics['open']),
                str(metrics['merged']),
                str(metrics['closed']),
                str(metrics['draft'])
            )
        
        self.console.print(repo_table)
        
        # Developer summary (top 10 most active)
        self.console.print(f"\n👥 Top Developers by Activity", style="bold green")
        dev_summary = summary['developer_summary']
        
        # Sort developers by total PRs
        sorted_devs = sorted(dev_summary.items(), 
                           key=lambda x: x[1]['basic_metrics']['total'], 
                           reverse=True)[:10]
        
        if sorted_devs:
            dev_table = Table(box=box.ROUNDED)
            dev_table.add_column("Developer", style="cyan", no_wrap=True)
            dev_table.add_column("Total PRs", justify="right", style="white")
            dev_table.add_column("Merged", justify="right", style="green")
            dev_table.add_column("Merge Rate", justify="right", style="bright_green")
            dev_table.add_column("Avg Time to Merge", justify="right", style="blue")
            dev_table.add_column("Avg PR Size", justify="right", style="magenta")
            
            for dev, metrics in sorted_devs:
                basic = metrics['basic_metrics']
                time_metrics = metrics['time_metrics']['time_to_merge']
                size_metrics = metrics['size_metrics']
                productivity = metrics['productivity_metrics']
                
                avg_size = (size_metrics['lines_added']['mean'] + size_metrics['lines_deleted']['mean'])
                
                dev_table.add_row(
                    dev,
                    str(basic['total']),
                    str(basic['merged']),
                    f"{productivity['merge_rate_percent']:.1f}%",
                    f"{time_metrics['mean']:.1f}h" if time_metrics['count'] > 0 else "N/A",
                    f"{avg_size:.0f} lines" if avg_size > 0 else "N/A"
                )
            
            self.console.print(dev_table)
        
        # Show detailed breakdown if verbose
        if self.verbose and summary['developer_summary']:
            self.console.print(f"\n📈 Detailed Developer Metrics", style="bold green")
            
            for dev, metrics in list(sorted_devs)[:5]:  # Show top 5 in detail
                self._print_developer_detail(dev, metrics)
        
        self.console.print(f"\n✅ Report generation complete!", style="bold green")
    
    def _print_developer_detail(self, developer: str, metrics: Dict):
        """Print detailed metrics for a single developer"""
        
        panel_content = []
        basic = metrics['basic_metrics']
        time_metrics = metrics['time_metrics']
        size_metrics = metrics['size_metrics']
        
        # Basic stats
        panel_content.append(f"📊 PRs: {basic['total']} total | {basic['merged']} merged | {basic['open']} open")
        
        # Time metrics
        if time_metrics['time_to_merge']['count'] > 0:
            ttm = time_metrics['time_to_merge']
            panel_content.append(f"⏱️  Time to Merge: {ttm['mean']:.1f}h avg | {ttm['median']:.1f}h median")
        
        # Size metrics
        if size_metrics['lines_added']['count'] > 0:
            added = size_metrics['lines_added']['mean']
            deleted = size_metrics['lines_deleted']['mean']
            panel_content.append(f"📝 Code Changes: +{added:.0f}/-{deleted:.0f} lines avg")
        
        content_text = "\n".join(panel_content)
        self.console.print(Panel(content_text, title=f"👤 {developer}", 
                               title_align="left", border_style="dim"))