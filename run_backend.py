#!/usr/bin/env python3
"""
Startup script for the GitHub PR Metrics Analyzer FastAPI backend
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🚀 Starting GitHub PR Metrics Analyzer API on {host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔍 ReDoc Documentation: http://{host}:{port}/redoc")
    print(f"❤️ Health Check: http://{host}:{port}/api/health")
    
    # Start the server
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )