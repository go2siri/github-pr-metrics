#!/usr/bin/env python3
"""
Example usage script for testing the GitHub PR Metrics Analyzer API
"""

import asyncio
import websockets
import requests
import json
import time
from datetime import datetime


def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy - Uptime: {data['uptime_seconds']:.1f}s")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def start_analysis(owner, repo, github_token):
    """Start a new analysis task"""
    print(f"🚀 Starting analysis for {owner}/{repo}...")
    
    payload = {
        "owner": owner,
        "repo": repo,
        "github_token": github_token,
        "since": "2023-01-01T00:00:00Z",  # Optional: filter by date
        # "until": "2024-01-01T00:00:00Z"  # Optional: filter by date
    }
    
    try:
        response = requests.post("http://localhost:8000/api/analyze", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Analysis task created: {data['task_id']}")
            return data['task_id']
        else:
            print(f"❌ Failed to start analysis: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error starting analysis: {e}")
        return None


def check_task_status(task_id):
    """Check the status of an analysis task"""
    print(f"📊 Checking status for task {task_id}...")
    
    try:
        response = requests.get(f"http://localhost:8000/api/analysis/{task_id}")
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            progress = data.get('progress', 0)
            message = data.get('message', '')
            
            print(f"📈 Status: {status} ({progress}%) - {message}")
            
            if status == 'completed':
                result = data.get('result')
                if result:
                    metadata = result.get('analysis_metadata', {})
                    print(f"🎉 Analysis completed!")
                    print(f"   - Total PRs processed: {metadata.get('total_prs_processed', 0)}")
                    print(f"   - Total developers: {metadata.get('total_developers', 0)}")
                    print(f"   - Analysis duration: {metadata.get('analysis_duration', 0):.1f}s")
            elif status == 'failed':
                error = data.get('error')
                print(f"💥 Analysis failed: {error}")
            
            return data
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None


async def monitor_websocket(task_id, duration=60):
    """Monitor analysis progress via WebSocket"""
    print(f"🔗 Monitoring WebSocket for task {task_id}...")
    
    uri = f"ws://localhost:8000/ws/{task_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            start_time = time.time()
            while time.time() - start_time < duration:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get('message_type') == 'progress':
                        progress_data = data.get('data', {})
                        status = progress_data.get('status', 'unknown')
                        progress = progress_data.get('progress', 0)
                        message = progress_data.get('message', '')
                        
                        print(f"📡 WebSocket Update: {status} ({progress}%) - {message}")
                    
                    elif data.get('message_type') == 'complete':
                        print("🎉 Analysis completed via WebSocket!")
                        break
                    
                    elif data.get('message_type') == 'error':
                        error_data = data.get('data', {})
                        error = error_data.get('error', 'Unknown error')
                        print(f"💥 Analysis failed via WebSocket: {error}")
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat
                    await websocket.send("ping")
                    continue
                    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")


def main():
    """Main example function"""
    print("🔬 GitHub PR Metrics Analyzer API Example")
    print("=" * 50)
    
    # Test health check
    if not test_health_check():
        print("❌ API not available. Make sure the backend is running.")
        print("   Run: python run_backend.py")
        return
    
    # Get configuration
    owner = input("Enter repository owner (e.g., 'microsoft'): ").strip()
    repo = input("Enter repository name (e.g., 'vscode'): ").strip()
    github_token = input("Enter your GitHub token: ").strip()
    
    if not owner or not repo or not github_token:
        print("❌ All fields are required")
        return
    
    # Start analysis
    task_id = start_analysis(owner, repo, github_token)
    if not task_id:
        return
    
    # Monitor via WebSocket in background
    print("\n" + "="*50)
    print("Choose monitoring method:")
    print("1. WebSocket (real-time updates)")
    print("2. Polling (check status every 5 seconds)")
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("🔗 Starting WebSocket monitoring...")
        asyncio.run(monitor_websocket(task_id, 300))  # 5 minutes max
    else:
        print("📊 Starting polling monitoring...")
        for i in range(60):  # Check for up to 5 minutes
            status_data = check_task_status(task_id)
            if status_data and status_data.get('status') in ['completed', 'failed']:
                break
            time.sleep(5)
    
    print("\n🏁 Example completed!")


if __name__ == "__main__":
    main()