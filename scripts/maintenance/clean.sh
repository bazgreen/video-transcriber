#!/bin/bash
# Video Transcriber Environment Cleanup Script
# Quick wrapper for the Python cleanup script

echo "🧹 Video Transcriber Environment Cleanup"
echo "========================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not found"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Run the Python cleanup script
python3 clean_environment.py

echo ""
echo "✅ Cleanup script completed"
