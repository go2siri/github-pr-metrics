# GitHub PR Metrics Analyzer - FastAPI Backend

A modern FastAPI backend for analyzing GitHub Pull Request metrics with real-time progress updates via WebSockets.

## Features

- **REST API** for starting and monitoring PR analysis
- **WebSocket support** for real-time progress updates
- **Background task processing** using asyncio
- **CORS enabled** for React frontend integration
- **Input validation** with Pydantic models
- **Comprehensive error handling**
- **Health check endpoint**
- **Interactive API documentation** with Swagger UI

## API Endpoints

### Core Analysis Endpoints

- `POST /api/analyze` - Start a new PR analysis task
- `GET /api/analysis/{task_id}` - Get analysis status and results
- `WebSocket /ws/{task_id}` - Real-time progress updates
- `DELETE /api/analysis/{task_id}` - Delete completed/failed task

### Utility Endpoints

- `GET /api/health` - Health check
- `GET /api/tasks` - List all tasks (debugging)
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the backend server:
```bash
python run_backend.py
```

Or directly with uvicorn:
```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

## Usage

### Starting an Analysis

Send a POST request to `/api/analyze`:

```json
{
  "owner": "microsoft",
  "repo": "vscode",
  "github_token": "your_github_token_here",
  "since": "2023-01-01T00:00:00Z",
  "until": "2024-01-01T00:00:00Z"
}
```

Response:
```json
{
  "task_id": "uuid-here",
  "status": "pending",
  "message": "Analysis task created successfully",
  "websocket_url": "ws://localhost:8000/ws/uuid-here",
  "status_url": "http://localhost:8000/api/analysis/uuid-here"
}
```

### Monitoring Progress

#### Option 1: WebSocket (Real-time)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/task-id');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.data.progress + '%');
  console.log('Status:', data.data.message);
};
```

#### Option 2: Polling
```bash
curl http://localhost:8000/api/analysis/task-id
```

### Example Usage Script

Run the interactive example:
```bash
python backend/example_usage.py
```

## Configuration

Environment variables:
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)  
- `RELOAD` - Enable auto-reload (default: true)

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture

### Components

1. **app.py** - FastAPI application with endpoints and WebSocket handling
2. **models.py** - Pydantic models for request/response validation
3. **services.py** - Business logic and background task processing
4. **example_usage.py** - Example client for testing

### Data Flow

1. Client sends analysis request to `/api/analyze`
2. Server creates background task and returns task ID
3. Client connects to WebSocket `/ws/{task_id}` for updates
4. Background task processes PR analysis and sends progress updates
5. Final results available at `/api/analysis/{task_id}`

### Error Handling

- **400 Bad Request** - Validation errors, invalid input
- **404 Not Found** - Task not found
- **500 Internal Server Error** - Server errors, GitHub API issues
- **WebSocket errors** - Connection issues, task failures

## Integration with Existing Code

The backend integrates seamlessly with existing modules:
- `github_client.py` - For GitHub API communication
- `pr_analyzer.py` - For PR metrics calculation

No modifications to existing code required.

## Testing

Test the health endpoint:
```bash
curl http://localhost:8000/api/health
```

Test a simple analysis:
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "octocat",
    "repo": "Hello-World", 
    "github_token": "your_token"
  }'
```

## Development

Start with auto-reload:
```bash
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

View logs for debugging:
- Task creation and progress
- WebSocket connections
- Error details and stack traces