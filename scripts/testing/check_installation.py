#!/usr/bin/env python3
"""
Installation Status Checker for Video Transcriber
Shows what features are currently available
"""

import os
import subprocess
import sys


def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if sys.platform == "win32":
        paths = [
            ".venv/Scripts/python.exe",
            "venv311/Scripts/python.exe",
            "venv/Scripts/python.exe",
        ]
    else:
        paths = [".venv/bin/python", "venv311/bin/python", "venv/bin/python"]

    for path in paths:
        if os.path.exists(path):
            return path
    return None


def check_installation_status():
    """Check what's currently installed"""
    print("🔍 Video Transcriber - Installation Status")
    print("=" * 50)

    # Check virtual environment
    venv_python = get_venv_python()
    if not venv_python:
        print("❌ No virtual environment found")
        print("Please run: ./run.sh (macOS/Linux) or run.bat (Windows)")
        return

    print(f"✅ Virtual environment: {venv_python}")

    # Check core features
    print("\n📦 Core Features:")
    try:
        subprocess.run(
            [venv_python, "-c", "import whisper"], check=True, capture_output=True
        )
        print("   ✅ OpenAI Whisper (Transcription)")
    except subprocess.CalledProcessError:
        print("   ❌ OpenAI Whisper (Transcription)")

    try:
        subprocess.run(
            [venv_python, "-c", "import flask"], check=True, capture_output=True
        )
        print("   ✅ Flask (Web Framework)")
    except subprocess.CalledProcessError:
        print("   ❌ Flask (Web Framework)")

    try:
        subprocess.run(
            [venv_python, "-c", "import ffmpeg"], check=True, capture_output=True
        )
        print("   ✅ FFmpeg-Python (Video Processing)")
    except subprocess.CalledProcessError:
        print("   ❌ FFmpeg-Python (Video Processing)")

    # Check AI features
    print("\n🧠 AI Features:")
    ai_count = 0

    try:
        subprocess.run(
            [venv_python, "-c", "import textblob"], check=True, capture_output=True
        )
        print("   ✅ TextBlob (Sentiment Analysis)")
        ai_count += 1
    except subprocess.CalledProcessError:
        print("   ❌ TextBlob (Sentiment Analysis)")

    try:
        subprocess.run(
            [venv_python, "-c", "import sklearn"], check=True, capture_output=True
        )
        print("   ✅ Scikit-learn (Topic Modeling)")
        ai_count += 1
    except subprocess.CalledProcessError:
        print("   ❌ Scikit-learn (Topic Modeling)")

    try:
        subprocess.run(
            [venv_python, "-c", "import spacy"], check=True, capture_output=True
        )
        print("   ✅ SpaCy (Advanced NLP)")

        # Check SpaCy model
        try:
            subprocess.run(
                [venv_python, "-c", "import spacy; spacy.load('en_core_web_sm')"],
                check=True,
                capture_output=True,
            )
            print("   ✅ SpaCy English Model")
            ai_count += 1
        except subprocess.CalledProcessError:
            print("   ⚠️  SpaCy installed but English model missing")
            print("      Run: python -m spacy download en_core_web_sm")
    except subprocess.CalledProcessError:
        print("   ❌ SpaCy (Advanced NLP)")

    # Check export features
    print("\n📄 Export Features:")
    export_count = 0

    print("   ✅ SRT/VTT Subtitles (Always available)")
    print("   ✅ Text/JSON/HTML (Always available)")

    try:
        subprocess.run(
            [venv_python, "-c", "import reportlab"], check=True, capture_output=True
        )
        print("   ✅ PDF Reports (ReportLab)")
        export_count += 1
    except subprocess.CalledProcessError:
        print("   ❌ PDF Reports (ReportLab)")

    try:
        subprocess.run(
            [venv_python, "-c", "import docx"], check=True, capture_output=True
        )
        print("   ✅ DOCX Documents (python-docx)")
        export_count += 1
    except subprocess.CalledProcessError:
        print("   ❌ DOCX Documents (python-docx)")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Installation Summary:")

    if ai_count == 3 and export_count == 2:
        print("🚀 FULL INSTALLATION - All features available!")
        print("   You have complete AI insights and export capabilities.")
    elif ai_count > 0:
        print("🔧 PARTIAL INSTALLATION - Some AI features available")
        print(f"   AI Features: {ai_count}/3 installed")
        print(f"   Export Features: {export_count}/2 installed")
        print("\n💡 To upgrade to full features:")
        print("   python install_ai_features.py")
    else:
        print("⚡ MINIMAL INSTALLATION - Core features only")
        print("   You have basic transcription capabilities.")
        print("\n💡 To add AI features:")
        print("   python install_ai_features.py")

    print("\n🎥 To start the application:")
    print("   ./run.sh (macOS/Linux) or run.bat (Windows)")


if __name__ == "__main__":
    try:
        check_installation_status()
    except Exception as e:
        print(f"❌ Error checking installation: {e}")
        sys.exit(1)
