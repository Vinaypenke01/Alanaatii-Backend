"""
Orders services — core business logic for the order lifecycle.
"""
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied

from .models import Order, Transaction, ScriptVersion, OrderStatusHistory, Refund, OrderStatus
from apps.notifications.services import create_notification, log_audit, generate_secure_link
from utils.email import (
    send_order_placed_email, send_payment_verified_email, send_payment_rejected_email,
    send_details_reminder_email, send_script_ready_email, send_revision_submitted_email,
    send_out_for_delivery_email, send_delivered_email,
    send_writer_assignment_email, send_writer_revision_email,
    send_admin_new_order_email, send_admin_assignment_rejected_email, send_admin_script_approved_email,
)

logger = logging.getLogger('apps')


def _record_status_change(order, old_status, new_status, changed_by_id=None, role='system', note=None):
    OrderStatusHistory.objects.create(
        order=order,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=str(changed_by_id) if changed_by_id else None,
        changed_by_role=role,
        note=note,
    )


def get_order_or_404(order_id: str) -> Order:
    try:
        return Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise NotFound(f'Order {order_id} not found.')


def calculate_order_total(data: dict) -> dict:
    """
    Pricing engine — computes full order breakdown.
    Returns a dict with all price components and total.
    """
    from apps.admin_ops.services import get_pincode_fee, get_early_fee, validate_coupon
    from apps.catalog.models import CatalogItem

    product_type = data.get('product_type')
    breakdown = {
        'base_price': Decimal('0'),
        'style_price': Decimal('0'),
        'box_price': Decimal('0'),
        'gift_price': Decimal('0'),
        'express_price': Decimal('0'),
        'pincode_fee': Decimal('0'),
        'early_fee': Decimal('0'),
        'discount_amt': Decimal('0'),
    }

    def get_price(item_id):
        if not item_id:
            return Decimal('0')
        try:
            return CatalogItem.objects.get(id=item_id, is_active=True).price
        except CatalogItem.DoesNotExist:
            return Decimal('0')

    if product_type == 'script':
        breakdown['base_price'] = get_price(data.get('script_package'))
        if data.get('express_script'):
            from apps.admin_ops.models import SiteSettings
            breakdown['express_price'] = Decimal('100')  # default express fee

    elif product_type == 'letterPaper':
        paper_price = get_price(data.get('paper'))
        qty = int(data.get('paper_quantity', 1))
        breakdown['base_price'] = paper_price * qty
        breakdown['pincode_fee'] = get_pincode_fee(data.get('pincode', ''))

    else:
        breakdown['base_price'] = get_price(data.get('letter_theme'))
        breakdown['style_price'] = get_price(data.get('text_style'))
        breakdown['box_price'] = get_price(data.get('box'))
        gift_id = data.get('gift')
        if gift_id:
            try:
                gift = CatalogItem.objects.get(id=gift_id, is_active=True)
                # 'custom' gifts are free (handled via WhatsApp separately)
                if gift.title.lower() != 'custom':
                    breakdown['gift_price'] = gift.price
            except CatalogItem.DoesNotExist:
                pass
        breakdown['early_fee'] = get_early_fee(data.get('delivery_date'))
        breakdown['pincode_fee'] = get_pincode_fee(data.get('pincode', ''))

    # Coupon discount
    coupon_code = data.get('coupon_code')
    subtotal = sum(breakdown.values())
    if coupon_code:
        try:
            discount = validate_coupon(coupon_code, subtotal)
            breakdown['discount_amt'] = discount
        except Exception:
            pass

    total = max(Decimal('0'), subtotal - breakdown['discount_amt'])
    breakdown['total_amount'] = total
    return breakdown


