# Video Transcriber Authentication System

This document describes the optional user authentication system for the Video Transcriber application.

## Overview

The authentication system provides:
- **User Registration & Login**: Create accounts and sign in securely
- **Session Management**: Track user sessions and associate files with users
- **File Access Control**: Secure transcript files so only owners can access them
- **Backward Compatibility**: Works alongside anonymous usage
- **Optional Deployment**: Can be enabled/disabled without breaking the application

## Quick Start

### 1. Install Authentication Dependencies

```bash
# Install auth dependencies
python install_auth.py

# Or manually install
pip install -r requirements-auth.txt
```

### 2. Start the Application

```bash
python main.py
```

The application will automatically detect and enable authentication if dependencies are available.

### 3. Create Your First Account

1. Navigate to `http://localhost:5001/auth/register`
2. Create your account with username, email, and password
3. Sign in at `http://localhost:5001/auth/login`

## Features

### User Management
- **Registration**: Create new user accounts
- **Login/Logout**: Secure session management
- **Profile Management**: Update user information and change passwords
- **Remember Me**: Optional persistent login sessions

### File Security
- **Access Control**: Transcript files are associated with user sessions
- **Secure Downloads**: Only file owners can download their transcripts
- **Anonymous Support**: Anonymous users can still use the application
- **Public Sessions**: Option to make sessions publicly viewable

### Session Association
- **User Sessions**: Transcriptions are tied to user accounts when logged in
- **Anonymous Sessions**: Anonymous users can still create transcriptions
- **Migration**: Existing anonymous sessions remain accessible
- **Ownership Transfer**: Anonymous sessions can be claimed by users

## Security Features

### Authentication Security
- **Password Hashing**: bcrypt with salt for secure password storage
- **Session Protection**: Strong session security to prevent fixation attacks
- **CSRF Protection**: Cross-site request forgery protection on all forms
- **Secure Cookies**: HTTP-only and secure cookies in production

### File Access Control
- **Ownership Validation**: Files can only be accessed by their owners
- **IP Logging**: File access attempts are logged for security monitoring
- **Session Validation**: Robust session ownership verification
- **Anonymous Protection**: Anonymous sessions are protected by session ID

## Configuration

### Environment Variables

```bash
# Enable/disable authentication
AUTH_ENABLED=true

# Database configuration
DATABASE_URL=sqlite:///data/video_transcriber.db

# Security settings
SECRET_KEY=your-secret-key-here
WTF_CSRF_ENABLED=true

# File access control
ENABLE_FILE_ACCESS_CONTROL=true
LOG_FILE_ACCESS=true
```

### Application Settings

Key settings in `src/config/settings.py`:

```python
# Authentication
AUTH_ENABLED = True
REGISTRATION_ENABLED = True
REQUIRE_EMAIL_VERIFICATION = False

# Password requirements
MIN_PASSWORD_LENGTH = 8
REQUIRE_PASSWORD_COMPLEXITY = True

# Session settings
SESSION_PROTECTION = "strong"
REMEMBER_COOKIE_DURATION = 30 * 24 * 3600  # 30 days
```

## API Integration

### Route Protection

Routes can be protected using decorators:

```python
from flask_login import login_required
from src.utils.security import require_session_access

@app.route('/protected')
@login_required
def protected_route():
    return "This requires login"

@app.route('/session/<session_id>')
@require_session_access
def session_route(session_id):
    return "This requires session access"
```

### File Access Control

Secure file downloads:

```python
from src.utils.security import SessionAccessControl

# Check if user can access a session
if SessionAccessControl.can_access_session(session_id, user_id):
    # Allow access
    return send_file(file_path)
else:
    # Deny access
    abort(403)
```

## Database Schema

### User Table
- `id`: Primary key
- `username`: Unique username
- `email`: User email address
- `password_hash`: bcrypt hashed password
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp
- `is_active`: Account status

### User Sessions Table
- `id`: Primary key
- `user_id`: Foreign key to users table
- `session_id`: Video transcription session ID
- `created_at`: Session creation timestamp

### Anonymous Sessions Table
- `id`: Primary key
- `session_id`: Session identifier
- `ip_address`: Creator IP address
- `created_at`: Session creation timestamp

## Development

### File Structure

```
src/
├── models/
│   └── auth.py              # Database models
├── routes/
│   └── auth.py              # Authentication routes
├── forms/
│   └── auth.py              # WTForms for user input
├── utils/
│   └── security.py          # Security utilities
├── config/
│   └── settings.py          # Configuration
└── auth_integration.py      # Main integration
```

### Testing

```bash
# Run authentication tests
pytest tests/test_auth.py

# Test specific features
pytest tests/test_auth.py::test_user_registration
pytest tests/test_auth.py::test_file_access_control
```

## Deployment

### Production Considerations

1. **Secret Key**: Set a strong `SECRET_KEY` environment variable
2. **Database**: Consider PostgreSQL for production instead of SQLite
3. **HTTPS**: Enable HTTPS and set `REMEMBER_COOKIE_SECURE=True`
4. **Email Verification**: Enable `REQUIRE_EMAIL_VERIFICATION=True`
5. **CORS**: Configure proper CORS origins for your domain

### Migration from Anonymous Usage

Existing installations can enable authentication without data loss:

1. Install authentication dependencies
2. Start the application (auth enables automatically)
3. Existing anonymous sessions remain accessible
4. Users can register and create new authenticated sessions
5. Both modes coexist seamlessly

## Troubleshooting

### Authentication Not Available

If you see "Authentication not available" in logs:

```bash
# Install dependencies
python install_auth.py

# Or manually
pip install flask-login flask-sqlalchemy flask-wtf bcrypt
```

### Database Issues

```bash
# Remove and recreate database
rm data/video_transcriber.db
python main.py  # Will recreate tables
```

### Import Errors

Ensure all authentication dependencies are installed:

```bash
pip list | grep -E "(Flask-Login|Flask-SQLAlchemy|Flask-WTF|bcrypt)"
```

## Support

For authentication-related issues:

1. Check the application logs for detailed error messages
2. Verify all dependencies are installed correctly
3. Ensure database permissions are correct
4. Check that environment variables are set properly

The authentication system is designed to be robust and fall back gracefully when not available, ensuring the core transcription functionality always works.
