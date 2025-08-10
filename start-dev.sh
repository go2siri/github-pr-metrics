#!/bin/bash

# GitHub PR Metrics Analyzer - Development Startup Script

echo "🚀 Starting GitHub PR Metrics Analyzer..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GitHub token before running again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start backend in development mode
echo "🔧 Starting FastAPI backend..."
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 3

# Start frontend in development mode
echo "🎨 Starting React frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Development servers started!"
echo "📱 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Trap Ctrl+C and cleanup
trap 'echo "🛑 Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT

# Wait for processes
wait