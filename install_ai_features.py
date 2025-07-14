"""
Installation script for AI features dependencies.
Installs advanced AI capabilities including sentiment analysis, topic modeling,
transcript correction, and professional export formats.
"""

import subprocess
import sys
import os


def main():
    """Install AI features using the main installation script."""
    script_path = os.path.join("scripts", "install_ai_features.py")
    
    if os.path.exists(script_path):
        # Run the main installation script
        subprocess.run([sys.executable, script_path])
    else:
        print("❌ AI features installation script not found!")
        print(f"Expected: {script_path}")
        print("\nPlease make sure you're in the project root directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()
