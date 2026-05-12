"""
Email sending utility for Alanaatii Backend.
Emails are sent asynchronously using background threads to prevent API delays.
"""
import logging
import threading
import resend
from django.conf import settings

logger = logging.getLogger('apps')

# Configure Resend
resend.api_key = settings.RESEND_API_KEY

FRONTEND_URL = settings.FRONTEND_URL


def send_email(to: str, subject: str, text_body: str, html_body: str = None):
    """
    Send a single email in the background via Resend API.
    """
    thread = threading.Thread(
        target=_send_email_sync,
        args=(to, subject, text_body, html_body)
    )
    thread.start()


def _send_email_sync(to: str, subject: str, text_body: str, html_body: str = None):
    """
    Synchronous email sending via Resend SDK.
    """
    try:
        params = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": to,
            "subject": subject,
            "text": text_body,
        }
        if html_body:
            params["html"] = html_body
            
        r = resend.Emails.send(params)
        logger.info(f'Email sent via Resend to {to}: {subject} | ID: {r.get("id")}')
    except Exception as e:
        # Log full error for debugging
        logger.error(f'Resend API Error for {to}: {str(e)}')
        print(f'❌ Resend Error: {str(e)}')


# ─── Helper ───────────────────────────────────────────────────────────────────

def _get_product_summary(order):
    """Generates a text summary of the product configuration."""
    summary = []
    if order.product_type == 'letterPaper':
        if order.paper:
            summary.append(f"Paper Selection: {order.paper.title}")
        summary.append(f"Sheet Quantity: {order.paper_quantity}")
    else:
        if order.letter_theme:
            summary.append(f"Letter Theme: {order.letter_theme.title}")
        if order.text_style:
            summary.append(f"Calligraphy Style: {order.text_style.title}")
        if order.box:
            summary.append(f"Luxury Box: {order.box.title}")
        if order.gift:
            summary.append(f"Gift Add-on: {order.gift.title}")
    
    if not summary:
        return "Standard Configuration"
    return "\n".join([f"• {item}" for item in summary])


# ─── Customer Emails ──────────────────────────────────────────────────────────

