"""
User authentication models and database setup.

This module provides user authentication functionality while maintaining
backward compatibility with anonymous usage.
"""

import os
from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    sessions = db.relationship("UserSession", back_populates="user", lazy="dynamic")

    def __init__(
        self, username: str, email: str, password: str, display_name: str = None
    ):
        """Initialize user with hashed password."""
        self.username = username
        self.email = email
        self.set_password(password)
        self.display_name = display_name or username

    def set_password(self, password: str) -> None:
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def get_session_count(self) -> int:
        """Get number of sessions owned by this user."""
        return self.sessions.count()

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class UserSession(db.Model):
    """Association between users and transcription sessions."""

    __tablename__ = "user_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    session_id = db.Column(db.String(255), nullable=False, index=True)
    session_name = db.Column(db.String(255), nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    shared_token = db.Column(db.String(64), nullable=True, unique=True, index=True)

    # Relationships
    user = db.relationship("User", back_populates="sessions")

    def __init__(
        self,
        user_id: int,
        session_id: str,
        session_name: str = None,
        is_public: bool = False,
    ):
        """Initialize user session association."""
        self.user_id = user_id
        self.session_id = session_id
        self.session_name = session_name
        self.is_public = is_public

    def generate_share_token(self) -> str:
        """Generate secure sharing token."""
        import secrets

        self.shared_token = secrets.token_urlsafe(32)
        db.session.commit()
        return self.shared_token

    def revoke_share_token(self) -> None:
        """Revoke sharing token."""
        self.shared_token = None
        db.session.commit()

    @staticmethod
    def find_by_session_id(session_id: str) -> Optional["UserSession"]:
        """Find user session by session ID."""
        return UserSession.query.filter_by(session_id=session_id).first()

    @staticmethod
    def find_by_share_token(token: str) -> Optional["UserSession"]:
        """Find user session by share token."""
        return UserSession.query.filter_by(shared_token=token).first()

    def __repr__(self) -> str:
        return f"<UserSession {self.session_id} -> User {self.user_id}>"


class AnonymousSession(db.Model):
    """Track anonymous sessions for backward compatibility."""

    __tablename__ = "anonymous_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.Text, nullable=True)

    def __init__(self, session_id: str, ip_address: str = None, user_agent: str = None):
        """Initialize anonymous session."""
        self.session_id = session_id
        self.ip_address = ip_address
        self.user_agent = user_agent

    @staticmethod
    def find_by_session_id(session_id: str) -> Optional["AnonymousSession"]:
        """Find anonymous session by session ID."""
        return AnonymousSession.query.filter_by(session_id=session_id).first()

    def __repr__(self) -> str:
        return f"<AnonymousSession {self.session_id}>"


def init_auth_db(app):
    """Initialize authentication database."""
    db.init_app(app)

    with app.app_context():
        # Create tables
        db.create_all()

        # Check if we need to migrate existing sessions
        _migrate_existing_sessions_if_needed(app)


def _migrate_existing_sessions_if_needed(app):
    """Migrate existing file-based sessions to anonymous sessions."""
    from src.config import AppConfig

    config = AppConfig()
    results_folder = config.RESULTS_FOLDER

    if not os.path.exists(results_folder):
        return

    # Check if migration already done
    migration_marker = os.path.join(results_folder, ".auth_migration_done")
    if os.path.exists(migration_marker):
        return

    # Count existing sessions
    existing_sessions = []
    for item in os.listdir(results_folder):
        session_path = os.path.join(results_folder, item)
        if os.path.isdir(session_path) and not item.startswith("."):
            existing_sessions.append(item)

    if existing_sessions:
        app.logger.info(
            f"Migrating {len(existing_sessions)} existing sessions to anonymous sessions"
        )

        for session_id in existing_sessions:
            # Check if already migrated
            if not AnonymousSession.find_by_session_id(session_id):
                anonymous_session = AnonymousSession(
                    session_id=session_id,
                    ip_address="migrated",
                    user_agent="legacy_migration",
                )
                db.session.add(anonymous_session)

        try:
            db.session.commit()
            # Create migration marker
            with open(migration_marker, "w") as f:
                f.write(f"Migration completed at {datetime.utcnow().isoformat()}")
            app.logger.info("Session migration completed successfully")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Session migration failed: {e}")
    else:
        # No existing sessions, just create marker
        with open(migration_marker, "w") as f:
            f.write(f"No migration needed at {datetime.utcnow().isoformat()}")
