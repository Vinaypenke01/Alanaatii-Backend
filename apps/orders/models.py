"""
Orders models — the core of the Alanaatii platform.
Implements the full 15-status order lifecycle.
"""
import uuid
from django.db import models
from django.utils import timezone


class ProductType(models.TextChoices):
    SCRIPT = 'script', 'Only Script'
    LETTER_PAPER = 'letterPaper', 'Only Letter Paper'
    LETTER = 'letter', 'Only Letter'
    LETTER_BOX = 'letterBox', 'Letter + Box'
    LETTER_BOX_GIFT = 'letterBoxGift', 'Letter + Box + Gift'


class OrderStatus(models.TextChoices):
    PAYMENT_PENDING = 'payment_pending', 'Payment Pending'
    PAYMENT_REJECTED = 'payment_rejected', 'Payment Rejected'
    AWAITING_DETAILS = 'awaiting_details', 'Awaiting Customer Details'
    ORDER_PLACED = 'order_placed', 'Order Placed'
    ASSIGNED_TO_WRITER = 'assigned_to_writer', 'Assigned to Writer'
    ASSIGNMENT_REJECTED = 'assignment_rejected', 'Assignment Rejected'
    ACCEPTED_BY_WRITER = 'accepted_by_writer', 'Accepted by Writer'
    SCRIPT_SUBMITTED = 'script_submitted', 'Script Submitted'
    CUSTOMER_REVIEW = 'customer_review', 'Customer Review'
    REVISION_REQUESTED = 'revision_requested', 'Revision Requested'
    APPROVED = 'approved', 'Script Approved'
    UNDER_WRITING = 'under_writing', 'Under Writing'
    OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'
    REFUNDED = 'refunded', 'Refunded'


class PrimaryContact(models.TextChoices):
    SENDER = 'sender', 'Sender'
    RECIPIENT = 'recipient', 'Recipient'


