#!/usr/bin/env python3
"""
Setup and Run Script for Video Transcriber
Handles virtual environment setup, dependency installation, and app launch
"""

import os
import platform
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


def print_header():
    """Print welcome header"""
    print("\n" + "=" * 60)
    print("🎥 Video Transcriber - Setup & Launch")
    print("=" * 60 + "\n")


def choose_installation_type():
    """Let user choose between minimal and full installation"""
    print("📦 Choose your installation type:")
    print("=" * 40)
    print("\n1. 🚀 MINIMAL INSTALLATION (Recommended for quick start)")
    print("   • Fast video transcription with OpenAI Whisper")
    print("   • Basic keyword detection and analysis")
    print("   • Export formats: SRT, VTT, Text, JSON, HTML")
    print("   • Session management and search")
    print("   • Performance monitoring")
    print("   • ~2-3 minutes install time")

    print("\n2. 🧠 FULL INSTALLATION (Complete feature set)")
    print("   • Everything from Minimal installation")
    print("   • AI-powered sentiment analysis")
    print("   • Advanced topic modeling")
    print("   • Named entity recognition (NLP)")
    print("   • Professional PDF and DOCX exports")
    print("   • Advanced analytics dashboard")
    print("   • ~5-8 minutes install time")

    print("\n" + "-" * 40)

    while True:
        choice = input("Enter your choice (1 for Minimal, 2 for Full) [1]: ").strip()

        if choice == "" or choice == "1":
            print("\n✅ Minimal installation selected")
            return "minimal"
        elif choice == "2":
            print("\n✅ Full installation selected")
            return "full"
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")
            continue


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
    # Use .venv as the primary virtual environment
    if platform.system() == "Windows":
        if os.path.exists(os.path.join(".venv", "Scripts", "python.exe")):
            return os.path.join(".venv", "Scripts", "python.exe")
        elif os.path.exists(os.path.join("env", "venv311", "Scripts", "python.exe")):
            return os.path.join("env", "venv311", "Scripts", "python.exe")
        elif os.path.exists(os.path.join("venv311", "Scripts", "python.exe")):
            return os.path.join("venv311", "Scripts", "python.exe")
        elif os.path.exists(os.path.join("env", "venv", "Scripts", "python.exe")):
            return os.path.join("env", "venv", "Scripts", "python.exe")
        else:
            # Default to .venv for newly created environments
            return os.path.join(".venv", "Scripts", "python.exe")
    else:
        if os.path.exists(os.path.join(".venv", "bin", "python")):
            return os.path.join(".venv", "bin", "python")
        elif os.path.exists(os.path.join("env", "venv311", "bin", "python")):
            return os.path.join("env", "venv311", "bin", "python")
        elif os.path.exists(os.path.join("venv311", "bin", "python")):
            return os.path.join("venv311", "bin", "python")
        elif os.path.exists(os.path.join("env", "venv", "bin", "python")):
            return os.path.join("env", "venv", "bin", "python")
        else:
            # Default to .venv for newly created environments
            return os.path.join(".venv", "bin", "python")


def setup_virtualenv():
    """Create virtual environment if it doesn't exist"""
    # Check for existing virtual environments, prefer .venv
    venv_python = get_venv_python()

    # Determine which venv path to use, prioritizing .venv
    if os.path.exists(".venv"):
        print("✅ Virtual environment already exists (.venv)")
    elif os.path.exists(os.path.join("env", "venv311")):
        print("✅ Virtual environment already exists (env/venv311)")
    elif os.path.exists("venv311"):
        print("✅ Virtual environment already exists (venv311)")
    elif os.path.exists(os.path.join("env", "venv")):
        print("✅ Virtual environment already exists (env/venv)")
    elif os.path.exists("venv"):
        print("✅ Virtual environment already exists (venv)")
    else:
        print("🔧 Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Virtual environment created (.venv)")

    return venv_python


