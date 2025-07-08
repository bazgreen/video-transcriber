"""Authentication routes for user login, registration, and profile management."""

import logging
from typing import Optional

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from src.forms.auth import LoginForm, PasswordChangeForm, ProfileForm, RegistrationForm
from src.models.auth import User, db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            # Try to find user by username or email
            user = User.query.filter(
                (User.username == form.username.data)
                | (User.email == form.username.data)
            ).first()

            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                user.update_last_login()

                flash(f"Welcome back, {user.display_name}!", "success")

                # Redirect to next page or home
                next_page = request.args.get("next")
                if next_page and next_page.startswith("/"):
                    return redirect(next_page)
                return redirect(url_for("main.index"))
            else:
                flash("Invalid username/email or password.", "error")
        else:
            # Handle validation errors
            if form.errors:
                # Check for CSRF errors specifically
                if "csrf_token" in form.errors:
                    flash("Security token expired. Please try again.", "error")
                else:
                    # Handle other validation errors
                    for field, errors in form.errors.items():
                        for error in errors:
                            if (
                                field != "csrf_token"
                            ):  # Skip CSRF token field name in display
                                flash(
                                    f"{field.replace('_', ' ').title()}: {error}",
                                    "error",
                                )

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password=form.password.data,
                    display_name=form.display_name.data or form.username.data,
                )
                db.session.add(user)
                db.session.commit()

                flash(
                    f"Account created successfully! Welcome, {user.display_name}!",
                    "success",
                )
                login_user(user)
                return redirect(url_for("main.index"))

            except Exception as e:
                db.session.rollback()
                logger.error(f"Registration error: {e}")
                flash("Registration failed. Please try again.", "error")
        else:
            # Handle validation errors
            if form.errors:
                # Check for CSRF errors specifically
                if "csrf_token" in form.errors:
                    flash("Security token expired. Please try again.", "error")
                else:
                    # Handle other validation errors
                    for field, errors in form.errors.items():
                        for error in errors:
                            if (
                                field != "csrf_token"
                            ):  # Skip CSRF token field name in display
                                flash(
                                    f"{field.replace('_', ' ').title()}: {error}",
                                    "error",
                                )

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout."""
    username = current_user.username
    logout_user()
    flash(f"You have been logged out. Goodbye, {username}!", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile page."""
    profile_form = ProfileForm(
        original_email=current_user.email,
        display_name=current_user.display_name,
        email=current_user.email,
    )
    password_form = PasswordChangeForm()

    if request.method == "POST":
        if "update_profile" in request.form and profile_form.validate():
            try:
                current_user.display_name = profile_form.display_name.data
                current_user.email = profile_form.email.data
                db.session.commit()
                flash("Profile updated successfully!", "success")
                return redirect(url_for("auth.profile"))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Profile update error: {e}")
                flash("Profile update failed. Please try again.", "error")

        elif "change_password" in request.form and password_form.validate():
            if current_user.check_password(password_form.current_password.data):
                try:
                    current_user.set_password(password_form.new_password.data)
                    db.session.commit()
                    flash("Password changed successfully!", "success")
                    return redirect(url_for("auth.profile"))
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Password change error: {e}")
                    flash("Password change failed. Please try again.", "error")
            else:
                flash("Current password is incorrect.", "error")

    # Get user statistics
    session_count = current_user.get_session_count()

    return render_template(
        "auth/profile.html",
        profile_form=profile_form,
        password_form=password_form,
        session_count=session_count,
    )


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password page."""
    form = PasswordChangeForm()
    if request.method == "POST":
        if form.validate_on_submit():
            if current_user.check_password(form.current_password.data):
                try:
                    current_user.set_password(form.new_password.data)
                    db.session.commit()
                    flash("Password changed successfully!", "success")
                    return redirect(url_for("auth.profile"))
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Password change error: {e}")
                    flash("Password change failed. Please try again.", "error")
            else:
                flash("Current password is incorrect.", "error")
        else:
            # Handle validation errors
            if form.errors:
                # Check for CSRF errors specifically
                if "csrf_token" in form.errors:
                    flash("Security token expired. Please try again.", "error")
                else:
                    # Handle other validation errors
                    for field, errors in form.errors.items():
                        for error in errors:
                            if (
                                field != "csrf_token"
                            ):  # Skip CSRF token field name in display
                                flash(
                                    f"{field.replace('_', ' ').title()}: {error}",
                                    "error",
                                )

    return render_template("auth/change_password.html", form=form)


def get_current_user_id() -> Optional[int]:
    """Get current user ID, returns None for anonymous users."""
    if current_user.is_authenticated:
        return current_user.id
    return None


def is_session_accessible(session_id: str, user_id: Optional[int] = None) -> bool:
    """
    Check if a session is accessible by the current user.

    Args:
        session_id: Session identifier
        user_id: User ID (None for current user)

    Returns:
        True if session is accessible, False otherwise
    """
    from src.models.auth import AnonymousSession, UserSession

    if user_id is None:
        user_id = get_current_user_id()

    # Check if it's a user session
    user_session = UserSession.find_by_session_id(session_id)
    if user_session:
        # User owns the session
        if user_id and user_session.user_id == user_id:
            return True
        # Session is public
        if user_session.is_public:
            return True
        return False

    # Check if it's an anonymous session (accessible by everyone for backward compatibility)
    anonymous_session = AnonymousSession.find_by_session_id(session_id)
    if anonymous_session:
        return True

    # Not found in either, might be a new anonymous session
    return True  # Allow access for new sessions


def associate_session_with_user(
    session_id: str, session_name: str = None, user_id: Optional[int] = None
) -> None:
    """
    Associate a session with the current user.

    Args:
        session_id: Session identifier
        session_name: Optional session name
        user_id: User ID (None for current user)
    """
    from src.models.auth import UserSession

    if user_id is None:
        user_id = get_current_user_id()

    if user_id:
        # Check if already associated
        existing = UserSession.find_by_session_id(session_id)
        if not existing:
            user_session = UserSession(
                user_id=user_id, session_id=session_id, session_name=session_name
            )
            db.session.add(user_session)
            try:
                db.session.commit()
                logger.info(f"Associated session {session_id} with user {user_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(
                    f"Failed to associate session {session_id} with user {user_id}: {e}"
                )
    else:
        # Anonymous user - create anonymous session record
        from src.models.auth import AnonymousSession

        existing = AnonymousSession.find_by_session_id(session_id)
        if not existing:
            anonymous_session = AnonymousSession(
                session_id=session_id,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get("User-Agent") if request else None,
            )
            db.session.add(anonymous_session)
            try:
                db.session.commit()
                logger.info(f"Created anonymous session record for {session_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(
                    f"Failed to create anonymous session record for {session_id}: {e}"
                )
