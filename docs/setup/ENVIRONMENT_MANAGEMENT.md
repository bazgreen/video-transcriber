# 🧹 Environment Management Scripts

This directory contains scripts for managing the Video Transcriber development and testing environment.

## 🚀 Quick Reference

### Installation
```bash
./run.sh                    # Interactive installation (macOS/Linux)
run.bat                     # Interactive installation (Windows)
```

### Environment Cleanup
```bash
./clean.sh                  # Quick cleanup (macOS/Linux)
clean.bat                   # Quick cleanup (Windows)
python3 clean_environment.py  # Full cleanup script
```

### Testing
```bash
python3 test_installation.py  # Complete installation test suite
```

## 📋 Script Details

### 🔧 Installation Scripts

**`scripts/setup/setup_and_run.py`**
- Main installation script with interactive setup
- Supports both minimal and full installation types
- Handles virtual environment creation and dependency installation
- Automatically starts the application after installation

**`run.sh` / `run.bat`**
- Simple wrappers for the main setup script
- Cross-platform compatibility

### 🧹 Cleanup Scripts

**`clean_environment.py`**
- **Purpose**: Complete environment reset for fresh testing
- **What it removes**:
  - Virtual environments (.venv, env/, venv*)
  - Python cache files (__pycache__, *.pyc)
  - Upload files and results
  - Log files and temporary data
  - Development artifacts (.pytest_cache, .mypy_cache, etc.)
- **What it preserves**:
  - Source code and configuration
  - README and documentation  
  - Git repository
- **Features**:
  - Interactive confirmation
  - Detailed progress reporting
  - Cross-platform process termination
  - Verification of cleanup success

**`clean.sh` / `clean.bat`**
- Simple wrappers for the Python cleanup script
- Cross-platform compatibility

### 🧪 Testing Scripts

**`test_installation.py`**
- **Purpose**: Automated testing of installation process
- **Test Coverage**:
  - Minimal installation process
  - Full installation process
  - Package availability verification
  - Upgrade path (minimal → full)
  - Application startup verification
- **Features**:
  - Automated cleanup between tests
  - Comprehensive test reporting
  - Timeout handling for long operations
  - Detailed pass/fail summary

## 🔄 Testing Workflow

### Complete Test Cycle
```bash
# 1. Clean environment
python3 clean_environment.py

# 2. Test minimal installation
echo "1" | python3 scripts/setup/setup_and_run.py

# 3. Clean and test full installation  
python3 clean_environment.py
echo "2" | python3 scripts/setup/setup_and_run.py

# 4. Or run automated test suite
python3 test_installation.py
```

### Manual Testing Steps
```bash
# 1. Start fresh
./clean.sh

# 2. Test installation
./run.sh

# 3. Verify application works
.venv/bin/python main.py

# 4. Test package imports
.venv/bin/python -c "import whisper, flask, textblob; print('All packages OK')"
```

## 📊 Test Scenarios

### Minimal Installation
- **Time**: ~2-3 minutes
- **Packages**: Core transcription, basic web framework, authentication
- **Features**: Video transcription, basic analysis, SRT/VTT export
- **Upgrade**: Can upgrade to full with `python install_ai_features.py`

### Full Installation  
- **Time**: ~5-8 minutes
- **Packages**: Everything from minimal + AI packages + export libraries
- **Features**: All features including sentiment analysis, PDF/DOCX export
- **AI Models**: Includes SpaCy English language model

### Upgrade Path Testing
- Install minimal → Run upgrade script → Verify AI features work

## 🛡️ Safety Features

### Cleanup Safety
- Interactive confirmation before cleanup
- Preserves source code and documentation
- Lists exactly what will be removed
- Verification step after cleanup

### Installation Safety
- Version checking (Python 3.8+)
- FFmpeg availability checking
- Graceful fallback for failed packages
- Virtual environment isolation

### Testing Safety
- Automated cleanup between tests
- Timeout protection for long operations
- Non-destructive testing (preserves source)
- Detailed error reporting

## 🎯 Use Cases

### Development
```bash
# Reset for clean development
./clean.sh
./run.sh  # Choose your preferred installation type
```

### Continuous Integration
```bash
# Automated testing in CI pipeline
python3 test_installation.py
```

### User Testing
```bash
# Simulate new user experience
./clean.sh
./run.sh  # Follow prompts as a new user would
```

### Debugging Installation Issues
```bash
# Manual step-by-step testing
python3 clean_environment.py
python3 scripts/setup/setup_and_run.py  # With detailed output
```

## 🔍 Troubleshooting

### Cleanup Issues
- **Permission errors**: Ensure write permissions in project directory
- **Process still running**: Manually kill processes with `pkill -f python.*main.py`
- **Incomplete cleanup**: Review verification output and manually remove remaining items

### Installation Issues
- **Python version**: Ensure Python 3.8+ is installed
- **Network issues**: Check internet connection for package downloads
- **Permission errors**: Ensure write permissions for virtual environment creation
- **Package conflicts**: Use fresh environment (run cleanup first)

### Testing Issues
- **Timeout errors**: Increase timeout values in test script for slower systems
- **Import errors**: Check that virtual environment is properly activated
- **Path issues**: Ensure scripts are run from project root directory

## 📝 Notes

- All scripts should be run from the project root directory
- Scripts are designed to be idempotent (safe to run multiple times)
- Virtual environments are created in `.venv` directory by default
- Cleanup preserves `.git` directory and all source code
- Test scripts provide detailed output for debugging failed installations
