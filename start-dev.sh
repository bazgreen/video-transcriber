#!/bin/bash
# Development server startup script with all required services

set -e

echo "🚀 Starting Video Transcriber Development Environment"
echo "======================================================="

# Function to cleanup on exit
cleanup() {
    echo -e "\n🧹 Cleaning up background processes..."
    
    # Kill Redis if we started it
    if [ ! -z "$REDIS_PID" ]; then
        kill $REDIS_PID 2>/dev/null || true
    fi
    
    # Kill Celery if we started it
    if [ ! -z "$CELERY_PID" ]; then
        kill $CELERY_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "redis-server" 2>/dev/null || true
    
    echo "✅ Cleanup completed"
    exit 0
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Check if Redis is running
if ! pgrep redis-server > /dev/null; then
    echo "🔴 Redis not running, starting it..."
    brew services start redis
    sleep 2
fi

# Verify Redis is accessible
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not accessible. Please check Redis installation."
    exit 1
fi

echo "✅ Redis is running"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./run.sh first to set up the environment."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Start Celery worker in background
echo "🔄 Starting Celery worker..."
celery -A celery_app worker --loglevel=info --concurrency=2 &
CELERY_PID=$!

# Give Celery time to start
sleep 3

# Check if Celery is running
if ! ps -p $CELERY_PID > /dev/null; then
    echo "❌ Celery failed to start"
    exit 1
fi

echo "✅ Celery worker started (PID: $CELERY_PID)"

# Start Flask application
echo "🌐 Starting Flask application..."
echo "   Access at: http://localhost:5001"
echo "   Press Ctrl+C to stop all services"
echo ""

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start the main application
python main.py