def send_order_placed_email(order):
    """Notify customer that their order was received and payment is pending verification."""
    product_details = _get_product_summary(order)
    subject = f'Order Received – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Thank you for placing your order with Alanaatii!\n\n'
        f'Your Order Details:\n'
        f'-------------------\n'
        f'Order ID: {order.id}\n'
        f'Product: {order.get_product_type_display()}\n'
        f'{product_details}\n'
        f'Total Amount: ₹{order.total_amount}\n\n'
        f'Our admin team will verify your payment and update you shortly.\n'
        f'You can track your order at: {FRONTEND_URL}/dashboard/orders/{order.id}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_payment_verified_email(order):
    """Notify customer that payment is verified."""
    product_details = _get_product_summary(order)
    
    if order.product_type == 'letterPaper':
        subject = f'Order Confirmed – #{order.id} | Alanaatii'
        action_text = (
            f'Next Step: Our professional artists will now begin processing your order. '
            f'We will notify you once your creation is ready for dispatch.\n\n'
            f'We would love to hear your experience with Alanaatii so far:\n'
            f'{FRONTEND_URL}/submit-review?order={order.id}'
        )
    else:
        subject = f'Payment Verified – #{order.id} | Alanaatii'
        # Dynamic body based on whether details are needed
        if order.status == 'awaiting_details':
            action_text = (
                f'Next Step: Please fill in the required details for your letter so our writer can begin crafting it.\n\n'
                f'Fill Details Here: {FRONTEND_URL}/dashboard/details/{order.id}'
            )
        else:
            action_text = (
                f'Next Step: Our professional artists will now begin processing your order. '
                f'We will notify you once your creation is ready.'
            )

    body = (
        f'Hi {order.customer_name},\n\n'
        f'Great news! Your payment for Order #{order.id} has been verified.\n\n'
        f'Order Summary:\n'
        f'{product_details}\n\n'
        f'{action_text}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_payment_rejected_email(order, reason: str):
    """Notify customer that payment screenshot was rejected."""
    subject = f'Payment Not Verified – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Unfortunately, we could not verify your payment for Order #{order.id}.\n\n'
        f'Reason: {reason}\n\n'
        f'Please upload a valid payment screenshot here:\n'
        f'{FRONTEND_URL}/dashboard/orders/{order.id}\n\n'
        f'If you need help, contact us at {settings.DEFAULT_FROM_EMAIL}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_details_reminder_email(order, secure_link_url: str = None):
    """Remind customer to fill in the relationship questionnaire."""
    subject = f'Action Required: Fill Order Details – #{order.id} | Alanaatii'
    link = secure_link_url or f'{FRONTEND_URL}/dashboard/details/{order.id}'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Your order #{order.id} is waiting for your story!\n\n'
        f'Our writer is ready to begin, but we need a few more details from you to craft the perfect letter.\n\n'
        f'Click here to fill in the details:\n{link}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_script_ready_email(order, secure_link_url: str = None):
    """Notify customer that their script is ready for review."""
    subject = f'Your Letter Script is Ready! – #{order.id} | Alanaatii'
    link = secure_link_url or f'{FRONTEND_URL}/dashboard/orders/{order.id}'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Exciting news! Our writer has completed the script for your letter (Order #{order.id}).\n\n'
        f'Please review it and let us know:\n'
        f'• Approve it — and we will begin writing the physical letter\n'
        f'• Request changes — and our writer will revise it\n\n'
        f'Review your script here:\n{link}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_revision_submitted_email(order):
    """Notify customer that writer submitted a revised script."""
    subject = f'Script Revision Ready – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Your writer has submitted the revised script for Order #{order.id}.\n\n'
        f'Review it here:\n{FRONTEND_URL}/dashboard/orders/{order.id}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_out_for_delivery_email(order):
    """Notify customer their order is out for delivery."""
    subject = f'Your Letter is On Its Way! – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Your luxury letter (Order #{order.id}) has been dispatched!\n\n'
        f'Courier: {order.courier_name or "Our Delivery Partner"}\n'
        f'Tracking ID: {order.tracking_id or "Will be updated shortly"}\n'
        f'Estimated Arrival: {order.est_arrival or "As per schedule"}\n\n'
        f'Track your order: {FRONTEND_URL}/dashboard/orders/{order.id}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


def send_delivered_email(order):
    """Notify customer their order is delivered."""
    subject = f'Delivered with Love – #{order.id} | Alanaatii'
    body = (
        f'Hi {order.customer_name},\n\n'
        f'Your order #{order.id} has been delivered!\n\n'
        f'We hope your letter brings joy to {order.recipient_name}.\n\n'
        f'We would love to hear your feedback:\n'
        f'{FRONTEND_URL}/submit-review?order={order.id}\n\n'
        f'With love,\nTeam Alanaatii'
    )
    send_email(order.customer_email, subject, body)


# ─── Writer Emails ────────────────────────────────────────────────────────────

def send_writer_assignment_email(writer, order):
    """Notify writer of a new assignment."""
    subject = f'New Assignment – Order #{order.id} | Alanaatii'
    body = (
        f'Hi {writer.full_name},\n\n'
        f'You have been assigned a new script writing task!\n\n'
        f'Order ID: {order.id}\n'
        f'Product Type: {order.product_type}\n'
        f'Delivery Date: {order.delivery_date}\n'
        f'Relation: {order.relation or "Not specified"}\n\n'
        f'Please log in to your writer dashboard to accept or decline:\n'
        f'{FRONTEND_URL}/writer/assignments\n\n'
        f'Team Alanaatii'
    )
    send_email(writer.email, subject, body)


def send_writer_revision_email(writer, order):
    """Notify writer of a revision request."""
    subject = f'Revision Requested – Order #{order.id} | Alanaatii'
    body = (
        f'Hi {writer.full_name},\n\n'
        f'The customer has requested a revision for Order #{order.id}.\n\n'
        f'Their feedback:\n{order.revision_note or "Please check your dashboard."}\n\n'
        f'Log in to revise: {FRONTEND_URL}/writer\n\n'
        f'Team Alanaatii'
    )
    send_email(writer.email, subject, body)


def send_writer_payout_email(writer, payout):
    """Notify writer of a new payout."""
    subject = f'Payout Processed – ₹{payout.amount} | Alanaatii'
    body = (
        f'Hi {writer.full_name},\n\n'
        f'Your payout of ₹{payout.amount} has been processed!\n\n'
        f'Reference ID: {payout.reference_id or "N/A"}\n'
        f'Period: {payout.period_start} to {payout.period_end}\n\n'
        f'View your payouts: {FRONTEND_URL}/writer/profile\n\n'
        f'Team Alanaatii'
    )
    send_email(writer.email, subject, body)


# ─── Admin Emails ─────────────────────────────────────────────────────────────

def send_admin_new_order_email(admin_email: str, order):
    """Notify admin of a new order requiring payment verification."""
    subject = f'New Order Pending Payment Verification – #{order.id}'
    body = (
        f'A new order has been placed and requires payment verification.\n\n'
        f'Order ID: {order.id}\n'
        f'Customer: {order.customer_name} ({order.customer_email})\n'
        f'Product: {order.product_type}\n'
        f'Amount: ₹{order.total_amount}\n\n'
        f'Verify Payment: {FRONTEND_URL}/admin/payments\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_admin_assignment_rejected_email(admin_email: str, writer, order, reason: str):
    """Notify admin that writer rejected an assignment."""
    subject = f'Assignment Rejected – Order #{order.id}'
    body = (
        f'Writer {writer.full_name} has declined the assignment for Order #{order.id}.\n\n'
        f'Reason: {reason}\n\n'
        f'Please re-assign: {FRONTEND_URL}/admin/orders\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)


def send_admin_script_approved_email(admin_email: str, order):
    """Notify admin that customer approved the script."""
    subject = f'Script Approved – Order #{order.id} Ready for Physical Writing'
    body = (
        f'The customer has approved the script for Order #{order.id}.\n\n'
        f'Customer: {order.customer_name}\n'
        f'Recipient: {order.recipient_name}\n\n'
        f'Please move the order to Under Writing status:\n'
        f'{FRONTEND_URL}/admin/orders\n\n'
        f'Alanaatii Admin System'
    )
    send_email(admin_email, subject, body)
