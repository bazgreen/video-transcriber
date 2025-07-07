# 🚀 Quick Start Guide

## Super Simple Installation

1. **Get the code:**
   ```bash
   git clone https://github.com/bazgreen/video-transcriber.git
   cd video-transcriber
   ```

2. **Run it:**
   ```bash
   ./run.sh  # macOS/Linux
   # or
   run.bat   # Windows
   ```

3. **Choose your installation:**
   - **🚀 Minimal** (2-3 minutes) - Core transcription features
   - **🧠 Full** (5-8 minutes) - Complete AI insights

That's it! Your browser will open automatically.

## Want More Features Later?

Started with Minimal but need AI features? One command:

```bash
python install_ai_features.py
```

Adds:
- 🎯 Sentiment analysis
- 📊 Topic modeling
- 🧠 Named entity recognition
- 📄 PDF reports
- 📝 DOCX documents

## Check What You Have

```bash
python check_installation.py
```

Shows exactly what features are available.

## Troubleshooting

**Something broken?** Fresh start:
```bash
rm -rf .venv && ./run.sh
```

**Missing FFmpeg?**
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: Download from ffmpeg.org

That's all you need to know! 🎉