@db_transaction.atomic
def create_order(data: dict, user=None) -> Order:
    """Create a new order with pricing calculation."""
    from apps.admin_ops.models import Coupon, SiteSettings

    breakdown = calculate_order_total(data)

    # Resolve coupon FK
    coupon_obj = None
    coupon_code = data.get('coupon_code')
    if coupon_code:
        try:
            coupon_obj = Coupon.objects.get(code__iexact=coupon_code, is_active=True)
            coupon_obj.current_uses += 1
            coupon_obj.save(update_fields=['current_uses'])
        except Coupon.DoesNotExist:
            pass

    order = Order(
        product_type=data['product_type'],
        customer_name=data['customer_name'],
        customer_country_code=data.get('customer_country_code', '+91'),
        customer_phone=data['customer_phone'],
        customer_email=data['customer_email'],
        recipient_name=data.get('recipient_name'),
        recipient_country_code=data.get('recipient_country_code', '+91'),
        recipient_phone=data.get('recipient_phone'),
        primary_contact=data.get('primary_contact'),
        relation=data.get('relation'),
        message_content=data.get('message_content'),
        special_notes=data.get('special_notes'),
        express_script=data.get('express_script', False),
        address=data.get('address'),
        city=data.get('city'),
        pincode=data.get('pincode'),
        delivery_date=data.get('delivery_date'),
        paper_quantity=data.get('paper_quantity', 1),
        custom_letter_length=data.get('custom_letter_length'),
        coupon=coupon_obj,
        user=user,
        **{k: v for k, v in breakdown.items()},
    )

    # Set FK catalog items
    for field in ['letter_theme', 'text_style', 'paper', 'box', 'gift', 'script_package']:
        val = data.get(field)
        if val:
            setattr(order, f'{field}_id', val)

    order.save()

    # Create transaction record (payment pending)
    screenshot_url = data.get('payment_screenshot', '')
    Transaction.objects.create(
        order=order,
        amount=breakdown['total_amount'],
        screenshot_url=screenshot_url,
        status='pending',
    )

    # Notify customer and admin
    try:
        send_order_placed_email(order)
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'support@alanaatii.com')
        send_admin_new_order_email(admin_email, order)
    except Exception as e:
        logger.error(f'Email failed for new order {order.id}: {e}')

    create_notification(
        target_id=str(user.id) if user else order.customer_email,
        role='user',
        ntype='payment',
        title='Order Received',
        message=f'Your order {order.id} has been placed. Payment is pending verification.',
        order_id=order.id,
    )

    logger.info(f'Order created: {order.id} for {order.customer_email}')
    return order


@db_transaction.atomic
def verify_payment(transaction_id: str, bank_txn_id: str, admin) -> Order:
    """Admin verifies payment — advances order to awaiting_details or order_placed."""
    from apps.admin_ops.models import SiteSettings

    try:
        txn = Transaction.objects.select_related('order').get(id=transaction_id)
    except Transaction.DoesNotExist:
        raise NotFound('Transaction not found.')

    if txn.status == 'verified':
        raise ValidationError('Payment already verified.')

    order = txn.order
    old_status = order.status

    txn.status = 'verified'
    txn.bank_transaction_id = bank_txn_id
    txn.verified_by = admin
    txn.save(update_fields=['status', 'bank_transaction_id', 'verified_by', 'updated_at'])

    # Determine next status
    # letterPaper never needs a questionnaire -> ORDER_PLACED
    # others: if answers missing -> AWAITING_DETAILS, else -> ORDER_PLACED
    if order.product_type == 'letterPaper':
        new_status = OrderStatus.ORDER_PLACED
    elif not order.user_answers:
        new_status = OrderStatus.AWAITING_DETAILS
    else:
        new_status = OrderStatus.ORDER_PLACED

    order.status = new_status
    order.save(update_fields=['status'])
    _record_status_change(order, old_status, new_status, changed_by_id=admin.id, role='admin', note='Payment verified')

    log_audit(str(admin.id), 'admin', 'PAYMENT_VERIFIED', 'ORDER', order.id,
              {'old_status': old_status, 'new_status': new_status})

    try:
        send_payment_verified_email(order)
        if new_status == OrderStatus.AWAITING_DETAILS:
            link = generate_secure_link(order.id, 'form_fill', order.customer_email)
            send_details_reminder_email(order, link)
    except Exception as e:
        logger.error(f'Email failed for payment verification {order.id}: {e}')

    create_notification(
        target_id=str(order.user.id) if order.user else order.customer_email,
        role='user',
        ntype='payment',
        title='Payment Verified!',
        message=f'Your payment for order {order.id} has been verified.',
        order_id=order.id,
    )

    # Auto-assign if order_placed and setting enabled (only for script-based products)
    if new_status == OrderStatus.ORDER_PLACED and order.product_type != 'letterPaper':
        settings = SiteSettings.get()
        if settings.auto_assign_writers:
            try:
                auto_assign_writer(order.id, admin)
            except Exception as e:
                logger.warning(f'Auto-assign failed for {order.id}: {e}')

    return order


@db_transaction.atomic
def reject_payment(transaction_id: str, reason: str, admin) -> Order:
    """Admin rejects payment screenshot."""
    try:
        txn = Transaction.objects.select_related('order').get(id=transaction_id)
    except Transaction.DoesNotExist:
        raise NotFound('Transaction not found.')

    order = txn.order
    old_status = order.status

    txn.status = 'rejected'
    txn.notes = reason
    txn.verified_by = admin
    txn.save(update_fields=['status', 'notes', 'verified_by', 'updated_at'])

    order.status = OrderStatus.PAYMENT_REJECTED
    order.save(update_fields=['status'])
    _record_status_change(order, old_status, OrderStatus.PAYMENT_REJECTED, admin.id, 'admin', reason)

    log_audit(str(admin.id), 'admin', 'PAYMENT_REJECTED', 'ORDER', order.id, {'reason': reason})

    try:
        send_payment_rejected_email(order, reason)
    except Exception as e:
        logger.error(f'Email failed for payment rejection {order.id}: {e}')

    create_notification(
        target_id=str(order.user.id) if order.user else order.customer_email,
        role='user',
        ntype='payment',
        title='Payment Not Verified',
        message=f'Your payment for order {order.id} could not be verified. Reason: {reason}',
        order_id=order.id,
    )
    return order


@db_transaction.atomic
def submit_questionnaire(order_id: str, answers: list, user) -> Order:
    """Customer submits relationship questionnaire — unlocks writer assignment."""
    from apps.admin_ops.models import SiteSettings

    order = get_order_or_404(order_id)

    if order.status != OrderStatus.AWAITING_DETAILS:
        raise ValidationError('Order is not waiting for details.')

    if order.user and order.user != user:
        raise PermissionDenied('This order does not belong to you.')

    old_status = order.status
    order.user_answers = answers
    order.status = OrderStatus.ORDER_PLACED
    order.save(update_fields=['user_answers', 'status'])

    _record_status_change(order, old_status, OrderStatus.ORDER_PLACED, user.id, 'user', 'Questionnaire submitted')

    settings = SiteSettings.get()
    if settings.auto_assign_writers:
        try:
            auto_assign_writer(order_id, None)
        except Exception as e:
            logger.warning(f'Auto-assign failed after questionnaire for {order_id}: {e}')

    return order


@db_transaction.atomic
def auto_assign_writer(order_id: str, admin=None) -> 'WriterAssignment':
    """
    Least-Loaded algorithm: find the active writer with fewest accepted assignments.
    """
    from apps.accounts.models import Writer
    from apps.writers.models import WriterAssignment
    from django.db.models import Count, Q

    order = get_order_or_404(order_id)

    # Find active writer with least current accepted jobs
    writer = (
        Writer.objects
        .filter(status='active', is_active=True)
        .annotate(active_jobs=Count('assignments', filter=Q(assignments__status='accepted')))
        .order_by('active_jobs')
        .first()
    )

    if not writer:
        logger.error(f'No active writers available for order {order_id}')
        raise ValidationError('No active writers available for assignment.')

    assignment = WriterAssignment.objects.create(
        order=order,
        writer=writer,
        status='pending',
        created_by=admin,
    )

    old_status = order.status
    order.status = OrderStatus.ASSIGNED_TO_WRITER
    order.writer = writer
    order.assigned_at = timezone.now()
    order.save(update_fields=['status', 'writer', 'assigned_at'])
    _record_status_change(order, old_status, OrderStatus.ASSIGNED_TO_WRITER,
                          str(admin.id) if admin else None, 'system' if not admin else 'admin',
                          f'Auto-assigned to writer {writer.full_name}')

    try:
        send_writer_assignment_email(writer, order)
    except Exception as e:
        logger.error(f'Email failed for writer assignment {order_id}: {e}')

    create_notification(
        target_id=str(writer.id),
        role='writer',
        ntype='assignment',
        title='New Assignment',
        message=f'You have been assigned order {order.id}. Please accept or decline.',
        order_id=order.id,
    )

    logger.info(f'Order {order_id} assigned to writer {writer.email}')
    return assignment


