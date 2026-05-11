"""
Admin ops models — business rules, pricing, coupons, settings, support.
"""
import uuid
from django.db import models
from django.utils import timezone


class PricingDayRule(models.Model):
    days_limit = models.IntegerField(unique=True, help_text='e.g. 28 means within 28 days = extra charge')
    extra_charge = models.DecimalField(max_digits=10, decimal_places=2)
    label = models.CharField(max_length=100, blank=True, help_text='Human readable label')
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='pricing_day_rules'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'pricing_day_rules'
        ordering = ['days_limit']

    def __str__(self):
        return f'Within {self.days_limit} days → +₹{self.extra_charge}'


class PincodeRule(models.Model):
    zip_prefix = models.CharField(max_length=10, unique=True, help_text='First 3-6 digits of pincode')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    region_name = models.CharField(max_length=100, blank=True, help_text='e.g. Hyderabad, Mumbai')
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='pincode_rules'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'pincode_rules'
        ordering = ['zip_prefix']

    def __str__(self):
        return f'{self.zip_prefix} ({self.region_name}) → ₹{self.delivery_fee}'


class MandatoryQuestion(models.Model):
    question_text = models.TextField()
    display_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='mandatory_questions'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'mandatory_questions'
        ordering = ['display_order']

    def __str__(self):
        return self.question_text[:60]


class DiscountType(models.TextChoices):
    PERCENTAGE = 'percentage', 'Percentage'
    FLAT = 'flat', 'Flat Amount'


class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    discount_val = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(max_length=15, choices=DiscountType.choices)
    max_uses = models.IntegerField(null=True, blank=True, help_text='Null = unlimited')
    current_uses = models.IntegerField(default=0)
    valid_from = models.DateField()
    valid_until = models.DateField()
    min_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='coupons'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.discount_type}: {self.discount_val})'


class SiteSettings(models.Model):
    """Singleton settings table — always id=1."""
    master_upi_id = models.CharField(max_length=100)
    support_email = models.EmailField(max_length=150)
    support_whatsapp = models.CharField(max_length=20)
    maintenance_mode = models.BooleanField(default=False)
    auto_assign_writers = models.BooleanField(default=True)
    default_delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    min_delivery_lead_days = models.IntegerField(default=7)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'site_settings'
        verbose_name = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={
            'master_upi_id': 'alanaatii@upi',
            'support_email': 'support@alanaatii.com',
            'support_whatsapp': '+91-0000000000',
            'default_delivery_fee': 100,
            'min_delivery_lead_days': 7,
        })
        return obj

    def __str__(self):
        return f'Site Settings (UPI: {self.master_upi_id})'


class SupportMessageStatus(models.TextChoices):
    NEW = 'new', 'New'
    READ = 'read', 'Read'
    RESPONDED = 'responded', 'Responded'


class SupportMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150)
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    status = models.CharField(max_length=15, choices=SupportMessageStatus.choices, default=SupportMessageStatus.NEW)
    admin_reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'support_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.email}) – {self.status}'
