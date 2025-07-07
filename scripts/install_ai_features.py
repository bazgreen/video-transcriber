#!/usr/bin/env python3
"""
AI Features Upgrade for Video Transcriber
Upgrades minimal installation to include full AI insights capabilities
"""

import os
import subprocess
import sys
from pathlib import Path


def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if sys.platform == "win32":
        if os.path.exists(os.path.join(".venv", "Scripts", "python.exe")):
            return os.path.join(".venv", "Scripts", "python.exe")
        elif os.path.exists(os.path.join("venv311", "Scripts", "python.exe")):
            return os.path.join("venv311", "Scripts", "python.exe")
        else:
            return os.path.join("venv", "Scripts", "python.exe")
    else:
        if os.path.exists(os.path.join(".venv", "bin", "python")):
            return os.path.join(".venv", "bin", "python")
        elif os.path.exists(os.path.join("venv311", "bin", "python")):
            return os.path.join("venv311", "bin", "python")
        else:
            return os.path.join("venv", "bin", "python")


def check_current_installation():
    """Check what's currently installed"""
    venv_python = get_venv_python()
    if not os.path.exists(venv_python):
        return None, None, None

    # Check for core dependencies
    try:
        subprocess.run(
            [venv_python, "-c", "import whisper, flask"],
            check=True,
            capture_output=True,
        )
        core_installed = True
    except subprocess.CalledProcessError:
        core_installed = False

    # Check for AI dependencies
    try:
        subprocess.run(
            [venv_python, "-c", "import textblob, sklearn"],
            check=True,
            capture_output=True,
        )
        ai_installed = True
    except subprocess.CalledProcessError:
        ai_installed = False

    # Check for SpaCy model
    try:
        subprocess.run(
            [venv_python, "-c", "import spacy; spacy.load('en_core_web_sm')"],
            check=True,
            capture_output=True,
        )
        spacy_model_installed = True
    except subprocess.CalledProcessError:
        spacy_model_installed = False

    return core_installed, ai_installed, spacy_model_installed


def install_ai_dependencies():
    """Install AI insights dependencies"""
    print("🧠 Upgrading to Full AI Features...")
    print("=" * 50)

    # Get virtual environment Python
    venv_python = get_venv_python()
    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found!")
        print("Please run the main setup script first:")
        print("   ./run.sh (macOS/Linux) or run.bat (Windows)")
        sys.exit(1)

    print(f"✅ Using virtual environment: {venv_python}")

    # Check current installation
    core_installed, ai_installed, spacy_model_installed = check_current_installation()

    if not core_installed:
        print("❌ Core Video Transcriber not found!")
        print("Please run the main installation first:")
        print("   ./run.sh (macOS/Linux) or run.bat (Windows)")
        sys.exit(1)

    if ai_installed and spacy_model_installed:
        print("✅ AI features are already fully installed!")
        print("🚀 Your Video Transcriber has complete AI capabilities.")
        return True

    # Install AI packages
    packages = [
        "textblob>=0.17.1",
        "scikit-learn>=1.3.0",
        "spacy>=3.7.0",
        "reportlab>=4.0.0",
        "python-docx>=1.1.0",
    ]

    print("📦 Installing AI and export packages...")
    for package in packages:
        try:
            print(f"   Installing {package}...")
            subprocess.run(
                [venv_python, "-m", "pip", "install", package],
                check=True,
                capture_output=True,
            )
            print(f"   ✅ {package.split('>=')[0]} installed")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {package}")
            return False

    # Install SpaCy English model
    if not spacy_model_installed:
        try:
            print("🧠 Installing SpaCy English language model...")
            subprocess.run(
                [venv_python, "-m", "spacy", "download", "en_core_web_sm"], check=True
            )
            print("✅ SpaCy English model installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install SpaCy English model")
            print("You can try installing it manually:")
            print(f"   {venv_python} -m spacy download en_core_web_sm")
            return False

    # Test installation
    try:
        print("🔍 Testing AI features...")
        subprocess.run(
            [
                venv_python,
                "-c",
                "import textblob, sklearn, spacy; nlp = spacy.load('en_core_web_sm'); print('All AI features working!')",
            ],
            check=True,
            capture_output=True,
        )
        print("✅ All AI features are working correctly!")
        return True
    except subprocess.CalledProcessError:
        print("❌ AI features test failed")
        print("Some dependencies may not be working correctly.")
        return False


def main():
    """Main installer function"""
    print("\n🧠 Video Transcriber - AI Features Upgrade")
    print("=" * 50)
    print("This will add these features to your installation:")
    print("  🎯 Sentiment Analysis - Detect emotional tone")
    print("  📊 Topic Modeling - Discover discussion themes")
    print("  🧠 Advanced NLP - Find people, places, organizations")
    print("  📄 PDF Reports - Professional analysis documents")
    print("  📝 DOCX Export - Microsoft Word format")
    print("\nEstimated time: 3-5 minutes")
    print("Your existing sessions and settings will be preserved.")

    # Auto-proceed for simplicity - no confirmation needed
    print("\n🚀 Starting upgrade...")

    # Change to project root
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    success = install_ai_dependencies()

    if success:
        print("\n" + "=" * 50)
        print("🎉 UPGRADE COMPLETE!")
        print("=" * 50)
        print("✅ Your Video Transcriber now has FULL AI capabilities!")
        print("\n🎯 What's new:")
        print("  • AI insights dashboard fully enabled")
        print("  • Advanced sentiment analysis")
        print("  • Intelligent topic modeling")
        print("  • Named entity recognition")
        print("  • Professional PDF and DOCX exports")
        print("\n🚀 Next steps:")
        print("  1. Restart the application (if running)")
        print("  2. Visit the AI Insights dashboard")
        print("  3. Process a video to see the new features!")
        print("\n💡 No more 'Limited features' messages!")
    else:
        print("\n❌ Upgrade failed!")
        print("Please check the error messages above.")
        print("You can try running the upgrade again or contact support.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Upgrade cancelled.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
