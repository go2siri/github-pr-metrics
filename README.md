# GitHub Pull Request Metrics Analyzer

A comprehensive Python tool for analyzing GitHub Pull Request metrics across repositories. This tool provides detailed insights into developer productivity, PR lifecycle metrics, and team performance analytics.

## Features

### Core Analytics
- **Multi-Repository Analysis**: Analyze single repositories or all repositories for a user/organization
- **Advanced Metrics**: Time to merge, time to close, code size metrics, merge rates
- **Date Filtering**: Filter PRs by creation date range (since/until)
- **Developer Insights**: Per-developer statistics across all analyzed repositories
- **Rich Reporting**: Beautiful console output with tables, progress bars, and insights

### Metrics Collected
- **Basic Counts**: Total, Open, Merged, Closed, Draft PRs
- **Time Metrics**: Average and median time to merge/close
- **Size Metrics**: Lines added/deleted, files changed, commits per PR
- **Productivity Metrics**: Merge rates, average PR size, developer rankings
- **Statistical Analysis**: Mean, median, min, max, standard deviation for all metrics

### Export & Integration
- **CSV Export**: Detailed metrics export for further analysis
- **Rich Console Output**: Professional reporting with color-coded insights
- **Docker Support**: Containerized deployment ready
- **Environment Configuration**: Flexible token and API configuration

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd github-pr-metrics
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up GitHub token:**
   
   **Option 1: Environment Variable**
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```
   
   **Option 2: .env file**
   ```bash
   echo "GITHUB_TOKEN=your_github_token_here" > .env
   ```

4. **Run analysis:**
   ```bash
   python main.py --owner octocat --repo Hello-World
   ```

### Creating a GitHub Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the following scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories)
   - `read:user` (for user information)
   - `read:org` (for organization repositories)
4. Copy the generated token

## Usage Examples

### Basic Repository Analysis
```bash
# Analyze a specific repository
python main.py --owner microsoft --repo vscode

# Analyze with verbose output
python main.py --owner octocat --repo Hello-World --verbose
```

### Organization/User Analysis
```bash
# Analyze all repositories for a user/organization
python main.py --owner microsoft

# Analyze with date filtering
python main.py --owner microsoft --since 2024-01-01 --until 2024-12-31
```

### Advanced Usage
```bash
# Export to CSV with date range
python main.py --owner octocat --since 2024-01-01 --output metrics.csv

# Use custom token
python main.py --owner octocat --token ghp_your_token_here

# Comprehensive analysis with all options
python main.py --owner microsoft --repo TypeScript --since 2024-01-01 --until 2024-06-30 --output typescript-metrics.csv --verbose
```

## Docker Usage

### Build and Run
```bash
# Build the Docker image
docker build -t github-pr-metrics .

# Run with environment variable
docker run -e GITHUB_TOKEN=your_token_here github-pr-metrics --owner octocat --repo Hello-World

# Run with volume for CSV export
docker run -e GITHUB_TOKEN=your_token_here -v $(pwd)/output:/app/output github-pr-metrics --owner octocat --output output/metrics.csv
```

### Docker Compose (Recommended)
```yaml
# docker-compose.yml
version: '3.8'
services:
  pr-metrics:
    build: .
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./output:/app/output
    command: ["--owner", "octocat", "--output", "output/metrics.csv"]
```

Run with:
```bash
export GITHUB_TOKEN=your_token_here
docker-compose run pr-metrics
```

## Command Line Options

| Option | Description | Required | Example |
|--------|-------------|----------|---------|
| `--owner` | GitHub repository owner (user/organization) | ✅ | `microsoft` |
| `--repo` | Specific repository name | ❌ | `vscode` |
| `--since` | Start date (YYYY-MM-DD) | ❌ | `2024-01-01` |
| `--until` | End date (YYYY-MM-DD) | ❌ | `2024-12-31` |
| `--output` | CSV output file path | ❌ | `metrics.csv` |
| `--token` | GitHub personal access token | ❌ | `ghp_xxxx` |
| `--verbose`, `-v` | Enable verbose output | ❌ | - |

## Output Formats

### Console Report
The tool provides a comprehensive console report with:

1. **Analysis Overview**: Summary statistics and metadata
2. **Key Insights**: Top developers, average metrics, trends
3. **Repository Summary**: PR counts by repository
4. **Developer Rankings**: Top contributors with detailed metrics
5. **Detailed Breakdown**: Individual developer statistics (verbose mode)

### CSV Export
When using `--output`, the tool exports detailed metrics to CSV with columns:

- `repository`: Repository name
- `developer`: Developer username  
- `total_prs`: Total pull requests
- `merged_prs`: Successfully merged PRs
- `merge_rate_percent`: Percentage of PRs merged
- `avg_time_to_merge_hours`: Average time from creation to merge
- `median_time_to_merge_hours`: Median time to merge
- `avg_lines_added`: Average lines of code added per PR
- `avg_lines_deleted`: Average lines of code deleted per PR
- `total_lines_added`: Total lines added across all PRs
- `max_pr_size_lines`: Largest PR by line count

## Advanced Configuration

### Environment Variables
```bash
# Required
GITHUB_TOKEN=your_github_token_here

