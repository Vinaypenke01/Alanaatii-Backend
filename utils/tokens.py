"""
Secure token generation for form-fill and script-review email links.
"""
import secrets
import string
from datetime import timedelta
from django.utils import timezone


def generate_secure_token(length: int = 48) -> str:
    """Generate a URL-safe cryptographically secure random token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_expiry(hours: int = 72):
    """Return a UTC datetime `hours` from now."""
    return timezone.now() + timedelta(hours=hours)


def is_token_expired(expires_at) -> bool:
    """Check if a token's expiry time has passed."""
    return timezone.now() > expires_at
