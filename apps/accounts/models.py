"""
Accounts app — User, Writer, Admin models.
Uses three separate AbstractBaseUser subclasses for clean separation.
JWT tokens carry a 'role' claim to distinguish between portals.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random


class OTPVerification(models.Model):
    PURPOSE_CHOICES = [
        ('reset_password', 'Reset Password'),
        ('update_password', 'Update Password'),
    ]
    email = models.EmailField()
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'otp_verifications'
        ordering = ['-created_at']

    def is_expired(self):
        # 10 minutes expiry
        return (timezone.now() - self.created_at).total_seconds() > 600

    @classmethod
    def generate_code(cls, email, purpose):
        code = str(random.randint(100000, 999999))
        return cls.objects.create(email=email, code=code, purpose=purpose)

    def __str__(self):
        return f'{self.email} – {self.purpose} ({self.code})'


# ─── Managers ─────────────────────────────────────────────────────────────────

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class WriterManager(BaseUserManager):
    def create_writer(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        writer = self.model(email=email, **extra_fields)
        writer.set_password(password)
        writer.save(using=self._db)
        return writer


class AdminManager(BaseUserManager):
    def create_admin(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        admin = self.model(email=email, **extra_fields)
        admin.set_password(password)
        admin.save(using=self._db)
        return admin


# ─── User (Customer) ──────────────────────────────────────────────────────────

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    phone_wa = models.CharField(max_length=20, blank=True, default='', help_text='WhatsApp number for alerts')

    # OAuth fields
    auth_provider = models.CharField(max_length=20, default='password', help_text='password | google')
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)

    # Optional profile fields
    address_def = models.TextField(blank=True, null=True, help_text='Default shipping address')
    city_def = models.CharField(max_length=50, blank=True, null=True)
    pincode_def = models.CharField(max_length=6, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    anniversary = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    # Fix reverse accessor clashes when multiple models use PermissionsMixin
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='customer_users',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='customer_users',
        verbose_name='user permissions',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_wa']

    class Meta:
        db_table = 'users'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.email})'


class UserAddress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, default='Home', help_text='e.g. Home, Office, Partner')
    receiver_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_addresses'
        verbose_name = 'User Address'
        verbose_name_plural = 'User Addresses'

    def save(self, *args, **kwargs):
        # Ensure only one primary address per user
        if self.is_primary:
            UserAddress.objects.filter(user=self.user, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.full_name} – {self.label}'


# ─── Writer ───────────────────────────────────────────────────────────────────

class WriterStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'


class Writer(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    phone_alt = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    languages = models.JSONField(default=list, help_text='Array of language skills e.g. ["Telugu","English"]')
    status = models.CharField(max_length=10, choices=WriterStatus.choices, default=WriterStatus.ACTIVE)
    created_by = models.ForeignKey(
        'Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_writers'
    )
    created_at = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)

    objects = WriterManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'writers'
        verbose_name = 'Writer'
        verbose_name_plural = 'Writers'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    @property
    def active_job_count(self):
        """Number of currently active assignments."""
        return self.assignments.filter(status='accepted').count()


# ─── Admin ────────────────────────────────────────────────────────────────────

class AdminRole(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    MANAGER = 'manager', 'Manager'
    MODERATOR = 'moderator', 'Moderator'


class Admin(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    role = models.CharField(max_length=20, choices=AdminRole.choices, default=AdminRole.MANAGER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    # Fix reverse accessor clashes when multiple models use PermissionsMixin
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='admin_users',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='admin_users',
        verbose_name='user permissions',
    )

    objects = AdminManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'admins'
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'

    def __str__(self):
        return f'{self.full_name} ({self.role})'