def install_dependencies(venv_python, installation_type="minimal"):
    """Install required dependencies based on installation type"""
    print(f"\n📚 Installing dependencies ({installation_type} installation)...")

    # Define package sets
    minimal_packages = [
        "torch",
        "numpy>=2.0.0",
        "flask>=3.0.0",
        "flask-socketio>=5.5.0",
        "ffmpeg-python>=0.2.0",
        "openai-whisper>=20231117",
        "psutil>=7.0.0",
    ]

    ai_packages = [
        "textblob>=0.17.1",
        "scikit-learn>=1.3.0",
        "spacy>=3.7.0",
    ]

    export_packages = [
        "reportlab>=4.0.0",
        "python-docx>=1.1.0",
    ]

    # Check if dependencies are already installed
    try:
        result = subprocess.run(
            [venv_python, "-c", "import whisper, flask, ffmpeg"], capture_output=True
        )
        if result.returncode == 0:
            print("✅ Core dependencies are already installed")

            # Check AI features for full installation
            if installation_type == "full":
                try:
                    subprocess.run(
                        [
                            venv_python,
                            "-c",
                            "import textblob, sklearn, spacy; spacy.load('en_core_web_sm')",
                        ],
                        capture_output=True,
                        check=True,
                    )
                    print("✅ AI features are already installed")
                    return
                except subprocess.CalledProcessError:
                    print("🔧 Installing AI features...")
                    install_ai_features(venv_python)
                    return
            else:
                return
    except Exception:
        pass

    print(f"📥 Installing dependencies (this may take a few minutes on first run)...")

    try:
        # Upgrade pip first
        print("📦 Upgrading pip...")
        subprocess.run(
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            check=True,
        )

        # Determine which requirements file to use
        if installation_type == "minimal":
            requirements_file = "requirements.txt"
        elif installation_type == "full":
            requirements_file = "requirements-full.txt"
        else:
            requirements_file = "requirements.txt"

        # Install from requirements file if it exists
        if os.path.exists(requirements_file):
            print(f"📦 Installing from {requirements_file}...")
            result = subprocess.run(
                [venv_python, "-m", "pip", "install", "-r", requirements_file],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print("✅ Dependencies installed successfully")
                if installation_type == "full":
                    install_spacy_model(venv_python)
                return
            else:
                print(
                    "⚠️ Requirements file installation failed, trying individual packages..."
                )

        # Fallback: install packages individually
        packages_to_install = minimal_packages.copy()

        if installation_type == "full":
            packages_to_install.extend(ai_packages)
            packages_to_install.extend(export_packages)

        for package in packages_to_install:
            try:
                print(f"📦 Installing {package}...")
                subprocess.run(
                    [venv_python, "-m", "pip", "install", package],
                    capture_output=True,
                    check=True,
                )
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(
                    f"⚠️ Failed to install {package}, trying without version constraints..."
                )
                try:
                    # Try without version constraints
                    base_package = package.split(">=")[0].split("==")[0]
                    subprocess.run(
                        [venv_python, "-m", "pip", "install", base_package],
                        capture_output=True,
                        check=True,
                    )
                    print(f"✅ {base_package} installed successfully (latest version)")
                except subprocess.CalledProcessError:
                    if package == "openai-whisper":
                        print("⚠️ Trying to install whisper from GitHub repository...")
                        try:
                            subprocess.run(
                                [
                                    venv_python,
                                    "-m",
                                    "pip",
                                    "install",
                                    "git+https://github.com/openai/whisper.git",
                                ],
                                capture_output=True,
                                check=True,
                            )
                            print(
                                "✅ openai-whisper installed successfully from GitHub"
                            )
                        except subprocess.CalledProcessError:
                            print("❌ Failed to install openai-whisper")
                    else:
                        print(f"❌ Failed to install {package}")

        print("✅ Dependencies installation completed")

        # Install SpaCy model for full installation
        if installation_type == "full":
            install_spacy_model(venv_python)

    except subprocess.CalledProcessError as e:
        print(f"❌ Error during dependency installation: {e}")
        print(
            "You may need to install dependencies manually in the virtual environment."
        )


def install_ai_features(venv_python):
    """Install AI features separately"""
    packages = ["textblob>=0.17.1", "scikit-learn>=1.3.0", "spacy>=3.7.0"]

    for package in packages:
        try:
            print(f"🧠 Installing {package}...")
            subprocess.run(
                [venv_python, "-m", "pip", "install", package],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")

    install_spacy_model(venv_python)


def install_spacy_model(venv_python):
    """Install SpaCy English language model"""
    try:
        print("🧠 Installing SpaCy English language model...")
        subprocess.run(
            [venv_python, "-m", "spacy", "download", "en_core_web_sm"],
            capture_output=True,
            check=True,
        )
        print("✅ SpaCy English model installed successfully")
        print("🚀 AI insights features are now fully enabled!")
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install SpaCy English model")
        print("   You can install it manually later with:")
        print(f"   {venv_python} -m spacy download en_core_web_sm")


def create_directories():
    """Create necessary directories"""
    dirs = ["uploads", "results", "templates", "scripts", "config", "docs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Required directories created")


def wait_for_app_ready(venv_python, url="http://localhost:5001", max_wait=30):
    """
    Wait for the Flask app to be ready by checking the health endpoint.

    Args:
        venv_python: Path to the virtual environment python
        url: Base URL of the application
        max_wait: Maximum time to wait in seconds

    Returns:
        bool: True if app is ready, False if timeout
    """
    import time

    try:
        # Try importing requests from the virtual environment
        result = subprocess.run(
            [venv_python, "-c", "import requests"], capture_output=True
        )
        if result.returncode != 0:
            # Install requests in the virtual environment
            print("📦 Installing requests for health checking...")
            subprocess.run(
                [venv_python, "-m", "pip", "install", "requests"],
                capture_output=True,
                check=True,
            )
    except Exception:
        print("⚠️  Could not install requests, using basic delay instead...")
        time.sleep(5)  # Basic fallback delay
        return True

    print(f"🔍 Waiting for application at {url}/health...")
    start_time = time.time()
    health_url = f"{url}/health"
    success_count = 0  # Count consecutive successes for reliability

    while time.time() - start_time < max_wait:
        try:
            # Run a simple health check in subprocess
            check_script = f"""
import requests
try:
    response = requests.get("{health_url}", timeout=2)
    exit(0 if response.status_code == 200 else 1)
except Exception as e:
    exit(1)
"""
            result = subprocess.run(
                [venv_python, "-c", check_script], capture_output=True, timeout=5
            )

            if result.returncode == 0:
                success_count += 1
                print(f"\n✅ Health check passed ({success_count}/2)")
                if success_count >= 2:  # Require 2 consecutive successes
                    print("✅ Application is ready and stable!")
                    return True
            else:
                success_count = 0  # Reset on failure

        except subprocess.TimeoutExpired:
            success_count = 0
            pass
        except Exception:
            success_count = 0
            pass

        elapsed = int(time.time() - start_time)
        dots = "." * ((elapsed % 4) + 1)
        print(f"\r⏳ Starting up{dots:<4}", end="", flush=True)
        time.sleep(1)

    print(f"\n⚠️  Application didn't respond within {max_wait} seconds")
    return False


def open_browser_when_ready(venv_python, url):
    """Open browser only after the app is confirmed to be ready."""
    # Use 127.0.0.1 instead of localhost for more reliable health check
    health_url = url.replace("localhost", "127.0.0.1")

    print("🔍 Checking if application is ready...")

    if wait_for_app_ready(venv_python, health_url):
        print(f"🌐 Opening browser at {url}")
        try:
            import webbrowser

            webbrowser.open(url)
            print("✅ Browser opened successfully!")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"   Please open manually: {url}")
    else:
        print(f"🌐 You can manually access the app at: {url}")
        print("   The application may still be starting up...")


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

    # Start browser opening in background with health check
    import threading

    browser_thread = threading.Thread(
        target=open_browser_when_ready, args=(venv_python, "http://localhost:5001")
    )
    browser_thread.daemon = True
    browser_thread.start()

    # Run the app
    env = os.environ.copy()
    env["FLASK_ENV"] = "production"

    app_file = "main.py"
    if not os.path.exists(app_file):
        print(f"❌ Error: {app_file} not found in the project root!")
        sys.exit(1)

    print(f"🚀 Starting Video Transcriber ({app_file})...")
    try:
        subprocess.run([venv_python, app_file], env=env)
    except KeyboardInterrupt:
        print("\n\n👋 Video Transcriber stopped. Goodbye!")


def main():
    """Main setup and run function"""
    print_header()

    # Change to project root directory to ensure paths are correct
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    print(f"✅ Working directory set to: {os.getcwd()}")

    # Choose installation type
    installation_type = choose_installation_type()

    # Run checks and setup
    check_python_version()
    ffmpeg_installed = check_ffmpeg()

    print("\n🔧 Setting up environment...")
    venv_python = setup_virtualenv()
    install_dependencies(venv_python, installation_type)
    create_directories()

    if not ffmpeg_installed:
        print("\n⚠️  Warning: FFmpeg is required for video processing")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            print("Setup cancelled.")
            sys.exit(0)

    # Display installation summary
    print("\n" + "=" * 50)
    print("🎉 Installation Complete!")
    print("=" * 50)

    if installation_type == "minimal":
        print("✅ Minimal installation ready with:")
        print("   • Fast video transcription")
        print("   • Basic analysis and keywords")
        print("   • Export: SRT, VTT, Text, JSON, HTML")
        print("   • Session management")
        print("\n💡 To upgrade to full features later, run:")
        print("   python install_ai_features.py")
    else:
        print("✅ Full installation ready with:")
        print("   • Advanced AI insights and NLP")
        print("   • Professional PDF and DOCX exports")
        print("   • Complete feature set")

    print(f"\n🚀 Starting Video Transcriber...")

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
