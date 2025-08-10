#!/usr/bin/env python3

import click
import os
import sys
from datetime import datetime, timezone
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from github_client import GitHubClient
from pr_analyzer import PRAnalyzer

console = Console()

def validate_date(date_str: str) -> datetime:
    """Validate and parse date string."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    except ValueError:
        raise click.BadParameter(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")

def validate_date_range(since_date: datetime, until_date: datetime):
    """Validate that date range is logical."""
    if since_date >= until_date:
        raise click.BadParameter("Start date must be before end date.")

@click.command()
@click.option('--owner', required=True, help='GitHub repository owner (user/organization)')
@click.option('--repo', help='Specific repository name (if not provided, analyzes all repos)')
@click.option('--since', help='Start date (YYYY-MM-DD)')
@click.option('--until', help='End date (YYYY-MM-DD)')
@click.option('--output', help='Output CSV file path')
@click.option('--token', help='GitHub personal access token (or set GITHUB_TOKEN env var)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(owner, repo, since, until, output, token, verbose):
    """
    GitHub Pull Request Metrics Analyzer
    
    Fetch and analyze pull request metrics from GitHub repositories.
    Provides detailed statistics per developer and per repository for a specified time duration.
    
    Examples:
    \b
        # Analyze specific repository
        python main.py --owner octocat --repo Hello-World
        
        # Analyze all repositories for a user/organization
        python main.py --owner microsoft
        
        # Filter by date range and export to CSV
        python main.py --owner octocat --since 2024-01-01 --until 2024-12-31 --output metrics.csv
    """
    
    try:
        # Display banner
        banner = Text("GitHub PR Metrics Analyzer", style="bold blue")
        console.print(Panel(banner, expand=False))
        
        # Parse and validate dates
        since_date = None
        until_date = None
        
        if since:
            since_date = validate_date(since)
            if verbose:
                console.print(f"Start date: {since_date.strftime('%Y-%m-%d')}", style="dim")
        
        if until:
            until_date = validate_date(until)
            if verbose:
                console.print(f"End date: {until_date.strftime('%Y-%m-%d')}", style="dim")
        
        if since_date and until_date:
            validate_date_range(since_date, until_date)
        
        # Initialize GitHub client with better error handling
        console.print("Initializing GitHub client...", style="blue")
        try:
            client = GitHubClient(token)
            if verbose:
                console.print("GitHub client initialized successfully", style="dim green")
        except ValueError as e:
            console.print(f"Authentication Error: {e}", style="red bold")
            console.print("Please ensure you have a valid GitHub token set via --token or GITHUB_TOKEN environment variable.", style="yellow")
            sys.exit(1)
        except Exception as e:
            console.print(f"Client initialization failed: {e}", style="red bold")
            sys.exit(1)
        
        # Initialize analyzer
        analyzer = PRAnalyzer(verbose=verbose)
        
        # Get repositories to analyze
        repositories = []
        if repo:
            # Single repository mode
            repositories = [{'name': repo, 'owner': {'login': owner}}]
            console.print(f"Analyzing repository: {owner}/{repo}", style="blue")
        else:
            # All repositories mode
            console.print(f"Fetching repositories for {owner}...", style="blue")
            try:
                repositories = client.get_repositories(owner)
                if not repositories:
                    console.print(f"No repositories found for {owner}", style="yellow")
                    sys.exit(0)
            except Exception as e:
                console.print(f"Error fetching repositories: {e}", style="red")
                console.print("This could be due to:")
                console.print("• Invalid owner/organization name")
                console.print("• Repository access restrictions")  
                console.print("• API rate limiting")
                sys.exit(1)
        
        console.print(f"Found {len(repositories)} repositories to analyze", style="green")
        
        # Analyze each repository with enhanced progress tracking
        total_prs = 0
        successful_repos = 0
        failed_repos = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            
            main_task = progress.add_task("Overall progress", total=len(repositories))
            
            for i, repo_data in enumerate(repositories):
                repo_name = repo_data['name']
                task = progress.add_task(f"Analyzing {repo_name}...", total=None)
                
                try:
                    # Fetch pull requests
                    pull_requests = client.get_pull_requests(
                        owner, repo_name, 
                        since=since_date, 
                        until=until_date
                    )
                    
                    if verbose and len(pull_requests) > 0:
                        console.print(f"Processing {len(pull_requests)} PRs from {repo_name}", style="dim")
                    
                    # Analyze pull requests
                    analyzer.analyze_pull_requests(
                        pull_requests, repo_name, 
                        since_date, until_date
                    )
                    
                    total_prs += len(pull_requests)
                    successful_repos += 1
                    
                    progress.update(task, description=f"{repo_name} ({len(pull_requests)} PRs)", completed=True)
                    progress.update(main_task, advance=1)
                    
                except Exception as e:
                    failed_repos += 1
                    error_msg = str(e)
                    if "404" in error_msg:
                        error_msg = "Repository not found or access denied"
                    elif "403" in error_msg:
                        error_msg = "API rate limit exceeded"
                    
                    progress.update(task, description=f"{repo_name} - Error: {error_msg}")
                    progress.update(main_task, advance=1)
                    
                    if verbose:
                        console.print(f"Failed to analyze {repo_name}: {e}", style="red dim")
                    continue
        
        # Display analysis summary
        console.print("\nAnalysis Summary:", style="green bold")
        console.print(f"• Successfully analyzed: {successful_repos} repositories")
        console.print(f"• Failed to analyze: {failed_repos} repositories") 
        console.print(f"• Total pull requests processed: {total_prs}")
        
        if total_prs == 0:
            console.print("No pull requests found matching the specified criteria.", style="yellow")
            sys.exit(0)
        
        # Display results
        console.print("\n" + "="*80)
        analyzer.print_detailed_report()
        
        # Export to CSV if requested
        if output:
            try:
                analyzer.export_to_csv(output)
                console.print(f"Results exported to {output}", style="green")
                
                # Verify file was created
                if os.path.exists(output):
                    file_size = os.path.getsize(output)
                    console.print(f"File size: {file_size} bytes", style="dim green")
                
            except Exception as e:
                console.print(f"Error exporting to CSV: {e}", style="red")
        
        console.print("\nAnalysis complete!", style="green bold")
        
    except click.BadParameter as e:
        console.print(f"Parameter Error: {e}", style="red bold")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\nOperation cancelled by user.", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"Unexpected error: {e}", style="red bold")
        if verbose:
            import traceback
            console.print(traceback.format_exc(), style="red dim")
        sys.exit(1)

if __name__ == '__main__':
    main()