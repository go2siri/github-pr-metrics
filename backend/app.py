from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime
from typing import Optional
import json
import asyncio
import os

# Import our models and services
from models import (
    AnalysisRequest, AnalysisResponse, AnalysisTaskResponse, TaskStatus,
    ErrorResponse, HealthResponse, WebSocketMessage
)
from services import analysis_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GitHub PR Metrics Analyzer API",
    description="API for analyzing GitHub Pull Request metrics with real-time progress updates",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Application startup time for health check
app_start_time = datetime.now()


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("GitHub PR Metrics Analyzer API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("GitHub PR Metrics Analyzer API shutting down...")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Calculate uptime
        uptime = (datetime.now() - app_start_time).total_seconds()
        
        # Test GitHub API accessibility (simple check)
        github_api_accessible = True
        try:
            import requests
            response = requests.get("https://api.github.com/", timeout=5)
            github_api_accessible = response.status_code == 200
        except Exception:
            github_api_accessible = False
        
        return HealthResponse(
            status="healthy",
            uptime_seconds=uptime,
            github_api_accessible=github_api_accessible
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/api/analyze", response_model=AnalysisTaskResponse)
async def start_analysis(request: AnalysisRequest):
    """Start a new PR analysis task"""
    try:
        # Create the analysis task
        task_id = await analysis_service.create_analysis_task(request)
        
        # Get base URL for building URLs
        base_url = "http://localhost:8000"  # Should be configurable
        
        response = AnalysisTaskResponse(
            task_id=task_id,
            status="pending",
            message="Analysis task created successfully",
            websocket_url=f"ws://{base_url.replace('http://', '')}/ws/{task_id}",
            status_url=f"{base_url}/api/analysis/{task_id}"
        )
        
        logger.info(f"Created analysis task {task_id} for {request.owner}/{request.repo}")
        return response
        
    except ValueError as e:
        # Validation error
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@app.get("/api/analysis/{task_id}", response_model=dict)
async def get_analysis_status(task_id: str):
    """Get the status and results of an analysis task"""
    try:
        # Get task status
        task_status = await analysis_service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # If task is completed, return the full result
        if task_status.status == "completed":
            result = await analysis_service.get_analysis_result(task_id)
            if result:
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result.dict()
                }
        
        # Otherwise, return just the status
        return {
            "task_id": task_id,
            "status": task_status.status,
            "progress": task_status.progress,
            "message": task_status.message,
            "created_at": task_status.created_at,
            "started_at": task_status.started_at,
            "completed_at": task_status.completed_at,
            "error": task_status.error
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    logger.info(f"WebSocket connection established for task {task_id}")
    
    try:
        # Register the WebSocket connection
        await analysis_service.register_websocket(task_id, websocket)
        
        # Send initial status if task exists
        task_status = await analysis_service.get_task_status(task_id)
        if task_status:
            initial_message = WebSocketMessage(
                task_id=task_id,
                message_type="status",
                data={
                    "status": task_status.status,
                    "progress": task_status.progress,
                    "message": task_status.message or "Connected"
                }
            )
            await websocket.send_text(initial_message.json())
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for any message from client (heartbeat, etc.)
                data = await websocket.receive_text()
                # Echo back for heartbeat
                await websocket.send_text(json.dumps({"type": "pong", "data": data}))
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for task {task_id}: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        # Unregister the WebSocket connection
        await analysis_service.unregister_websocket(task_id)


@app.get("/api/tasks", response_model=dict)
async def list_tasks():
    """List all analysis tasks (for debugging/monitoring)"""
    try:
        tasks_data = {}
        for task_id, task_status in analysis_service.tasks.items():
            tasks_data[task_id] = {
                "task_id": task_id,
                "status": task_status.status,
                "progress": task_status.progress,
                "message": task_status.message,
                "created_at": task_status.created_at,
                "started_at": task_status.started_at,
                "completed_at": task_status.completed_at,
                "error": task_status.error
            }
        
        return {
            "total_tasks": len(tasks_data),
            "tasks": tasks_data
        }
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list tasks")


@app.delete("/api/analysis/{task_id}")
async def delete_task(task_id: str):
    """Delete a completed or failed analysis task"""
    try:
        task_status = await analysis_service.get_task_status(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task_status.status in ["running", "pending"]:
            raise HTTPException(status_code=400, detail="Cannot delete running or pending tasks")
        
        # Remove task and result
        if task_id in analysis_service.tasks:
            del analysis_service.tasks[task_id]
        if task_id in analysis_service.results:
            del analysis_service.results[task_id]
        
        logger.info(f"Deleted task {task_id}")
        return {"message": f"Task {task_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )


@app.exception_handler(ValueError)
async def validation_exception_handler(request, exc):
    """Handle validation exceptions"""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Validation error",
            detail=str(exc)
        ).dict()
    )


# Additional utility endpoints

@app.get("/api/docs-json")
async def get_openapi_schema():
    """Get OpenAPI schema JSON"""
    return app.openapi()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GitHub PR Metrics Analyzer API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }


if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )