"""
Accounts services — business logic for auth and user management.
Views should call services, not contain logic directly.
"""
import logging
from .models import User, Writer, Admin, UserAddress
from .serializers import get_tokens_for_user

logger = logging.getLogger('apps')


def register_user(data: dict) -> dict:
    """Create a new customer account and return JWT tokens."""
    from .serializers import UserRegisterSerializer
    serializer = UserRegisterSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    tokens = get_tokens_for_user(user, role='user')
    logger.info(f'New user registered: {user.email}')
    return {'user': user, 'tokens': tokens}


def login_user(email: str, password: str) -> dict:
    """Authenticate customer, return JWT tokens."""
    from .serializers import UserLoginSerializer
    serializer = UserLoginSerializer(data={'email': email, 'password': password})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    tokens = get_tokens_for_user(user, role='user')
    return {'user': user, 'tokens': tokens}


def login_writer(email: str, password: str) -> dict:
    """Authenticate writer, return JWT tokens."""
    from .serializers import WriterLoginSerializer
    serializer = WriterLoginSerializer(data={'email': email, 'password': password})
    serializer.is_valid(raise_exception=True)
    writer = serializer.validated_data['writer']
    tokens = get_tokens_for_user(writer, role='writer')
    return {'writer': writer, 'tokens': tokens}


def login_admin(email: str, password: str) -> dict:
    """Authenticate admin, return JWT tokens."""
    from .serializers import AdminLoginSerializer
    serializer = AdminLoginSerializer(data={'email': email, 'password': password})
    serializer.is_valid(raise_exception=True)
    admin = serializer.validated_data['admin']
    tokens = get_tokens_for_user(admin, role='admin')
    return {'admin': admin, 'tokens': tokens}


def get_writer_by_id(writer_id: str) -> Writer:
    """Fetch writer or raise 404-style error."""
    from rest_framework.exceptions import NotFound
    try:
        return Writer.objects.get(id=writer_id)
    except Writer.DoesNotExist:
        raise NotFound('Writer not found.')


def check_writer_has_active_jobs(writer_id: str) -> bool:
    """Return True if writer has active (accepted) assignments."""
    from apps.writers.models import WriterAssignment
    return WriterAssignment.objects.filter(
        writer_id=writer_id, status='accepted'
    ).exists()


def delete_writer(writer_id: str, admin) -> None:
    """
    Delete writer. Blocks deletion if writer has active jobs.
    Sets to inactive instead.
    """
    from rest_framework.exceptions import ValidationError
    writer = get_writer_by_id(writer_id)
    if check_writer_has_active_jobs(writer_id):
        raise ValidationError(
            'Cannot delete writer with active jobs. Set them to inactive first.'
        )
    logger.warning(f'Admin {admin.email} deleted writer {writer.email}')
    writer.delete()
