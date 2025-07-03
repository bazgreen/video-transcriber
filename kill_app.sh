#!/bin/bash
# This script finds and kills the running video-transcriber Flask application.

echo "Searching for running video-transcriber app processes..."

# Method 1: Find processes by command pattern
PIDS=$(ps aux | grep "[p]ython.*main.py\|[p]ython.*app.py\|[m]ain.py\|[a]pp.py" | awk '{print $2}')

# Method 2: Find processes using port 5001
PORT_PIDS=$(lsof -ti :5001 2>/dev/null)

# Combine all PIDs
ALL_PIDS="$PIDS $PORT_PIDS"

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