@db_transaction.atomic
def reassign_order(order_id: str, exclude_writer_id: str, admin) -> 'WriterAssignment':
    """Admin manually re-assigns order, excluding the writer who declined."""
    from apps.accounts.models import Writer
    from apps.writers.models import WriterAssignment
    from django.db.models import Count, Q

    order = get_order_or_404(order_id)

    writer = (
        Writer.objects
        .filter(status='active', is_active=True)
        .exclude(id=exclude_writer_id)
        .annotate(active_jobs=Count('assignments', filter=Q(assignments__status='accepted')))
        .order_by('active_jobs')
        .first()
    )

    if not writer:
        raise ValidationError('No other active writers available.')

    assignment = WriterAssignment.objects.create(
        order=order, writer=writer, status='pending', created_by=admin,
    )

    old_status = order.status
    order.status = OrderStatus.ASSIGNED_TO_WRITER
    order.writer = writer
    order.assigned_at = timezone.now()
    order.save(update_fields=['status', 'writer', 'assigned_at'])
    _record_status_change(order, old_status, OrderStatus.ASSIGNED_TO_WRITER, admin.id, 'admin', 'Reassigned')

    try:
        send_writer_assignment_email(writer, order)
    except Exception as e:
        logger.error(f'Reassign email failed for {order_id}: {e}')

    return assignment


@db_transaction.atomic
def submit_script(order_id: str, content: str, writer_note: str, writer) -> ScriptVersion:
    """Writer submits a script draft — creates ScriptVersion, advances to customer_review."""
    order = get_order_or_404(order_id)

    if str(order.writer_id) != str(writer.id):
        raise PermissionDenied('You are not assigned to this order.')

    # Auto-increment version
    last_version = order.script_versions.order_by('-version_num').first()
    version_num = (last_version.version_num + 1) if last_version else 1

    script_version = ScriptVersion.objects.create(
        order=order, writer=writer,
        version_num=version_num, content=content, writer_note=writer_note,
    )

    old_status = order.status
    order.status = OrderStatus.CUSTOMER_REVIEW
    order.submitted_at = order.submitted_at or timezone.now()
    order.save(update_fields=['status', 'submitted_at'])
    _record_status_change(order, old_status, OrderStatus.CUSTOMER_REVIEW, writer.id, 'writer', f'Script v{version_num} submitted')

    # Delete draft after submission
    from apps.writers.models import WriterDraft
    WriterDraft.objects.filter(order=order, writer=writer).delete()

    try:
        link = generate_secure_link(order.id, 'script_review', order.customer_email)
        send_script_ready_email(order, link)
    except Exception as e:
        logger.error(f'Script ready email failed for {order_id}: {e}')

    create_notification(
        target_id=str(order.user.id) if order.user else order.customer_email,
        role='user',
        ntype='script',
        title='Your Script is Ready!',
        message=f'The writer has completed your script for order {order.id}. Please review it.',
        order_id=order.id,
    )
    return script_version


@db_transaction.atomic
def approve_script(order_id: str, user) -> Order:
    """Customer approves the script — advances to approved."""
    from apps.admin_ops.models import SiteSettings

    order = get_order_or_404(order_id)

    if order.status not in [OrderStatus.CUSTOMER_REVIEW, OrderStatus.REVISION_REQUESTED]:
        raise ValidationError('Order is not in review state.')

    if order.user and order.user != user:
        raise PermissionDenied('This order does not belong to you.')

    # Copy latest script content to order
    latest = order.script_versions.order_by('-version_num').first()
    if latest:
        order.script_content = latest.content

    old_status = order.status
    order.status = OrderStatus.APPROVED
    order.approved_at = timezone.now()
    order.save(update_fields=['status', 'approved_at', 'script_content'])
    _record_status_change(order, old_status, OrderStatus.APPROVED, user.id, 'user', 'Customer approved script')

    try:
        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'support@alanaatii.com')
        send_admin_script_approved_email(admin_email, order)
    except Exception as e:
        logger.error(f'Script approved email failed for {order_id}: {e}')

    return order


