"""
Accounts serializers — User, Writer, Admin registration/login/profile.
JWT tokens include a 'role' field in the payload for portal discrimination.
"""
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, Writer, Admin, UserAddress



def get_tokens_for_user(user_obj, role: str) -> dict:
    """
    Generate JWT tokens for any of the three user types.

    - For `User` (AUTH_USER_MODEL): uses RefreshToken.for_user() so the token
      is tracked in OutstandingToken and blacklisting on logout works fully.
    - For `Writer` / `Admin`: creates a raw RefreshToken without calling
      for_user(), because OutstandingToken has a hard FK to AUTH_USER_MODEL.
      These tokens are still valid JWTs — they just aren't stored in DB.
    """
    from apps.accounts.models import User as CustomerUser

    if isinstance(user_obj, CustomerUser):
        token = RefreshToken.for_user(user_obj)
    else:
        # Manually build token — avoids OutstandingToken FK constraint
        token = RefreshToken()
        token[jwt_settings.USER_ID_CLAIM] = str(user_obj.id)

    # Inject shared claims used by permission layer
    token['role'] = role
    token['full_name'] = user_obj.full_name
    token['email'] = user_obj.email

    return {
        'refresh': str(token),
        'access': str(token.access_token),
    }



# ─── Google OAuth ─────────────────────────────────────────────────────────────

class GoogleLoginSerializer(serializers.Serializer):
    """
    Accepts a Google `id_token` from the frontend (obtained via Google Sign-In).
    Verifies it against Google's public keys, then either:
      - Logs in the existing user, or
      - Auto-creates a new account (no password set — can never log in with password).
    Returns the same JWT token structure as a normal login.
    """
    id_token = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.conf import settings
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        raw_token = data.get('id_token')
        client_id = settings.GOOGLE_CLIENT_ID

        try:
            id_info = google_id_token.verify_oauth2_token(
                raw_token,
                google_requests.Request(),
                client_id,
            )
        except ValueError as e:
            raise serializers.ValidationError(f'Invalid Google token: {str(e)}')

        # Google guarantees these are present when verification passes
        google_sub = id_info['sub']          # Unique stable Google user ID
        email      = id_info['email'].lower()
        full_name  = id_info.get('name', email.split('@')[0])

        # Look up by google_id first (fastest, handles email changes)
        user = User.objects.filter(google_id=google_sub).first()

        if user is None:
            # Fall back to email match — user might have registered with password before
            user = User.objects.filter(email=email).first()
            if user:
                # Link the Google account to the existing email account
                user.google_id = google_sub
                user.auth_provider = 'google'
                user.save(update_fields=['google_id', 'auth_provider'])
            else:
                # Brand new user — create account silently, no password needed
                user = User.objects.create(
                    email=email,
                    full_name=full_name,
                    google_id=google_sub,
                    auth_provider='google',
                )
                user.set_unusable_password()
                user.save()

        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')

        data['user'] = user
        data['is_new'] = user.created_at is not None and (
            (timezone.now() - user.created_at).total_seconds() < 10
        )
        return data


# ─── User (Customer) ──────────────────────────────────────────────────────────

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_wa', 'password', 'password_confirm']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An account with this email already exists.')
        return value.lower()

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        data.pop('password_confirm')
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('Your account has been deactivated.')
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone_wa',
            'address_def', 'city_def', 'pincode_def',
            'birthday', 'anniversary', 'auth_provider', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'auth_provider', 'created_at']


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ['id', 'label', 'receiver_name', 'phone', 'address', 'city', 'pincode', 'is_primary']
        read_only_fields = ['id']


# ─── Writer ───────────────────────────────────────────────────────────────────

class WriterLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password')
        try:
            writer = Writer.objects.get(email=email)
        except Writer.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')
        if not writer.check_password(password):
            raise serializers.ValidationError('Invalid email or password.')
        if not writer.is_active:
            raise serializers.ValidationError('Your writer account is inactive. Contact admin.')
        if writer.status == 'inactive':
            raise serializers.ValidationError('Your account is currently marked as inactive.')
        data['writer'] = writer
        return data


