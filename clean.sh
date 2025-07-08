#!/bin/bash
# Video Transcriber Environment Cleanup Launcher
# Wrapper script to run the maintenance cleanup from project root

echo "🧹 Video Transcriber Environment Cleanup"
echo "========================================"

# Change to project root if not already there
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not found"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Run the Python cleanup script from the maintenance directory
echo "🔄 Launching cleanup script..."
cd scripts/maintenance
python3 clean_environment.py

# Return to project root
cd "$SCRIPT_DIR"

echo ""
echo "🎯 Cleanup process completed!"
echo "📁 You are now back in the project root directory"
