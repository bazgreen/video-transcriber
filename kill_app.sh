#!/bin/bash
# Enhanced kill script for Video Transcriber application and all related services
# This script stops the main application, Docker services, and background processes

echo "🛑 Stopping Video Transcriber Application and Services"
echo "======================================================"

# Function to check if a process is running
check_process() {
    local process_name="$1"
    local count=$(ps aux | grep "$process_name" | grep -v grep | wc -l)
    echo $count
}

# Function to kill processes by pattern
kill_by_pattern() {
    local pattern="$1"
    local description="$2"
    
    local pids=$(ps aux | grep -E "$pattern" | grep -v grep | awk '{print $2}')
    if [ ! -z "$pids" ]; then
        echo "🔄 Stopping $description..."
        for pid in $pids; do
            kill $pid 2>/dev/null && echo "  ✅ Stopped process $pid"
        done
    else
        echo "  ℹ️  No $description processes found"
    fi
}

# 1. Stop Docker services first
echo "🐳 Stopping Docker services..."
if command -v docker-compose >/dev/null 2>&1; then
    if [ -f "docker-compose.yml" ]; then
        docker-compose down 2>/dev/null && echo "  ✅ Docker Compose services stopped"
    fi
    
    # Stop individual containers if any
    containers=$(docker ps -q --filter "name=video-transcriber" 2>/dev/null)
    if [ ! -z "$containers" ]; then
        docker stop $containers 2>/dev/null && echo "  ✅ Video Transcriber containers stopped"
    fi
else
    echo "  ℹ️  Docker not available"
fi

# 2. Stop Python application processes
echo "🐍 Stopping Python processes..."
kill_by_pattern "[p]ython.*main\.py" "Flask application"
kill_by_pattern "[c]elery.*worker" "Celery workers"
kill_by_pattern "[c]elery.*beat" "Celery beat scheduler"

# 3. Stop processes using specific ports
echo "🌐 Freeing up ports..."
ports=(5001 6379 9090 3000 5432)
port_names=("Flask App" "Redis" "Prometheus" "Grafana" "PostgreSQL")

for i in "${!ports[@]}"; do
    port=${ports[$i]}
    name=${port_names[$i]}
    
    if lsof -i :$port >/dev/null 2>&1; then
        echo "🔌 Port $port ($name) is in use, freeing it..."
        pids=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$pids" ]; then
            for pid in $pids; do
                kill $pid 2>/dev/null && echo "  ✅ Freed port $port (PID: $pid)"
            done
        fi
    fi
done

# 4. Force kill any remaining processes if needed
echo "🔧 Final cleanup..."
sleep 2

# Check for any remaining processes on port 5001
if lsof -i :5001 >/dev/null 2>&1; then
    echo "⚠️  Port 5001 still in use, force killing..."
    remaining_pids=$(lsof -ti :5001 2>/dev/null)
    for pid in $remaining_pids; do
        kill -9 $pid 2>/dev/null && echo "  🔥 Force killed process $pid"
    done
fi

# 5. Clean up any leftover PID files
echo "🧹 Cleaning up PID files..."
find . -name "*.pid" -type f -delete 2>/dev/null && echo "  ✅ Removed PID files"

# 6. Final verification
echo "🔍 Verification..."
if lsof -i :5001 >/dev/null 2>&1; then
    echo "  ❌ Port 5001 is still in use"
    lsof -i :5001
else
    echo "  ✅ Port 5001 is free"
fi

# Show summary
main_processes=$(check_process "[p]ython.*main\.py")
celery_processes=$(check_process "[c]elery.*worker")

if [ "$main_processes" -eq 0 ] && [ "$celery_processes" -eq 0 ]; then
    echo ""
    echo "🎉 Successfully stopped all Video Transcriber services!"
    echo "✅ Application is completely shut down"
else
    echo ""
    echo "⚠️  Some processes may still be running:"
    if [ "$main_processes" -gt 0 ]; then
        echo "   • Main application: $main_processes processes"
    fi
    if [ "$celery_processes" -gt 0 ]; then
        echo "   • Celery workers: $celery_processes processes"
    fi
    echo ""
    echo "💡 You may need to manually kill remaining processes with:"
    echo "   sudo kill -9 <PID>"
fi

echo ""
echo "🚀 Ready for fresh application start!"