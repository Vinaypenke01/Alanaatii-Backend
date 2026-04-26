"""
Accounts serializers — User, Writer, Admin registration/login/profile.
JWT tokens include a 'role' field in the payload for portal discrimination.
"""
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from django.contrib.auth import authenticate
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
            'birthday', 'anniversary', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'created_at']


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

    class Meta:
        model = Writer
        fields = [
            'id', 'full_name', 'email', 'phone', 'phone_alt',
            'address', 'languages', 'status', 'active_job_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'active_job_count']


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

    class Meta:
        model = Writer
        fields = ['id', 'full_name', 'email', 'phone', 'phone_alt', 'address', 'languages', 'status', 'active_job_count']
        read_only_fields = ['id', 'email']


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
