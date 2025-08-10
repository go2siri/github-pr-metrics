import os
import requests
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union
from dotenv import load_dotenv

load_dotenv()

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(self.message)

class RateLimitError(GitHubAPIError):
    """Exception for rate limit exceeded errors"""
    def __init__(self, reset_time: int = None):
        self.reset_time = reset_time
        message = "GitHub API rate limit exceeded"
        if reset_time:
            reset_datetime = datetime.fromtimestamp(reset_time, tz=timezone.utc)
            message += f". Rate limit resets at {reset_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        super().__init__(message, 403)

class GitHubClient:
    """
    Enhanced GitHub API client with rate limiting, error handling, and retry logic.
    """
    
    def __init__(self, token: Optional[str] = None, max_retries: int = 3, retry_delay: int = 5):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = os.getenv('GITHUB_API_BASE_URL', 'https://api.github.com')
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or provide --token parameter.")
        
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-PR-Metrics-Analyzer/1.0'
        }
        
        # Validate token on initialization
        self._validate_token()
    
    def _validate_token(self):
        """Validate the GitHub token by making a test API call"""
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers, timeout=10)
            if response.status_code == 401:
                raise ValueError("Invalid GitHub token. Please check your token and try again.")
            elif response.status_code != 200:
                raise ValueError(f"Token validation failed: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            raise ValueError(f"Failed to validate token: {e}")
    
    def _handle_rate_limit(self, response: requests.Response):
        """Handle rate limiting with intelligent backoff"""
        if response.status_code == 403 and 'rate limit' in response.text.lower():
            reset_time = response.headers.get('X-RateLimit-Reset')
            if reset_time:
                reset_time = int(reset_time)
                raise RateLimitError(reset_time)
            else:
                raise RateLimitError()
    
    def _make_request(self, endpoint: str, params: Dict = None, timeout: int = 30) -> Union[List[Dict], Dict]:
        """Make paginated requests to GitHub API with retry logic and rate limiting"""
        all_data = []
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        
        # Use smaller page size for better reliability
        params['per_page'] = 100
        page = 1
        retries = 0
        
        while True:
            params['page'] = page
            
            while retries < self.max_retries:
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
                    
                    # Handle different response codes
                    if response.status_code == 200:
                        break
                    elif response.status_code == 404:
                        raise GitHubAPIError(f"Resource not found: {endpoint}", 404, response.text)
                    elif response.status_code == 403:
                        self._handle_rate_limit(response)
                        if 'rate limit' not in response.text.lower():
                            # Not a rate limit error, likely access denied
                            raise GitHubAPIError(f"Access denied: {endpoint}", 403, response.text)
                    elif response.status_code == 422:
                        raise GitHubAPIError(f"Validation failed: {response.text}", 422, response.text)
                    else:
                        raise GitHubAPIError(f"API request failed: {response.status_code} - {response.text}", 
                                           response.status_code, response.text)
                
                except RateLimitError:
                    raise  # Don't retry rate limit errors, let caller handle
                except (requests.RequestException, GitHubAPIError) as e:
                    retries += 1
                    if retries >= self.max_retries:
                        raise GitHubAPIError(f"Request failed after {self.max_retries} retries: {str(e)}")
                    
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** (retries - 1))
                    time.sleep(wait_time)
                    continue
            
            # Reset retries for next page
            retries = 0
            
            try:
                data = response.json()
            except ValueError as e:
                raise GitHubAPIError(f"Invalid JSON response: {e}")
            
            if not data:
                break
            
            # Handle single object response vs array response
            if isinstance(data, list):
                all_data.extend(data)
            else:
                return data  # Single object, return directly
                
            page += 1
            
            # Check if we've reached the last page
            if 'Link' not in response.headers:
                break
            
            if 'rel="next"' not in response.headers['Link']:
                break
            
            # Rate limiting: respect GitHub's rate limit headers
            remaining = response.headers.get('X-RateLimit-Remaining')
            if remaining and int(remaining) < 10:
                # Slow down if we're close to rate limit
                time.sleep(1)
        
        return all_data
    
    def get_pull_requests(self, owner: str, repo: str, state: str = 'all', 
                         since: Optional[datetime] = None, 
                         until: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch pull requests for a repository with enhanced filtering and error handling
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state ('open', 'closed', 'all')
            since: Filter PRs created after this date
            until: Filter PRs created before this date
        
        Returns:
            List of pull request dictionaries
        """
        endpoint = f"repos/{owner}/{repo}/pulls"
        params = {'state': state, 'sort': 'created', 'direction': 'desc', 'per_page': 100}
        
        # Add a safety limit for large repositories
        max_pages = 10  # Limit to 1000 PRs max to prevent hanging
        
        try:
            # Use pagination with limits to prevent hanging on massive repos
            all_prs = []
            page = 1
            
            while page <= max_pages:
                params['page'] = page
                page_prs = self._make_request(endpoint, params)
                
                if not page_prs:
                    break
                    
                all_prs.extend(page_prs)
                
                # If we got less than per_page, we've reached the end
                if len(page_prs) < 100:
                    break
                    
                page += 1
            
            pull_requests = all_prs
            
            # Enhanced date filtering with timezone handling
            if since or until:
                filtered_prs = []
                for pr in pull_requests:
                    created_at_str = pr['created_at']
                    try:
                        # Handle different datetime formats
                        if created_at_str.endswith('Z'):
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        else:
                            created_at = datetime.fromisoformat(created_at_str)
                            if created_at.tzinfo is None:
                                created_at = created_at.replace(tzinfo=timezone.utc)
                    except ValueError:
                        # Skip PRs with invalid dates
                        continue
                    
                    if since and created_at < since:
                        continue
                    if until and created_at > until:
                        continue
                        
                    filtered_prs.append(pr)
                
                return filtered_prs
            
            return pull_requests
            
        except GitHubAPIError as e:
            if e.status_code == 404:
                raise GitHubAPIError(f"Repository {owner}/{repo} not found or not accessible")
            raise
    
    def get_pull_request_details(self, owner: str, repo: str, pr_number: int) -> Dict:
        """
        Get detailed information about a specific pull request
        
        Args:
            owner: Repository owner
            repo: Repository name  
            pr_number: Pull request number
        
        Returns:
            Detailed pull request dictionary
        """
        endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}"
        return self._make_request(endpoint)
    
    def get_pull_request_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Get reviews for a specific pull request
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
        
        Returns:
            List of review dictionaries
        """
        endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        return self._make_request(endpoint)
    
    def get_repositories(self, owner: str, repo_type: str = 'all') -> List[Dict]:
        """
        Get all repositories for a user/organization with better error handling
        
        Args:
            owner: GitHub username or organization name
            repo_type: Type of repos ('all', 'owner', 'member', 'public', 'private')
        
        Returns:
            List of repository dictionaries
        """
        # Try different endpoints based on whether it's a user or organization
        endpoints_to_try = [
            f"users/{owner}/repos",
            f"orgs/{owner}/repos"
        ]
        
        params = {'type': repo_type, 'sort': 'updated', 'direction': 'desc'}
        
        for endpoint in endpoints_to_try:
            try:
                repos = self._make_request(endpoint, params)
                if repos:  # If we got results, return them
                    return repos
            except GitHubAPIError as e:
                if e.status_code == 404:
                    continue  # Try next endpoint
                raise  # Re-raise non-404 errors
        
        # If we get here, neither endpoint worked
        raise GitHubAPIError(f"User or organization '{owner}' not found", 404)
    
    def get_repository_contributors(self, owner: str, repo: str) -> List[Dict]:
        """
        Get contributors for a repository
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            List of contributor dictionaries
        """
        endpoint = f"repos/{owner}/{repo}/contributors"
        try:
            return self._make_request(endpoint)
        except GitHubAPIError as e:
            if e.status_code == 404:
                raise GitHubAPIError(f"Repository {owner}/{repo} not found or contributors not accessible")
            raise
    
    def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit status
        
        Returns:
            Dictionary with rate limit information
        """
        endpoint = "rate_limit"
        return self._make_request(endpoint)