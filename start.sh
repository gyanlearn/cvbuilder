#!/bin/bash

# CV Parser & ATS Scorer - Quick Start Script
# This script helps you start the application for development

echo "🚀 Starting CV Parser & ATS Scorer..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  .env file not found in backend directory."
    echo "📝 Creating .env file from template..."
    cp env.example backend/.env
    echo "✅ Created .env file. Please edit backend/.env with your API keys:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY" 
    echo "   - GEMINI_API_KEY"
    echo ""
    echo "After setting up your .env file, run this script again."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if backend dependencies are installed
if ! python3 -c "import fastapi, supabase, google.generativeai" 2>/dev/null; then
    echo "❌ Some required packages are missing. Installing..."
    pip install -r requirements.txt
fi

# Start backend server
echo "🔧 Starting backend server..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend server is running on http://localhost:8000"
else
    echo "❌ Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend server
echo "🎨 Starting frontend server..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 2

echo ""
echo "🎉 CV Parser & ATS Scorer is now running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running
wait
