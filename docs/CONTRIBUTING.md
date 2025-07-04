# Contributing to Video Transcriber

Thank you for your interest in contributing to the Video Transcriber project! This guide will help you get started with development and contributions.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- FFmpeg installed on your system
- Git for version control

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/bazgreen/video-transcriber.git
   cd video-transcriber
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Start development server**
   ```bash
   python main.py
   ```

## 📁 Project Structure

```
video-transcriber/
├── src/                    # Main application code
│   ├── config/            # Configuration management
│   ├── models/            # Data models and managers
│   ├── routes/            # Flask routes and handlers
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── benchmarks/       # Performance tests
├── scripts/              # Development and maintenance scripts
├── docs/                 # Documentation
└── data/                 # Templates and static data
```

## 🔧 Development Guidelines

### Code Style
- Follow PEP 8 standards
- Use type hints for all functions
- Maximum line length: 88 characters (Black default)
- Use descriptive variable and function names

### Testing
- Write tests for all new features
- Maintain or improve test coverage
- Run the full test suite before submitting PRs
- Include both unit and integration tests

### Documentation
- Update README.md for user-facing changes
- Add docstrings to all public functions
- Update API documentation for endpoint changes
- Include examples in documentation

## 🔄 Development Workflow

### 1. Issue Creation
- Check existing issues before creating new ones
- Use issue templates when available
- Provide clear descriptions and acceptance criteria
- Add appropriate labels and milestones

### 2. Branch Strategy
- Create feature branches from `main`
- Use descriptive branch names: `feature/video-player`, `fix/memory-leak`
- Keep branches focused on single features or fixes

### 3. Code Changes
- Make atomic commits with clear messages
- Follow conventional commit format when possible
- Keep commits focused and logical
- Test changes thoroughly

### 4. Pull Request Process
- Fill out the PR template completely
- Reference related issues
- Include screenshots for UI changes
- Ensure all checks pass

## 📋 Coding Standards

### Python Code
```python
# Good example
def process_video_file(
    file_path: str, 
    session_name: str = "", 
    options: Optional[Dict[str, Any]] = None
) -> VideoProcessingResult:
    """
    Process a video file for transcription.
    
    Args:
        file_path: Path to the video file
        session_name: Optional name for the processing session
        options: Additional processing options
        
    Returns:
        Processing result with transcript and analysis
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        ProcessingError: If transcription fails
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")
    
    # Implementation here
    return result
```

### Error Handling
- Use custom exceptions for domain-specific errors
- Provide helpful error messages
- Log errors appropriately
- Handle edge cases gracefully

### Performance Considerations
- Use appropriate data structures
- Avoid premature optimization
- Profile performance-critical code
- Consider memory usage for large files

## 🧪 Testing Guidelines

### Test Structure
```python
import pytest
from src.services.transcription import VideoTranscriber

class TestVideoTranscriber:
    """Test suite for VideoTranscriber service."""
    
    def test_video_processing_success(self, mock_video_file):
        """Test successful video processing."""
        # Arrange
        transcriber = VideoTranscriber()
        
        # Act
        result = transcriber.process_video(mock_video_file)
        
        # Assert
        assert result.success is True
        assert len(result.segments) > 0
```

### Test Categories
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Benchmark critical operations

## 📝 Documentation Standards

### Code Documentation
- Write clear docstrings for all public APIs
- Include parameter types and descriptions
- Document return values and exceptions
- Provide usage examples

### API Documentation
- Document all endpoints with examples
- Include request/response schemas
- Document error responses
- Provide authentication details

## 🏷️ Issue and PR Labels

### Priority Labels
- `high-priority`: Critical issues requiring immediate attention
- `medium-priority`: Important issues for next release
- `low-priority`: Nice-to-have improvements

### Type Labels
- `bug`: Something isn't working correctly
- `enhancement`: New feature requests
- `documentation`: Documentation improvements
- `performance`: Performance-related changes

### Component Labels
- `video`: Video processing features
- `ui/ux`: User interface improvements
- `api`: Backend API changes
- `testing`: Test-related changes

## 🔒 Security Guidelines

### Code Security
- Validate all user inputs
- Use parameterized queries
- Avoid hardcoded secrets
- Follow OWASP guidelines

### File Handling
- Validate file types and sizes
- Use secure temporary directories
- Clean up temporary files
- Prevent path traversal attacks

## 🚀 Release Process

### Version Numbering
- Follow semantic versioning (SemVer)
- Major.Minor.Patch format
- Tag releases in Git

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Security scan passed

## 🤝 Community

### Communication
- Use GitHub Issues for bug reports and feature requests
- Join discussions for architecture decisions
- Be respectful and constructive in feedback

### Getting Help
- Check existing documentation first
- Search issues for similar problems
- Provide detailed information when asking for help
- Include steps to reproduce issues

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Whisper Documentation](https://github.com/openai/whisper)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

Thank you for contributing to Video Transcriber! 🎉
