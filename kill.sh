#!/bin/bash
# This script finds and kills the running video-transcriber Flask application and related services.

echo "Searching for running video-transcriber app processes..."

# Method 1: Find processes by command pattern (includes new Celery workers)
PIDS=$(ps aux | grep -E "[p]ython.*main.py|[p]ython.*app.py|[m]ain.py|[a]pp.py|[c]elery.*worker|[c]elery.*beat" | awk '{print $2}')

# Method 2: Find processes using port 5001 (main app)
PORT_PIDS=$(lsof -ti :5001 2>/dev/null)

# Method 3: Find Redis processes (if running locally for Celery)
REDIS_PIDS=$(ps aux | grep "[r]edis-server" | awk '{print $2}')

# Method 4: Find any Docker containers related to video-transcriber
echo "Checking for Docker containers..."
DOCKER_CONTAINERS=$(docker ps -q --filter "name=video-transcriber" 2>/dev/null)
if [ ! -z "$DOCKER_CONTAINERS" ]; then
    echo "Stopping Docker containers..."
    docker stop $DOCKER_CONTAINERS 2>/dev/null
    echo "✅ Stopped Docker containers"
fi

# Stop Docker Compose services if running
if [ -f "docker-compose.yml" ]; then
    echo "Stopping Docker Compose services..."
    docker-compose down 2>/dev/null || true
    echo "✅ Stopped Docker Compose services"
fi

# Combine all PIDs
ALL_PIDS="$PIDS $PORT_PIDS $REDIS_PIDS"

# Remove duplicates and empty values
UNIQUE_PIDS=$(echo $ALL_PIDS | tr ' ' '\n' | sort -u | grep -v '^$')

if [ -z "$UNIQUE_PIDS" ]; then
  echo "No running app processes found."
else
  echo "Found running processes with PIDs: $UNIQUE_PIDS"
  for PID in $UNIQUE_PIDS; do
    echo "Killing process $PID..."
    kill $PID 2>/dev/null
    if [ $? -eq 0 ]; then
      echo "  ✅ Process $PID killed successfully"
    else
      echo "  ⚠️  Failed to kill process $PID (may already be stopped)"
    fi
  done

  # Wait a moment and check if port 5001 is still in use
  sleep 2
  if lsof -i :5001 >/dev/null 2>&1; then
    echo "⚠️  Port 5001 is still in use. Trying force kill..."
    REMAINING_PIDS=$(lsof -ti :5001 2>/dev/null)
    for PID in $REMAINING_PIDS; do
      echo "Force killing process $PID..."
      kill -9 $PID 2>/dev/null
    done
  else
    echo "✅ Port 5001 is now free"
  fi
fi

# Check and clean up other common ports used by the application
OTHER_PORTS="6379 9090 3000 5432"  # Redis, Prometheus, Grafana, PostgreSQL
for PORT in $OTHER_PORTS; do
    if lsof -i :$PORT >/dev/null 2>&1; then
        echo "⚠️  Port $PORT is in use (may be Redis/Prometheus/Grafana/PostgreSQL)"
        PORT_PIDS=$(lsof -ti :$PORT 2>/dev/null)
        if [ ! -z "$PORT_PIDS" ]; then
            echo "Processes using port $PORT: $PORT_PIDS"
            # Only kill if they seem to be related to our application
            ps -p $PORT_PIDS | grep -E "(redis|prometheus|grafana|postgres)" && {
                echo "Killing related service processes on port $PORT..."
                kill $PORT_PIDS 2>/dev/null
            }
        fi
    fi
done

echo "✅ Application cleanup complete"
