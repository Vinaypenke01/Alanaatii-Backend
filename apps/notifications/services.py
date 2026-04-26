"""
Notifications services — cross-app notification, audit log, secure link helpers.
"""
import logging
from django.utils import timezone
from utils.tokens import generate_secure_token, get_expiry
from django.conf import settings

logger = logging.getLogger('apps')


def create_notification(target_id: str, role: str, ntype: str, title: str, message: str, order_id=None):
    """Create an in-app notification for user/writer/admin."""
    try:
        from .models import Notification
        Notification.objects.create(
            target_id=str(target_id),
            target_role=role,
            order_id=str(order_id) if order_id else None,
            type=ntype,
            title=title,
            message=message,
        )
    except Exception as e:
        logger.error(f'Failed to create notification for {target_id}: {e}')


def log_audit(user_id: str, user_role: str, action_key: str, entity_type: str, entity_id: str, changes: dict = None):
    """Write an audit log entry."""
    try:
        from .models import AuditLog
        AuditLog.objects.create(
            user_id=str(user_id),
            user_role=user_role,
            action_key=action_key,
            entity_type=entity_type,
            entity_id=str(entity_id),
            changes=changes,
        )
    except Exception as e:
        logger.error(f'Failed to write audit log [{action_key}]: {e}')


def generate_secure_link(order_id: str, link_type: str, target_email: str, expiry_hours: int = 72) -> str:
    """
    Generate a one-time secure link for email.
    Returns the full URL string.
    """
    try:
        from .models import SecureLink
        token = generate_secure_token()
        SecureLink.objects.create(
            token=token,
            link_type=link_type,
            order_id=str(order_id),
            target_email=target_email,
            expires_at=get_expiry(expiry_hours),
        )
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        if link_type == 'form_fill':
            return f'{frontend_url}/dashboard/details/{order_id}?token={token}'
        elif link_type == 'script_review':
            return f'{frontend_url}/dashboard/orders/{order_id}?token={token}'
        return f'{frontend_url}?token={token}'
    except Exception as e:
        logger.error(f'Failed to generate secure link for order {order_id}: {e}')
        return ''


def validate_secure_link(token: str) -> 'SecureLink':
    """Validate a secure token from an email link. Returns the SecureLink or raises."""
    from .models import SecureLink
    from rest_framework.exceptions import ValidationError
    from utils.tokens import is_token_expired

    try:
        link = SecureLink.objects.get(token=token)
    except SecureLink.DoesNotExist:
        raise ValidationError('Invalid or expired link.')

    if link.is_used:
        raise ValidationError('This link has already been used.')

    if is_token_expired(link.expires_at):
        raise ValidationError('This link has expired. Please request a new one.')

    return link
