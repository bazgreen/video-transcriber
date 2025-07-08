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
CLEANUP_EXIT_CODE=$?

echo ""
if [ $CLEANUP_EXIT_CODE -eq 0 ]; then
    echo "✅ Cleanup script completed successfully"
    echo "🎯 Environment has been reset to pristine state"
    echo "🚀 Ready for fresh installation testing"
else
    echo "❌ Cleanup script encountered issues (exit code: $CLEANUP_EXIT_CODE)"
    echo "⚠️  Some manual cleanup may be required"
fi
