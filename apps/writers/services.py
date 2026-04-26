"""
Writers services.
"""
import logging
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound

logger = logging.getLogger('apps')


def get_writer_stats(writer_id: str) -> dict:
    from .models import WriterAssignment, Payout
    active = WriterAssignment.objects.filter(writer_id=writer_id, status='accepted').count()
    completed = WriterAssignment.objects.filter(writer_id=writer_id, status='accepted').filter(
        order__status='delivered'
    ).count()
    pending_payout = Payout.objects.filter(writer_id=writer_id, status='pending').count()
    return {'active_jobs': active, 'completed_jobs': completed, 'pending_payouts': pending_payout}


def accept_assignment(assignment_id: int, writer) -> 'WriterAssignment':
    from .models import WriterAssignment
    from apps.orders.models import Order, OrderStatus
    from apps.orders.models import OrderStatusHistory
    try:
        assignment = WriterAssignment.objects.select_related('order').get(id=assignment_id, writer=writer)
    except WriterAssignment.DoesNotExist:
        raise NotFound('Assignment not found.')
    if assignment.status != 'pending':
        raise ValidationError('This assignment is no longer pending.')
    assignment.status = 'accepted'
    assignment.responded_at = timezone.now()
    assignment.save(update_fields=['status', 'responded_at'])
    order = assignment.order
    old_status = order.status
    order.status = OrderStatus.ACCEPTED_BY_WRITER
    order.save(update_fields=['status'])
    OrderStatusHistory.objects.create(
        order=order, old_status=old_status, new_status=OrderStatus.ACCEPTED_BY_WRITER,
        changed_by_id=str(writer.id), changed_by_role='writer', note='Writer accepted assignment'
    )
    return assignment


def decline_assignment(assignment_id: int, writer, reason: str) -> 'WriterAssignment':
    from .models import WriterAssignment
    from apps.orders.models import Order, OrderStatus, OrderStatusHistory
    from apps.admin_ops.models import SiteSettings
    from apps.notifications.services import create_notification
    from utils.email import send_admin_assignment_rejected_email

    try:
        assignment = WriterAssignment.objects.select_related('order').get(id=assignment_id, writer=writer)
    except WriterAssignment.DoesNotExist:
        raise NotFound('Assignment not found.')
    if assignment.status != 'pending':
        raise ValidationError('This assignment is no longer pending.')

    assignment.status = 'declined'
    assignment.decline_reason = reason
    assignment.responded_at = timezone.now()
    assignment.save(update_fields=['status', 'decline_reason', 'responded_at'])

    order = assignment.order
    old_status = order.status
    order.status = OrderStatus.ASSIGNMENT_REJECTED
    order.save(update_fields=['status'])
    OrderStatusHistory.objects.create(
        order=order, old_status=old_status, new_status=OrderStatus.ASSIGNMENT_REJECTED,
        changed_by_id=str(writer.id), changed_by_role='writer', note=f'Declined: {reason}'
    )

    try:
        settings = SiteSettings.get()
        send_admin_assignment_rejected_email(settings.support_email, writer, order, reason)
    except Exception as e:
        logger.error(f'Decline email failed: {e}')

    create_notification(
        target_id='admin', role='admin', ntype='assignment',
        title='Assignment Declined',
        message=f'Writer {writer.full_name} declined order {order.id}. Reason: {reason}',
        order_id=order.id,
    )
    return assignment


def create_payout(writer_id, amount, period_start, period_end, admin) -> 'Payout':
    from .models import Payout
    from apps.accounts.models import Writer
    from utils.email import send_writer_payout_email
    from apps.notifications.services import create_notification

    try:
        writer = Writer.objects.get(id=writer_id)
    except Writer.DoesNotExist:
        raise NotFound('Writer not found.')

    payout = Payout.objects.create(
        writer=writer, amount=amount, period_start=period_start,
        period_end=period_end, created_by=admin,
    )
    try:
        send_writer_payout_email(writer, payout)
    except Exception as e:
        logger.error(f'Payout email failed: {e}')

    create_notification(
        target_id=str(writer.id), role='writer', ntype='payout',
        title='Payout Issued',
        message=f'Your payout of ₹{amount} has been processed.',
    )
    return payout
