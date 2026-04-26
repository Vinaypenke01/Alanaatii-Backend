"""
Writers models — assignments, drafts, payouts.
"""
import uuid
from django.db import models
from django.utils import timezone


class AssignmentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Response'
    ACCEPTED = 'accepted', 'Accepted'
    DECLINED = 'declined', 'Declined'


class WriterAssignment(models.Model):
    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, related_name='assignments'
    )
    writer = models.ForeignKey(
        'accounts.Writer', on_delete=models.CASCADE, related_name='assignments'
    )
    status = models.CharField(max_length=10, choices=AssignmentStatus.choices, default=AssignmentStatus.PENDING)
    decline_reason = models.TextField(blank=True, null=True)
    assigned_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_assignments'
    )

    class Meta:
        db_table = 'writer_assignments'
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['writer', 'status']),
            models.Index(fields=['order']),
        ]

    def __str__(self):
        return f'Assignment: Order {self.order_id} → Writer {self.writer_id} [{self.status}]'


class WriterDraft(models.Model):
    """Auto-save draft. One draft per order per writer — composite PK via unique_together."""
    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE, related_name='drafts'
    )
    writer = models.ForeignKey(
        'accounts.Writer', on_delete=models.CASCADE, related_name='drafts'
    )
    draft_content = models.TextField()
    last_saved_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'writer_drafts'
        unique_together = ('order', 'writer')

    def __str__(self):
        return f'Draft: Order {self.order_id} by Writer {self.writer_id}'


class PayoutStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSED = 'processed', 'Processed'
    FAILED = 'failed', 'Failed'


class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    writer = models.ForeignKey(
        'accounts.Writer', on_delete=models.CASCADE, related_name='payouts'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    reference_id = models.CharField(max_length=100, blank=True, null=True, help_text='Bank/UPI reference')
    period_start = models.DateField()
    period_end = models.DateField()
    created_by = models.ForeignKey(
        'accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_payouts'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'payouts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['writer', 'status']),
        ]

    def __str__(self):
        return f'Payout [{self.status}] ₹{self.amount} – Writer {self.writer_id}'
