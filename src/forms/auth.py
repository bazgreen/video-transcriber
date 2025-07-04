"""
Authentication forms using Flask-WTF.
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from src.models.auth import User


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField(
        "Username or Email",
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={"placeholder": "Enter username or email"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter password"},
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    """Registration form."""

    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={"placeholder": "Choose a username"},
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Enter your email"},
    )
    display_name = StringField(
        "Display Name (Optional)",
        validators=[Length(max=100)],
        render_kw={"placeholder": "Your display name"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8)],
        render_kw={"placeholder": "Choose a strong password"},
    )
    password2 = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
        render_kw={"placeholder": "Confirm your password"},
    )
    submit = SubmitField("Create Account")

    def validate_username(self, username):
        """Check if username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                "Username already taken. Please choose a different one."
            )

    def validate_email(self, email):
        """Check if email is already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(
                "Email already registered. Please use a different email."
            )


class ProfileForm(FlaskForm):
    """User profile edit form."""

    display_name = StringField(
        "Display Name",
        validators=[Length(max=100)],
        render_kw={"placeholder": "Your display name"},
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "Your email address"},
    )
    submit = SubmitField("Update Profile")

    def __init__(self, original_email, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

    def validate_email(self, email):
        """Check if email is already registered by another user."""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError("Email already registered by another user.")


class PasswordChangeForm(FlaskForm):
    """Password change form."""

    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter current password"},
    )
    new_password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=8)],
        render_kw={"placeholder": "Enter new password"},
    )
    new_password2 = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match"),
        ],
        render_kw={"placeholder": "Confirm new password"},
    )
    submit = SubmitField("Change Password")
