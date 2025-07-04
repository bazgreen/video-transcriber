#!/usr/bin/env python3
"""
Authentication dependency installer for Video Transcriber.

This script installs the required dependencies for the authentication system.
Run this after setting up the base application to enable user authentication.
"""

import logging
import subprocess
import sys
from pathlib import Path


def setup_logging():
    """Configure logging for the installer."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return Path(file_path).exists()


def install_auth_dependencies(logger):
    """Install authentication dependencies."""
    requirements_file = "requirements-auth.txt"

    if not check_file_exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return False

    try:
        logger.info("Installing authentication dependencies...")
        logger.info(f"Using requirements file: {requirements_file}")

        # Install dependencies
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            capture_output=True,
            text=True,
            check=True,
        )

        logger.info("Authentication dependencies installed successfully!")
        logger.info("Output:")
        for line in result.stdout.split("\n"):
            if line.strip():
                logger.info(f"  {line}")

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def create_data_directory(logger):
    """Create data directory for authentication database."""
    data_dir = Path("data")
    if not data_dir.exists():
        logger.info("Creating data directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Data directory created")
    else:
        logger.info("Data directory already exists")


def check_auth_status(logger):
    """Check if authentication system is working."""
    try:
        # Try importing auth dependencies
        import bcrypt
        import flask_login
        import flask_sqlalchemy
        import flask_wtf

        logger.info("✅ Authentication dependencies are available:")
        logger.info(f"  Flask-Login: {getattr(flask_login, '__version__', 'unknown')}")
        logger.info(
            f"  Flask-SQLAlchemy: {getattr(flask_sqlalchemy, '__version__', 'unknown')}"
        )
        logger.info(f"  Flask-WTF: {getattr(flask_wtf, '__version__', 'unknown')}")
        logger.info(f"  bcrypt: {getattr(bcrypt, '__version__', 'unknown')}")

        # Try importing our auth modules
        from src.models.auth import User
        from src.routes.auth import auth_bp
        from src.utils.security import SessionAccessControl

        logger.info("✅ Authentication modules are importable")
        return True

    except ImportError as e:
        logger.error(f"❌ Authentication not available: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking auth status: {e}")
        return False


def main():
    """Main installation function."""
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("Video Transcriber Authentication Setup")
    logger.info("=" * 60)

    # Create necessary directories
    create_data_directory(logger)

    # Install dependencies
    if not install_auth_dependencies(logger):
        logger.error("Failed to install authentication dependencies")
        sys.exit(1)

    # Check if everything is working
    logger.info("\nChecking authentication system status...")
    if check_auth_status(logger):
        logger.info("\n✅ Authentication system is ready!")
        logger.info("\nNext steps:")
        logger.info("1. Start the application with: python main.py")
        logger.info(
            "2. Navigate to http://localhost:5001/auth/register to create an account"
        )
        logger.info("3. Sign in at http://localhost:5001/auth/login")
        logger.info("\nFeatures enabled:")
        logger.info("- User registration and login")
        logger.info("- Session-based file access control")
        logger.info("- Secure transcript file downloads")
        logger.info("- User profile management")
    else:
        logger.error("\n❌ Authentication system setup failed")
        logger.error("Please check the error messages above and try again")
        sys.exit(1)


if __name__ == "__main__":
    main()