class Order(models.Model):
    id = models.CharField(
        max_length=20, primary_key=True,
        help_text='Human-readable order ID e.g. ORDER-2000'
    )
    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    product_type = models.CharField(max_length=20, choices=ProductType.choices)

    # Catalog selections (FK to catalog items)
    letter_theme = models.ForeignKey(
        'catalog.CatalogItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='letter_theme_orders', limit_choices_to={'category': 'letter_theme'}
    )
    text_style = models.ForeignKey(
        'catalog.CatalogItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='style_orders', limit_choices_to={'category': 'style'}
    )
    paper = models.ForeignKey(
        'catalog.CatalogItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='paper_orders', limit_choices_to={'category': 'paper'}
    )
    paper_quantity = models.IntegerField(default=1)
    box = models.ForeignKey(
        'catalog.CatalogItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='box_orders', limit_choices_to={'category': 'box'}
    )
    gift = models.ForeignKey(
        'catalog.CatalogItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='gift_orders', limit_choices_to={'category': 'gift'}
    )
    script_package = models.ForeignKey(
        'catalog.CatalogItem', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='package_orders', limit_choices_to={'category': 'package'}
    )

    # Order status & lifecycle
    status = models.CharField(max_length=25, choices=OrderStatus.choices, default=OrderStatus.PAYMENT_PENDING)

    # Sender details
    customer_name = models.CharField(max_length=100)
    customer_country_code = models.CharField(max_length=10, default='+91')
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(max_length=150)

    # Recipient details
    recipient_name = models.CharField(max_length=100, blank=True, null=True)
    recipient_country_code = models.CharField(max_length=10, default='+91', blank=True, null=True)
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)
    primary_contact = models.CharField(max_length=10, choices=PrimaryContact.choices, blank=True, null=True)

    # Letter content
    relation = models.CharField(max_length=50, blank=True, null=True)
    message_content = models.TextField(blank=True, null=True)
    special_notes = models.TextField(blank=True, null=True)
    express_script = models.BooleanField(default=False)
    custom_letter_length = models.CharField(max_length=50, blank=True, null=True, help_text='Custom length/quantity if required')
    pricing_unit = models.CharField(max_length=10, default='page', help_text='Unit used for calculation (page/feet)')
    unit_price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Price per unit at time of order')

    # Delivery details
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    delivery_date = models.DateField(null=True, blank=True)

    # Payment
    payment_ss = models.CharField(max_length=500, blank=True, null=True, help_text='Payment screenshot URL')
    coupon = models.ForeignKey(
        'admin_ops.Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )

    # Pricing breakdown
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    style_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    box_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gift_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    express_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pincode_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    early_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Script content
    script_content = models.TextField(blank=True, null=True, help_text='Final approved script text')
    revision_note = models.TextField(blank=True, null=True, help_text='Customer feedback for revision')
    internal_notes = models.TextField(blank=True, null=True, help_text='Private admin/writer notes (not visible to customer)')

    # Relationship questionnaire answers
    user_answers = models.JSONField(default=list, help_text='Answers to mandatory relationship questions')

    # Writer assignment
    writer = models.ForeignKey(
        'accounts.Writer', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders'
    )

    # Delivery tracking
    tracking_id = models.CharField(max_length=100, blank=True, null=True)
    courier_name = models.CharField(max_length=50, blank=True, null=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    est_arrival = models.DateField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    assigned_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer_email']),
            models.Index(fields=['writer']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'{self.id} – {self.customer_name} ({self.status})'

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self._generate_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_id():
        """Generate a sequential human-readable order ID starting from ORDER-2000."""
        prefix = 'ORDER-'
        # Fetch existing IDs with this prefix to find the max number
        existing_ids = Order.objects.filter(id__startswith=prefix).values_list('id', flat=True)
        
        max_num = 1999
        for oid in existing_ids:
            try:
                num_str = oid[len(prefix):]
                num = int(num_str)
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                continue
        
        return f'{prefix}{max_num + 1}'

    @property
    def can_cancel(self):
        """Order can be cancelled if writer has not yet accepted."""
        blocked_statuses = [
            OrderStatus.ACCEPTED_BY_WRITER,
            OrderStatus.SCRIPT_SUBMITTED,
            OrderStatus.CUSTOMER_REVIEW,
            OrderStatus.APPROVED,
            OrderStatus.UNDER_WRITING,
            OrderStatus.OUT_FOR_DELIVERY,
            OrderStatus.DELIVERED,
        ]
        return self.status not in blocked_statuses


class TransactionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Verification'
    VERIFIED = 'verified', 'Verified'
    REJECTED = 'rejected', 'Rejected'


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    screenshot_url = models.CharField(max_length=500)
    status = models.CharField(max_length=10, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    bank_transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text='Bank/UPI reference ID entered by Admin')
    notes = models.TextField(blank=True, null=True, help_text='Rejection reason or admin note')
    verified_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_transactions'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f'TX-{self.id} [{self.status}] ₹{self.amount}'


class ScriptVersion(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='script_versions')
    writer = models.ForeignKey(
        'accounts.Writer', on_delete=models.SET_NULL, null=True, related_name='script_versions'
    )
    version_num = models.IntegerField(default=1, help_text='1=initial, 2=first revision, etc.')
    content = models.TextField()
    writer_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'script_versions'
        ordering = ['-version_num']
        unique_together = ('order', 'version_num')
        indexes = [
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f'Script v{self.version_num} – Order {self.order_id}'


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=25, choices=OrderStatus.choices)
    new_status = models.CharField(max_length=25, choices=OrderStatus.choices)
    changed_by_id = models.CharField(max_length=36, blank=True, null=True)
    changed_by_role = models.CharField(max_length=10, default='system')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'order_status_history'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_id}: {self.old_status} → {self.new_status}'


class RefundStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    REJECTED = 'rejected', 'Rejected'


class Refund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=RefundStatus.choices, default=RefundStatus.PENDING)
    processed_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'refunds'
        ordering = ['-created_at']

    def __str__(self):
        return f'Refund [{self.status}] ₹{self.amount} – Order {self.order_id}'