# Optional
GITHUB_API_BASE_URL=https://api.github.com  # For GitHub Enterprise
```

### Rate Limiting
The tool automatically handles GitHub API rate limits:
- Implements exponential backoff for retries
- Respects rate limit headers
- Provides clear error messages for rate limit issues

### Error Handling
- **Network Issues**: Automatic retry with exponential backoff
- **Authentication Errors**: Clear error messages and troubleshooting tips
- **Repository Access**: Handles private/public repository permissions
- **API Changes**: Graceful handling of API response variations

## Development

### Requirements
- Python 3.8+
- Dependencies listed in `requirements.txt`

### Project Structure
```
github-pr-metrics/
├── main.py              # CLI application entry point
├── github_client.py     # GitHub API client with rate limiting
├── pr_analyzer.py       # Advanced metrics calculation and reporting
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── README.md           # This file
└── .env.example        # Example environment configuration
```

### Dependencies
- **click**: Command-line interface framework
- **requests**: HTTP client for GitHub API
- **rich**: Beautiful terminal formatting and progress bars
- **pandas**: Data manipulation and CSV export
- **python-dotenv**: Environment variable management

## Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Error: Invalid GitHub token
# Solution: Verify token permissions and expiration
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

**Rate Limit Exceeded**
```bash
# Error: API rate limit exceeded
# Solution: Wait for reset or use a different token
# Check rate limit status:
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

**Repository Not Found**
```bash
# Error: Repository not found or not accessible
# Solution: Check repository name and permissions
# Verify repository exists and is accessible:
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/repos/owner/repo
```

### Getting Help

1. **Check token permissions**: Ensure your token has appropriate scopes
2. **Verify repository access**: Test API access manually
3. **Use verbose mode**: Add `--verbose` for detailed error information
4. **Check rate limits**: Monitor your API usage

## API Rate Limits

GitHub API limits:
- **Authenticated requests**: 5,000 requests/hour
- **Search API**: 30 requests/minute
- **Secondary rate limits**: Dynamic based on usage patterns

The tool optimizes API usage by:
- Using pagination efficiently
- Caching repository lists
- Implementing intelligent retry logic
- Respecting rate limit headers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. See LICENSE file for details.

## Example Output

```
GitHub PR Metrics Analyzer
==========================

📊 Analysis Overview
Total Repositories: 3
Total Developers: 12
Total PRs Processed: 247
Analysis Duration: 8.2 seconds

🏆 Key Insights
Most Active Developer: john_doe
Average Time to Merge: 24.3 hours
Median Time to Merge: 8.5 hours
Average PR Size: 156 lines

📁 Repository Summary
┌─────────────────┬───────────┬──────┬────────┬────────┬───────┐
│ Repository      │ Total PRs │ Open │ Merged │ Closed │ Draft │
├─────────────────┼───────────┼──────┼────────┼────────┼───────┤
│ frontend-app    │ 89        │ 12   │ 71     │ 4      │ 2     │
│ backend-api     │ 156       │ 18   │ 128    │ 8      │ 2     │
│ mobile-app      │ 67        │ 9    │ 52     │ 3      │ 3     │
└─────────────────┴───────────┴──────┴────────┴────────┴───────┘

👥 Top Developers by Activity
┌──────────────┬───────────┬────────┬────────────┬───────────────────┬─────────────┐
│ Developer    │ Total PRs │ Merged │ Merge Rate │ Avg Time to Merge │ Avg PR Size │
├──────────────┼───────────┼────────┼────────────┼───────────────────┼─────────────┤
│ john_doe     │ 45        │ 41     │ 91.1%      │ 18.5h             │ 203 lines   │
│ jane_smith   │ 38        │ 35     │ 92.1%      │ 22.1h             │ 145 lines   │
│ bob_wilson   │ 33        │ 29     │ 87.9%      │ 31.2h             │ 178 lines   │
└──────────────┴───────────┴────────┴────────────┴───────────────────┴─────────────┘

✅ Report generation complete!
```