#!/usr/bin/env python3
"""
Setup and Run Script for Video Transcriber
Handles virtual environment setup, dependency installation, and app launch
"""

import os
import sys
import subprocess
import platform
import webbrowser
import time
from pathlib import Path

def print_header():
    """Print welcome header"""
    print("\n" + "="*60)
    print("🎥 Video Transcriber - Setup & Launch")
    print("="*60 + "\n")

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  FFmpeg is not installed")
        print("\nPlease install FFmpeg:")
        if platform.system() == "Darwin":
            print("  macOS: brew install ffmpeg")
        elif platform.system() == "Linux":
            print("  Linux: sudo apt update && sudo apt install ffmpeg")
        elif platform.system() == "Windows":
            print("  Windows: Download from https://ffmpeg.org/download.html")
        print("\nContinuing without FFmpeg (required for video processing)...")
        return False

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if platform.system() == "Windows":
        return os.path.join("venv", "Scripts", "python.exe")
    return os.path.join("venv", "bin", "python")

def setup_virtualenv():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    venv_python = get_venv_python()
    
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")
    
    return venv_python

def install_dependencies(venv_python):
    """Install required dependencies"""
    print("\n📚 Checking dependencies...")
    
    # Check if dependencies are already installed
    try:
        result = subprocess.run(
            [venv_python, "-c", "import whisper, flask, ffmpeg"],
            capture_output=True
        )
        if result.returncode == 0:
            print("✅ All dependencies are already installed")
            return
    except:
        pass
    
    print("📥 Installing dependencies (this may take a few minutes on first run)...")
    
    try:
        # Upgrade pip first
        print("📦 Upgrading pip...")
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], 
                       capture_output=True, check=True)
        
        # Install requirements
        if os.path.exists("requirements.txt"):
            print("📦 Installing from requirements.txt...")
            result = subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  Standard installation failed, trying alternative approach...")
                # Try installing packages individually for better error handling
                packages = ["torch", "numpy", "flask", "ffmpeg-python", "openai-whisper"]
                for package in packages:
                    try:
                        print(f"📦 Installing {package}...")
                        subprocess.run([venv_python, "-m", "pip", "install", package], 
                                     capture_output=True, check=True)
                        print(f"✅ {package} installed successfully")
                    except subprocess.CalledProcessError as e:
                        print(f"⚠️  Failed to install {package}, trying without version constraints...")
                        try:
                            # Try without version constraints
                            base_package = package.split(">=")[0].split("==")[0]
                            subprocess.run([venv_python, "-m", "pip", "install", base_package], 
                                         capture_output=True, check=True)
                            print(f"✅ {base_package} installed successfully (latest version)")
                        except subprocess.CalledProcessError:
                            if package == "openai-whisper":
                                print("⚠️  Trying to install whisper from GitHub repository...")
                                try:
                                    subprocess.run([venv_python, "-m", "pip", "install", 
                                                  "git+https://github.com/openai/whisper.git"], 
                                                 capture_output=True, check=True)
                                    print("✅ openai-whisper installed successfully from GitHub")
                                except subprocess.CalledProcessError:
                                    print("❌ Failed to install openai-whisper")
                                    print("   You may need to install openai-whisper manually:")
                                    print("   source venv/bin/activate && pip install git+https://github.com/openai/whisper.git")
                            else:
                                print(f"❌ Failed to install {package}")
        else:
            # Fallback if requirements.txt is missing
            packages = ["torch", "numpy", "flask", "ffmpeg-python", "openai-whisper"]
            for package in packages:
                try:
                    print(f"📦 Installing {package}...")
                    subprocess.run([venv_python, "-m", "pip", "install", package], check=True)
                except subprocess.CalledProcessError:
                    print(f"⚠️  Failed to install {package}")
        
        print("✅ Dependencies installation completed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during dependency installation: {e}")
        print("You may need to install dependencies manually in the virtual environment.")
        print("Common solutions:")
        print("1. Update your Python version (3.8-3.12 recommended)")
        print("2. Install dependencies manually: source venv/bin/activate && pip install flask torch numpy ffmpeg-python")
        print("3. For whisper: pip install git+https://github.com/openai/whisper.git")

def create_directories():
    """Create necessary directories"""
    dirs = ["uploads", "results", "templates", "scripts", "config", "docs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Required directories created")

def open_browser_delayed(url, delay=2):
    """Open browser after a delay to ensure server is running"""
    time.sleep(delay)
    print(f"\n🌐 Opening browser at {url}")
    webbrowser.open(url)

def run_app(venv_python):
    """Run the Flask application"""
    print("\n🚀 Starting Video Transcriber...")
    print("   Access the app at: http://localhost:5001")
    print("   Press Ctrl+C to stop the server\n")
    
    # Start browser opening in background
    import threading
    browser_thread = threading.Thread(
        target=open_browser_delayed, 
        args=("http://localhost:5001",)
    )
    browser_thread.daemon = True
    browser_thread.start()
    
    # Run the app
    env = os.environ.copy()
    env['FLASK_ENV'] = 'production'
    
    try:
        subprocess.run([venv_python, "app.py"], env=env)
    except KeyboardInterrupt:
        print("\n\n👋 Video Transcriber stopped. Goodbye!")

def main():
    """Main setup and run function"""
    print_header()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run checks and setup
    check_python_version()
    ffmpeg_installed = check_ffmpeg()
    
    print("\n🔧 Setting up environment...")
    venv_python = setup_virtualenv()
    install_dependencies(venv_python)
    create_directories()
    
    if not ffmpeg_installed:
        print("\n⚠️  Warning: FFmpeg is required for video processing")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    # Run the application
    run_app(venv_python)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nIf you continue to have issues, please check:")
        print("  1. You have Python 3.8+ installed")
        print("  2. You have write permissions in this directory")
        print("  3. Your antivirus isn't blocking the installation")
        sys.exit(1)