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


def request_otp(email: str, role: str, purpose: str) -> None:
    """Generate and send OTP to user based on role."""
    from .models import Admin, Writer, OTPVerification
    from utils.email import send_otp_email
    from rest_framework.exceptions import NotFound

    if role == 'admin':
        model = Admin
    elif role == 'writer':
        model = Writer
    elif role == 'user':
        model = User
    else:
        raise ValueError('Invalid role for OTP request.')

    try:
        user_obj = model.objects.get(email=email)
    except model.DoesNotExist:
        if purpose != 'create_writer':
            raise NotFound(f'No {role} account found with this email.')

    otp_obj = OTPVerification.generate_code(email, purpose)
    send_otp_email(email, otp_obj.code, purpose, role)
    logger.info(f'OTP sent to {role} {email} for {purpose}')


def verify_otp(email: str, code: str, purpose: str) -> bool:
    """Verify OTP and return True if valid."""
    from .models import OTPVerification
    from rest_framework.exceptions import ValidationError

    try:
        otp_obj = OTPVerification.objects.get(email=email, code=code, purpose=purpose)
    except OTPVerification.DoesNotExist:
        raise ValidationError('Invalid verification code.')

    if otp_obj.is_expired():
        raise ValidationError('Verification code has expired.')

    if otp_obj.is_verified:
        raise ValidationError('This code has already been used.')

    return True


def reset_password_with_otp(email: str, role: str, code: str, new_password: str) -> None:
    """Reset user password after OTP verification."""
    from .models import Admin, Writer, OTPVerification
    
    verify_otp(email, code, 'reset_password')
    
    otp_obj = OTPVerification.objects.get(email=email, code=code, purpose='reset_password')
    
    if role == 'admin':
        user_obj = Admin.objects.get(email=email)
    elif role == 'writer':
        user_obj = Writer.objects.get(email=email)
    else:
        user_obj = User.objects.get(email=email)

    user_obj.set_password(new_password)
    user_obj.save()

    otp_obj.is_verified = True
    otp_obj.save()
    logger.info(f'{role.capitalize()} {email} reset password successfully')


def update_password_with_otp(user_id: str, role: str, code: str, new_password: str) -> None:
    """Update user password from profile after OTP verification."""
    from .models import Admin, Writer, OTPVerification

    if role == 'admin':
        user_obj = Admin.objects.get(id=user_id)
    elif role == 'writer':
        user_obj = Writer.objects.get(id=user_id)
    else:
        user_obj = User.objects.get(id=user_id)

    verify_otp(user_obj.email, code, 'update_password')
    
    otp_obj = OTPVerification.objects.get(email=user_obj.email, code=code, purpose='update_password')
    user_obj.set_password(new_password)
    user_obj.save()

    otp_obj.is_verified = True
    otp_obj.save()
    logger.info(f'{role.capitalize()} {user_obj.email} updated password successfully via profile')