@db_transaction.atomic
def request_revision(order_id: str, feedback: str, user) -> Order:
    """Customer requests a revision — notifies writer."""
    order = get_order_or_404(order_id)

    if order.status != OrderStatus.CUSTOMER_REVIEW:
        raise ValidationError('Order is not in customer review state.')

    if order.user and order.user != user:
        raise PermissionDenied('This order does not belong to you.')

    old_status = order.status
    order.status = OrderStatus.REVISION_REQUESTED
    order.revision_note = feedback
    order.save(update_fields=['status', 'revision_note'])
    _record_status_change(order, old_status, OrderStatus.REVISION_REQUESTED, user.id, 'user', feedback)

    if order.writer:
        try:
            send_writer_revision_email(order.writer, order)
        except Exception as e:
            logger.error(f'Revision email failed for {order_id}: {e}')

        create_notification(
            target_id=str(order.writer_id),
            role='writer',
            ntype='revision',
            title='Revision Requested',
            message=f'Customer has requested changes for order {order.id}.',
            order_id=order.id,
        )
    return order


@db_transaction.atomic
def admin_update_order_status(order_id: str, new_status: str, admin, note: str = None, extra_data: dict = None) -> Order:
    """Generic admin order status update with validation."""
    order = get_order_or_404(order_id)
    old_status = order.status

    update_fields = ['status']
    order.status = new_status

    if extra_data:
        for field, val in extra_data.items():
            if val is not None:
                setattr(order, field, val)
                if field not in update_fields:
                    update_fields.append(field)

    if note:
        # If internal_notes is passed in extra_data, it's already set.
        pass

    # Auto-set timestamps
    if new_status == OrderStatus.OUT_FOR_DELIVERY:
        order.shipped_at = timezone.now()
        update_fields.append('shipped_at')

    order.save(update_fields=update_fields)
    _record_status_change(order, old_status, new_status, admin.id, 'admin', note)
    log_audit(str(admin.id), 'admin', 'ORDER_STATUS_UPDATED', 'ORDER', order.id,
              {'old': old_status, 'new': new_status})

    # Trigger delivery emails
    try:
        if new_status == OrderStatus.OUT_FOR_DELIVERY:
            send_out_for_delivery_email(order)
        elif new_status == OrderStatus.DELIVERED:
            send_delivered_email(order)
    except Exception as e:
        logger.error(f'Status update email failed for {order_id}: {e}')

    return order


@db_transaction.atomic
def cancel_order(order_id: str, requester, role: str = 'user') -> Order:
    """Cancel an order. Blocked once writer has accepted."""
    order = get_order_or_404(order_id)

    if not order.can_cancel:
        raise ValidationError('This order cannot be cancelled once the writer has accepted it.')

    old_status = order.status
    order.status = OrderStatus.CANCELLED
    order.save(update_fields=['status'])
    _record_status_change(order, old_status, OrderStatus.CANCELLED,
                          str(requester.id), role, 'Order cancelled')
    log_audit(str(requester.id), role, 'ORDER_CANCELLED', 'ORDER', order.id, {})
    return order


@db_transaction.atomic
def process_refund(order_id: str, amount: Decimal, reason: str, admin) -> Refund:
    """Create and process a refund record."""
    order = get_order_or_404(order_id)

    refund = Refund.objects.create(
        order=order, amount=amount, reason=reason,
        status='pending', processed_by=admin,
    )

    order.status = OrderStatus.REFUNDED
    order.save(update_fields=['status'])
    log_audit(str(admin.id), 'admin', 'REFUND_CREATED', 'ORDER', order.id,
              {'amount': str(amount), 'reason': reason})
    return refund


def resend_order_notification(order_id: str, admin):
    """Manually re-trigger the email based on current order status."""
    order = get_order_or_404(order_id)
    
    if order.status == OrderStatus.AWAITING_DETAILS:
        link = generate_secure_link(order.id, 'form_fill', order.customer_email)
        send_details_reminder_email(order, link)
    elif order.status == OrderStatus.SCRIPT_READY:
        send_script_ready_email(order)
    elif order.status == OrderStatus.OUT_FOR_DELIVERY:
        send_out_for_delivery_email(order)
    elif order.status == OrderStatus.DELIVERED:
        send_delivered_email(order)
    elif order.status == OrderStatus.PAYMENT_VERIFIED:
        send_payment_verified_email(order)
    elif order.status == OrderStatus.PAYMENT_REJECTED:
        send_payment_rejected_email(order)
    
    log_audit(str(admin.id), 'admin', 'NOTIFICATION_RESENT', 'ORDER', order.id, {'status': order.status})