class WriterSerializer(serializers.ModelSerializer):
    active_job_count = serializers.ReadOnlyField()
    assigned_count = serializers.SerializerMethodField()
    pending_response_count = serializers.SerializerMethodField()
    active_scripts_count = serializers.SerializerMethodField()
    rejected_count = serializers.SerializerMethodField()
    approved_count = serializers.SerializerMethodField()

    class Meta:
        model = Writer
        fields = [
            'id', 'full_name', 'email', 'phone', 'phone_alt',
            'address', 'languages', 'status', 'active_job_count', 
            'assigned_count', 'pending_response_count', 'active_scripts_count', 
            'rejected_count', 'approved_count', 'delayed_submissions_count',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'active_job_count']

    def get_assigned_count(self, obj):
        """Total number of assignments ever given."""
        return obj.assignments.count()

    def get_pending_response_count(self, obj):
        """Assignments waiting for writer to accept/decline."""
        return obj.assignments.filter(status='pending').count()

    def get_active_scripts_count(self, obj):
        """Accepted assignments that are still in progress (not yet approved/delivered)."""
        from apps.orders.models import OrderStatus
        return obj.assignments.filter(
            status='accepted'
        ).exclude(
            order__status__in=[
                OrderStatus.APPROVED,
                OrderStatus.UNDER_WRITING,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED,
                OrderStatus.REFUNDED
            ]
        ).count()

    def get_rejected_count(self, obj):
        """Assignments declined by the writer."""
        return obj.assignments.filter(status='declined').count()

    def get_approved_count(self, obj):
        """Assignments where the script has been approved or beyond."""
        from apps.orders.models import Order, OrderStatus
        return Order.objects.filter(writer=obj, status__in=[
            OrderStatus.APPROVED,
            OrderStatus.UNDER_WRITING,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED
        ]).count()


class WriterCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Writer
        fields = ['full_name', 'email', 'phone', 'phone_alt', 'address', 'languages', 'password']

    def validate_email(self, value):
        if Writer.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A writer with this email already exists.')
        return value.lower()

    def create(self, validated_data):
        admin = self.context.get('admin')
        password = validated_data.pop('password')
        writer = Writer(**validated_data)
        writer.set_password(password)
        if admin:
            writer.created_by = admin
        writer.save()
        return writer


class WriterUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = Writer
        fields = ['full_name', 'phone', 'phone_alt', 'address', 'languages', 'status', 'password']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class WriterProfileSerializer(serializers.ModelSerializer):
    active_job_count = serializers.ReadOnlyField()
    assigned_count = serializers.SerializerMethodField()
    pending_response_count = serializers.SerializerMethodField()
    active_scripts_count = serializers.SerializerMethodField()
    rejected_count = serializers.SerializerMethodField()
    approved_count = serializers.SerializerMethodField()

    class Meta:
        model = Writer
        fields = [
            'id', 'full_name', 'email', 'phone', 'phone_alt', 
            'address', 'languages', 'status', 'active_job_count',
            'assigned_count', 'pending_response_count', 'active_scripts_count', 
            'rejected_count', 'approved_count', 'delayed_submissions_count'
        ]
        read_only_fields = ['id', 'email']

    def get_assigned_count(self, obj):
        return obj.assignments.count()

    def get_pending_response_count(self, obj):
        return obj.assignments.filter(status='pending').count()

    def get_active_scripts_count(self, obj):
        from apps.orders.models import OrderStatus
        return obj.assignments.filter(
            status='accepted'
        ).exclude(
            order__status__in=[
                OrderStatus.APPROVED,
                OrderStatus.UNDER_WRITING,
                OrderStatus.OUT_FOR_DELIVERY,
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED,
                OrderStatus.REFUNDED
            ]
        ).count()

    def get_rejected_count(self, obj):
        return obj.assignments.filter(status='declined').count()

    def get_approved_count(self, obj):
        from apps.orders.models import Order, OrderStatus
        return Order.objects.filter(writer=obj, status__in=[
            OrderStatus.APPROVED,
            OrderStatus.UNDER_WRITING,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED
        ]).count()


# ─── Admin ────────────────────────────────────────────────────────────────────

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').lower()
        password = data.get('password')
        try:
            admin = Admin.objects.get(email=email)
        except Admin.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')
        if not admin.check_password(password):
            raise serializers.ValidationError('Invalid email or password.')
        if not admin.is_active:
            raise serializers.ValidationError('Your admin account has been deactivated.')
        data['admin'] = admin
        return data


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['id', 'full_name', 'email', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class AdminCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Admin
        fields = ['full_name', 'email', 'role', 'password']

    def validate_email(self, value):
        if Admin.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('An admin with this email already exists.')
        return value.lower()

    def create(self, validated_data):
        password = validated_data.pop('password')
        admin = Admin(**validated_data)
        admin.set_password(password)
        admin.save()
        return admin
