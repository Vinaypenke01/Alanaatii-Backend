"""
Notifications, Audit Logs, Assets, SecureLinks models.
"""
import uuid
from django.db import models
from django.utils import timezone


class NotificationTargetRole(models.TextChoices):
    USER = 'user', 'Customer'
    WRITER = 'writer', 'Writer'
    ADMIN = 'admin', 'Admin'


class NotificationType(models.TextChoices):
    PAYMENT = 'payment', 'Payment'
    SCRIPT = 'script', 'Script'
    REVISION = 'revision', 'Revision'
    ASSIGNMENT = 'assignment', 'Assignment'
    PAYOUT = 'payout', 'Payout'
    DELIVERY = 'delivery', 'Delivery'
    SYSTEM = 'system', 'System'


class Notification(models.Model):
    target_id = models.CharField(max_length=36, db_index=True, help_text='ID of the user/writer/admin')
    target_role = models.CharField(max_length=10, choices=NotificationTargetRole.choices)
    order_id = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    type = models.CharField(max_length=15, choices=NotificationType.choices)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target_id', 'target_role', 'is_read']),
        ]

    def __str__(self):
        return f'[{self.target_role}:{self.target_id}] {self.title}'


class AuditLog(models.Model):
    user_id = models.CharField(max_length=36, help_text='Admin or Writer UUID')
    user_role = models.CharField(max_length=10, choices=NotificationTargetRole.choices, default='admin')
    action_key = models.CharField(max_length=50, help_text='e.g. PAYMENT_VERIFIED')
    entity_type = models.CharField(max_length=30, help_text='e.g. ORDER, WRITER, PRICING')
    entity_id = models.CharField(max_length=36)
    changes = models.JSONField(null=True, blank=True, help_text='Before/After snapshot')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['user_id']),
        ]

    def __str__(self):
        return f'[{self.action_key}] {self.entity_type}:{self.entity_id}'


class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=500)
    mime_type = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50, help_text='e.g. order_payment, catalog_img')
    entity_id = models.CharField(max_length=36)
    uploaded_by = models.CharField(max_length=36, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'assets'
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
        ]

    def __str__(self):
        return f'{self.entity_type}:{self.entity_id} – {self.file_name}'


class SecureLinkType(models.TextChoices):
    FORM_FILL = 'form_fill', 'Form Fill (Details Questionnaire)'
    SCRIPT_REVIEW = 'script_review', 'Script Review'


class SecureLink(models.Model):
    """Token-based links sent in emails for secure access without login."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True)
    link_type = models.CharField(max_length=20, choices=SecureLinkType.choices)
    order_id = models.CharField(max_length=20, db_index=True)
    target_email = models.EmailField(max_length=150)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'secure_links'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['order_id']),
        ]

    def __str__(self):
        return f'[{self.link_type}] Order:{self.order_id} – {"USED" if self.is_used else "ACTIVE"}'
